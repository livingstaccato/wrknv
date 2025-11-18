#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Task Configuration Schema

Data models for task definitions and execution results."""

from __future__ import annotations

from pathlib import Path

from attrs import define, field


@define(frozen=True)
class TaskNamespace:
    """Hierarchical task namespace (e.g., test.unit.fast)."""

    parts: list[str]

    @classmethod
    def parse(cls, name: str) -> TaskNamespace:
        """Parse a task name into namespace components.

        Supports both dot (test.unit) and colon (test:unit) syntax.
        Maximum depth is 3 levels.

        Args:
            name: Task name (e.g., "test.unit" or "test:unit")

        Returns:
            TaskNamespace instance

        Raises:
            ValueError: If nesting is too deep (>3 levels)
        """
        # Normalize colons to dots
        normalized = name.replace(":", ".")
        parts = normalized.split(".")

        if len(parts) > 3:
            msg = f"Task nesting too deep: {name} (max 3 levels)"
            raise ValueError(msg)

        return cls(parts=parts)

    @property
    def full_name(self) -> str:
        """Get the full dotted name."""
        return ".".join(self.parts)

    @property
    def namespace(self) -> str | None:
        """Get the namespace (all but last part), or None for flat tasks."""
        if len(self.parts) == 1:
            return None
        return ".".join(self.parts[:-1])

    @property
    def name(self) -> str:
        """Get the task name (last part)."""
        return self.parts[-1]

    @property
    def depth(self) -> int:
        """Get the nesting depth (1=flat, 2=one level, 3=two levels)."""
        return len(self.parts)

    def parent(self) -> TaskNamespace | None:
        """Get the parent namespace, or None if flat."""
        if len(self.parts) <= 1:
            return None
        return TaskNamespace(parts=self.parts[:-1])

    def matches(self, pattern: str) -> bool:
        """Check if this namespace matches a pattern (starts with)."""
        return self.full_name.startswith(pattern)


@define(frozen=True)
class PackageTaskReference:
    """Reference to a task from another package (@package.task)."""

    package: str
    task_name: str

    @classmethod
    def parse(cls, reference: str) -> PackageTaskReference:
        """Parse a package task reference.

        Args:
            reference: Reference string (e.g., "@pyvider-cty.test")

        Returns:
            PackageTaskReference instance

        Raises:
            ValueError: If not a valid package reference
        """
        if not reference.startswith("@"):
            msg = f"Package reference must start with @: {reference}"
            raise ValueError(msg)

        # Remove @ prefix
        ref = reference[1:]

        # Split on first dot
        if "." not in ref:
            msg = f"Package reference must include task name: {reference}"
            raise ValueError(msg)

        package, task_name = ref.split(".", 1)

        return cls(package=package, task_name=task_name)

    @property
    def full_reference(self) -> str:
        """Get the full reference string."""
        return f"@{self.package}.{self.task_name}"

    @staticmethod
    def is_package_reference(name: str) -> bool:
        """Check if a string is a package reference."""
        return name.startswith("@")


@define(frozen=True)
class TaskConfig:
    """Configuration for a single task."""

    name: str
    run: str | list[str]  # Command string or list of task names
    description: str | None = None
    env: dict[str, str] = field(factory=dict)
    depends_on: list[str] = field(factory=list)
    working_dir: Path | None = None
    namespace: str | None = None  # Parent namespace (e.g., "test" for test.unit)
    is_exported: bool = False  # Whether this task is exported to other packages
    package: str | None = None  # Source package if imported
    requires: list[str] = field(factory=list)  # Dependencies required to run
    timeout: float | None = None  # Task execution timeout in seconds
    stream_output: bool = False  # Stream output in real-time
    process_title_format: str = "full"  # How to format process title: "full", "leaf", "abbreviated"
    command_prefix: str | None = None  # Optional command prefix (e.g., "uv run")
    execution_mode: str = "auto"  # Execution mode: "auto", "uv_run", "direct", "system"

    @property
    def is_composite(self) -> bool:
        """Check if task runs other tasks (composite task)."""
        return isinstance(self.run, list)

    @property
    def is_default(self) -> bool:
        """Check if this is a default task (_default)."""
        return self.name == "_default"

    @property
    def full_name(self) -> str:
        """Get the full namespaced name."""
        if self.namespace:
            return f"{self.namespace}.{self.name}"
        return self.name

    @property
    def depth(self) -> int:
        """Get the nesting depth."""
        if self.namespace:
            return len(self.namespace.split(".")) + 1
        return 1


@define(frozen=True)
class ExportedTask:
    """Metadata for an exported task."""

    task: TaskConfig
    description: str | None = None
    requires: list[str] = field(factory=list)


@define
class TaskResult:
    """Result of task execution."""

    task: TaskConfig
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float
