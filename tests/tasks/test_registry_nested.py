#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for nested task registry functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from wrknv.tasks.registry import TaskRegistry


class TestNestedTaskLoading:
    """Tests for loading nested tasks from TOML."""

    def test_load_flat_tasks_backward_compat(self, tmp_path: Path) -> None:
        """Test that flat tasks still work (backward compatibility)."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks]
lint = "ruff check src/"
format = "ruff format src/"
"""
        )

        registry = TaskRegistry.from_repo(tmp_path)

        assert "lint" in registry.tasks
        assert "format" in registry.tasks
        assert registry.tasks["lint"].run == "ruff check src/"
        assert registry.tasks["lint"].namespace is None

    def test_load_2level_nested_tasks(self, tmp_path: Path) -> None:
        """Test loading 2-level nested tasks."""
        fixture = Path(__file__).parent / "fixtures" / "nested_2level.toml"
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(fixture.read_text())

        registry = TaskRegistry.from_repo(tmp_path)

        # Flat tasks still work
        assert "lint" in registry.tasks
        assert "format" in registry.tasks

        # Nested tasks are registered with full names
        assert "test.unit" in registry.tasks
        assert "test.integration" in registry.tasks
        assert "test.all" in registry.tasks

        # Check task properties
        task = registry.tasks["test.unit"]
        assert task.name == "unit"
        assert task.namespace == "test"
        assert task.full_name == "test.unit"
        assert task.depth == 2
        assert task.run == "pytest tests/unit/"

    def test_load_3level_nested_tasks(self, tmp_path: Path) -> None:
        """Test loading 3-level nested tasks."""
        fixture = Path(__file__).parent / "fixtures" / "nested_3level.toml"
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(fixture.read_text())

        registry = TaskRegistry.from_repo(tmp_path)

        # 3-level tasks exist
        assert "test.unit.fast" in registry.tasks
        assert "test.unit.coverage" in registry.tasks
        assert "test.unit.verbose" in registry.tasks

        # Check properties
        task = registry.tasks["test.unit.fast"]
        assert task.name == "fast"
        assert task.namespace == "test.unit"
        assert task.full_name == "test.unit.fast"
        assert task.depth == 3
        assert task.run == "pytest tests/unit/ -x --ff"

    def test_load_default_tasks(self, tmp_path: Path) -> None:
        """Test that _default tasks are loaded and marked correctly."""
        fixture = Path(__file__).parent / "fixtures" / "nested_3level.toml"
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(fixture.read_text())

        registry = TaskRegistry.from_repo(tmp_path)

        # _default tasks exist
        assert "test.unit._default" in registry.tasks
        assert "test.integration._default" in registry.tasks

        # Check is_default property
        default_task = registry.tasks["test.unit._default"]
        assert default_task.is_default is True
        assert default_task.name == "_default"
        assert default_task.namespace == "test.unit"

    def test_mixed_flat_and_nested(self, tmp_path: Path) -> None:
        """Test mixing flat and nested tasks in same file."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks]
lint = "ruff check src/"

[tasks.test.unit]
_default = "pytest tests/unit/"
fast = "pytest tests/unit/ -x"
"""
        )

        registry = TaskRegistry.from_repo(tmp_path)

        assert "lint" in registry.tasks  # Flat
        assert "test.unit._default" in registry.tasks  # 3-level default
        assert "test.unit.fast" in registry.tasks  # 3-level


class TestExportSection:
    """Tests for parsing [export] section."""

    def test_parse_export_section(self, tmp_path: Path) -> None:
        """Test parsing [export] section."""
        fixture = Path(__file__).parent / "fixtures" / "with_exports.toml"
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(fixture.read_text())

        registry = TaskRegistry.from_repo_with_exports(tmp_path)
        exported = registry.get_exported_tasks()

        assert len(exported) == 3
        exported_names = [e.task.full_name for e in exported]
        assert "test.unit" in exported_names
        assert "test.all" in exported_names
        assert "quality.check" in exported_names

    def test_export_section_optional(self, tmp_path: Path) -> None:
        """Test that [export] section is optional."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks]
lint = "ruff check src/"
"""
        )

        registry = TaskRegistry.from_repo_with_exports(tmp_path)
        exported = registry.get_exported_tasks()

        assert len(exported) == 0

    def test_export_marks_task_as_exported(self, tmp_path: Path) -> None:
        """Test that tasks in export section are marked is_exported=True."""
        fixture = Path(__file__).parent / "fixtures" / "with_exports.toml"
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(fixture.read_text())

        registry = TaskRegistry.from_repo_with_exports(tmp_path)

        # Exported task should be marked
        assert registry.tasks["test.unit"].is_exported is True

        # Non-exported task should not be marked
        assert registry.tasks["lint"].is_exported is False


