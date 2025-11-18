#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for task executor."""

from __future__ import annotations

from pathlib import Path

import pytest

from wrknv.tasks.executor import TaskExecutor
from wrknv.tasks.schema import TaskConfig


class TestTaskExecutor:
    """Tests for TaskExecutor."""

    @pytest.mark.asyncio
    async def test_execute_successful_command(self, tmp_path: Path) -> None:
        """Test executing a command that succeeds."""
        task = TaskConfig(name="echo", run="echo 'Hello World'")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        assert result.success is True
        assert result.exit_code == 0
        assert "Hello World" in result.stdout
        assert result.stderr == ""
        assert result.duration > 0

    @pytest.mark.asyncio
    async def test_execute_failed_command(self, tmp_path: Path) -> None:
        """Test executing a command that fails."""
        task = TaskConfig(name="fail", run="exit 1")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        assert result.success is False
        assert result.exit_code == 1

    @pytest.mark.asyncio
    async def test_execute_command_with_stdout(self, tmp_path: Path) -> None:
        """Test capturing stdout from command."""
        task = TaskConfig(name="output", run="echo 'test output'")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        assert "test output" in result.stdout
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_command_with_stderr(self, tmp_path: Path) -> None:
        """Test capturing stderr from command."""
        task = TaskConfig(name="error", run="echo 'error message' >&2")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        assert "error message" in result.stderr

    @pytest.mark.asyncio
    async def test_execute_with_custom_env(self, tmp_path: Path) -> None:
        """Test executing with custom environment variables."""
        task = TaskConfig(
            name="env-test",
            run="echo $TEST_VAR",
            env={"TEST_VAR": "custom_value"},
        )
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        assert "custom_value" in result.stdout
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_base_env(self, tmp_path: Path) -> None:
        """Test that base environment is merged with task environment."""
        task = TaskConfig(name="env", run="echo $BASE_VAR $TASK_VAR", env={"TASK_VAR": "task"})
        executor = TaskExecutor(repo_path=tmp_path, env={"BASE_VAR": "base"})

        result = await executor.execute(task)

        assert "base" in result.stdout
        assert "task" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_measures_duration(self, tmp_path: Path) -> None:
        """Test that execution duration is measured."""
        task = TaskConfig(name="sleep", run="sleep 0.1")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        assert result.duration >= 0.1

    @pytest.mark.asyncio
    async def test_execute_with_dry_run(self, tmp_path: Path) -> None:
        """Test dry run mode doesn't execute command."""
        task = TaskConfig(name="fail", run="exit 1")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task, dry_run=True)

        # Dry run always succeeds without executing
        assert result.success is True
        assert result.exit_code == 0
        assert result.duration == 0.0

    @pytest.mark.asyncio
    async def test_execute_in_custom_working_dir(self, tmp_path: Path) -> None:
        """Test executing command in custom working directory."""
        # Create a subdirectory with a file
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "testfile.txt").write_text("content")

        task = TaskConfig(
            name="pwd",
            run="ls testfile.txt",
            working_dir=subdir,
        )
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        assert result.success is True
        assert "testfile.txt" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_handles_command_not_found(self, tmp_path: Path) -> None:
        """Test handling of non-existent commands."""
        task = TaskConfig(name="bad", run="nonexistentcommand12345")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        assert result.success is False
        assert result.exit_code != 0
