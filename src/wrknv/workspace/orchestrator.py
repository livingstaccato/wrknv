#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Workspace Task Orchestration
============================
Execute tasks across multiple repositories in workspace."""

from __future__ import annotations

import asyncio
from fnmatch import fnmatch
from pathlib import Path

from attrs import define, field
from provide.foundation import logger

from wrknv.tasks.executor import TaskExecutor
from wrknv.tasks.registry import TaskRegistry
from wrknv.tasks.schema import TaskResult

from .discovery import RepoInfo, WorkspaceDiscovery


@define
class WorkspaceTaskResult:
    """Result of running a task across workspace repos."""

    task_name: str
    repo_results: dict[str, TaskResult]  # repo_name -> TaskResult
    total_repos: int
    succeeded: int
    failed: int
    skipped: int
    duration: float

    @property
    def success(self) -> bool:
        """Check if all repos succeeded."""
        return self.failed == 0

    def get_failed_repos(self) -> list[str]:
        """Get list of repo names that failed."""
        return [name for name, result in self.repo_results.items() if not result.success]

    def get_succeeded_repos(self) -> list[str]:
        """Get list of repo names that succeeded."""
        return [name for name, result in self.repo_results.items() if result.success]


@define
class WorkspaceOrchestrator:
    """Orchestrates task execution across workspace repositories."""

    root: Path = field(converter=Path)
    discovery: WorkspaceDiscovery = field(init=False)

    def __attrs_post_init__(self) -> None:
        """Initialize discovery after attrs creates instance."""
        object.__setattr__(self, "discovery", WorkspaceDiscovery(root=self.root))

    def discover_repos(
        self,
        patterns: list[str] | None = None,
        repo_filter: str | None = None,
    ) -> list[RepoInfo]:
        """Discover repositories with optional pattern filtering.

        Args:
            patterns: Discovery patterns (default: ["*"] to find all)
            repo_filter: Additional glob pattern to filter discovered repos

        Returns:
            List of discovered RepoInfo objects
        """
        # Use discovery patterns or default to all
        if patterns is None:
            patterns = ["*"]

        # Discover all repos matching initial patterns
        repos = self.discovery.discover_repos(patterns=patterns)

        # Apply additional filter if provided
        if repo_filter:
            repos = [repo for repo in repos if fnmatch(repo.name or "", repo_filter)]
            logger.info("Filtered repositories", filter=repo_filter, count=len(repos))

        return repos

    async def run_task_sequential(
        self,
        task_name: str,
        repos: list[RepoInfo],
        fail_fast: bool = False,
        env: dict[str, str] | None = None,
    ) -> WorkspaceTaskResult:
        """Run task sequentially across repos with streaming output.

        Args:
            task_name: Name of task to run
            repos: List of repositories to execute in
            fail_fast: Stop on first failure if True
            env: Additional environment variables

        Returns:
            WorkspaceTaskResult with aggregated results
        """
        import time

        start_time = time.time()
        results: dict[str, TaskResult] = {}
        succeeded = 0
        failed = 0
        skipped = 0

        logger.info(
            "Running task sequentially across workspace",
            task=task_name,
            repos=len(repos),
            fail_fast=fail_fast,
        )

        for repo in repos:
            repo_name = repo.name or repo.path.name

            # Print separator for clarity
            logger.info("=" * 80)
            logger.info(f"▶ Running '{task_name}' in {repo_name}", repo=repo_name, task=task_name)
            logger.info("=" * 80)

            try:
                # Load task registry for this repo
                registry = TaskRegistry.from_repo(repo.path)

                # Resolve task (handles _default resolution)
                try:
                    task, task_args = registry.resolve_task(task_name)
                except ValueError:
                    logger.warning(
                        f"Task '{task_name}' not found in {repo_name}",
                        repo=repo_name,
                        task=task_name,
                    )
                    skipped += 1
                    continue

                # Create executor for this repo
                executor = TaskExecutor(
                    repo_path=repo.path,
                    env=env,
                    package_name=repo.name,
                    auto_detect_env=True,
                )

                # Execute with streaming
                result = await executor.execute(task, args=task_args, dry_run=False)
                results[repo_name] = result

                if result.success:
                    succeeded += 1
                    logger.info(
                        f"✓ Task '{task_name}' succeeded in {repo_name}",
                        repo=repo_name,
                        duration=result.duration,
                    )
                else:
                    failed += 1
                    logger.error(
                        f"✗ Task '{task_name}' failed in {repo_name}",
                        repo=repo_name,
                        exit_code=result.exit_code,
                        duration=result.duration,
                    )

                    # Fail-fast: stop on first failure
                    if fail_fast:
                        logger.error("Stopping due to --fail-fast", failed_repo=repo_name)
                        break

            except Exception as e:
                failed += 1
                logger.error(
                    f"Exception running task in {repo_name}",
                    repo=repo_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                # Create minimal task config for error result
                from wrknv.tasks.schema import TaskConfig

                error_task = TaskConfig(name=task_name, run=f"# Error: {e}")
                results[repo_name] = TaskResult(
                    task=error_task,
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    duration=0.0,
                )

                if fail_fast:
                    logger.error("Stopping due to --fail-fast", failed_repo=repo_name)
                    break

        duration = time.time() - start_time

        return WorkspaceTaskResult(
            task_name=task_name,
            repo_results=results,
            total_repos=len(repos),
            succeeded=succeeded,
            failed=failed,
            skipped=skipped,
            duration=duration,
        )

    async def run_task_parallel(
        self,
        task_name: str,
        repos: list[RepoInfo],
        env: dict[str, str] | None = None,
    ) -> WorkspaceTaskResult:
        """Run task in parallel across repos.

        Args:
            task_name: Name of task to run
            repos: List of repositories to execute in
            env: Additional environment variables

        Returns:
            WorkspaceTaskResult with aggregated results

        Note:
            Parallel mode runs all repos concurrently. Output from different
            repos may be interleaved. Use sequential mode for clearer output.
        """
        import time

        start_time = time.time()

        logger.info(
            "Running task in parallel across workspace",
            task=task_name,
            repos=len(repos),
        )

        async def run_in_repo(repo: RepoInfo) -> tuple[str, TaskResult | None]:
            """Run task in a single repo."""
            repo_name = repo.name or repo.path.name

            try:
                # Load task registry
                registry = TaskRegistry.from_repo(repo.path)

                # Resolve task (handles _default resolution)
                try:
                    task, task_args = registry.resolve_task(task_name)
                except ValueError:
                    logger.warning(
                        f"Task '{task_name}' not found in {repo_name}",
                        repo=repo_name,
                        task=task_name,
                    )
                    return (repo_name, None)

                # Create executor
                executor = TaskExecutor(
                    repo_path=repo.path,
                    env=env,
                    package_name=repo.name,
                    auto_detect_env=True,
                )

                # Execute
                result = await executor.execute(task, args=task_args, dry_run=False)
                return (repo_name, result)

            except Exception as e:
                logger.error(
                    f"Exception running task in {repo_name}",
                    repo=repo_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                # Return error result
                from wrknv.tasks.schema import TaskConfig

                error_task = TaskConfig(name=task_name, run=f"# Error: {e}")
                error_result = TaskResult(
                    task=error_task,
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    duration=0.0,
                )
                return (repo_name, error_result)

        # Run all repos in parallel
        repo_results_list = await asyncio.gather(*[run_in_repo(repo) for repo in repos])

        # Aggregate results
        results: dict[str, TaskResult] = {}
        succeeded = 0
        failed = 0
        skipped = 0

        for repo_name, result in repo_results_list:
            if result is None:
                skipped += 1
            else:
                results[repo_name] = result
                if result.success:
                    succeeded += 1
                else:
                    failed += 1

        duration = time.time() - start_time

        return WorkspaceTaskResult(
            task_name=task_name,
            repo_results=results,
            total_repos=len(repos),
            succeeded=succeeded,
            failed=failed,
            skipped=skipped,
            duration=duration,
        )

    async def run_task(
        self,
        task_name: str,
        repo_patterns: list[str] | None = None,
        repo_filter: str | None = None,
        parallel: bool = False,
        fail_fast: bool = False,
        env: dict[str, str] | None = None,
    ) -> WorkspaceTaskResult:
        """Run task across workspace repositories.

        Args:
            task_name: Name of task to run (e.g., "test", "typecheck")
            repo_patterns: Discovery patterns for finding repos (default: ["*"])
            repo_filter: Additional glob filter to apply to repo names
            parallel: Run in parallel if True, sequential if False
            fail_fast: Stop on first failure (sequential mode only)
            env: Additional environment variables to pass to tasks

        Returns:
            WorkspaceTaskResult with aggregated results

        Examples:
            # Run tests across all repos
            result = await orchestrator.run_task("test")

            # Run typecheck on pyvider packages only
            result = await orchestrator.run_task(
                "typecheck",
                repo_filter="pyvider-*"
            )

            # Parallel execution
            result = await orchestrator.run_task("build", parallel=True)
        """
        # Discover repos
        repos = self.discover_repos(patterns=repo_patterns, repo_filter=repo_filter)

        if not repos:
            logger.warning("No repositories found", patterns=repo_patterns, filter=repo_filter)
            return WorkspaceTaskResult(
                task_name=task_name,
                repo_results={},
                total_repos=0,
                succeeded=0,
                failed=0,
                skipped=0,
                duration=0.0,
            )

        # Execute in parallel or sequential mode
        if parallel:
            return await self.run_task_parallel(task_name, repos, env=env)
        else:
            return await self.run_task_sequential(task_name, repos, fail_fast=fail_fast, env=env)


# 🧰🌍🔚
