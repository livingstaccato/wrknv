#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Command Implementations
=================================
Command implementations for container management."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from wrknv.config import WorkenvConfig

from .manager import ContainerManager


def build_container(config: WorkenvConfig | None = None, rebuild: bool = False) -> bool:
    """Build the development container image."""
    manager = ContainerManager(config)
    return manager.build_image(rebuild=rebuild)


def start_container(config: WorkenvConfig | None = None, rebuild: bool = False) -> bool:
    """Start the development container."""
    manager = ContainerManager(config)
    return manager.start(force_rebuild=rebuild)


def enter_container(
    config: WorkenvConfig | None = None,
    command: list[str] | None = None,
    shell: str | None = None,
    working_dir: str | None = None,
    environment: dict[str, str] | None = None,
    user: str | None = None,
    auto_start: bool = False,
) -> None:
    """Enter the running container."""
    manager = ContainerManager(config)
    manager.enter(
        command=command,
        shell=shell,
        working_dir=working_dir,
        environment=environment,
        user=user,
        auto_start=auto_start,
    )


def stop_container(config: WorkenvConfig | None = None) -> bool:
    """Stop the development container."""
    manager = ContainerManager(config)
    return manager.stop()


def restart_container(config: WorkenvConfig | None = None) -> bool:
    """Restart the development container."""
    manager = ContainerManager(config)
    return manager.restart()


def container_status(config: WorkenvConfig | None = None) -> None:
    """Display container status information."""
    manager = ContainerManager(config)
    console = Console()

    status = manager.status()

    # Docker status
    if not status["docker_available"]:
        docker_status = "[red]❌ Not Available[/red]"
    else:
        docker_status = "[green]✅ Available[/green]"

    # Image status
    image_status = "[red]❌ Not Found[/red]" if not status["image_found"] else "[green]✅ Found[/green]"

    # Create status table
    table = Table(title="📊 Container Status", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Status", style="green")

    # Docker status
    table.add_row("Docker", docker_status)

    # Image status
    table.add_row(f"Image ({manager.full_image})", image_status)

    # Container status
    if status["container_exists"]:
        container_status = "\U0001f7e2 Running" if status["container_running"] else "\U0001f7e1 Stopped"
    else:
        container_status = "❌ Not Created"
    table.add_row(f"Container ({manager.container_name})", container_status)

    # Additional info if container exists
    if status["container_info"]:
        info = status["container_info"]
        table.add_row("Container ID", info.get("id", "N/A"))
        table.add_row("State", info.get("state", "N/A"))

    console.print(table)

    # Show helpful commands
    if not status["docker_available"]:
        console.print("\n[yellow]Please install Docker to use container features[/yellow]")
    elif not status["container_running"]:
        console.print("\n[dim]Run 'wrknv container start' to start the container[/dim]")
    else:
        console.print("\n[dim]Run 'wrknv container enter' to access the container[/dim]")


def container_logs(
    config: WorkenvConfig | None = None,
    follow: bool = False,
    tail: int = 100,
    since: str | None = None,
    timestamps: bool = False,
    details: bool = False,
) -> None:
    """Show container logs."""
    manager = ContainerManager(config)
    # Note: details parameter is ignored for now
    manager.logs.get_logs(
        follow=follow,
        tail=tail,
        since=since,
        timestamps=timestamps,
    )


def clean_container(config: WorkenvConfig | None = None) -> bool:
    """Clean up container and image."""
    manager = ContainerManager(config)
    return manager.clean()


def rebuild_container(config: WorkenvConfig | None = None) -> bool:
    """Rebuild the container from scratch."""
    manager = ContainerManager(config)
    console = Console()

    console.print("🔨 Rebuilding container from scratch...")

    # Clean existing resources
    if not manager.clean():
        return False

    # Build fresh image
    if not manager.build_image(rebuild=True):
        return False

    # Start new container
    return manager.start()


def list_volumes(config: WorkenvConfig | None = None) -> None:
    """List container volumes with information."""
    manager = ContainerManager(config)
    console = Console()

    volumes = manager.list_volumes()

    if not volumes:
        console.print("[yellow]No volumes found[/yellow]")
        return

    # Create table
    table = Table(title="📦 Container Volumes", show_header=True)
    table.add_column("Volume", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Size", justify="right")
    table.add_column("Files", justify="right")

    for volume in volumes:
        # Format size
        size = volume["size"]
        if size > 1024 * 1024 * 1024:  # GB
            size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"
        elif size > 1024 * 1024:  # MB
            size_str = f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:  # KB
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"

        files_str = f"{volume['files']} files" if volume["exists"] else "-"
        status = "[green]✅ Mounted[/green]" if volume["exists"] else "[yellow]⚠️ Not Mounted[/yellow]"

        table.add_row(volume["name"], volume["path"], status, size_str if volume["exists"] else "-", files_str)

    console.print(table)


def backup_volumes(config: WorkenvConfig | None = None, name: str | None = None) -> bool:
    """Create a backup of container volumes."""
    manager = ContainerManager(config)
    console = Console()

    try:
        backup_path = manager.backup_volumes(compress=True, include_metadata=True, name=name)

        size = backup_path.stat().st_size
        size_str = f"{size / (1024 * 1024):.1f} MB" if size > 1024 * 1024 else f"{size / 1024:.1f} KB"

        console.print(f"[green]✅ Backup created successfully: {backup_path.name} ({size_str})[/green]")
        return True

    except Exception as e:
        console.print(f"[red]❌ Failed to create backup: {e}[/red]")
        return False


def restore_volumes(
    config: WorkenvConfig | None = None, backup_path: str | None = None, force: bool = False
) -> bool:
    """Restore container volumes from a backup."""
    manager = ContainerManager(config)
    console = Console()

    # Get backup path
    if backup_path:
        backup = Path(backup_path)
    else:
        # Use latest backup
        backup = manager.get_latest_backup()
        if not backup:
            console.print("[red]❌ No backups found[/red]")
            console.print("[dim]Create a backup first with 'wrknv container volumes backup'[/dim]")
            return False

    try:
        success = manager.restore_volumes(backup, force=force)
        if success:
            console.print(f"[green]✅ Volumes restored successfully from {backup.name}[/green]")
        else:
            console.print("[red]❌ Failed to restore volumes[/red]")
            if not force:
                console.print("[dim]Use --force to overwrite existing volumes[/dim]")
        return success

    except Exception as e:
        console.print(f"[red]❌ Failed to restore volumes: {e}[/red]")
        return False


def clean_volumes(config: WorkenvConfig | None = None, preserve: list[str] | None = None) -> bool:
    """Clean container volumes."""
    manager = ContainerManager(config)
    console = Console()

    preserve = preserve or []

    # Confirm with user
    if preserve:
        console.print(f"[yellow]⚠️  This will clean all volumes except: {', '.join(preserve)}[/yellow]")
    else:
        console.print("[yellow]⚠️  This will clean ALL container volumes[/yellow]")

    if not click.confirm("Are you sure you want to continue?"):
        console.print("[dim]Cancelled[/dim]")
        return False

    try:
        success = manager.clean_volumes(preserve=preserve)
        if success:
            console.print("[green]✅ Volumes cleaned successfully[/green]")
        return success

    except Exception as e:
        console.print(f"[red]❌ Failed to clean volumes: {e}[/red]")
        return False


# 🧰🌍🔚
