#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for TaskExecutor timeout functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from wrknv.errors import TaskTimeoutError
from wrknv.tasks.executor import TaskExecutor
from wrknv.tasks.schema import TaskConfig


class TestExecutorTimeout:
    """Tests for timeout handling in task execution."""

    @pytest.mark.asyncio
    async def test_task_with_custom_timeout(self, tmp_path: Path) -> None:
        """Test that custom timeout is respected."""
        # Fast task with short timeout should succeed
        task = TaskConfig(name="fast", run="echo 'hello'", timeout=5.0)
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        assert result.success is True
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_task_timeout_raises_error(self, tmp_path: Path) -> None:
        """Test that exceeding timeout raises TaskTimeoutError."""
        # Sleep for 2 seconds with 1 second timeout
        task = TaskConfig(name="slow", run="sleep 2", timeout=1.0)
        executor = TaskExecutor(repo_path=tmp_path)

        with pytest.raises(TaskTimeoutError) as exc_info:
            await executor.execute(task)

        assert exc_info.value.task_name == "slow"
        assert exc_info.value.timeout == 1.0

    @pytest.mark.asyncio
    async def test_task_uses_default_timeout_if_not_specified(self, tmp_path: Path) -> None:
        """Test that tasks use executor default timeout."""
        # Fast task without explicit timeout
        task = TaskConfig(name="test", run="echo 'hello'")
        executor = TaskExecutor(repo_path=tmp_path, default_timeout=10.0)

        result = await executor.execute(task)

        assert result.success is True
        # Task should complete well before default timeout

    @pytest.mark.asyncio
    async def test_timeout_with_nested_task_name(self, tmp_path: Path) -> None:
        """Test timeout error shows full task name."""
        task = TaskConfig(
            name="fast",
            namespace="test.unit",
            run="sleep 2",
            timeout=0.5,
        )
        executor = TaskExecutor(repo_path=tmp_path)

        with pytest.raises(TaskTimeoutError) as exc_info:
            await executor.execute(task)

        assert exc_info.value.task_name == "test.unit.fast"
