#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Docker Runtime Implementation
=============================
Docker-specific implementation of the container runtime."""

from __future__ import annotations

import json
from typing import Any

from attrs import define
from provide.foundation import logger
from provide.foundation.process import (
    CompletedProcess,
    ProcessError,
    run,
)
from provide.foundation.resilience import circuit_breaker

from wrknv.container.runtime.base import ContainerRuntime


@define
class DockerRuntime(ContainerRuntime):
    """Docker implementation of container runtime."""

    runtime_name: str
    runtime_command: str

    def run_container(
        self,
        image: str,
        name: str,
        detach: bool,
        volumes: list[str] | None,
        environment: dict[str, str] | None,
        ports: list[str] | None,
        workdir: str | None,
        command: list[str] | None,
        **extra_options: Any,
    ) -> CompletedProcess:
        """Start a new Docker container."""
        cmd = [self.runtime_command, "run"]

        if detach:
            cmd.append("-d")

        cmd.extend(["--name", name])

        # Add volumes
        for volume in volumes or []:
            cmd.extend(["-v", volume])

        # Add environment variables
        for key, value in (environment or {}).items():
            cmd.extend(["-e", f"{key}={value}"])

        # Add ports
        for port in ports or []:
            cmd.extend(["-p", port])

        # Add workdir
        if workdir:
            cmd.extend(["--workdir", workdir])

        # Add extra Docker-specific options
        if extra_options.get("restart"):
            cmd.extend(["--restart", extra_options["restart"]])
        if extra_options.get("network"):
            cmd.extend(["--network", extra_options["network"]])
        if extra_options.get("hostname"):
            cmd.extend(["--hostname", extra_options["hostname"]])

        # Add image
        cmd.append(image)

        # Add command
        if command:
            cmd.extend(command)

        try:
            result = run(cmd, check=True)
            logger.info(
                "Docker container started",
                name=name,
                image=image,
                container_id=result.stdout.strip()[:12] if result.stdout else None,
            )
            return result
        except ProcessError as e:
            logger.error(
                "Failed to start Docker container",
                name=name,
                image=image,
                error=str(e),
                stderr=e.stderr,
            )
            raise

    def start_container(self, name: str) -> CompletedProcess:
        """Start an existing Docker container."""
        try:
            result = run([self.runtime_command, "start", name], check=True)
            logger.info("Docker container started", name=name)
            return result
        except ProcessError as e:
            logger.error("Failed to start Docker container", name=name, error=str(e))
            raise

    def stop_container(self, name: str, timeout: int) -> CompletedProcess:
        """Stop a running Docker container."""
        try:
            result = run([self.runtime_command, "stop", "-t", str(timeout), name], check=True)
            logger.info("Docker container stopped", name=name)
            return result
        except ProcessError as e:
            logger.error("Failed to stop Docker container", name=name, error=str(e))
            raise

    def remove_container(self, name: str, force: bool) -> CompletedProcess:
        """Remove a Docker container."""
        cmd = [self.runtime_command, "rm"]
        if force:
            cmd.append("-f")
        cmd.append(name)

        try:
            result = run(cmd, check=True)
            logger.info("Docker container removed", name=name, forced=force)
            return result
        except ProcessError as e:
            logger.error("Failed to remove Docker container", name=name, error=str(e))
            raise

    def exec_in_container(
        self,
        name: str,
        command: list[str],
        interactive: bool,
        tty: bool,
        user: str | None,
        workdir: str | None,
        environment: dict[str, str] | None,
    ) -> CompletedProcess:
        """Execute command in a running Docker container."""
        cmd = [self.runtime_command, "exec"]

        if interactive:
            cmd.append("-i")
        if tty:
            cmd.append("-t")
        if user:
            cmd.extend(["-u", user])
        if workdir:
            cmd.extend(["-w", workdir])

        for key, value in (environment or {}).items():
            cmd.extend(["-e", f"{key}={value}"])

        cmd.append(name)
        cmd.extend(command)

        try:
            # Note: Interactive mode may need special handling
            # Check if foundation.process supports it
            result = run(cmd, check=True)
            logger.debug(
                "Docker exec completed",
                name=name,
                command=command,
                interactive=interactive,
            )
            return result
        except ProcessError as e:
            logger.error(
                "Docker exec failed",
                name=name,
                command=command,
                error=str(e),
            )
            raise

    def container_exists(self, name: str) -> bool:
        """Check if Docker container exists."""
        try:
            result = run([self.runtime_command, "ps", "-a", "--format", "{{.Names}}"], check=False)
            return name in result.stdout.splitlines() if result.stdout else False
        except ProcessError:
            return False

    def container_running(self, name: str) -> bool:
        """Check if Docker container is running."""
        try:
            result = run([self.runtime_command, "ps", "--format", "{{.Names}}"], check=False)
            return name in result.stdout.splitlines() if result.stdout else False
        except ProcessError:
            return False

    def get_container_logs(
        self,
        name: str,
        follow: bool,
        tail: int | None,
        since: str | None,
    ) -> CompletedProcess:
        """Get Docker container logs."""
        cmd = [self.runtime_command, "logs"]

        if follow:
            cmd.append("-f")
        if tail is not None:
            cmd.extend(["--tail", str(tail)])
        if since:
            cmd.extend(["--since", since])

        cmd.append(name)

        try:
            result = run(cmd, check=True)
            return result
        except ProcessError as e:
            logger.error("Failed to get Docker logs", name=name, error=str(e))
            raise

    def build_image(
        self,
        dockerfile: str,
        tag: str,
        context: str,
        build_args: dict[str, str] | None,
        **extra_options: Any,
    ) -> CompletedProcess:
        """Build a Docker image."""
        cmd = [self.runtime_command, "build", "-f", dockerfile, "-t", tag]

        for key, value in (build_args or {}).items():
            cmd.extend(["--build-arg", f"{key}={value}"])

        if extra_options.get("no_cache"):
            cmd.append("--no-cache")
        if extra_options.get("platform"):
            cmd.extend(["--platform", extra_options["platform"]])

        cmd.append(context)

        try:
            result = run(cmd, check=True)
            logger.info("Docker image built", tag=tag, dockerfile=dockerfile)
            return result
        except ProcessError as e:
            logger.error(
                "Docker build failed",
                tag=tag,
                dockerfile=dockerfile,
                error=str(e),
            )
            raise

    def list_containers(self, all: bool) -> list[dict[str, Any]]:
        """List Docker containers."""
        cmd = [self.runtime_command, "ps", "--format", "json"]
        if all:
            cmd.append("-a")

        try:
            result = run(cmd, check=True)
            containers = []
            if result.stdout:
                for line in result.stdout.strip().splitlines():
                    if line:
                        containers.append(json.loads(line))
            return containers
        except (ProcessError, json.JSONDecodeError) as e:
            logger.error("Failed to list Docker containers", error=str(e))
            return []

    def inspect_container(self, name: str) -> dict[str, Any]:
        """Get detailed Docker container information."""
        try:
            result = run([self.runtime_command, "inspect", name], check=True)
            if result.stdout:
                data = json.loads(result.stdout)
                return data[0] if data else {}
            return {}
        except (ProcessError, json.JSONDecodeError) as e:
            logger.error("Failed to inspect Docker container", name=name, error=str(e))
            return {}

    @circuit_breaker(
        failure_threshold=3,
        recovery_timeout=30.0,
        expected_exception=(ProcessError, OSError),
    )
    def is_available(self) -> bool:
        """Check if Docker is available.

        Uses circuit breaker to prevent repeated checks when Docker is unavailable.
        If circuit is open, raises RuntimeError which callers should catch.
        """
        try:
            result = run([self.runtime_command, "version"], check=False)
            if result.returncode != 0:
                # Treat non-zero exit as failure to trigger circuit breaker
                raise ProcessError(
                    message="Docker not available",
                    command=[self.runtime_command, "version"],
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            return True
        except (ProcessError, OSError):
            # Re-raise to let circuit breaker count this as a failure
            raise


# 🧰🌍🔚
