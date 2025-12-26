#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Manager Implementation
================================
Thin orchestration facade for container operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from attrs import define, field
from provide.foundation import logger
from rich.console import Console

from wrknv.config import WorkenvConfig
from wrknv.container.metadata import ContainerMetadata
from wrknv.container.operations import (
    ContainerBuilder,
    ContainerExec,
    ContainerLifecycle,
    ContainerLogs,
    VolumeManager,
)
from wrknv.container.runtime.docker import DockerRuntime
from wrknv.container.storage import ContainerStorage
from wrknv.wenv.schema import ContainerConfig, get_default_config


@define
class ContainerManager:
    """Orchestrates container operations through specialized components."""

    config: WorkenvConfig = field()
    console: Console = field(factory=Console)

    # Container identification
    container_name: str = field(init=False)
    image_name: str = field(init=False)
    image_tag: str = field(init=False, default="latest")
    full_image: str = field(init=False)

    # Container configuration
    container_config: ContainerConfig = field(init=False)

    # Operations components
    storage: ContainerStorage = field(init=False)
    runtime: DockerRuntime = field(init=False)
    lifecycle: ContainerLifecycle = field(init=False)
    exec: ContainerExec = field(init=False)
    builder: ContainerBuilder = field(init=False)
    logs: ContainerLogs = field(init=False)
    volumes: VolumeManager = field(init=False)
    metadata: ContainerMetadata = field(init=False)

    def __attrs_post_init__(self) -> None:
        """Initialize container components."""
        # Get container configuration
        self.container_config = self.config.container or ContainerConfig()

        # Set container and image names
        project_name = self.config.project_name.replace(" ", "-").lower()
        self.container_name = f"{project_name}-dev" if project_name != "my-project" else "wrknv-dev"
        self.image_name = self.container_name
        self.full_image = f"{self.image_name}:{self.image_tag}"

        # Initialize storage
        self.storage = ContainerStorage(
            container_name=self.container_name,
            container_config=self.container_config,
        )
        self.storage.setup_storage()

        # Initialize runtime
        self.runtime = DockerRuntime(runtime_name="docker", runtime_command="docker")

        # Initialize operations
        self.lifecycle = ContainerLifecycle(
            runtime=self.runtime,
            container_name=self.container_name,
            console=self.console,
            start_emoji="🚀",
            stop_emoji="⏹️",
            restart_emoji="🔄",
            status_emoji="📊",
        )

        self.exec = ContainerExec(
            runtime=self.runtime,
            container_name=self.container_name,
            console=self.console,
            available_shells=["/bin/bash", "/bin/sh"],
            default_shell="/bin/bash",
        )

        self.builder = ContainerBuilder(runtime=self.runtime, console=self.console)

        self.logs = ContainerLogs(
            runtime=self.runtime, container_name=self.container_name, console=self.console
        )

        self.volumes = VolumeManager(
            runtime=self.runtime,
            console=self.console,
            backup_dir=self.storage.get_container_path("backups"),
        )

        self.metadata = ContainerMetadata(
            storage=self.storage,
            container_name=self.container_name,
            image_name=self.full_image,
            config=self.config,
        )

    # Status checks

    def check_docker(self) -> bool:
        """Check if Docker is available and running."""
        try:
            return self.runtime.is_available()
        except RuntimeError:
            return False

    def container_exists(self) -> bool:
        """Check if the container exists."""
        return self.lifecycle.exists()

    def container_running(self) -> bool:
        """Check if the container is currently running."""
        return self.lifecycle.is_running()

    def image_exists(self) -> bool:
        """Check if the container image exists."""
        return self.builder.image_exists(self.full_image)

    # Build operations

    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile content from configuration.

        This is a convenience wrapper for testing.

        Returns:
            Dockerfile content as string
        """
        return self.builder.generate_dockerfile(self.container_config)

    def build_image(self, rebuild: bool = False) -> bool:
        """Build the container image."""
        build_dir = self.storage.get_container_path("build")
        build_dir.mkdir(parents=True, exist_ok=True)

        # Generate and save Dockerfile
        dockerfile_path = build_dir / "Dockerfile"
        dockerfile_content = self._generate_dockerfile()
        dockerfile_path.write_text(dockerfile_content)

        # Build arguments from config
        build_args = {}
        if self.container_config.environment:
            build_args.update(self.container_config.environment)

        # Build the image
        return self.builder.build(
            dockerfile=str(dockerfile_path),
            tag=self.full_image,
            context=str(build_dir),
            build_args=build_args,
            stream_output=False,
        )

    # Lifecycle operations

    def start(self, force_rebuild: bool = False) -> bool:
        """Start the container, building if necessary."""
        # Build image if needed
        if (force_rebuild or not self.image_exists()) and not self.build_image(rebuild=force_rebuild):
            return False

        # Prepare run options
        run_options = {
            "image": self.full_image,
            "volumes": self.storage.get_volume_mappings(),
            "environment": self.container_config.environment or {},
            "ports": self.container_config.ports or [],
            "workdir": "/workspace",
        }

        return self.lifecycle.start(create_if_missing=True, **run_options)

    def stop(self, timeout: int = 10) -> bool:
        """Stop the container."""
        return self.lifecycle.stop(timeout=timeout)

    def restart(self, timeout: int = 10) -> bool:
        """Restart the container."""
        return self.lifecycle.restart(timeout=timeout)

    def enter(
        self,
        command: str | None = None,
        user: str | None = None,
        workdir: str | None = None,
        environment: dict[str, str] | None = None,
    ) -> bool:
        """Enter the container with an interactive shell or command."""
        return self.exec.enter(command=command, user=user, workdir=workdir, environment=environment)

    def status(self) -> dict[str, Any]:
        """Get container status information."""
        lifecycle_status = self.lifecycle.status()

        try:
            docker_available = self.runtime.is_available()
        except RuntimeError:
            docker_available = False

        return {
            "docker_available": docker_available,
            "container_exists": lifecycle_status.get("exists", False),
            "container_running": lifecycle_status.get("running", False),
            "container_info": {
                "name": lifecycle_status.get("name"),
                "state": lifecycle_status.get("status"),
                "id": lifecycle_status.get("id"),
                "image": lifecycle_status.get("image"),
            },
        }

    # Volume operations (delegate to VolumeManager)

    def backup_volumes(
        self,
        backup_path: Path | None = None,
        volumes: list[str] | None = None,
        compress: bool = True,
    ) -> Path | None:
        """Backup container volumes."""
        import tarfile

        from provide.foundation.time import provide_now

        try:
            if backup_path is None:
                timestamp = provide_now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.storage.get_backup_path(f"volumes_backup_{timestamp}.tar.gz")

            backup_path.parent.mkdir(parents=True, exist_ok=True)
            volumes_dir = self.storage.get_container_path("volumes")

            if not volumes_dir.exists():
                logger.warning("No volumes directory to backup", path=str(volumes_dir))
                return None

            with tarfile.open(backup_path, "w:gz" if compress else "w") as tar:
                tar.add(volumes_dir, arcname="volumes")

            return backup_path

        except Exception as e:
            logger.error("Failed to backup volumes", error=str(e))
            return None

    def restore_volumes(self, backup_path: Path, force: bool = False) -> bool:
        """Restore container volumes from backup."""
        import shutil
        import tarfile

        from provide.foundation.archive.security import is_safe_path

        try:
            if not backup_path.exists():
                logger.error("Backup file not found", path=str(backup_path))
                return False

            container_dir = self.storage.get_container_path()
            volumes_dir = container_dir / "volumes"

            if volumes_dir.exists() and not force:
                logger.warning("Volumes already exist, use force=True to overwrite")
                return False

            if volumes_dir.exists() and force:
                shutil.rmtree(volumes_dir)

            with tarfile.open(backup_path, "r:*") as tar:
                # Filter members using foundation's is_safe_path to prevent path traversal
                safe_members = [m for m in tar.getmembers() if is_safe_path(container_dir, m.name)]
                # Log any skipped members
                skipped = len(tar.getmembers()) - len(safe_members)
                if skipped > 0:
                    logger.warning(
                        "Skipped potentially unsafe tar members",
                        skipped_count=skipped,
                    )
                tar.extractall(container_dir, members=safe_members)

            logger.info("📥 Restored volumes from backup", backup=str(backup_path))
            return True

        except Exception as e:
            logger.error("Failed to restore volumes", error=str(e), backup=str(backup_path))
            return False

    def clean_volumes(self, preserve: list[str] | None = None) -> bool:
        """Clean up container volumes."""
        import shutil

        try:
            volumes_dir = self.storage.get_container_path("volumes")

            if not volumes_dir.exists():
                return True

            for volume_path in volumes_dir.iterdir():
                if volume_path.is_dir():
                    if preserve and volume_path.name in preserve:
                        logger.debug("Preserving volume", volume=volume_path.name)
                        continue

                    shutil.rmtree(volume_path)
                    volume_path.mkdir(exist_ok=True)
                    logger.info("🗑️ Cleaned volume", volume=volume_path.name)

            return True

        except Exception as e:
            logger.error("Failed to clean volumes", error=str(e))
            return False

    # Logs operations

    def get_logs(
        self,
        lines: int | None = None,
        follow: bool = False,
        since: str | None = None,
    ) -> str | None:
        """Get container logs."""
        return self.logs.get_logs(tail=lines, follow=follow, since=since, timestamps=False)

    # Cleanup operations

    def clean(self, preserve_volumes: bool = False) -> bool:
        """Clean up container and optionally volumes."""
        success = True

        if self.container_exists():
            if self.container_running():
                success = self.stop() and success
            success = self.lifecycle.remove(force=False) and success

        if not preserve_volumes:
            success = self.clean_volumes() and success

        success = self.storage.clean_storage(preserve_backups=True) and success

        if success:
            logger.info("🧹 Container cleanup completed", container=self.container_name)
        else:
            logger.warning("⚠️ Container cleanup had some issues", container=self.container_name)

        return success

    # Storage delegation

    def get_container_path(self, subpath: str = "") -> Path:
        """Get path to container-specific directory or file."""
        return self.storage.get_container_path(subpath)

    def get_volume_mappings(self) -> dict[str, str]:
        """Get volume mappings for the container."""
        return self.storage.get_volume_mappings()

    # Metadata delegation

    def save_metadata(self) -> None:
        """Save container metadata."""
        self.metadata.save()

    def load_metadata(self) -> dict[str, Any] | None:
        """Load container metadata."""
        return self.metadata.load()

    def update_metadata(self, updates: dict[str, Any]) -> None:
        """Update container metadata."""
        self.metadata.update(updates)


def create_container_manager(project_name: str | None = None) -> ContainerManager:
    """Create a ContainerManager with default configuration."""
    config = get_default_config(project_name or "my-project")
    return ContainerManager(config=config)


# 🧰🌍🔚
