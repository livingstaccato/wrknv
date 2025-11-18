#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Hub-based CLI Entry Point
=========================
Main CLI using provide.foundation.hub for command registration."""

from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import click
from provide.foundation.cli import echo_error, echo_info, echo_success
from provide.foundation.console.output import perr, pout
from provide.foundation.hub import get_hub
from provide.foundation.logger import get_logger

from wrknv.config import WorkenvConfig

if TYPE_CHECKING:
    from wrknv.tasks.registry import TaskRegistry

logger = get_logger(__name__)


class WrknvContext:
    """Shared context for wrknv CLI commands."""

    _config = None

    @classmethod
    def get_config(cls) -> WorkenvConfig:
        """Get or load the WorkenvConfig singleton."""
        if cls._config is None:
            cls._config = WorkenvConfig.load()
        return cls._config

    @classmethod
    def reset(cls) -> None:
        """Reset config cache (for testing)."""
        cls._config = None


def load_commands() -> None:
    """Import all command modules to trigger registration."""
    # List of command modules to load
    command_modules = [
        "wrknv.cli.commands.config",
        "wrknv.cli.commands.container",
        "wrknv.cli.commands.doctor",
        "wrknv.cli.commands.gitignore",
        "wrknv.cli.commands.lock",
        "wrknv.cli.commands.profile",
        "wrknv.cli.commands.run",
        "wrknv.cli.commands.secrets",
        "wrknv.cli.commands.setup",
        "wrknv.cli.commands.terraform",
        "wrknv.cli.commands.tools",
        "wrknv.cli.commands.workspace",
    ]

    # Import or reload command modules to trigger @register_command decorators
    # Reload is needed when Foundation clears the registry between tests
    for module_name in command_modules:
        if module_name in sys.modules:
            # Module already imported - reload to re-run decorators
            importlib.reload(sys.modules[module_name])
        else:
            # First import
            importlib.import_module(module_name)

    logger.debug("Loaded wrknv command modules")


def create_cli() -> click.Command:
    """Create the main CLI application using the hub."""
    # Get or create hub
    hub = get_hub()

    # Clear existing command registrations to allow re-creation in tests
    # This prevents AlreadyExistsError when create_cli() is called multiple times
    from provide.foundation.hub.categories import ComponentCategory

    hub.clear(dimension=ComponentCategory.COMMAND.value)

    # Reset config cache when creating CLI (for test isolation)
    WrknvContext.reset()

    # Load all commands (this will register them in the cleared registry)
    load_commands()

    # Create CLI with standard options
    cli = hub.create_cli(
        name="wrknv",
        version="0.1.0",
        help="wrknv provides cross-platform tool installation and version management "
        "for development environments, including Terraform, OpenTofu, Go, UV, and more.",
    )

    return cli


def intercept_task_command() -> bool:
    """Intercept and run task commands before Click processes them.

    Enables running tasks without the 'run' subcommand (e.g., `we test` instead of `we run test`).

    Returns:
        True if a task was intercepted and executed, False to continue with normal CLI flow
    """
    # Built-in commands that should not be intercepted
    BUILT_IN_COMMANDS = {
        "config",
        "container",
        "doctor",
        "gitignore",
        "lock",
        "profile",
        "run",
        "secrets",
        "setup",
        "terraform",
        "tools",
        "workspace",
        "tasks",
        "--help",
        "-h",
        "--version",
        "-v",
    }

    # Get command line args (skip program name)
    args = sys.argv[1:]

    if not args or args[0] in BUILT_IN_COMMANDS:
        return False

    # Try to resolve as a task
    try:
        repo_path = Path.cwd()
        from wrknv.tasks.registry import TaskRegistry

        registry = TaskRegistry.from_repo(repo_path)

        # Try to match task name from args (greedy matching)
        match = _try_resolve_task_from_args(registry, args)
        if not match:
            return False

        task_name, remaining_args = match

        # Run the task
        asyncio.run(_run_task_for_intercept(registry, task_name, remaining_args))
        return True

    except Exception as e:
        # If anything goes wrong, let Click handle it
        logger.debug(f"Task intercept failed: {e}")
        return False


def _try_resolve_task_from_args(
    registry: TaskRegistry,
    args: list[str],
) -> tuple[str, list[str]] | None:
    """Try to resolve a task name from command args using greedy matching.

    Tries progressively longer task names from left to right until a match is found.

    Args:
        registry: Task registry to search
        args: Command line arguments

    Returns:
        (task_name, remaining_args) if task found, None otherwise

    Examples:
        ["test", "unit", "--verbose"] -> ("test.unit", ["--verbose"])
        ["test", "--verbose"] -> ("test", ["--verbose"])
    """
    # Try progressively longer task names (greedy matching from longest to shortest)
    for i in range(len(args), 0, -1):
        task_parts = args[:i]
        task_name = ".".join(task_parts)
        remaining_args = args[i:]

        if registry.get_task(task_name):
            return (task_name, remaining_args)

    return None


async def _run_task_for_intercept(
    registry: TaskRegistry,
    task_name: str,
    args: list[str],
) -> None:
    """Run a task for auto-detection (simplified version of run command).

    Args:
        registry: Task registry
        task_name: Task name to run
        args: Arguments to pass to the task
    """
    from provide.foundation.process import set_process_title

    # Set process title for the task
    set_process_title(f"we: {task_name}")

    echo_info(f"\n▶ Running task: {task_name}")

    try:
        result = await registry.run_task(task_name, args=args, dry_run=False, env=None)

        if result.stdout:
            pout(result.stdout, end="")
        if result.stderr:
            perr(result.stderr, end="")

        if result.success:
            echo_success(f"✓ Task {task_name} completed in {result.duration:.2f}s")
            sys.exit(0)
        else:
            echo_error(f"✗ Task {task_name} failed (exit code {result.exit_code})")
            sys.exit(result.exit_code)

    except Exception as e:
        echo_error(f"Error running task: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    from attrs import evolve
    from provide.foundation import TelemetryConfig
    from provide.foundation.process import set_process_title

    # Load wrknv configuration to get log level
    from wrknv.config import WorkenvConfig

    wrknv_config = WorkenvConfig.from_env()

    # Get base telemetry config from environment
    base_telemetry = TelemetryConfig.from_env()

    # Merge with wrknv-specific settings
    telemetry_config = evolve(
        base_telemetry,
        service_name="wrknv",
        logging=evolve(
            base_telemetry.logging,
            default_level=wrknv_config.workenv.log_level,
        ),
    )

    # Initialize Foundation with merged config
    hub = get_hub()
    hub.initialize_foundation(telemetry_config)

    # Set up wrknv-specific logging (emoji hierarchy)
    from wrknv.logging.setup import setup_wrknv_logging

    setup_wrknv_logging()

    # Set initial process title
    set_process_title("we")

    # Try to intercept and run task commands directly (auto-detection)
    if intercept_task_command():
        return  # Task was run, exit

    # Fall through to normal CLI if not a task
    cli = create_cli()
    cli()


if __name__ == "__main__":
    main()

# 🧰🌍🔚
