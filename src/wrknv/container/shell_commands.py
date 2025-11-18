#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Shell Commands
========================
Commands for interacting with running containers."""

from __future__ import annotations

from typing import Any

from provide.foundation import logger
from provide.foundation.process import CompletedProcess, run, stream
from rich.console import Console

from wrknv.config import WorkenvConfig
from wrknv.container.manager import ContainerManager


def shell_into_container(
    config: WorkenvConfig,
    shell: str = "/bin/bash",
    working_dir: str | None = None,
    environment: dict[str, str] | None = None,
    auto_start: bool = False,
) -> bool:
    """
    Open an interactive shell session in the container.

    Args:
        config: Workenv configuration
        shell: Shell to use (default: /bin/bash)
        working_dir: Working directory in container
        environment: Environment variables to set
        auto_start: Auto-start container if not running

    Returns:
        True if shell session was successful
    """
    console = Console()

    if not config.container or not config.container.enabled:
        console.print("[red]❌ Container support is not enabled[/red]")
        return False

    # Reuse existing ContainerManager
    manager = ContainerManager(config)

    # Check if container is running
    if not manager.container_running():
        if not manager.container_exists():
            console.print(f"[yellow]⚠️  Container {manager.container_name} doesn't exist[/yellow]")
            return False

        if auto_start:
            console.print(
                f"[yellow]⚠️  Container {manager.container_name} is not running. Starting...[/yellow]"
            )
            if not manager.start():
                console.print("[red]❌ Failed to start container[/red]")
                return False
        else:
            console.print(f"[yellow]⚠️  Container {manager.container_name} is not running[/yellow]")
            console.print("Use --auto-start to start it automatically")
            return False

    # Build docker exec command
    cmd = ["docker", "exec", "-it"]

    # Add working directory if specified
    if working_dir:
        cmd.extend(["-w", working_dir])

    # Add environment variables
    if environment:
        for key, value in environment.items():
            cmd.extend(["-e", f"{key}={value}"])

    # Add container name and shell
    cmd.extend([manager.container_name, shell])

    logger.info(f"Opening shell in container: {' '.join(cmd)}")
    console.print(f"[green]🐚 Opening {shell} in {manager.container_name}...[/green]")

    try:
        # Run interactively without capturing output
        result = run(cmd, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        console.print("\n[yellow]Shell session interrupted[/yellow]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Failed to open shell: {e}[/red]")
        logger.error(f"Shell failed: {e}")
        return False


def exec_in_container(
    config: WorkenvConfig,
    command: list[str],
    working_dir: str | None = None,
    environment: dict[str, str] | None = None,
    user: str | None = None,
    interactive: bool = False,
) -> CompletedProcess | None:
    """
    Execute a command in the container.

    Args:
        config: Workenv configuration
        command: Command and arguments to execute
        working_dir: Working directory in container
        environment: Environment variables to set
        user: User to run command as
        interactive: Run interactively (for commands like python, node, etc.)

    Returns:
        CompletedProcess result or None if container not running
    """
    console = Console()

    if not config.container or not config.container.enabled:
        console.print("[red]❌ Container support is not enabled[/red]")
        return None

    # Reuse existing ContainerManager
    manager = ContainerManager(config)

    # Check if container is running
    if not manager.container_running():
        console.print(f"[yellow]⚠️  Container {manager.container_name} is not running[/yellow]")
        return None

    # Build docker exec command
    cmd = ["docker", "exec"]

    # Add interactive flags if needed
    if interactive:
        cmd.append("-it")

    # Add working directory if specified
    if working_dir:
        cmd.extend(["-w", working_dir])

    # Add user if specified
    if user:
        cmd.extend(["-u", user])

    # Add environment variables
    if environment:
        for key, value in environment.items():
            cmd.extend(["-e", f"{key}={value}"])

    # Add container name and command
    cmd.append(manager.container_name)
    cmd.extend(command)

    logger.info(f"Executing in container: {' '.join(cmd)}")

    try:
        # Run command (interactively if requested)
        result = run(cmd, check=False)

        if result.returncode != 0 and result.stderr:
            console.print(f"[red]Command failed: {result.stderr}[/red]")

        return result
    except Exception as e:
        console.print(f"[red]❌ Failed to execute command: {e}[/red]")
        logger.error(f"Exec failed: {e}")
        return None


def get_container_logs(
    config: WorkenvConfig,
    follow: bool = False,
    tail: int | None = None,
    since: str | None = None,
    timestamps: bool = False,
) -> str | None:
    """
    Get container logs.

    Args:
        config: Workenv configuration
        follow: Follow log output (like tail -f)
        tail: Number of lines to show from the end
        since: Show logs since timestamp (e.g., "1h", "2023-01-01")
        timestamps: Show timestamps in logs

    Returns:
        Log output as string, or None if container doesn't exist
    """
    console = Console()

    if not config.container or not config.container.enabled:
        console.print("[red]❌ Container support is not enabled[/red]")
        return None

    # Reuse existing ContainerManager
    manager = ContainerManager(config)

    # Check if container exists
    if not manager.container_exists():
        console.print(f"[yellow]⚠️  Container {manager.container_name} doesn't exist[/yellow]")
        return None

    # Build docker logs command
    cmd = ["docker", "logs"]

    # Add options
    if follow:
        cmd.append("-f")

    if timestamps:
        cmd.append("-t")

    if tail is not None:
        cmd.extend(["--tail", str(tail)])

    if since:
        cmd.extend(["--since", since])

    # Add container name
    cmd.append(manager.container_name)

    logger.info(f"Getting container logs: {' '.join(cmd)}")

    try:
        if follow:
            # Stream logs without capturing (for follow mode)
            run(cmd, check=False)
            return None
        else:
            # Capture and return logs
            result = run(cmd, check=False)

            if result.returncode != 0:
                console.print(f"[red]Failed to get logs: {result.stderr}[/red]")
                return None

            return result.stdout
    except Exception as e:
        console.print(f"[red]❌ Failed to get logs: {e}[/red]")
        logger.error(f"Logs failed: {e}")
        return None


def stream_container_logs(
    config: WorkenvConfig,
    filter_pattern: str | None = None,
    highlight_pattern: str | None = None,
) -> bool:
    """
    Stream container logs with optional filtering and highlighting.

    Args:
        config: Workenv configuration
        filter_pattern: Regex pattern to filter logs
        highlight_pattern: Pattern to highlight in output

    Returns:
        True if streaming was successful
    """
    console = Console()

    if not config.container or not config.container.enabled:
        console.print("[red]❌ Container support is not enabled[/red]")
        return False

    # Reuse existing ContainerManager
    manager = ContainerManager(config)

    if not manager.container_exists():
        console.print(f"[yellow]⚠️  Container {manager.container_name} doesn't exist[/yellow]")
        return False

    console.print(f"[green]📜 Streaming logs from {manager.container_name}...[/green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    # Build command
    cmd = ["docker", "logs", "-f", manager.container_name]

    try:
        import re

        # Start streaming process
        for line in stream(cmd):
            # Apply filter if specified
            if filter_pattern and not re.search(filter_pattern, line):
                continue

            # Apply highlighting if specified
            if highlight_pattern:
                line = re.sub(f"({highlight_pattern})", r"[bold yellow]\1[/bold yellow]", line)

            console.print(line, end="")

    except KeyboardInterrupt:
        console.print("\n[yellow]Log streaming stopped[/yellow]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Failed to stream logs: {e}[/red]")
        logger.error(f"Log streaming failed: {e}")
        return False

    return True


def get_container_stats(config: WorkenvConfig) -> dict[str, Any] | None:
    """
    Get container resource usage statistics.

    Args:
        config: Workenv configuration

    Returns:
        Dictionary with container stats or None
    """
    Console()

    if not config.container or not config.container.enabled:
        return None

    # Reuse existing ContainerManager
    manager = ContainerManager(config)

    if not manager.container_running():
        return None

    try:
        # Get container stats
        cmd = ["docker", "stats", "--no-stream", "--format", "json", manager.container_name]
        result = run(cmd, check=False)

        if result.returncode == 0 and result.stdout:
            import json

            stats = json.loads(result.stdout)

            # Parse and format stats
            return {
                "name": stats.get("Name", manager.container_name),
                "cpu": stats.get("CPUPerc", "0%"),
                "memory": {"usage": stats.get("MemUsage", "0B / 0B"), "percent": stats.get("MemPerc", "0%")},
                "network": stats.get("NetIO", "0B / 0B"),
                "disk": stats.get("BlockIO", "0B / 0B"),
                "pids": stats.get("PIDs", "0"),
            }
    except Exception as e:
        logger.error(f"Failed to get container stats: {e}")

    return None


# 🧰🌍🔚
