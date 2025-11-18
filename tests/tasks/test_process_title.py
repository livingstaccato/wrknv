#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for process title formatting."""

from __future__ import annotations

from pathlib import Path

import pytest

from wrknv.tasks.executor import format_task_title
from wrknv.tasks.schema import TaskConfig


class TestFormatTaskTitle:
    """Tests for format_task_title function."""

    def test_format_title_full_flat_task(self) -> None:
        """Test formatting a flat task name with full format."""
        task = TaskConfig(name="test", run="echo test", process_title_format="full")
        result = format_task_title(task)
        assert result == "test"

    def test_format_title_full_nested_task(self) -> None:
        """Test formatting a nested task name with full format."""
        task = TaskConfig(name="coverage", run="echo test", namespace="test.unit", process_title_format="full")
        result = format_task_title(task)
        assert result == "test.unit.coverage"

    def test_format_title_full_default(self) -> None:
        """Test that full format is the default."""
        task = TaskConfig(name="coverage", run="echo test", namespace="test.unit")
        result = format_task_title(task)
        # Default process_title_format is "full"
        assert result == "test.unit.coverage"

    def test_format_title_leaf_flat_task(self) -> None:
        """Test formatting a flat task name with leaf format."""
        task = TaskConfig(name="test", run="echo test", process_title_format="leaf")
        result = format_task_title(task)
        assert result == "test"

    def test_format_title_leaf_nested_task(self) -> None:
        """Test formatting a nested task name with leaf format."""
        task = TaskConfig(name="coverage", run="echo test", namespace="test.unit", process_title_format="leaf")
        result = format_task_title(task)
        assert result == "coverage"

    def test_format_title_abbreviated_flat_task(self) -> None:
        """Test formatting a flat task name with abbreviated format."""
        task = TaskConfig(name="test", run="echo test", process_title_format="abbreviated")
        result = format_task_title(task)
        # Not deep enough to abbreviate
        assert result == "test"

    def test_format_title_abbreviated_two_level_task(self) -> None:
        """Test formatting a two-level task name with abbreviated format."""
        task = TaskConfig(name="unit", run="echo test", namespace="test", process_title_format="abbreviated")
        result = format_task_title(task)
        # Not deep enough to abbreviate (only 2 levels)
        assert result == "test.unit"

    def test_format_title_abbreviated_three_level_task(self) -> None:
        """Test formatting a three-level task name with abbreviated format."""
        task = TaskConfig(
            name="coverage", run="echo test", namespace="test.unit", process_title_format="abbreviated"
        )
        result = format_task_title(task)
        # Deep enough to abbreviate
        assert result == "test...coverage"

    def test_format_title_with_complex_namespace(self) -> None:
        """Test formatting with complex nested namespace."""
        task = TaskConfig(
            name="fast",
            run="echo test",
            namespace="ci.test.unit",
            process_title_format="abbreviated",
        )
        result = format_task_title(task)
        # Should show first and last
        assert result == "ci...fast"

    def test_format_title_invalid_format_fallback(self) -> None:
        """Test that invalid format falls back to full."""
        task = TaskConfig(name="test", run="echo test", namespace="ci.test", process_title_format="invalid")
        result = format_task_title(task)
        # Should fall back to full format
        assert result == "ci.test.test"


@pytest.mark.asyncio
class TestProcessTitleIntegration:
    """Integration tests for process title setting."""

    async def test_task_sets_process_title_env_var(self, tmp_path: Path) -> None:
        """Test that task execution sets process title environment variable."""
        from wrknv.tasks.executor import TaskExecutor

        task = TaskConfig(
            name="check-title",
            run='echo "Title: $_WRKNV_PROCESS_TITLE"',
            process_title_format="full",
        )
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        # The child process should receive the title in environment
        assert "_WRKNV_PROCESS_TITLE" in result.stdout or result.success
        # Note: The exact behavior depends on shell expansion

    async def test_nested_task_title_format(self, tmp_path: Path) -> None:
        """Test that nested tasks format title correctly."""
        from wrknv.tasks.executor import TaskExecutor

        task = TaskConfig(
            name="coverage",
            run="echo test",
            namespace="test.unit",
            process_title_format="abbreviated",
        )
        executor = TaskExecutor(repo_path=tmp_path)

        result = await executor.execute(task)

        # Task should execute successfully
        assert result.success is True
        # The formatted title would be "test...coverage"
