#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Task Runner Commands

Commands for running tasks defined in wrknv.toml."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from typing import Annotated

from provide.foundation.cli import echo_error, echo_info, echo_success
from provide.foundation.console.output import perr, pout
from provide.foundation.hub import register_command

from wrknv.tasks.registry import TaskRegistry
from wrknv.tasks.schema import TaskConfig


@register_command("run", description="Run tasks defined in wrknv.toml")
def run_command(
    task: Annotated[str, "argument"],
    dry_run: bool = False,
    info: bool = False,
    env: tuple[str, ...] | None = None,
) -> None:
    """Run a task.

    Examples:
        wrknv run test
        wrknv run build --dry-run
        wrknv run test --env PYTEST_WORKERS=4
    """
    tasks = (task,)  # Convert to tuple for compatibility

    # Parse environment variables
    env_dict = {}
    for e in env or ():
        if "=" not in e:
            echo_error(f"Invalid env format: {e}. Use KEY=VALUE")
            sys.exit(1)
        key, value = e.split("=", 1)
        env_dict[key] = value

    # Load task registry
    repo_path = Path.cwd()
    registry = TaskRegistry.from_repo(repo_path)

    # Show info mode
    if info:
        for task_name in tasks:
            found_task = registry.get_task(task_name)
            if not found_task:
                echo_error(f"Task not found: {task_name}")
                continue

            echo_info(f"\nTask: {found_task.name}")
            if found_task.description:
                echo_info(f"  Description: {found_task.description}")
            echo_info(f"  Command: {found_task.run}")
            if found_task.depends_on:
                echo_info(f"  Depends on: {', '.join(found_task.depends_on)}")
            if found_task.env:
                echo_info(f"  Environment: {found_task.env}")
        return

    # Execute tasks
    asyncio.run(_run_tasks(registry, tasks, dry_run, env_dict))


async def _run_tasks(
    registry: TaskRegistry,
    task_names: tuple[str, ...],
    dry_run: bool,
    env: dict[str, str],
) -> None:
    """Run tasks sequentially."""

    for task_name in task_names:
        echo_info(f"\n▶ Running task: {task_name}")

        try:
            result = await registry.run_task(task_name, args=None, dry_run=dry_run, env=env)

            if result.stdout:
                pout(result.stdout, end="")
            if result.stderr:
                perr(result.stderr, end="")

            if result.success:
                echo_success(f"✓ Task {task_name} completed in {result.duration:.2f}s")
            else:
                echo_error(f"✗ Task {task_name} failed (exit code {result.exit_code})")
                sys.exit(result.exit_code)

        except ValueError as e:
            echo_error(str(e))
            sys.exit(1)


def _display_tasks_hierarchical(tasks: list[TaskConfig], verbose: bool) -> None:
    """Display tasks in a hierarchical tree structure.

    Groups tasks by namespace and shows them in a tree format.
    Flat tasks are shown separately at the end.

    Args:
        tasks: List of TaskConfig objects to display
        verbose: If True, show detailed task information
    """
    # Organize tasks by namespace
    namespaced_tasks: dict[str, list[TaskConfig]] = {}
    flat_tasks: list[TaskConfig] = []

    for task in tasks:
        if task.namespace:
            if task.namespace not in namespaced_tasks:
                namespaced_tasks[task.namespace] = []
            namespaced_tasks[task.namespace].append(task)
        else:
            flat_tasks.append(task)

    echo_info("\nAvailable tasks:")

    # Display namespaced tasks as trees
    for namespace in sorted(namespaced_tasks.keys()):
        echo_info(f"\n{namespace}")
        tasks_in_namespace = sorted(namespaced_tasks[namespace], key=lambda t: t.name)

        for i, task in enumerate(tasks_in_namespace):
            is_last = i == len(tasks_in_namespace) - 1
            prefix = "└── " if is_last else "├── "

            # Build task display
            task_display = task.name
            if task.is_default:
                task_display += " (default)"

            if task.description:
                task_display += f"  {task.description}"

            echo_info(f"{prefix}{task_display}")

            # Show details in verbose mode
            if verbose:
                detail_prefix = "    " if is_last else "│   "
                if task.is_composite:
                    assert isinstance(task.run, list)
                    echo_info(f"{detail_prefix}Runs: {', '.join(task.run)}")
                else:
                    cmd_preview = str(task.run)[:60]
                    if len(str(task.run)) > 60:
                        cmd_preview += "..."
                    echo_info(f"{detail_prefix}Command: {cmd_preview}")

    # Display flat tasks
    if flat_tasks:
        echo_info("\nFlat tasks:")
        for task in sorted(flat_tasks, key=lambda t: t.name):
            task_display = f"• {task.name}"
            if task.description:
                task_display += f"  {task.description}"

            echo_info(f"  {task_display}")

            if verbose:
                if task.is_composite:
                    assert isinstance(task.run, list)
                    echo_info(f"    Runs: {', '.join(task.run)}")
                else:
                    cmd_preview = str(task.run)[:60]
                    if len(str(task.run)) > 60:
                        cmd_preview += "..."
                    echo_info(f"    Command: {cmd_preview}")


@register_command("tasks", description="List available tasks")
def tasks_command(verbose: bool = False) -> None:
    """List all available tasks defined in wrknv.toml.

    Examples:
        wrknv tasks              # List all tasks
        wrknv tasks --verbose    # Show task details
    """
    repo_path = Path.cwd()
    registry = TaskRegistry.from_repo(repo_path)

    tasks = registry.list_tasks()

    if not tasks:
        echo_info("No tasks defined in wrknv.toml")
        return

    _display_tasks_hierarchical(tasks, verbose)
