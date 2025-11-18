#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Metadata Management
==============================
Handles persistence and management of container metadata."""

from __future__ import annotations

from typing import Any

from attrs import define
from provide.foundation import logger

from wrknv.config import WorkenvConfig
from wrknv.container.storage import ContainerStorage


@define
class ContainerMetadata:
    """Manages container metadata persistence."""

    storage: ContainerStorage
    container_name: str
    image_name: str
    config: WorkenvConfig

    def save(self, additional_data: dict[str, Any] | None = None) -> None:
        """
        Save container metadata.

        Args:
            additional_data: Optional additional metadata to include
        """
        metadata = self.create_from_config()

        if additional_data:
            metadata.update(additional_data)

        self.storage.save_metadata(metadata)
        logger.debug("💾 Saved container metadata", container=self.container_name)

    def load(self) -> dict[str, Any] | None:
        """
        Load container metadata.

        Returns:
            Metadata dict if exists, None otherwise
        """
        metadata = self.storage.load_metadata()

        if metadata:
            logger.debug(f"Loaded metadata: {metadata}")

        return metadata

    def update(self, updates: dict[str, Any]) -> None:
        """
        Update container metadata.

        Args:
            updates: Dictionary of updates to apply
        """
        self.storage.update_metadata(updates)
        logger.debug("🔄 Updated container metadata", container=self.container_name, keys=list(updates.keys()))

    def create_from_config(self) -> dict[str, Any]:
        """
        Create metadata dictionary from current configuration.

        Returns:
            Metadata dictionary
        """
        return {
            "container_name": self.container_name,
            "image_name": self.image_name,
            "project_name": self.config.project_name,
            "config_version": self.config.version,
            "config": {
                "python_version": self.config.container.python_version if self.config.container else None,
                "base_image": self.config.container.base_image if self.config.container else None,
            },
        }

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate that loaded metadata matches current configuration.

        Returns:
            Tuple of (is_valid, list of issues)
        """
        metadata = self.load()

        if not metadata:
            return False, ["No metadata found"]

        issues = []

        # Check project name
        if metadata.get("project_name") != self.config.project_name:
            issues.append(
                f"Project name mismatch: {metadata.get('project_name')} != {self.config.project_name}"
            )

        # Check container name
        if metadata.get("container_name") != self.container_name:
            issues.append(
                f"Container name mismatch: {metadata.get('container_name')} != {self.container_name}"
            )

        return (len(issues) == 0, issues)


# 🧰🌍🔚
