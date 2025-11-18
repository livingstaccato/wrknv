#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for task registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from wrknv.tasks.registry import TaskRegistry
from wrknv.tasks.schema import TaskConfig


@pytest.fixture
def fixtures_dir() -> Path:
    """Get the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_tasks_toml(fixtures_dir: Path) -> Path:
    """Get path to simple_tasks.toml fixture."""
    return fixtures_dir / "simple_tasks.toml"


@pytest.fixture
def complex_tasks_toml(fixtures_dir: Path) -> Path:
    """Get path to complex_tasks.toml fixture."""
    return fixtures_dir / "complex_tasks.toml"


@pytest.fixture
def mixed_tasks_toml(fixtures_dir: Path) -> Path:
    """Get path to mixed_tasks.toml fixture."""
    return fixtures_dir / "mixed_tasks.toml"


class TestTaskRegistryLoading:
    """Tests for loading tasks from TOML files."""

    def test_from_repo_with_simple_tasks(self, tmp_path: Path) -> None:
        """Test loading simple task definitions from wrknv.toml."""
        # Create a wrknv.toml with simple tasks
        toml_content = """
[tasks]
test = "uv run pytest tests/"
lint = "uv run ruff check src/"
"""
        (tmp_path / "wrknv.toml").write_text(toml_content)

        registry = TaskRegistry.from_repo(tmp_path)

        assert len(registry.tasks) == 2
        assert "test" in registry.tasks
        assert "lint" in registry.tasks

        test_task = registry.get_task("test")
        assert test_task is not None
        assert test_task.name == "test"
        assert test_task.run == "uv run pytest tests/"
        assert not test_task.is_composite

    def test_from_repo_with_complex_tasks(self, tmp_path: Path) -> None:
        """Test loading complex task definitions with full config."""
        toml_content = """
[tasks.build]
run = "uv build"
description = "Build the package"
env = { PYTHONPATH = "src" }
"""
        (tmp_path / "wrknv.toml").write_text(toml_content)

        registry = TaskRegistry.from_repo(tmp_path)

        assert len(registry.tasks) == 1
        build_task = registry.get_task("build")
        assert build_task is not None
        assert build_task.name == "build"
        assert build_task.run == "uv build"
        assert build_task.description == "Build the package"
        assert build_task.env == {"PYTHONPATH": "src"}

    def test_from_repo_with_composite_tasks(self, tmp_path: Path) -> None:
        """Test loading composite tasks that run other tasks."""
        toml_content = """
[tasks.quality]
run = ["lint", "typecheck"]
description = "Run quality checks"
"""
        (tmp_path / "wrknv.toml").write_text(toml_content)

        registry = TaskRegistry.from_repo(tmp_path)

        quality_task = registry.get_task("quality")
        assert quality_task is not None
        assert quality_task.is_composite
        assert quality_task.run == ["lint", "typecheck"]

    def test_from_repo_without_wrknv_toml(self, tmp_path: Path) -> None:
        """Test loading from directory without wrknv.toml returns empty registry."""
        registry = TaskRegistry.from_repo(tmp_path)

        assert registry.repo_path == tmp_path
        assert len(registry.tasks) == 0

    def test_from_repo_with_mixed_tasks(self, tmp_path: Path) -> None:
        """Test loading a mix of simple and complex tasks."""
        toml_content = """
[tasks]
simple = "echo hello"

[tasks.complex]
run = "echo complex"
description = "A complex task"
env = { VAR = "value" }

[tasks.composite]
run = ["simple", "complex"]
"""
        (tmp_path / "wrknv.toml").write_text(toml_content)

        registry = TaskRegistry.from_repo(tmp_path)

        assert len(registry.tasks) == 3
        assert not registry.get_task("simple").is_composite  # type: ignore[union-attr]
        assert not registry.get_task("complex").is_composite  # type: ignore[union-attr]
        assert registry.get_task("composite").is_composite  # type: ignore[union-attr]


class TestTaskRegistryAPI:
    """Tests for TaskRegistry API methods."""

    def test_get_task_returns_task_when_exists(self) -> None:
        """Test get_task returns TaskConfig when task exists."""
        task = TaskConfig(name="test", run="pytest")
        registry = TaskRegistry(repo_path=Path(), tasks={"test": task})

        result = registry.get_task("test")

        assert result == task

    def test_get_task_returns_none_when_not_exists(self) -> None:
        """Test get_task returns None when task doesn't exist."""
        registry = TaskRegistry(repo_path=Path(), tasks={})

        result = registry.get_task("nonexistent")

        assert result is None

    def test_list_tasks_returns_all_tasks(self) -> None:
        """Test list_tasks returns all registered tasks."""
        task1 = TaskConfig(name="test", run="pytest")
        task2 = TaskConfig(name="lint", run="ruff")
        registry = TaskRegistry(
            repo_path=Path(),
            tasks={"test": task1, "lint": task2},
        )

        tasks = registry.list_tasks()

        assert len(tasks) == 2
        assert task1 in tasks
        assert task2 in tasks

    def test_list_tasks_returns_empty_list_when_no_tasks(self) -> None:
        """Test list_tasks returns empty list when registry is empty."""
        registry = TaskRegistry(repo_path=Path(), tasks={})

        tasks = registry.list_tasks()

        assert tasks == []
