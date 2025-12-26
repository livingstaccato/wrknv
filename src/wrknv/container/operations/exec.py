#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Exec Operations
=========================
Execute commands inside running containers."""

from __future__ import annotations

import subprocess
from typing import Any

from attrs import define
from provide.foundation import logger
from provide.foundation.errors import resilient
from provide.foundation.process import ProcessError
from rich.console import Console

from wrknv.container.runtime.base import ContainerRuntime


@define
class ContainerExec:
    """Handles container exec operations."""

    runtime: ContainerRuntime
    container_name: str
    console: Console
    available_shells: list[str]
    default_shell: str

    @resilient
    def exec(
        self,
        command: list[str] | None = None,
        shell: str | None = None,
        interactive: bool = False,
        tty: bool = False,
        user: str | None = None,
        workdir: str | None = None,
        environment: dict[str, str] | None = None,
    ) -> bool:
        """Execute a command in the container.

        Args:
            command: Command to execute (defaults to shell)
            shell: Shell to use (defaults to /bin/bash or /bin/sh)
            interactive: Keep STDIN open
            tty: Allocate pseudo-TTY
            user: User to run as
            workdir: Working directory
            environment: Environment variables

        Returns:
            True if successful
        """
        try:
            # Check if container is running
            if not self.runtime.container_running(self.container_name):
                self.console.print(f"[red]❌ Container {self.container_name} is not running[/red]")
                return False

            # Determine command to run
            if command is None:
                # Use shell
                if shell is None:
                    # Try to detect available shell
                    shell = self._detect_shell()
                command = [shell]

            # Execute command

            # For interactive commands, we need to use subprocess.run directly
            # as foundation.process might not support interactive TTY yet
            if interactive and tty:
                # Build command as a list for subprocess
                cmd_list = self._build_exec_command_list(
                    command=command,
                    interactive=True,
                    tty=True,
                    user=user,
                    workdir=workdir,
                    environment=environment,
                )

                # Use subprocess.run for interactive TTY support (shell=False for security)
                result = subprocess.run(cmd_list, check=False)
                return result.returncode == 0

            else:
                # Non-interactive, use foundation.process
                result = self.runtime.exec_in_container(
                    name=self.container_name,
                    command=command,
                    interactive=interactive,
                    tty=tty,
                    user=user,
                    workdir=workdir,
                    environment=environment,
                )

                if result.stdout:
                    self.console.print(result.stdout)

                return True

        except ProcessError as e:
            logger.error(
                "Container exec failed",
                container=self.container_name,
                command=command,
                error=str(e),
                stderr=e.stderr,
            )
            self.console.print(f"[red]❌ Exec failed: {e}[/red]")
            return False

    def enter(self, shell: str | None, **kwargs: Any) -> bool:
        """Enter the container with an interactive shell.

        Args:
            shell: Shell to use
            **kwargs: Additional exec options

        Returns:
            True if successful
        """
        return self.exec(command=None, shell=shell, interactive=True, tty=True, **kwargs)

    @resilient
    def run_command(
        self,
        command: list[str],
        capture_output: bool,
        **kwargs: Any,
    ) -> str | None:
        """Run a command in the container and return output.

        Args:
            command: Command to run
            capture_output: Whether to capture output
            **kwargs: Additional exec options

        Returns:
            Command output if capture_output is True, else None
        """
        try:
            result = self.runtime.exec_in_container(
                name=self.container_name,
                command=command,
                interactive=False,
                tty=False,
                user=kwargs.get("user"),
                workdir=kwargs.get("workdir"),
                environment=kwargs.get("environment"),
            )

            if capture_output:
                return result.stdout

            if result.stdout:
                self.console.print(result.stdout)

            return None

        except ProcessError as e:
            logger.error(
                "Command execution failed",
                container=self.container_name,
                command=command,
                error=str(e),
            )
            if capture_output:
                return None
            self.console.print(f"[red]❌ Command failed: {e}[/red]")
            return None

    def _detect_shell(self) -> str:
        """Detect available shell in container.

        Returns:
            Path to available shell
        """
        for shell in self.available_shells:
            try:
                # Check if shell exists
                self.runtime.exec_in_container(
                    name=self.container_name,
                    command=["test", "-f", shell],
                    interactive=False,
                    tty=False,
                    user=None,
                    workdir=None,
                    environment=None,
                )
                # If command succeeds, shell exists
                return shell
            except ProcessError:
                continue

        # Return configured default if nothing found
        return self.default_shell

    def _build_exec_command_list(
        self,
        command: list[str],
        interactive: bool,
        tty: bool,
        user: str | None,
        workdir: str | None,
        environment: dict[str, str] | None,
    ) -> list[str]:
        """Build docker exec command as a list for subprocess.run.

        Args:
            command: Command to execute
            interactive: Keep STDIN open
            tty: Allocate pseudo-TTY
            user: User to run as
            workdir: Working directory
            environment: Environment variables

        Returns:
            Command as list of strings (safe for subprocess with shell=False)
        """
        parts = [self.runtime.runtime_command, "exec"]

        if interactive:
            parts.append("-i")
        if tty:
            parts.append("-t")
        if user:
            parts.extend(["-u", user])
        if workdir:
            parts.extend(["-w", workdir])

        for key, value in (environment or {}).items():
            parts.extend(["-e", f"{key}={value}"])

        parts.append(self.container_name)
        parts.extend(command)

        return parts


# 🧰🌍🔚
