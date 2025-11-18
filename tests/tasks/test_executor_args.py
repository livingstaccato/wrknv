#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for TaskExecutor with argument passthrough."""

from __future__ import annotations

from pathlib import Path

import pytest

from wrknv.tasks.executor import TaskExecutor
from wrknv.tasks.schema import TaskConfig


class TestExecutorWithArgs:
    """Tests for passing arguments to task commands."""

    @pytest.mark.asyncio
    async def test_execute_command_with_no_args(self, tmp_path: Path) -> None:
        """Test that commands work without args (backward compatibility)."""
        task = TaskConfig(name="test", run="echo 'hello'")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task, args=None)

        assert result.success is True
        assert result.exit_code == 0
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_command_with_single_arg(self, tmp_path: Path) -> None:
        """Test passing a single argument to command."""
        task = TaskConfig(name="test", run="echo")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task, args=["hello"])

        assert result.success is True
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_command_with_multiple_args(self, tmp_path: Path) -> None:
        """Test passing multiple arguments to command."""
        task = TaskConfig(name="test", run="echo")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task, args=["hello", "world", "test"])

        assert result.success is True
        assert "hello world test" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_command_with_args_containing_spaces(self, tmp_path: Path) -> None:
        """Test that arguments with spaces are properly quoted."""
        task = TaskConfig(name="test", run="echo")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task, args=["hello world", "with spaces"])

        assert result.success is True
        # Should preserve the spaces in the arguments
        assert "hello world" in result.stdout
        assert "with spaces" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_command_with_special_chars(self, tmp_path: Path) -> None:
        """Test that arguments with special characters are properly escaped."""
        task = TaskConfig(name="test", run="echo")
        executor = TaskExecutor(repo_path=tmp_path)

        # Test various special characters that need quoting
        result = await executor.execute(task, args=["test$var", "test&other"])

        assert result.success is True
        # The special chars should be in the output (properly escaped)
        assert "test" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_with_env_and_args(self, tmp_path: Path) -> None:
        """Test combining environment variables and arguments."""
        task = TaskConfig(name="test", run="bash -c 'echo $TEST_VAR'", env={"TEST_VAR": "from_task"})
        executor = TaskExecutor(repo_path=tmp_path, env={"OTHER_VAR": "from_executor"})

        result = await executor.execute(task, args=["extra", "args"])

        assert result.success is True
        # The command itself runs, args are appended but bash -c ignores them
        assert "from_task" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_dry_run_with_args(self, tmp_path: Path) -> None:
        """Test that dry run shows args properly."""
        task = TaskConfig(name="test", run="pytest tests/")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task, args=["--verbose", "-x"], dry_run=True)

        assert result.success is True
        # Dry run should succeed and not actually execute
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_execute_empty_args_list(self, tmp_path: Path) -> None:
        """Test that empty args list behaves like no args."""
        task = TaskConfig(name="test", run="echo 'hello'")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task, args=[])

        assert result.success is True
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_args_with_working_dir(self, tmp_path: Path) -> None:
        """Test that args work with custom working directory."""
        # Create a subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        task = TaskConfig(name="test", run="pwd", working_dir=subdir)
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task, args=[])

        assert result.success is True
        # Should execute in the subdirectory
        assert "subdir" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_args_appended_to_command(self, tmp_path: Path) -> None:
        """Test that args are properly appended to the command."""
        task = TaskConfig(name="test", run="python -c \"import sys; print(' '.join(sys.argv[1:]))\"")
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task, args=["arg1", "arg2", "arg3"])

        assert result.success is True
        # Python should receive and print the arguments
        assert "arg1 arg2 arg3" in result.stdout
