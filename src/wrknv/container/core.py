#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Core Management
=========================
Core container management functionality for wrknv."""

from __future__ import annotations

from pathlib import Path

from provide.foundation import logger
from provide.foundation.process import run
from rich.console import Console

from wrknv.config import WorkenvConfig
from wrknv.wenv.schema import ContainerConfig, get_default_config


class ContainerManager:
    """Manages Docker containers for wrknv development environments."""

    # Default values (can be overridden by config)
    DEFAULT_CONTAINER_NAME = "wrknv-dev"
    DEFAULT_IMAGE_NAME = "wrknv-dev"
    DEFAULT_IMAGE_TAG = "latest"

    # Emoji constants for visual feedback
    CONTAINER_EMOJI = "🐳"
    BUILD_EMOJI = "🔨"
    START_EMOJI = "🚀"
    STOP_EMOJI = "⏹️"
    CLEAN_EMOJI = "🧹"
    STATUS_EMOJI = "📊"

    def __init__(self, config: WorkenvConfig | None = None) -> None:
        self.config = config or get_default_config()
        self.console = Console()

        # Get container configuration
        self.container_config = self.config.container or ContainerConfig()

        # Set container and image names (can be customized in config)
        project_name = self.config.project_name.replace(" ", "-").lower()
        if project_name != "my-project":
            self.CONTAINER_NAME = f"{project_name}-dev"
        else:
            self.CONTAINER_NAME = self.DEFAULT_CONTAINER_NAME
        self.IMAGE_NAME = self.CONTAINER_NAME
        self.IMAGE_TAG = self.DEFAULT_IMAGE_TAG
        self.full_image = f"{self.IMAGE_NAME}:{self.IMAGE_TAG}"

        # Initialize storage on creation
        self._setup_storage()

    def _setup_storage(self) -> None:
        """Set up the container storage directory structure."""
        # Expand storage path
        storage_base = Path(self.container_config.storage_path).expanduser()

        # Create base directories
        storage_base.mkdir(parents=True, exist_ok=True)

        # Create shared directories
        shared_dir = storage_base / "shared"
        shared_dir.mkdir(exist_ok=True)
        (shared_dir / "downloads").mkdir(exist_ok=True)

        # Create container-specific directories
        container_dir = storage_base / self.CONTAINER_NAME
        container_dir.mkdir(exist_ok=True)

        # Create subdirectories
        volumes_dir = container_dir / "volumes"
        volumes_dir.mkdir(exist_ok=True)

        # Create persistent volume directories
        for volume_name in self.container_config.persistent_volumes:
            (volumes_dir / volume_name).mkdir(exist_ok=True)

        (container_dir / "build").mkdir(exist_ok=True)
        (container_dir / "logs").mkdir(exist_ok=True)
        (container_dir / "backups").mkdir(exist_ok=True)

    def get_container_path(self, subpath: str = "") -> Path:
        """Get path to container-specific directory or file.

        Args:
            subpath: Relative path within the container directory

        Returns:
            Path object pointing to the requested location
        """
        storage_base = Path(self.container_config.storage_path).expanduser()
        container_path = storage_base / self.CONTAINER_NAME

        if subpath:
            return container_path / subpath
        return container_path

    def check_docker(self) -> bool:
        """Check if Docker is installed and running."""
        try:
            result = run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Docker check failed: {e}")
            return False

    def container_exists(self) -> bool:
        """Check if the container exists."""
        try:
            result = run(
                ["docker", "container", "inspect", self.CONTAINER_NAME],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Container exists check failed: {e}")
            return False

    def container_running(self) -> bool:
        """Check if the container is currently running."""
        if not self.container_exists():
            return False

        try:
            result = run(
                ["docker", "container", "inspect", "-f", "{{.State.Running}}", self.CONTAINER_NAME],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 and result.stdout.strip() == "true"
        except Exception as e:
            logger.debug(f"Container running check failed: {e}")
            return False

    def image_exists(self) -> bool:
        """Check if the container image exists."""
        try:
            result = run(
                ["docker", "image", "inspect", self.full_image],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Image exists check failed: {e}")
            return False

    def get_volume_mappings(self) -> dict[str, str]:
        """Get volume mappings for the container."""
        # Use configured volume mappings if available
        if self.container_config.volume_mappings:
            return self.container_config.volume_mappings.copy()

        # Default volume mappings
        volumes_base = self.get_container_path("volumes")
        mappings = {}

        # Map persistent volumes
        for volume_name in self.container_config.persistent_volumes:
            host_path = volumes_base / volume_name
            container_path = f"/wrknv/{volume_name}"
            mappings[str(host_path)] = container_path

        # Add current working directory mapping
        mappings[str(Path.cwd())] = "/workspace"

        return mappings


# 🧰🌍🔚
