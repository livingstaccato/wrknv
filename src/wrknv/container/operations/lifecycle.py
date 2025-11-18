#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Lifecycle Operations
==============================
Start, stop, restart, and status operations for containers."""

from __future__ import annotations

from typing import Any

from attrs import define
from provide.foundation import logger
from provide.foundation.process import ProcessError
from rich.console import Console

from wrknv.container.runtime.base import ContainerRuntime


@define
class ContainerLifecycle:
    """Manages container lifecycle operations."""

    runtime: ContainerRuntime
    container_name: str
    console: Console
    start_emoji: str
    stop_emoji: str
    restart_emoji: str
    status_emoji: str

    def exists(self) -> bool:
        """Check if container exists."""
        return self.runtime.container_exists(self.container_name)

    def is_running(self) -> bool:
        """Check if container is running."""
        return self.runtime.container_running(self.container_name)

    def start(self, create_if_missing: bool, **run_options: Any) -> bool:
        """Start the container.

        Args:
            create_if_missing: Create container if it doesn't exist
            **run_options: Options for container creation

        Returns:
            True if successful
        """
        try:
            # Check if container exists
            if self.runtime.container_exists(self.container_name):
                # Container exists, just start it
                if self.runtime.container_running(self.container_name):
                    self.console.print(
                        f"[yellow]⚠️  Container {self.container_name} is already running[/yellow]"
                    )
                    return True

                self.console.print(f"{self.start_emoji} Starting container {self.container_name}...")
                self.runtime.start_container(self.container_name)
                return True

            elif create_if_missing and "image" in run_options:
                # Container doesn't exist, create and start it
                self.console.print(
                    f"{self.start_emoji} Creating and starting container {self.container_name}..."
                )

                image = run_options.pop("image")

                # Convert volume mappings dict to list format for Docker
                volumes_dict = run_options.get("volumes", {})
                volumes_list = None
                if isinstance(volumes_dict, dict):
                    volumes_list = [f"{host}:{container}" for host, container in volumes_dict.items()]
                elif volumes_dict:
                    volumes_list = volumes_dict  # Already a list

                self.runtime.run_container(
                    image=image,
                    name=self.container_name,
                    detach=True,
                    volumes=volumes_list,
                    environment=run_options.get("environment"),
                    ports=run_options.get("ports"),
                    workdir=run_options.get("workdir"),
                    command=run_options.get("command"),
                )

                self.console.print()
                return True

            else:
                self.console.print(f"[red]❌ Container {self.container_name} does not exist[/red]")
                return False

        except ProcessError as e:
            logger.error(
                "Failed to start container",
                name=self.container_name,
                error=str(e),
                stderr=e.stderr,
            )
            self.console.print(f"[red]❌ Failed to start container: {e}[/red]")
            return False

    def stop(self, timeout: int) -> bool:
        """Stop the container.

        Args:
            timeout: Seconds to wait before force stopping

        Returns:
            True if successful
        """
        try:
            if not self.runtime.container_running(self.container_name):
                self.console.print(f"[yellow]⚠️  Container {self.container_name} is not running[/yellow]")
                return True

            self.console.print(f"{self.stop_emoji} Stopping container {self.container_name}...")

            self.runtime.stop_container(self.container_name, timeout=timeout)

            return True

        except ProcessError as e:
            logger.error(
                "Failed to stop container",
                name=self.container_name,
                error=str(e),
            )
            self.console.print(f"[red]❌ Failed to stop container: {e}[/red]")
            return False

    def restart(self, timeout: int) -> bool:
        """Restart the container.

        Args:
            timeout: Seconds to wait before force stopping

        Returns:
            True if successful
        """
        self.console.print(f"{self.restart_emoji} Restarting container {self.container_name}...")

        # Stop if running
        if self.runtime.container_running(self.container_name) and not self.stop(timeout=timeout):
            return False

        # Start again
        return self.start(create_if_missing=False)

    def status(self) -> dict[str, Any]:
        """Get container status.

        Returns:
            Status information dictionary
        """
        try:
            exists = self.runtime.container_exists(self.container_name)
            running = False
            info = {}

            if exists:
                running = self.runtime.container_running(self.container_name)
                info = self.runtime.inspect_container(self.container_name)

            status = {
                "name": self.container_name,
                "exists": exists,
                "running": running,
                "status": "running" if running else ("stopped" if exists else "not found"),
            }

            # Add extra info if available
            if info:
                status["id"] = info.get("Id", "")[:12]
                status["image"] = info.get("Config", {}).get("Image", "")

                if info.get("State"):
                    state = info["State"]
                    status["started_at"] = state.get("StartedAt")
                    status["finished_at"] = state.get("FinishedAt")

            return status

        except ProcessError as e:
            logger.error(
                "Failed to get container status",
                name=self.container_name,
                error=str(e),
            )
            return {
                "name": self.container_name,
                "exists": False,
                "running": False,
                "status": "error",
                "error": str(e),
            }

    def remove(self, force: bool) -> bool:
        """Remove the container.

        Args:
            force: Force removal even if running

        Returns:
            True if successful
        """
        try:
            if not self.runtime.container_exists(self.container_name):
                self.console.print(f"[yellow]⚠️  Container {self.container_name} does not exist[/yellow]")
                return True

            # Stop first if running and not forcing
            if not force and self.runtime.container_running(self.container_name):
                self.console.print(
                    f"[yellow]⚠️  Stopping container {self.container_name} before removal[/yellow]"
                )
                if not self.stop():
                    return False

            self.console.print(f"🗑️  Removing container {self.container_name}...")

            self.runtime.remove_container(self.container_name, force=force)

            return True

        except ProcessError as e:
            logger.error(
                "Failed to remove container",
                name=self.container_name,
                error=str(e),
            )
            self.console.print(f"[red]❌ Failed to remove container: {e}[/red]")
            return False


# 🧰🌍🔚
