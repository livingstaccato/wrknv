#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Workspace CLI Commands
======================
Commands for managing multi-repo workspaces."""

from __future__ import annotations

from pathlib import Path

from provide.foundation import logger
from provide.foundation.hub import register_command

from wrknv.workspace.manager import WorkspaceManager
from wrknv.workspace.orchestrator import WorkspaceOrchestrator


# Register the workspace group
@register_command("workspace", group=True, description="Manage multi-repo workspaces")
def workspace_group() -> None:
    """Commands for managing workspaces."""


@register_command("workspace.init", description="Initialize workspace in current directory")
def init(template_source: str | None = None, auto_discover: bool = True) -> None:
    """Initialize workspace in current directory."""
    logger.info("🚀 Initializing workspace", auto_discover=auto_discover)

    try:
        manager = WorkspaceManager()
        config = manager.init_workspace(template_source=template_source, auto_discover=auto_discover)

        if config.template_source:
            logger.info(f"📋 Template source: {config.template_source.location}")

    except Exception as e:
        logger.error("❌ Failed to initialize workspace", error=str(e))
        raise


@register_command("workspace.add", description="Add repository to workspace")
def add_repo(
    repo_path: str, name: str | None = None, repo_type: str | None = None, template_profile: str | None = None
) -> None:
    """Add repository to workspace."""
    path = Path(repo_path)

    try:
        manager = WorkspaceManager()
        config = manager.add_repo(
            repo_path=path, name=name, repo_type=repo_type, template_profile=template_profile
        )

        logger.info(f"📊 Total repositories: {len(config.repos)}")

    except Exception as e:
        logger.error("❌ Failed to add repository", error=str(e))
        raise


@register_command("workspace.remove", description="Remove repository from workspace")
def remove_repo(name: str) -> None:
    """Remove repository from workspace."""
    logger.info("🗑️ Removing repository from workspace", name=name)

    try:
        manager = WorkspaceManager()
        config = manager.remove_repo(name)

        logger.info(f"📊 Remaining repositories: {len(config.repos)}")

    except Exception as e:
        logger.error("❌ Failed to remove repository", error=str(e))
        raise


@register_command("workspace.list", description="List repositories in workspace")
def list_repos() -> None:
    """List repositories in workspace."""
    logger.info("📋 Listing workspace repositories")

    try:
        manager = WorkspaceManager()
        config = manager.load_config()

        if not config:
            logger.warning("⚠️ No workspace configuration found")
            logger.info("💡 Initialize with: wrknv workspace init")
            return

        logger.info(f"📊 Total repositories: {len(config.repos)}")

        for repo in config.repos:
            logger.info(f"    📍 Path: {repo.path}")
            logger.info(f"    🎯 Profile: {repo.template_profile}")
            logger.info(f"    🎨 Features: {', '.join(repo.features)}")

    except Exception as e:
        logger.error("❌ Failed to list repositories", error=str(e))
        raise


@register_command("workspace.status", description="Show workspace status")
def status() -> None:
    """Show workspace status."""
    logger.info("📊 Getting workspace status")

    try:
        manager = WorkspaceManager()
        status_info = manager.get_workspace_status()

        if "error" in status_info:
            logger.error(f"❌ {status_info['error']}")
            return

        logger.info(f"🔍 Discovered repos: {status_info['repos_discovered']}")
        logger.info(f"🔄 Sync strategy: {status_info['sync_strategy']}")

        if status_info.get("type_distribution"):
            logger.info("📊 Repository types:")
            for repo_type, count in status_info["type_distribution"].items():
                logger.info(f"  {repo_type}: {count}")

        if status_info.get("issues"):
            logger.warning("⚠️ Issues found:")
            for issue in status_info["issues"]:
                logger.warning(f"  • {issue}")

        if status_info.get("template_source"):
            source = status_info["template_source"]
            logger.info(f"📋 Template source: {source['location']} ({source['type']})")

    except Exception as e:
        logger.error("❌ Failed to get workspace status", error=str(e))
        raise


@register_command("workspace.sync", description="Sync configurations across repositories")
def sync_all(dry_run: bool = False) -> None:
    """Sync configurations across repositories."""
    import asyncio

    async def _sync_all() -> None:
        action = "🔍 Checking" if dry_run else "🔄 Syncing"
        logger.info(f"{action} workspace configurations", dry_run=dry_run)

        try:
            manager = WorkspaceManager()
            results = await manager.sync_all(dry_run=dry_run)

            success_count = sum(1 for result in results.values() if result.get("success"))
            total_count = len(results)

            if dry_run:
                logger.info(f"🔍 Sync check completed: {success_count}/{total_count} repos ready")
            else:
                logger.info(f"✅ Sync completed: {success_count}/{total_count} repos synced")

            for repo_name, result in results.items():
                if result.get("success"):
                    logger.info(f"  ✅ {repo_name}")
                else:
                    error = result.get("error", "Unknown error")
                    logger.error(f"  ❌ {repo_name}: {error}")

        except Exception as e:
            logger.error("❌ Failed to sync workspace", error=str(e))
            raise

    asyncio.run(_sync_all())


@register_command("workspace.sync-repo", description="Sync configuration for specific repository")
def sync_repo(name: str, dry_run: bool = False) -> None:
    """Sync configuration for specific repository."""
    import asyncio

    async def _sync_repo() -> None:
        action = "🔍 Checking" if dry_run else "🔄 Syncing"
        logger.info(f"{action} repository configuration", name=name, dry_run=dry_run)

        try:
            manager = WorkspaceManager()
            result = await manager.sync_repo(name, dry_run=dry_run)

            if result.get(name, {}).get("success"):
                if dry_run:
                    logger.info(f"✅ {name} is ready to sync")
                else:
                    logger.info(f"✅ {name} synced successfully")
            else:
                error = result.get(name, {}).get("error", "Unknown error")
                logger.error(f"❌ {name}: {error}")

        except Exception as e:
            logger.error("❌ Failed to sync repository", error=str(e))
            raise

    asyncio.run(_sync_repo())


@register_command("workspace.drift", description="Check for configuration drift")
def check_drift() -> None:
    """Check for configuration drift."""
    logger.info("🔍 Checking for configuration drift")

    try:
        manager = WorkspaceManager()
        drift_info = manager.check_drift()

        if drift_info.get("drift_detected"):
            logger.warning("⚠️ Configuration drift detected")

            if "drifted_repos" in drift_info:
                logger.info("📊 Repositories with drift:")
                for repo_name in drift_info["drifted_repos"]:
                    logger.warning(f"  • {repo_name}")

            logger.info("💡 Run 'wrknv workspace sync' to resolve drift")
        else:
            logger.info("✅ No configuration drift detected")

    except Exception as e:
        logger.error("❌ Failed to check drift", error=str(e))
        raise


@register_command("workspace.setup", description="Setup all repositories in workspace")
def setup_workspace(generate_only: bool = False) -> None:
    """Setup all repositories in workspace.

    Args:
        generate_only: If True, only generate env scripts without running them
    """
    logger.info("🚀 Setting up workspace", generate_only=generate_only)

    try:
        manager = WorkspaceManager()
        results = manager.setup_workspace(generate_only=generate_only)

        success_count = results.get("success_count", 0)
        total_count = results.get("total_count", 0)

        if generate_only:
            logger.info(f"✅ Generated env scripts: {success_count}/{total_count} repos")
        else:
            logger.info(f"✅ Setup completed: {success_count}/{total_count} repos")

        if results.get("failures"):
            logger.warning("⚠️ Some repositories failed:")
            for repo_name, error in results["failures"].items():
                logger.error(f"  ❌ {repo_name}: {error}")

    except Exception as e:
        logger.error("❌ Failed to setup workspace", error=str(e))
        raise


@register_command("workspace.run", description="Run task across workspace repositories")
def run_task(
    task: str,
    repos: str | None = None,
    parallel: bool = False,
    fail_fast: bool = False,
) -> None:
    """Run task across workspace repositories.

    Args:
        task: Name of task to run (e.g., "test", "typecheck", "build")
        repos: Glob pattern to filter repositories (e.g., "pyvider-*")
        parallel: Run in parallel across all repos (default: sequential)
        fail_fast: Stop on first failure (sequential mode only, default: continue-on-error)

    Examples:
        # Run tests across all repositories
        we workspace run test

        # Run typecheck on pyvider packages only
        we workspace run typecheck --repos="pyvider-*"

        # Parallel execution with fail-fast
        we workspace run test --parallel --fail-fast
    """
    import asyncio

    async def _run_task() -> None:
        try:
            # Determine workspace root (parent of current directory by default)
            root = Path.cwd().parent
            logger.info(
                "🚀 Running task across workspace",
                task=task,
                root=str(root),
                repos_filter=repos,
                parallel=parallel,
                fail_fast=fail_fast,
            )

            # Create orchestrator
            orchestrator = WorkspaceOrchestrator(root=root)

            # Run task
            result = await orchestrator.run_task(
                task_name=task,
                repo_filter=repos,
                parallel=parallel,
                fail_fast=fail_fast,
            )

            # Print summary separator
            logger.info("")
            logger.info("=" * 80)
            logger.info("📊 Workspace Task Summary")
            logger.info("=" * 80)

            # Print summary
            logger.info(f"Task: {result.task_name}")
            logger.info(f"Total repos: {result.total_repos}")
            logger.info(f"✅ Succeeded: {result.succeeded}")
            logger.info(f"❌ Failed: {result.failed}")
            logger.info(f"⏭️  Skipped: {result.skipped}")
            logger.info(f"⏱️  Duration: {result.duration:.2f}s")

            # Show failed repos if any
            if result.failed > 0:
                logger.error("")
                logger.error("Failed repositories:")
                for repo_name in result.get_failed_repos():
                    repo_result = result.repo_results[repo_name]
                    logger.error(f"  ❌ {repo_name} (exit code: {repo_result.exit_code})")

                # Exit with error code
                import sys

                sys.exit(1)
            else:
                logger.info("")
                logger.info("✅ All repositories succeeded!")

        except Exception as e:
            logger.error("❌ Failed to run workspace task", error=str(e), error_type=type(e).__name__)
            raise

    asyncio.run(_run_task())


# 🧰🌍🔚
