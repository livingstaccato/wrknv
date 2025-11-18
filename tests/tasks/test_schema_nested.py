#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for nested task schema."""

from __future__ import annotations

import pytest

from wrknv.tasks.schema import (
    ExportedTask,
    PackageTaskReference,
    TaskConfig,
    TaskNamespace,
)


class TestTaskNamespace:
    """Tests for TaskNamespace parsing and resolution."""

    def test_parse_flat_task_name(self) -> None:
        """Test parsing a flat task name with no namespace."""
        ns = TaskNamespace.parse("test")

        assert ns.parts == ["test"]
        assert ns.full_name == "test"
        assert ns.namespace is None
        assert ns.name == "test"
        assert ns.depth == 1

    def test_parse_two_level_namespace(self) -> None:
        """Test parsing a two-level namespaced task."""
        ns = TaskNamespace.parse("test.unit")

        assert ns.parts == ["test", "unit"]
        assert ns.full_name == "test.unit"
        assert ns.namespace == "test"
        assert ns.name == "unit"
        assert ns.depth == 2

    def test_parse_three_level_namespace(self) -> None:
        """Test parsing a three-level namespaced task."""
        ns = TaskNamespace.parse("docs.api.build")

        assert ns.parts == ["docs", "api", "build"]
        assert ns.full_name == "docs.api.build"
        assert ns.namespace == "docs.api"
        assert ns.name == "build"
        assert ns.depth == 3

    def test_parse_colon_syntax(self) -> None:
        """Test parsing colon-separated syntax."""
        ns = TaskNamespace.parse("test:unit")

        assert ns.parts == ["test", "unit"]
        assert ns.full_name == "test.unit"
        assert ns.namespace == "test"
        assert ns.name == "unit"

    def test_parse_mixed_syntax_normalized(self) -> None:
        """Test that mixed syntax is normalized to dots."""
        ns = TaskNamespace.parse("test:unit.fast")

        # Should normalize to all dots
        assert ns.full_name == "test.unit.fast"
        assert ns.parts == ["test", "unit", "fast"]

    def test_reject_too_deep_nesting(self) -> None:
        """Test that >3 levels are rejected."""
        with pytest.raises(ValueError, match="too deep"):
            TaskNamespace.parse("level1.level2.level3.level4")

    def test_parent_namespace(self) -> None:
        """Test getting parent namespace."""
        ns = TaskNamespace.parse("test.unit.fast")

        parent = ns.parent()
        assert parent is not None
        assert parent.full_name == "test.unit"
        assert parent.depth == 2

    def test_parent_of_flat_is_none(self) -> None:
        """Test that parent of flat task is None."""
        ns = TaskNamespace.parse("test")

        assert ns.parent() is None

    def test_matches_pattern(self) -> None:
        """Test namespace pattern matching."""
        ns = TaskNamespace.parse("test.unit")

        assert ns.matches("test")  # Starts with
        assert ns.matches("test.unit")  # Exact match
        assert not ns.matches("test.integration")
        assert not ns.matches("docs")


class TestTaskConfigNested:
    """Tests for nested TaskConfig functionality."""

    def test_task_with_namespace(self) -> None:
        """Test creating a task with namespace."""
        task = TaskConfig(
            name="unit",
            run="pytest tests/unit/",
            namespace="test",
        )

        assert task.name == "unit"
        assert task.namespace == "test"
        assert task.full_name == "test.unit"
        assert task.depth == 2

    def test_task_without_namespace(self) -> None:
        """Test flat task (no namespace)."""
        task = TaskConfig(name="lint", run="ruff check .")

        assert task.name == "lint"
        assert task.namespace is None
        assert task.full_name == "lint"
        assert task.depth == 1

    def test_default_task_marker(self) -> None:
        """Test that _default is recognized."""
        task = TaskConfig(name="_default", run="pytest tests/")

        assert task.name == "_default"
        assert task.is_default is True

    def test_non_default_task(self) -> None:
        """Test regular task is not marked as default."""
        task = TaskConfig(name="unit", run="pytest tests/unit/")

        assert task.is_default is False


class TestExportedTask:
    """Tests for ExportedTask metadata."""

    def test_create_exported_task(self) -> None:
        """Test creating an exported task with metadata."""
        task = TaskConfig(name="test", run="pytest tests/")
        exported = ExportedTask(
            task=task,
            description="Run project tests",
            requires=["pytest>=7.0", "pytest-cov"],
        )

        assert exported.task == task
        assert exported.description == "Run project tests"
        assert exported.requires == ["pytest>=7.0", "pytest-cov"]

    def test_exported_task_defaults(self) -> None:
        """Test exported task with defaults."""
        task = TaskConfig(name="lint", run="ruff check .")
        exported = ExportedTask(task=task)

        assert exported.task == task
        assert exported.description is None
        assert exported.requires == []


class TestPackageTaskReference:
    """Tests for package task references."""

    def test_parse_package_reference(self) -> None:
        """Test parsing @package.task syntax."""
        ref = PackageTaskReference.parse("@pyvider-cty.test")

        assert ref.package == "pyvider-cty"
        assert ref.task_name == "test"
        assert ref.full_reference == "@pyvider-cty.test"

    def test_parse_nested_package_task(self) -> None:
        """Test parsing @package.namespace.task syntax."""
        ref = PackageTaskReference.parse("@pyvider-cty.test.unit")

        assert ref.package == "pyvider-cty"
        assert ref.task_name == "test.unit"
        assert ref.full_reference == "@pyvider-cty.test.unit"

    def test_reject_non_package_reference(self) -> None:
        """Test that non-@ references are rejected."""
        with pytest.raises(ValueError, match="must start with @"):
            PackageTaskReference.parse("pyvider-cty.test")

    def test_is_package_reference_detection(self) -> None:
        """Test detecting if a string is a package reference."""
        assert PackageTaskReference.is_package_reference("@pyvider-cty.test")
        assert PackageTaskReference.is_package_reference("@pkg.task")
        assert not PackageTaskReference.is_package_reference("test.unit")
        assert not PackageTaskReference.is_package_reference("local-task")
