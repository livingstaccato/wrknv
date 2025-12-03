#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tf Manager Base
===============
Base class for Tf (IBM Terraform/OpenTofu) managers that use ~/.terraform.versions
directory structure. This implementation is compatible with tfswitch and
designed for managing Tf tool versions."""

from __future__ import annotations

from abc import abstractmethod
import os
import pathlib
from typing import TYPE_CHECKING

from provide.foundation import logger
from provide.foundation.file import safe_copy, safe_delete, safe_rmtree
from provide.foundation.time import provide_now

from wrknv.managers.base import BaseToolManager, ToolManagerError
from wrknv.managers.tf.bin_ops import copy_tf_binaries_to_workenv
from wrknv.managers.tf.metadata import TfMetadataManager
from wrknv.managers.tf.utils import (
    calculate_file_hash,
    get_tool_version_key,
    version_sort_key,
)
from wrknv.wenv.bin_manager import get_workenv_bin_dir

if TYPE_CHECKING:
    from wrknv.config import WorkenvConfig


class TfManager(BaseToolManager):
    """
    Base class for Tf tool managers using ~/.terraform.versions directory.

    This directory structure is compatible with tfswitch, allowing users to
    use either tool interchangeably while providing enhanced metadata tracking
    for advanced features. Supports both IBM Terraform (formerly HashiCorp) and OpenTofu.
    """

    def __init__(self, config: WorkenvConfig | None = None) -> None:
        super().__init__(config)
        # Override install path to use tf versions directory
        self.install_path = pathlib.Path("~/.terraform.versions").expanduser()
        self.install_path.mkdir(parents=True, exist_ok=True)

        # Get workenv bin directory for copying active binaries
        self.workenv_bin_dir = get_workenv_bin_dir(config)

        # Metadata manager
        self.metadata_manager = TfMetadataManager(self.install_path, self.tool_name)
        self.metadata_manager.load_metadata()

        # Expose metadata for backward compatibility
        self.metadata = self.metadata_manager.metadata
        self.metadata_file = self.metadata_manager.metadata_file

    @property
    @abstractmethod
    def tool_prefix(self) -> str:
        """Prefix for version files (e.g., 'terraform' or 'opentofu')."""

    def _save_metadata(self) -> None:
        """Save metadata to JSON file."""
        self.metadata_manager.save_metadata()

    def _update_recent_file(self) -> None:
        """Update the RECENT file with current installed versions."""
        installed_versions = self.get_installed_versions()
        self.metadata_manager.update_recent_file(installed_versions)

    def _update_recent_file_with_active(self, version: str) -> None:
        """Update RECENT file to put active version first."""
        installed_versions = self.get_installed_versions()
        self.metadata_manager.update_recent_file_with_active(version, installed_versions)

    def get_binary_path(self, version: str) -> pathlib.Path:
        """Get path to the installed binary for a version."""
        # In tf versions format, binaries are stored as prefix_version
        binary_name = f"{self.tool_prefix}_{version}"
        return self.install_path / binary_name

    def get_installed_versions(self) -> list[str]:
        """Get all installed versions of this tool."""
        versions = []

        prefix = f"{self.tool_prefix}_"
        for item in self.install_path.iterdir():
            if item.is_file() and item.name.startswith(prefix):
                # Extract version from filename
                version = item.name[len(prefix) :]
                if self._is_version_dir(version):
                    versions.append(version)

        return sorted(versions, key=version_sort_key, reverse=True)

    def get_installed_version(self) -> str | None:
        """Get currently active version from metadata only (no system fallbacks)."""
        # Get current profile (default to 'default')
        profile = self._get_current_profile()

        # Check metadata for active version in workenv
        if "workenv" in self.metadata:
            profile_data = self.metadata["workenv"].get(profile, {})
            tool_key = get_tool_version_key(self.tool_name)

            if tool_key in profile_data:
                return profile_data[tool_key]

        # No fallbacks - workenv is completely self-contained
        return None

    def set_installed_version(self, version: str) -> None:
        """Set the active version in metadata."""
        # Get current profile
        profile = self._get_current_profile()

        # Ensure workenv structure exists
        if "workenv" not in self.metadata:
            self.metadata["workenv"] = {}
        if profile not in self.metadata["workenv"]:
            self.metadata["workenv"][profile] = {}

        # Store active version in metadata under workenv profile
        tool_key = get_tool_version_key(self.tool_name)
        self.metadata["workenv"][profile][tool_key] = version
        self._save_metadata()

        # Also ensure it's at the front of RECENT
        self._update_recent_file_with_active(version)

        # Note: actual venv copying happens in create_symlink()

        logger.info(f"Set {self.tool_name} active version to {version} in profile '{profile}'")

    def remove_version(self, version: str) -> None:
        """Remove a specific version of the tool."""
        binary_path = self.get_binary_path(version)

        if binary_path.exists():
            safe_delete(binary_path, missing_ok=True)
            logger.info(f"Removed {self.tool_name} {version}")

            # Update metadata
            version_key = f"{self.tool_prefix}_{version}"
            if version_key in self.metadata:
                del self.metadata[version_key]
                self._save_metadata()

            # Update RECENT file
            self._update_recent_file()

        # Update config if this was the current version
        if self.get_installed_version() == version:
            try:
                self.config.set_tool_version(self.tool_name, "")
            except Exception:
                logger.debug(f"Could not clear {self.tool_name} version in config")

    def _install_from_archive(self, archive_path: pathlib.Path, version: str) -> None:
        """Install tool from downloaded archive in tf versions format."""
        # Extract to temporary directory
        extract_dir = self.cache_dir / f"{self.tool_prefix}_{version}_extract"
        extract_dir.mkdir(exist_ok=True)

        try:
            self.extract_archive(archive_path, extract_dir)

            # Find the binary in extracted files
            # Note: Archive contains binary with original name (terraform/tofu)
            # We search for the archive name, then copy to our target name
            if self.tool_name == "tofu":
                archive_binary_name = "tofu"
            elif self.tool_name == "ibmtf":
                archive_binary_name = "terraform"  # IBM Terraform binary is named "terraform" in archive
            else:
                archive_binary_name = self.executable_name

            binary_path = None
            for file_path in extract_dir.rglob(f"{archive_binary_name}*"):
                if file_path.is_file() and file_path.name in [
                    archive_binary_name,
                    f"{archive_binary_name}.exe",
                ]:
                    binary_path = file_path
                    break

            if not binary_path:
                raise ToolManagerError(
                    f"{self.tool_name} binary not found in archive (looking for {archive_binary_name})"
                )

            # Copy to tf versions location with the correct target name
            target_path = self.get_binary_path(version)
            safe_copy(binary_path, target_path, overwrite=True)

            # Make executable (Unix systems)
            self.make_executable(target_path)

            logger.info(f"Installed {self.tool_name} binary to: {target_path}")

            # Calculate installed binary hash
            binary_hash = calculate_file_hash(target_path)

            # Update metadata with comprehensive information
            self._update_install_metadata(version, archive_path, binary_hash)

            # Update RECENT file
            self._update_recent_file()

            # Verify installation
            if not self.verify_installation(version):
                raise ToolManagerError(f"{self.tool_name} {version} installation verification failed")

        finally:
            # Clean up extraction directory
            safe_rmtree(extract_dir, missing_ok=True)

    def _update_install_metadata(self, version: str, archive_path: pathlib.Path, binary_hash: str) -> None:
        """Update metadata for installed version with comprehensive information."""
        version_key = f"{self.tool_prefix}_{version}"

        # Get download URL for source tracking
        download_url = self.get_download_url(version)
        checksum_url = self.get_checksum_url(version)

        # Get file size
        binary_path = self.get_binary_path(version)
        file_size = binary_path.stat().st_size if binary_path.exists() else 0

        # Look for signature files
        sig_patterns = [
            f"{self.tool_prefix}_*.asc",
            f"{self.tool_prefix}_*SHA256SUMS.sig",
            f"{self.tool_name}_*.asc",
        ]
        signature_files = []
        for pattern in sig_patterns:
            signature_files.extend(self.install_path.glob(pattern))

        self.metadata[version_key] = {
            "tool": self.tool_name,
            "version": version,
            "installed_at": provide_now().isoformat(),
            "download_url": download_url,
            "checksum_url": checksum_url if checksum_url else None,
            "archive_path": str(archive_path),
            "archive_size": archive_path.stat().st_size if archive_path.exists() else 0,
            "binary_path": str(binary_path),
            "binary_size": file_size,
            "binary_sha256": binary_hash,
            "signature_files": [str(f) for f in signature_files],
            "platform": self.get_platform_info(),
            "wrknv_version": "0.1.0",  # Track which version of wrknv installed this
        }

        self._save_metadata()

    def create_symlink(self, version: str) -> None:
        """Copy active tf binaries to venv bin directory for direct access.

        This replaces symlinks with a copy strategy that works on all platforms
        including Windows. The active binaries are copied to the venv's bin
        directory where they can be executed directly.
        """
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.warning(f"Binary not found at {binary_path}, skipping activation")
            return

        # Track the active version in metadata first
        self.set_installed_version(version)

        # Copy all active tf binaries to venv bin directory
        self._copy_active_binaries_to_venv()

        logger.info(f"Copied {self.tool_name} {version} to venv bin directory")

    def set_global_version(self, version: str) -> None:
        """Set a version as the global system version by copying to ~/.local/bin/."""
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.warning(f"Binary not found at {binary_path}, cannot set global version")
            return

        # Ensure ~/.local/bin directory exists
        local_bin_dir = pathlib.Path.home() / ".local" / "bin"
        local_bin_dir.mkdir(parents=True, exist_ok=True)

        # Determine target executable name
        target_name = "tofu" if self.tool_name == "tofu" else "terraform"

        if os.name == "nt":  # Windows
            target_name += ".exe"

        target_path = local_bin_dir / target_name

        # Copy the binary to ~/.local/bin
        safe_copy(binary_path, target_path, overwrite=True)

        # Make executable on Unix systems
        if os.name != "nt":
            target_path.chmod(0o755)

        # Update metadata to track global version
        if "global" not in self.metadata:
            self.metadata["global"] = {}

        tool_key = "opentofu_version" if self.tool_name == "tofu" else f"{self.tool_name}_version"

        self.metadata["global"][tool_key] = version
        self._save_metadata()

        logger.info(f"Set {self.tool_name} {version} as global system version at {target_path}")

    def get_global_version(self) -> str | None:
        """Get the currently set global version."""
        if "global" not in self.metadata:
            return None

        tool_key = "opentofu_version" if self.tool_name == "tofu" else f"{self.tool_name}_version"

        return self.metadata["global"].get(tool_key)

    def get_metadata_for_version(self, version: str) -> dict | None:
        """Get metadata for a specific version."""
        version_key = f"{self.tool_prefix}_{version}"
        return self.metadata.get(version_key)

    def get_active_version_info(self) -> dict | None:
        """Get detailed information about the currently active version."""
        version = self.get_installed_version()
        if version:
            info = self.get_metadata_for_version(version)
            if info:
                # Add current status
                binary_path = self.get_binary_path(version)
                info["is_active"] = True
                info["binary_exists"] = binary_path.exists()
                return info
        return None

    def _get_current_profile(self) -> str:
        """Get the current workenv profile name."""
        # Check environment variable first
        profile = os.environ.get("WRKENV_PROFILE")
        if profile:
            return profile

        # Check metadata for current profile setting
        if "workenv" in self.metadata and "_current_profile" in self.metadata["workenv"]:
            return self.metadata["workenv"]["_current_profile"]

        # Default to 'default' profile
        return "default"

    def _copy_active_binaries_to_venv(self) -> None:
        """Copy all active tf binaries to workenv bin directory."""
        copy_tf_binaries_to_workenv(self.workenv_bin_dir, self.config)

    def switch_version(self, version: str, dry_run: bool = False) -> None:
        """Switch to a specific version (like nvm use, tfswitch).

        This method:
        1. Installs the version if not present
        2. Updates workenv by copying binaries to venv bin
        3. Sets active version in metadata
        4. Regenerates env.sh script

        Args:
            version: Version to switch to
            dry_run: If True, show what would be done without doing it
        """
        if dry_run:
            logger.info(f"[DRY-RUN] Would switch to {self.tool_name} {version}")
            if not self.get_binary_path(version).exists():
                logger.info(f"[DRY-RUN] Would install {self.tool_name} {version}")
            return

        # 1. Install if not present
        if not self.get_binary_path(version).exists():
            logger.info(f"Installing {self.tool_name} {version}...")
            self.install_version(version, dry_run=False)

        # 2. Activate in workenv (copies binaries to venv bin)
        self.create_symlink(version)

        # 3. Regenerate env script
        try:
            from wrknv.wenv.env_generator import create_project_env_scripts

            project_dir = pathlib.Path.cwd()
            # Only regenerate if we're in a project directory
            if (project_dir / "pyproject.toml").exists() or (project_dir / "wrknv.toml").exists():
                create_project_env_scripts(project_dir)
                logger.debug("Regenerated env.sh with new version")
        except Exception as e:
            logger.debug(f"Could not regenerate env.sh: {e}")

        logger.info(f"Switched to {self.tool_name} {version}")


# 🧰🌍🔚
