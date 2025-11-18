#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tf Metadata Management
======================
Metadata and RECENT file management for Terraform/OpenTofu managers."""

from __future__ import annotations

import json
import pathlib

from provide.foundation import logger


class TfMetadataManager:
    """Manages metadata and RECENT files for tf tools."""

    def __init__(self, install_path: pathlib.Path, tool_name: str) -> None:
        self.install_path = install_path
        self.tool_name = tool_name
        self.metadata_file = install_path / "metadata.json"
        self.metadata: dict = {}

    def load_metadata(self) -> None:
        """Load metadata from JSON file."""
        if self.metadata_file.exists():
            try:
                with self.metadata_file.open() as f:
                    self.metadata = json.load(f)
                # Migrate old format if needed
                self._migrate_metadata_format()
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _migrate_metadata_format(self) -> None:
        """Migrate old metadata format to new workenv structure."""
        needs_save = False

        # Migrate old active_* keys to workenv structure
        for old_key in ["active_tofu", "active_terraform"]:
            if old_key in self.metadata:
                tool = old_key.replace("active_", "")
                version = self.metadata.pop(old_key)

                # Ensure workenv structure exists
                if "workenv" not in self.metadata:
                    self.metadata["workenv"] = {}
                if "default" not in self.metadata["workenv"]:
                    self.metadata["workenv"]["default"] = {}

                # Set version in new structure
                # Use 'opentofu_version' for tofu
                version_key = "opentofu_version" if tool == "tofu" else f"{tool}_version"

                self.metadata["workenv"]["default"][version_key] = version
                needs_save = True

        if needs_save:
            self.save_metadata()

    def save_metadata(self) -> None:
        """Save metadata to JSON file."""
        try:
            with self.metadata_file.open("w") as f:
                json.dump(self.metadata, f, indent=2, sort_keys=True, default=str)
        except Exception as e:
            logger.warning(f"Failed to save metadata: {e}")

    def update_recent_file(self, installed_versions: list[str]) -> None:
        """Update the RECENT file with current installed versions."""
        recent_file = self.install_path / "RECENT"
        recent_data = {}

        # Read existing RECENT file if it exists
        if recent_file.exists():
            try:
                with recent_file.open() as f:
                    recent_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                recent_data = {}

        # Get tool key for RECENT file
        tool_key = self.tool_name if self.tool_name != "tofu" else "opentofu"

        if installed_versions:
            # Keep only the 5 most recent versions
            recent_data[tool_key] = installed_versions[:5]
        elif tool_key in recent_data:
            # Remove tool if no versions installed
            del recent_data[tool_key]

        # Write updated RECENT file
        try:
            with recent_file.open("w") as f:
                json.dump(recent_data, f)
        except Exception as e:
            logger.warning(f"Failed to update RECENT file: {e}")

    def update_recent_file_with_active(self, version: str, installed_versions: list[str]) -> None:
        """Update RECENT file to put active version first."""
        recent_file = self.install_path / "RECENT"
        recent_data = {}

        # Read existing RECENT file if it exists
        if recent_file.exists():
            try:
                with recent_file.open() as f:
                    recent_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                recent_data = {}

        # Get tool key
        tool_key = self.tool_name if self.tool_name != "tofu" else "opentofu"

        # Put active version first, then other recent versions
        versions_list = [version]
        for v in installed_versions:
            if v != version and len(versions_list) < 5:
                versions_list.append(v)

        recent_data[tool_key] = versions_list

        # Write updated RECENT file
        try:
            with recent_file.open("w") as f:
                json.dump(recent_data, f)
        except Exception as e:
            logger.warning(f"Failed to update RECENT file with active version: {e}")


# 🧰🌍🔚
