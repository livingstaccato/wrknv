#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for workspace task orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from wrknv.workspace.orchestrator import WorkspaceOrchestrator, WorkspaceTaskResult


class TestWorkspaceOrchestrator:
    """Test WorkspaceOrchestrator class."""

    def test_orchestrator_initialization(self, tmp_path: Path) -> None:
        """Test orchestrator can be initialized."""
        orchestrator = WorkspaceOrchestrator(root=tmp_path)
        assert orchestrator.root == tmp_path
        assert orchestrator.discovery is not None
        assert orchestrator.discovery.root == tmp_path

    def test_discover_repos_empty(self, tmp_path: Path) -> None:
        """Test discovery with no repos."""
        orchestrator = WorkspaceOrchestrator(root=tmp_path)
        repos = orchestrator.discover_repos()
        assert repos == []

    def test_discover_repos_with_pattern_filtering(self, tmp_path: Path) -> None:
        """Test repo discovery with pattern filtering."""
        # Create some test repos
        (tmp_path / "pyvider-test").mkdir()
        (tmp_path / "pyvider-test" / ".git").mkdir()
        (tmp_path / "pyvider-test" / "pyproject.toml").write_text('[project]\nname = "pyvider-test"')

        (tmp_path / "wrknv").mkdir()
        (tmp_path / "wrknv" / ".git").mkdir()
        (tmp_path / "wrknv" / "pyproject.toml").write_text('[project]\nname = "wrknv"')

        (tmp_path / "other-repo").mkdir()
        (tmp_path / "other-repo" / ".git").mkdir()
        (tmp_path / "other-repo" / "pyproject.toml").write_text('[project]\nname = "other"')

        orchestrator = WorkspaceOrchestrator(root=tmp_path)

        # Discover all
        all_repos = orchestrator.discover_repos()
        assert len(all_repos) == 3

        # Filter for pyvider-*
        pyvider_repos = orchestrator.discover_repos(repo_filter="pyvider-*")
        assert len(pyvider_repos) == 1
        assert pyvider_repos[0].name == "pyvider-test"

        # Filter for wrknv
        wrknv_repos = orchestrator.discover_repos(repo_filter="wrknv")
        assert len(wrknv_repos) == 1
        assert wrknv_repos[0].name == "wrknv"

    @pytest.mark.asyncio
    async def test_run_task_sequential_no_repos(self, tmp_path: Path) -> None:
        """Test sequential execution with no repos."""
        orchestrator = WorkspaceOrchestrator(root=tmp_path)
        result = await orchestrator.run_task("test")

        assert isinstance(result, WorkspaceTaskResult)
        assert result.task_name == "test"
        assert result.total_repos == 0
        assert result.succeeded == 0
        assert result.failed == 0
        assert result.skipped == 0

    @pytest.mark.asyncio
    async def test_run_task_sequential_repo_missing_task(self, tmp_path: Path) -> None:
        """Test sequential execution when task doesn't exist in repo."""
        # Create a test repo with wrknv.toml but missing the requested task
        repo_path = tmp_path / "test-repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / "pyproject.toml").write_text('[project]\nname = "test-repo"')
        (repo_path / "wrknv.toml").write_text('[tasks]\nother = "echo other"')

        orchestrator = WorkspaceOrchestrator(root=tmp_path)
        result = await orchestrator.run_task("missing-task")

        assert result.total_repos == 1
        assert result.succeeded == 0
        assert result.failed == 0
        assert result.skipped == 1

    @pytest.mark.asyncio
    async def test_run_task_parallel_no_repos(self, tmp_path: Path) -> None:
        """Test parallel execution with no repos."""
        orchestrator = WorkspaceOrchestrator(root=tmp_path)
        result = await orchestrator.run_task("test", parallel=True)

        assert isinstance(result, WorkspaceTaskResult)
        assert result.task_name == "test"
        assert result.total_repos == 0
        assert result.succeeded == 0
        assert result.failed == 0
        assert result.skipped == 0


class TestWorkspaceTaskResult:
    """Test WorkspaceTaskResult class."""

    def test_success_property_all_succeeded(self) -> None:
        """Test success property when all repos succeeded."""
        from wrknv.tasks.schema import TaskConfig, TaskResult

        task = TaskConfig(name="test", run="echo test")
        repo_results = {
            "repo1": TaskResult(task=task, success=True, exit_code=0, stdout="", stderr="", duration=1.0),
            "repo2": TaskResult(task=task, success=True, exit_code=0, stdout="", stderr="", duration=1.0),
        }

        result = WorkspaceTaskResult(
            task_name="test",
            repo_results=repo_results,
            total_repos=2,
            succeeded=2,
            failed=0,
            skipped=0,
            duration=2.0,
        )

        assert result.success is True

    def test_success_property_some_failed(self) -> None:
        """Test success property when some repos failed."""
        from wrknv.tasks.schema import TaskConfig, TaskResult

        task = TaskConfig(name="test", run="echo test")
        repo_results = {
            "repo1": TaskResult(task=task, success=True, exit_code=0, stdout="", stderr="", duration=1.0),
            "repo2": TaskResult(
                task=task, success=False, exit_code=1, stdout="", stderr="error", duration=1.0
            ),
        }

        result = WorkspaceTaskResult(
            task_name="test",
            repo_results=repo_results,
            total_repos=2,
            succeeded=1,
            failed=1,
            skipped=0,
            duration=2.0,
        )

        assert result.success is False

    def test_get_failed_repos(self) -> None:
        """Test getting list of failed repos."""
        from wrknv.tasks.schema import TaskConfig, TaskResult

        task = TaskConfig(name="test", run="echo test")
        repo_results = {
            "repo1": TaskResult(task=task, success=True, exit_code=0, stdout="", stderr="", duration=1.0),
            "repo2": TaskResult(
                task=task, success=False, exit_code=1, stdout="", stderr="error", duration=1.0
            ),
            "repo3": TaskResult(
                task=task, success=False, exit_code=1, stdout="", stderr="error", duration=1.0
            ),
        }

        result = WorkspaceTaskResult(
            task_name="test",
            repo_results=repo_results,
            total_repos=3,
            succeeded=1,
            failed=2,
            skipped=0,
            duration=3.0,
        )

        failed_repos = result.get_failed_repos()
        assert set(failed_repos) == {"repo2", "repo3"}

    def test_get_succeeded_repos(self) -> None:
        """Test getting list of succeeded repos."""
        from wrknv.tasks.schema import TaskConfig, TaskResult

        task = TaskConfig(name="test", run="echo test")
        repo_results = {
            "repo1": TaskResult(task=task, success=True, exit_code=0, stdout="", stderr="", duration=1.0),
            "repo2": TaskResult(
                task=task, success=False, exit_code=1, stdout="", stderr="error", duration=1.0
            ),
            "repo3": TaskResult(task=task, success=True, exit_code=0, stdout="", stderr="", duration=1.0),
        }

        result = WorkspaceTaskResult(
            task_name="test",
            repo_results=repo_results,
            total_repos=3,
            succeeded=2,
            failed=1,
            skipped=0,
            duration=3.0,
        )

        succeeded_repos = result.get_succeeded_repos()
        assert set(succeeded_repos) == {"repo1", "repo3"}