class TestTaskResolution:
    """Tests for smart task resolution with hierarchical fallback."""

    def test_exact_match_resolution(self, tmp_path: Path) -> None:
        """Test exact task name match (priority 1)."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks.test.unit]
fast = "pytest tests/unit/ -x"
"""
        )

        registry = TaskRegistry.from_repo(tmp_path)
        task, remaining_args = registry.resolve_task("test.unit.fast")

        assert task.full_name == "test.unit.fast"
        assert remaining_args == []

    def test_parent_plus_args_resolution(self, tmp_path: Path) -> None:
        """Test resolution to parent task with args (priority 2)."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks.test]
unit = "pytest tests/unit/"
"""
        )

        registry = TaskRegistry.from_repo(tmp_path)
        task, remaining_args = registry.resolve_task("test.unit", ["fast", "--verbose"])

        assert task.full_name == "test.unit"
        assert remaining_args == ["fast", "--verbose"]

    def test_grandparent_plus_args_resolution(self, tmp_path: Path) -> None:
        """Test resolution to grandparent task with args (priority 3)."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks]
test = "pytest tests/"
"""
        )

        registry = TaskRegistry.from_repo(tmp_path)
        task, remaining_args = registry.resolve_task("test.unit.fast", [])

        # Should resolve to "test" with args ["unit", "fast"]
        assert task.full_name == "test"
        assert remaining_args == ["unit", "fast"]

    def test_default_task_resolution(self, tmp_path: Path) -> None:
        """Test that _default task is used when resolving parent."""
        fixture = Path(__file__).parent / "fixtures" / "nested_3level.toml"
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(fixture.read_text())

        registry = TaskRegistry.from_repo(tmp_path)

        # Resolving "test.unit" should get the _default task
        task, remaining_args = registry.resolve_task("test.unit")

        assert task.full_name == "test.unit._default"
        assert task.is_default is True
        assert remaining_args == []

    def test_resolution_with_args_no_exact_match(self, tmp_path: Path) -> None:
        """Test resolution falls back when exact match doesn't exist."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks.test]
unit = "pytest tests/unit/"
"""
        )

        registry = TaskRegistry.from_repo(tmp_path)

        # "test.unit.nonexistent" doesn't exist, should resolve to "test.unit"
        task, remaining_args = registry.resolve_task("test.unit.nonexistent")

        assert task.full_name == "test.unit"
        assert remaining_args == ["nonexistent"]

    def test_resolution_not_found_error(self, tmp_path: Path) -> None:
        """Test that ValueError is raised if no task matches."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks]
lint = "ruff check src/"
"""
        )

        registry = TaskRegistry.from_repo(tmp_path)

        with pytest.raises(ValueError, match="Task not found"):
            registry.resolve_task("nonexistent.task")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_reject_too_deep_nesting(self, tmp_path: Path) -> None:
        """Test that >3 level nesting is rejected."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks.level1.level2.level3]
level4 = "echo 'too deep'"
"""
        )

        with pytest.raises(ValueError, match="too deep"):
            TaskRegistry.from_repo(tmp_path)

    def test_empty_namespace_table(self, tmp_path: Path) -> None:
        """Test handling of empty namespace tables."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks.test]
# Empty namespace - should be fine
"""
        )

        registry = TaskRegistry.from_repo(tmp_path)
        # Should not crash, but have no tasks in that namespace
        assert not any(task.startswith("test.") for task in registry.tasks)

    def test_get_task_backward_compat(self, tmp_path: Path) -> None:
        """Test that get_task() still works for simple lookup."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text(
            """
[tasks.test]
unit = "pytest tests/unit/"
"""
        )

        registry = TaskRegistry.from_repo(tmp_path)

        task = registry.get_task("test.unit")
        assert task is not None
        assert task.full_name == "test.unit"

        # Non-existent task
        assert registry.get_task("nonexistent") is None
