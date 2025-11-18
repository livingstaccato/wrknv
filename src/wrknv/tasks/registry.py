#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Task Registry

Manages task discovery and loading from wrknv.toml files."""

from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any

from attrs import define

from wrknv.errors import TaskNotFoundError

from .executor import TaskExecutor
from .schema import ExportedTask, TaskConfig, TaskNamespace, TaskResult


@define
class TaskRegistry:
    """Manages task discovery and execution for a repository."""

    repo_path: Path
    tasks: dict[str, TaskConfig]
    package_name: str | None = None
    execution_mode: str = "auto"
    auto_detect_env: bool = True

    @classmethod
    def from_repo(cls, repo_path: Path) -> TaskRegistry:
        """Load tasks from wrknv.toml in the repository.

        Args:
            repo_path: Path to repository root containing wrknv.toml

        Returns:
            TaskRegistry with loaded tasks
        """
        config_path = repo_path / "wrknv.toml"

        if not config_path.exists():
            return cls(repo_path=repo_path, tasks={})

        with config_path.open("rb") as f:
            config = tomllib.load(f)

        tasks: dict[str, TaskConfig] = {}

        # Load tasks section (supports nested tasks)
        if "tasks" in config and isinstance(config["tasks"], dict):
            cls._parse_tasks_recursive(config["tasks"], tasks, namespace=None)

        # Extract configuration metadata for environment detection
        package_name = config.get("project_name") or config.get("package", {}).get("name")
        execution_mode = config.get("execution_mode", "auto")
        auto_detect_env = config.get("task_auto_detect", True)

        return cls(
            repo_path=repo_path,
            tasks=tasks,
            package_name=package_name,
            execution_mode=execution_mode,
            auto_detect_env=auto_detect_env,
        )

    @classmethod
    def from_repo_with_exports(cls, repo_path: Path) -> TaskRegistry:
        """Load tasks from wrknv.toml including export section.

        Args:
            repo_path: Path to repository root containing wrknv.toml

        Returns:
            TaskRegistry with loaded tasks and export markers
        """
        config_path = repo_path / "wrknv.toml"

        if not config_path.exists():
            return cls(repo_path=repo_path, tasks={})

        with config_path.open("rb") as f:
            config = tomllib.load(f)

        tasks: dict[str, TaskConfig] = {}

        # Load tasks section (supports nested tasks)
        if "tasks" in config and isinstance(config["tasks"], dict):
            cls._parse_tasks_recursive(config["tasks"], tasks, namespace=None)

        # Process export section
        exported_names: set[str] = set()
        if "export" in config and isinstance(config["export"], dict):
            export_config = config["export"]
            if "tasks" in export_config and isinstance(export_config["tasks"], list):
                exported_names.update(export_config["tasks"])

        # Mark exported tasks
        for task_name in exported_names:
            if task_name in tasks:
                # Replace task with is_exported=True version
                old_task = tasks[task_name]
                tasks[task_name] = TaskConfig(
                    name=old_task.name,
                    run=old_task.run,
                    description=old_task.description,
                    env=old_task.env,
                    depends_on=old_task.depends_on,
                    working_dir=old_task.working_dir,
                    namespace=old_task.namespace,
                    is_exported=True,
                    package=old_task.package,
                    requires=old_task.requires,
                    timeout=old_task.timeout,
                    stream_output=old_task.stream_output,
                    process_title_format=old_task.process_title_format,
                    command_prefix=old_task.command_prefix,
                    execution_mode=old_task.execution_mode,
                )

        # Extract configuration metadata for environment detection
        package_name = config.get("project_name") or config.get("package", {}).get("name")
        execution_mode = config.get("execution_mode", "auto")
        auto_detect_env = config.get("task_auto_detect", True)

        return cls(
            repo_path=repo_path,
            tasks=tasks,
            package_name=package_name,
            execution_mode=execution_mode,
            auto_detect_env=auto_detect_env,
        )

    @classmethod
    def _parse_tasks_recursive(
        cls,
        tasks_dict: dict[str, Any],
        output: dict[str, TaskConfig],
        namespace: str | None,
        depth: int = 1,
    ) -> None:
        """Recursively parse nested task tables.

        Args:
            tasks_dict: TOML dictionary containing tasks
            output: Output dictionary to populate with TaskConfig objects
            namespace: Current namespace (e.g., "test" or "test.unit")
            depth: Current nesting depth (1=flat, 2=one level, 3=two levels)

        Raises:
            ValueError: If nesting exceeds 3 levels
        """
        if depth > 3:
            msg = "Task nesting too deep (max 3 levels)"
            raise ValueError(msg)

        for name, value in tasks_dict.items():
            # Build full task name
            full_name = f"{namespace}.{name}" if namespace else name

            # Check if this is a nested table or a task definition
            if isinstance(value, dict) and "run" not in value:
                # This is a namespace table, recurse
                cls._parse_tasks_recursive(value, output, namespace=full_name, depth=depth + 1)
            else:
                # This is a task definition
                task = cls._parse_task(name, value, namespace=namespace)
                if task:
                    output[full_name] = task

    @classmethod
    def _parse_task(cls, name: str, value: Any, namespace: str | None = None) -> TaskConfig | None:
        """Parse a task definition from TOML value.

        Args:
            name: Task name (last part, e.g., "unit" in "test.unit")
            value: Task definition (string or dict)
            namespace: Parent namespace (e.g., "test" for "test.unit")

        Returns:
            TaskConfig or None if invalid
        """
        if isinstance(value, str):
            # Simple task: name = "command"
            return TaskConfig(name=name, run=value, namespace=namespace)

        if isinstance(value, dict):
            # Complex task with full configuration
            run = value.get("run")
            if run is None:
                return None

            return TaskConfig(
                name=name,
                run=run,
                description=value.get("description"),
                env=value.get("env", {}),
                depends_on=value.get("depends_on", []),
                working_dir=Path(value["working_dir"]) if "working_dir" in value else None,
                namespace=namespace,
                timeout=value.get("timeout"),
                stream_output=value.get("stream_output", False),
                process_title_format=value.get("process_title_format", "full"),
                command_prefix=value.get("command_prefix"),
                execution_mode=value.get("execution_mode", "auto"),
            )

        return None

    def get_task(self, name: str) -> TaskConfig | None:
        """Get a task by name.

        Args:
            name: Task name

        Returns:
            TaskConfig if found, None otherwise
        """
        return self.tasks.get(name)

    def list_tasks(self) -> list[TaskConfig]:
        """List all registered tasks.

        Returns:
            List of all TaskConfig objects
        """
        return list(self.tasks.values())

    def resolve_task(self, name: str, args: list[str] | None = None) -> tuple[TaskConfig, list[str]]:
        """Smart task resolution with hierarchical fallback.

        Resolution priority:
        1. Exact match (e.g., "test.unit.fast")
        2. Parent + args (e.g., "test.unit" with args=["fast"])
        3. Grandparent + args (e.g., "test" with args=["unit", "fast"])
        4. Check for _default task in namespace

        Args:
            name: Task name to resolve
            args: Optional arguments to pass to task

        Returns:
            Tuple of (TaskConfig, remaining_args)

        Raises:
            ValueError: If task cannot be resolved
        """
        if args is None:
            args = []

        # Parse the task name into namespace
        ns = TaskNamespace.parse(name)

        # Priority 1: Exact match
        if ns.full_name in self.tasks:
            return (self.tasks[ns.full_name], args)

        # Priority 2: Check for _default task in this namespace
        default_name = f"{ns.full_name}._default"
        if default_name in self.tasks:
            return (self.tasks[default_name], args)

        # Priority 3: Try parent namespace + args
        if ns.depth >= 2:
            parent_ns = ns.parent()
            if parent_ns:
                # Check exact parent match
                if parent_ns.full_name in self.tasks:
                    # Last part becomes an argument
                    new_args = [ns.name, *args]
                    return (self.tasks[parent_ns.full_name], new_args)

                # Check for _default in parent
                parent_default = f"{parent_ns.full_name}._default"
                if parent_default in self.tasks:
                    new_args = [ns.name, *args]
                    return (self.tasks[parent_default], new_args)

        # Priority 4: Try grandparent namespace + args
        if ns.depth >= 3:
            parent_ns = ns.parent()
            if parent_ns:
                grandparent_ns = parent_ns.parent()
                if grandparent_ns and grandparent_ns.full_name in self.tasks:
                    # Last two parts become arguments
                    new_args = [parent_ns.name, ns.name, *args]
                    return (self.tasks[grandparent_ns.full_name], new_args)

        # Not found
        msg = f"Task not found: {name}"
        raise ValueError(msg)

    def get_exported_tasks(self) -> list[ExportedTask]:
        """Get all tasks marked for export.

        Returns:
            List of ExportedTask objects
        """
        exported = []
        for task in self.tasks.values():
            if task.is_exported:
                exported.append(
                    ExportedTask(
                        task=task,
                        description=task.description,
                        requires=task.requires,
                    )
                )
        return exported

    async def run_task(
        self,
        name: str,
        args: list[str] | None = None,
        dry_run: bool = False,
        env: dict[str, str] | None = None,
    ) -> TaskResult:
        """Run a task by name with smart resolution.

        Args:
            name: Task name to execute (supports default task resolution)
            args: Optional arguments to pass to the task command
            dry_run: If True, show what would be executed without running
            env: Additional environment variables

        Returns:
            TaskResult with execution details

        Raises:
            TaskNotFoundError: If task not found
        """
        # Try smart resolution (handles _default tasks)
        try:
            task, resolved_args = self.resolve_task(name, args or [])
            # Merge provided args with resolved args
            final_args = resolved_args if resolved_args else args
        except ValueError as err:
            raise TaskNotFoundError(name, available_tasks=list(self.tasks.keys())) from err

        # Check if composite task
        if task.is_composite:
            return await self._run_composite_task(task, dry_run, env)

        # Run single task with environment auto-detection
        executor = TaskExecutor(
            repo_path=self.repo_path,
            env=env,
            package_name=self.package_name,
            execution_mode=self.execution_mode,  # type: ignore[arg-type]
            auto_detect_env=self.auto_detect_env,
        )
        return await executor.execute(task, args=final_args, dry_run=dry_run)

    async def _run_composite_task(
        self,
        task: TaskConfig,
        dry_run: bool,
        env: dict[str, str] | None,
    ) -> TaskResult:
        """Run a composite task that executes other tasks.

        Args:
            task: Composite task to execute
            dry_run: If True, show what would be executed
            env: Additional environment variables

        Returns:
            TaskResult aggregating all subtask results
        """
        assert isinstance(task.run, list)

        results = []
        for subtask_name in task.run:
            result = await self.run_task(subtask_name, args=None, dry_run=dry_run, env=env)
            results.append(result)

            if not result.success:
                # Stop on first failure
                break

        # Aggregate results
        success = all(r.success for r in results)
        exit_code = 0 if success else 1

        return TaskResult(
            task=task,
            success=success,
            exit_code=exit_code,
            stdout="",
            stderr="",
            duration=sum(r.duration for r in results),
        )
