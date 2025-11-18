#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for task configuration schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from wrknv.tasks.schema import TaskConfig, TaskResult


class TestTaskConfig:
    """Tests for TaskConfig data class."""

    def test_simple_task_creation(self) -> None:
        """Test creating a simple task with just a command."""
        task = TaskConfig(
            name="test",
            run="pytest tests/",
        )

        assert task.name == "test"
        assert task.run == "pytest tests/"
        assert task.description is None
        assert task.env == {}
        assert task.depends_on == []
        assert task.working_dir is None
        assert not task.is_composite

    def test_complex_task_creation(self) -> None:
        """Test creating a complex task with all fields."""
        task = TaskConfig(
            name="build",
            run="uv build",
            description="Build the package",
            env={"PYTHONPATH": "src", "BUILD_ENV": "test"},
            depends_on=["test", "lint"],
            working_dir=Path("/tmp/build"),
        )

        assert task.name == "build"
        assert task.run == "uv build"
        assert task.description == "Build the package"
        assert task.env == {"PYTHONPATH": "src", "BUILD_ENV": "test"}
        assert task.depends_on == ["test", "lint"]
        assert task.working_dir == Path("/tmp/build")
        assert not task.is_composite

    def test_composite_task_creation(self) -> None:
        """Test creating a composite task that runs other tasks."""
        task = TaskConfig(
            name="ci",
            run=["lint", "test", "build"],
            description="Complete CI pipeline",
        )

        assert task.name == "ci"
        assert task.run == ["lint", "test", "build"]
        assert task.description == "Complete CI pipeline"
        assert task.is_composite

    def test_is_composite_detection(self) -> None:
        """Test is_composite property correctly identifies task type."""
        simple_task = TaskConfig(name="simple", run="echo hello")
        composite_task = TaskConfig(name="composite", run=["task1", "task2"])

        assert not simple_task.is_composite
        assert composite_task.is_composite

    def test_taskconfig_is_frozen(self) -> None:
        """Test that TaskConfig is immutable (frozen)."""
        task = TaskConfig(name="test", run="pytest")

        with pytest.raises(AttributeError):
            task.name = "modified"  # type: ignore[misc]


class TestTaskResult:
    """Tests for TaskResult data class."""

    def test_successful_result_creation(self) -> None:
        """Test creating a successful task result."""
        task = TaskConfig(name="test", run="pytest")
        result = TaskResult(
            task=task,
            success=True,
            exit_code=0,
            stdout="All tests passed\n",
            stderr="",
            duration=1.5,
        )

        assert result.task == task
        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == "All tests passed\n"
        assert result.stderr == ""
        assert result.duration == 1.5

    def test_failed_result_creation(self) -> None:
        """Test creating a failed task result."""
        task = TaskConfig(name="lint", run="ruff check")
        result = TaskResult(
            task=task,
            success=False,
            exit_code=1,
            stdout="",
            stderr="Found 5 errors\n",
            duration=0.8,
        )

        assert result.task == task
        assert result.success is False
        assert result.exit_code == 1
        assert result.stderr == "Found 5 errors\n"
        assert result.duration == 0.8

    def test_result_with_zero_exit_code_is_successful(self) -> None:
        """Test that exit code 0 indicates success."""
        task = TaskConfig(name="test", run="true")
        result = TaskResult(
            task=task,
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            duration=0.1,
        )

        assert result.exit_code == 0
        assert result.success is True

    def test_result_with_nonzero_exit_code_is_failure(self) -> None:
        """Test that non-zero exit code indicates failure."""
        task = TaskConfig(name="test", run="false")
        result = TaskResult(
            task=task,
            success=False,
            exit_code=1,
            stdout="",
            stderr="",
            duration=0.1,
        )

        assert result.exit_code != 0
        assert result.success is False
