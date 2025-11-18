#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Storage Management
============================
Storage path management and volume operations for containers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from attrs import define
from provide.foundation import logger
from provide.foundation.time import provide_now

from wrknv.wenv.schema import ContainerConfig


@define
class ContainerStorage:
    """Manages container storage paths and metadata."""

    container_name: str
    container_config: ContainerConfig

    def setup_storage(self) -> None:
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
        container_dir = storage_base / self.container_name
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
        container_path = storage_base / self.container_name

        if subpath:
            return container_path / subpath
        return container_path

    def get_volume_mappings(self) -> dict[str, str]:
        """Get volume mappings for the container."""
        # Use configured volume mappings if available
        if self.container_config.volume_mappings:
            return self.container_config.volume_mappings.copy()

        # Default volume mappings
        storage_base = Path(self.container_config.storage_path).expanduser()
        volumes_base = self.get_container_path("volumes")
        mappings = {}

        # Map persistent volumes
        for volume_name in self.container_config.persistent_volumes:
            host_path = volumes_base / volume_name
            container_path = f"/wrknv/{volume_name}"
            mappings[str(host_path)] = container_path

        # Map shared downloads (read-only)
        shared_downloads = storage_base / "shared" / "downloads"
        mappings[str(shared_downloads)] = "/downloads:ro"

        # Add current working directory mapping
        mappings[str(Path.cwd())] = "/workspace"

        return mappings

    def save_metadata(self, metadata: dict[str, Any]) -> None:
        """Save container metadata to storage."""
        metadata_path = self.get_container_path("metadata.json")
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        # Add timestamp to metadata
        metadata["last_updated"] = provide_now().isoformat()

        try:
            with metadata_path.open("w") as f:
                json.dump(metadata, f, indent=2)
            logger.debug("📝 Saved container metadata", path=str(metadata_path))
        except Exception as e:
            logger.warning("⚠️ Failed to save metadata", error=str(e))

    def load_metadata(self) -> dict[str, Any] | None:
        """Load container metadata from storage."""
        metadata_path = self.get_container_path("metadata.json")

        if not metadata_path.exists():
            return None

        try:
            with metadata_path.open() as f:
                metadata = json.load(f)
            return metadata
        except Exception as e:
            logger.warning("⚠️ Failed to load metadata", error=str(e))
            return None

    def update_metadata(self, updates: dict[str, Any]) -> None:
        """Update existing metadata with new values."""
        metadata = self.load_metadata() or {}
        metadata.update(updates)
        self.save_metadata(metadata)

    def get_backup_path(self, backup_name: str | None = None) -> Path:
        """Get path for volume backups."""
        backup_dir = self.get_container_path("backups")
        backup_dir.mkdir(exist_ok=True)

        if not backup_name:
            timestamp = provide_now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"volumes_backup_{timestamp}.tar.gz"

        return backup_dir / backup_name

    def get_latest_backup(self) -> Path | None:
        """Get the latest backup file."""
        backup_dir = self.get_container_path("backups")

        if not backup_dir.exists():
            return None

        backup_files = list(backup_dir.glob("volumes_backup_*.tar.gz"))
        if not backup_files:
            return None

        # Sort by modification time, newest first
        backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backup_files[0]

    def clean_storage(self, preserve_backups: bool = True) -> bool:
        """Clean up container storage, optionally preserving backups."""
        container_dir = self.get_container_path()

        if not container_dir.exists():
            return True

        try:
            # Clean up volumes
            volumes_dir = container_dir / "volumes"
            if volumes_dir.exists():
                for volume_path in volumes_dir.iterdir():
                    if volume_path.is_dir():
                        import shutil

                        shutil.rmtree(volume_path)
                        logger.info("🗑️ Removed volume", volume=volume_path.name)

            # Clean up build artifacts
            build_dir = container_dir / "build"
            if build_dir.exists():
                import shutil

                shutil.rmtree(build_dir)
                build_dir.mkdir(exist_ok=True)

            # Clean up logs
            logs_dir = container_dir / "logs"
            if logs_dir.exists():
                for log_file in logs_dir.glob("*.log"):
                    log_file.unlink()

            # Optionally clean up backups
            if not preserve_backups:
                backups_dir = container_dir / "backups"
                if backups_dir.exists():
                    import shutil

                    shutil.rmtree(backups_dir)
                    backups_dir.mkdir(exist_ok=True)

            logger.info("🧹 Cleaned container storage", container=self.container_name)
            return True

        except Exception as e:
            logger.error("❌ Failed to clean storage", error=str(e))
            return False


# 🧰🌍🔚
