#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Runtime Base Abstraction
===================================
Abstract base class for container runtime implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from attrs import define
from provide.foundation.process import CompletedProcess


@define
class ContainerRuntime(ABC):
    """Abstract base class for container runtimes (Docker, Podman, etc.)."""

    runtime_name: str

    @abstractmethod
    def run_container(
        self,
        image: str,
        name: str,
        detach: bool = True,
        volumes: list[str] | None = None,
        environment: dict[str, str] | None = None,
        ports: list[str] | None = None,
        workdir: str | None = None,
        command: list[str] | None = None,
        **extra_options: Any,
    ) -> CompletedProcess:
        """Start a new container.

        Args:
            image: Container image to run
            name: Container name
            detach: Run in detached mode
            volumes: Volume mappings (host:container)
            environment: Environment variables
            ports: Port mappings (host:container)
            workdir: Working directory inside container
            command: Command to run in container
            **extra_options: Runtime-specific options

        Returns:
            CompletedProcess with container ID in stdout
        """
        pass

    @abstractmethod
    def start_container(self, name: str) -> CompletedProcess:
        """Start an existing container.

        Args:
            name: Container name

        Returns:
            CompletedProcess
        """
        pass

    @abstractmethod
    def stop_container(self, name: str, timeout: int = 10) -> CompletedProcess:
        """Stop a running container.

        Args:
            name: Container name
            timeout: Seconds to wait before force stopping

        Returns:
            CompletedProcess
        """
        pass

    @abstractmethod
    def remove_container(self, name: str, force: bool = False) -> CompletedProcess:
        """Remove a container.

        Args:
            name: Container name
            force: Force removal of running container

        Returns:
            CompletedProcess
        """
        pass

    @abstractmethod
    def exec_in_container(
        self,
        name: str,
        command: list[str],
        interactive: bool = False,
        tty: bool = False,
        user: str | None = None,
        workdir: str | None = None,
        environment: dict[str, str] | None = None,
    ) -> CompletedProcess:
        """Execute command in a running container.

        Args:
            name: Container name
            command: Command to execute
            interactive: Keep STDIN open
            tty: Allocate pseudo-TTY
            user: User to run as
            workdir: Working directory
            environment: Environment variables

        Returns:
            CompletedProcess with command output
        """
        pass

    @abstractmethod
    def container_exists(self, name: str) -> bool:
        """Check if container exists.

        Args:
            name: Container name

        Returns:
            True if container exists
        """
        pass

    @abstractmethod
    def container_running(self, name: str) -> bool:
        """Check if container is running.

        Args:
            name: Container name

        Returns:
            True if container is running
        """
        pass

    @abstractmethod
    def get_container_logs(
        self,
        name: str,
        follow: bool = False,
        tail: int | None = None,
        since: str | None = None,
    ) -> CompletedProcess:
        """Get container logs.

        Args:
            name: Container name
            follow: Follow log output
            tail: Number of lines to tail
            since: Show logs since timestamp

        Returns:
            CompletedProcess with logs in stdout
        """
        pass

    @abstractmethod
    def build_image(
        self,
        dockerfile: str,
        tag: str,
        context: str = ".",
        build_args: dict[str, str] | None = None,
        **extra_options: Any,
    ) -> CompletedProcess:
        """Build a container image.

        Args:
            dockerfile: Path to Dockerfile
            tag: Image tag
            context: Build context directory
            build_args: Build arguments
            **extra_options: Runtime-specific options

        Returns:
            CompletedProcess
        """
        pass

    @abstractmethod
    def list_containers(self, all: bool = False) -> list[dict[str, Any]]:
        """List containers.

        Args:
            all: Include stopped containers

        Returns:
            List of container information dicts
        """
        pass

    @abstractmethod
    def inspect_container(self, name: str) -> dict[str, Any]:
        """Get detailed container information.

        Args:
            name: Container name

        Returns:
            Container inspection data
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the container runtime is available.

        Returns:
            True if runtime is available and functional
        """
        pass


# 🧰🌍🔚
