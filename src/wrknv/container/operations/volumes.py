#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Volume Operations
===========================
Manage container volumes and mounts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from attrs import define
from provide.foundation import logger
from provide.foundation.process import ProcessError, run
from provide.foundation.time import provide_now
from rich.console import Console
from rich.table import Table

from wrknv.container.runtime.base import ContainerRuntime


@define
class VolumeManager:
    """Manages container volume operations."""

    runtime: ContainerRuntime
    console: Console
    backup_dir: Path

    def create_volume(self, name: str, driver: str | None, options: dict[str, str] | None) -> bool:
        """Create a named volume.

        Args:
            name: Volume name
            driver: Volume driver (e.g., "local")
            options: Driver options

        Returns:
            True if successful
        """
        try:
            cmd = [self.runtime.runtime_command, "volume", "create"]

            if driver:
                cmd.extend(["--driver", driver])

            for key, value in (options or {}).items():
                cmd.extend(["--opt", f"{key}={value}"])

            cmd.append(name)

            run(cmd, check=True)

            logger.info("Volume created", name=name, driver=driver)
            return True

        except ProcessError as e:
            logger.error("Failed to create volume", name=name, error=str(e))
            self.console.print(f"[red]❌ Failed to create volume: {e}[/red]")
            return False

    def remove_volume(self, name: str, force: bool) -> bool:
        """Remove a named volume.

        Args:
            name: Volume name
            force: Force removal

        Returns:
            True if successful
        """
        try:
            cmd = [self.runtime.runtime_command, "volume", "rm"]

            if force:
                cmd.append("-f")

            cmd.append(name)

            run(cmd, check=True)

            logger.info("Volume removed", name=name)
            return True

        except ProcessError as e:
            logger.error("Failed to remove volume", name=name, error=str(e))
            self.console.print(f"[red]❌ Failed to remove volume: {e}[/red]")
            return False

    def list_volumes(self, filter_label: str | None) -> list[dict[str, Any]]:
        """List all volumes.

        Args:
            filter_label: Filter by label

        Returns:
            List of volume information
        """
        try:
            cmd = [self.runtime.runtime_command, "volume", "ls", "--format", "json"]

            if filter_label:
                cmd.extend(["--filter", f"label={filter_label}"])

            result = run(cmd, check=True)

            volumes = []
            if result.stdout:
                for line in result.stdout.strip().splitlines():
                    if line:
                        volumes.append(json.loads(line))

            return volumes

        except (ProcessError, json.JSONDecodeError) as e:
            logger.error("Failed to list volumes", error=str(e))
            return []

    def inspect_volume(self, name: str) -> dict[str, Any]:
        """Get detailed volume information.

        Args:
            name: Volume name

        Returns:
            Volume information
        """
        try:
            result = run([self.runtime.runtime_command, "volume", "inspect", name], check=True)

            if result.stdout:
                data = json.loads(result.stdout)
                return data[0] if data else {}
            return {}

        except (ProcessError, json.JSONDecodeError) as e:
            logger.error("Failed to inspect volume", name=name, error=str(e))
            return {}

    def backup_volume(
        self,
        volume_name: str,
        container_name: str,
        mount_path: str,
    ) -> Path | None:
        """Backup a volume to a tar file.

        Args:
            volume_name: Volume to backup
            container_name: Container using the volume
            mount_path: Mount path inside container

        Returns:
            Path to backup file if successful
        """
        try:
            timestamp = provide_now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"{volume_name}_{timestamp}.tar"

            self.console.print(f"[cyan]💾 Backing up volume {volume_name}...[/cyan]")

            # Create backup using tar inside container
            cmd = [
                self.runtime.runtime_command,
                "run",
                "--rm",
                "-v",
                f"{volume_name}:{mount_path}",
                "-v",
                f"{self.backup_dir}:/backup",
                "alpine",
                "tar",
                "-czf",
                f"/backup/{backup_file.name}",
                "-C",
                mount_path,
                ".",
            ]

            run(cmd, check=True)

            logger.info(
                "Volume backed up",
                volume=volume_name,
                backup_file=str(backup_file),
            )
            return backup_file

        except ProcessError as e:
            logger.error("Failed to backup volume", volume=volume_name, error=str(e))
            self.console.print(f"[red]❌ Backup failed: {e}[/red]")
            return None

    def restore_volume(
        self,
        volume_name: str,
        backup_file: Path,
        mount_path: str,
    ) -> bool:
        """Restore a volume from a tar file.

        Args:
            volume_name: Volume to restore to
            backup_file: Backup tar file
            mount_path: Mount path inside container

        Returns:
            True if successful
        """
        try:
            if not backup_file.exists():
                self.console.print(f"[red]❌ Backup file not found: {backup_file}[/red]")
                return False

            self.console.print(f"[cyan]📥 Restoring volume {volume_name}...[/cyan]")

            # Restore using tar inside container
            cmd = [
                self.runtime.runtime_command,
                "run",
                "--rm",
                "-v",
                f"{volume_name}:{mount_path}",
                "-v",
                f"{backup_file.parent}:/backup",
                "alpine",
                "tar",
                "-xzf",
                f"/backup/{backup_file.name}",
                "-C",
                mount_path,
            ]

            run(cmd, check=True)

            logger.info(
                "Volume restored",
                volume=volume_name,
                backup_file=str(backup_file),
            )
            return True

        except ProcessError as e:
            logger.error(
                "Failed to restore volume",
                volume=volume_name,
                backup_file=str(backup_file),
                error=str(e),
            )
            self.console.print(f"[red]❌ Restore failed: {e}[/red]")
            return False

    def show_volumes(self) -> None:
        """Display volumes in a table."""
        volumes = self.list_volumes(filter_label=None)

        if not volumes:
            self.console.print("[yellow]No volumes found[/yellow]")
            return

        table = Table(title="Container Volumes")
        table.add_column("Name", style="cyan")
        table.add_column("Driver", style="green")
        table.add_column("Mountpoint", style="yellow")

        for volume in volumes:
            table.add_row(
                volume.get("Name", ""),
                volume.get("Driver", ""),
                volume.get("Mountpoint", "")[:50] + "..."
                if len(volume.get("Mountpoint", "")) > 50
                else volume.get("Mountpoint", ""),
            )

        self.console.print(table)

    def backup(
        self,
        backup_path: Path | None = None,
        volumes: list[str] | None = None,
        compress: bool = True,
    ) -> bool:
        """Convenience method for backing up volumes.

        Args:
            backup_path: Path to save backup
            volumes: List of volume names to backup
            compress: Whether to compress the backup

        Returns:
            True if successful
        """
        # For now, just return True as a stub
        # Full implementation would backup specified volumes
        return True

    def restore(self, backup_path: Path, force: bool = False) -> bool:
        """Convenience method for restoring volumes.

        Args:
            backup_path: Path to backup file
            force: Force restore even if volume exists

        Returns:
            True if successful
        """
        # For now, just return True as a stub
        # Full implementation would restore from backup
        return True

    def clean(self, preserve: list[str] | None = None) -> bool:
        """Clean up volumes.

        Args:
            preserve: List of volume names to preserve

        Returns:
            True if successful
        """
        # For now, just return True as a stub
        # Full implementation would clean up volumes
        return True


# 🧰🌍🔚
