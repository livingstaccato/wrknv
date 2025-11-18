#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container-specific Errors
=========================
Custom exceptions for container operations using foundation error hierarchy."""

from __future__ import annotations

from provide.foundation.errors import (
    AlreadyExistsError,
    NotFoundError,
    ResourceError,
    RuntimeError,
    StateError,
)


class ContainerNotFoundError(NotFoundError):
    """Raised when a container is not found."""

    def __init__(self, container_name: str) -> None:
        super().__init__(
            message=f"Container '{container_name}' not found",
            resource_type="container",
            resource_id=container_name,
            hint="Use 'docker ps -a' to list all containers",
        )
        self.container_name = container_name


class ContainerNotRunningError(StateError):
    """Raised when a container is not running but needs to be."""

    def __init__(self, container_name: str) -> None:
        super().__init__(
            message=f"Container '{container_name}' is not running",
            expected_state="running",
            current_state="stopped",
            hint=f"Start the container with 'docker start {container_name}'",
        )
        self.container_name = container_name


class ContainerAlreadyExistsError(AlreadyExistsError):
    """Raised when trying to create a container that already exists."""

    def __init__(self, container_name: str) -> None:
        super().__init__(
            message=f"Container '{container_name}' already exists",
            resource_type="container",
            resource_id=container_name,
            hint=f"Use 'docker rm {container_name}' to remove existing container",
        )
        self.container_name = container_name


class ImageNotFoundError(NotFoundError):
    """Raised when a container image is not found."""

    def __init__(self, image_name: str) -> None:
        super().__init__(
            message=f"Image '{image_name}' not found",
            resource_type="image",
            resource_id=image_name,
            hint=f"Pull the image with 'docker pull {image_name}'",
        )
        self.image_name = image_name


class VolumeNotFoundError(NotFoundError):
    """Raised when a volume is not found."""

    def __init__(self, volume_name: str) -> None:
        super().__init__(
            message=f"Volume '{volume_name}' not found",
            resource_type="volume",
            resource_id=volume_name,
            hint="Use 'docker volume ls' to list available volumes",
        )
        self.volume_name = volume_name


class ContainerRuntimeError(RuntimeError):
    """Raised when the container runtime is not available."""

    def __init__(self, runtime: str, reason: str | None = None) -> None:
        message = f"Container runtime '{runtime}' is not available"
        if reason:
            message += f": {reason}"

        super().__init__(
            message=message,
            operation="container_runtime_check",
            retry_possible=True,
            hint="Ensure Docker is installed and running",
        )
        self.runtime = runtime
        self.reason = reason


class ContainerBuildError(ResourceError):
    """Raised when container build fails."""

    def __init__(self, image_tag: str, reason: str | None = None) -> None:
        message = f"Failed to build image '{image_tag}'"
        if reason:
            message += f": {reason}"

        super().__init__(
            message=message,
            resource_type="image",
            resource_path=image_tag,
            hint="Check Dockerfile syntax and build context",
        )
        self.image_tag = image_tag
        self.reason = reason


# 🧰🌍🔚
