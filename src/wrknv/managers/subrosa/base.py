#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""SubRosaManager Base Class
=========================
Base class for sub rosa (secret) management tools.

'Sub rosa' - under the rose - in confidence.
Manages secret management tool variants (OpenBao, HashiCorp Vault, etc.)"""

from __future__ import annotations

from abc import abstractmethod
import json
import pathlib
from typing import TYPE_CHECKING

from provide.foundation import logger
from provide.foundation.file import safe_copy, safe_delete, safe_rmtree

from wrknv.managers.base import BaseToolManager, ToolManagerError
from wrknv.wenv.bin_manager import get_workenv_bin_dir

if TYPE_CHECKING:
    from wrknv.config import WorkenvConfig


class SubRosaManager(BaseToolManager):
    """
    Base class for secret management tool managers.

    Provides common functionality for managing secret management tools
    like OpenBao and HashiCorp Vault, with version switching and
    workenv integration.
    """

    def __init__(self, config: WorkenvConfig | None = None) -> None:
        super().__init__(config)

        # Override install path to use subrosa directory
        self.install_path = pathlib.Path("~/.wrknv/subrosa").expanduser()
        self.install_path.mkdir(parents=True, exist_ok=True)

        # Get workenv bin directory for symlinking active version
        self.workenv_bin_dir = get_workenv_bin_dir(config)

        # Metadata file for tracking active versions
        self.metadata_file = self.install_path / "metadata.json"
        self.metadata = self._load_metadata()

    @property
    @abstractmethod
    def variant_name(self) -> str:
        """Variant name (e.g., 'bao' or 'vault')."""

    @property
    def tool_name(self) -> str:
        """Tool name for CLI - all variants use 'bao'."""
        return "bao"

    @property
    def executable_name(self) -> str:
        """Executable name in PATH."""
        return "bao"

    def _load_metadata(self) -> dict:
        """Load metadata from JSON file."""
        if self.metadata_file.exists():
            try:
                with self.metadata_file.open() as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load subrosa metadata: {e}")
                return {}
        return {}

    def _save_metadata(self) -> None:
        """Save metadata to JSON file."""
        try:
            with self.metadata_file.open("w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save subrosa metadata: {e}")

    def get_binary_path(self, version: str) -> pathlib.Path:
        """Get path to installed binary for a version.

        Format: ~/.wrknv/subrosa/{variant}_{version}
        Example: ~/.wrknv/subrosa/bao_2.1.0
        """
        binary_name = f"{self.variant_name}_{version}"
        return self.install_path / binary_name

    def get_installed_versions(self) -> list[str]:
        """Get all installed versions of this variant."""
        versions = []

        prefix = f"{self.variant_name}_"
        for item in self.install_path.iterdir():
            if item.is_file() and item.name.startswith(prefix):
                # Extract version from filename
                version = item.name[len(prefix) :]
                versions.append(version)

        # Sort by version
        try:
            from packaging.version import parse as parse_version

            versions.sort(key=lambda v: parse_version(v), reverse=True)
        except Exception:
            versions.sort(reverse=True)

        return versions

    def get_installed_version(self) -> str | None:
        """Get currently active version from metadata."""
        active_versions = self.metadata.get("active_versions", {})
        return active_versions.get(self.variant_name)

    def set_installed_version(self, version: str) -> None:
        """Set the active version in metadata."""
        if "active_versions" not in self.metadata:
            self.metadata["active_versions"] = {}

        self.metadata["active_versions"][self.variant_name] = version
        self._save_metadata()

        logger.info(f"Set {self.variant_name} active version to {version}")

    def _update_workenv_symlink(self, version: str) -> None:
        """Update workenv bin symlink to point to active version."""
        binary_path = self.get_binary_path(version)

        if not binary_path.exists():
            logger.warning(f"Binary not found at {binary_path}, cannot update symlink")
            return

        # Create symlink in workenv bin directory
        if self.workenv_bin_dir:
            symlink_path = self.workenv_bin_dir / self.executable_name

            # Remove existing symlink
            if symlink_path.exists() or symlink_path.is_symlink():
                safe_delete(symlink_path, missing_ok=True)

            try:
                symlink_path.symlink_to(binary_path)
                logger.info(f"Updated symlink: {symlink_path} -> {binary_path}")
            except OSError as e:
                logger.warning(f"Could not create symlink: {e}")

    def _regenerate_env_script(self) -> None:
        """Regenerate env.sh script with updated version."""
        try:
            from wrknv.wenv.env_generator import create_project_env_scripts

            project_dir = pathlib.Path.cwd()
            # Only regenerate if we're in a project directory
            if (project_dir / "pyproject.toml").exists() or (project_dir / "wrknv.toml").exists():
                create_project_env_scripts(project_dir)
                logger.debug("Regenerated env.sh with new version")
        except Exception as e:
            logger.debug(f"Could not regenerate env.sh: {e}")

    def switch_version(self, version: str, dry_run: bool = False) -> None:
        """Switch to a specific version (like nvm use, tfswitch).

        This method:
        1. Installs the version if not present
        2. Updates workenv bin symlinks
        3. Sets active version in metadata
        4. Regenerates env.sh script

        Args:
            version: Version to switch to
            dry_run: If True, show what would be done without doing it
        """
        if dry_run:
            logger.info(f"[DRY-RUN] Would switch to {self.variant_name} {version}")
            if not self.get_binary_path(version).exists():
                logger.info(f"[DRY-RUN] Would install {self.variant_name} {version}")
            return

        # 1. Install if not present
        if not self.get_binary_path(version).exists():
            logger.info(f"Installing {self.variant_name} {version}...")
            self.install_version(version, dry_run=False)

        # 2. Update workenv symlinks
        self._update_workenv_symlink(version)

        # 3. Set active version
        self.set_installed_version(version)

        # 4. Regenerate env script
        self._regenerate_env_script()

        logger.info(f"Switched to {self.variant_name} {version}")

    def remove_version(self, version: str) -> None:
        """Remove a specific version of the tool."""
        binary_path = self.get_binary_path(version)

        if binary_path.exists():
            binary_path.unlink()
            logger.info(f"Removed {self.variant_name} {version}")

            # Update metadata if this was the current version
            if self.get_installed_version() == version and (
                "active_versions" in self.metadata and self.variant_name in self.metadata["active_versions"]
            ):
                del self.metadata["active_versions"][self.variant_name]
                self._save_metadata()

    def _install_from_archive(self, archive_path: pathlib.Path, version: str) -> None:
        """Install tool from downloaded archive.

        Subclasses can override this for variant-specific extraction logic.
        """
        # Create extraction directory
        extract_dir = self.cache_dir / f"{self.variant_name}_{version}_extract"
        extract_dir.mkdir(exist_ok=True)

        try:
            self.extract_archive(archive_path, extract_dir)

            # Find binary in extracted files
            binary_path = None
            for file_path in extract_dir.rglob(f"{self.variant_name}*"):
                if file_path.is_file() and file_path.name in [
                    self.variant_name,
                    f"{self.variant_name}.exe",
                ]:
                    binary_path = file_path
                    break

            if not binary_path:
                raise ToolManagerError(f"{self.variant_name} binary not found in archive")

            # Copy to target location
            target_path = self.get_binary_path(version)
            safe_copy(binary_path, target_path, overwrite=True)

            # Make executable (Unix systems)
            self.make_executable(target_path)

            logger.info(f"Installed {self.variant_name} binary to: {target_path}")

            # Verify installation
            if not self.verify_installation(version):
                raise ToolManagerError(f"{self.variant_name} {version} installation verification failed")

        finally:
            # Clean up extraction directory
            safe_rmtree(extract_dir, missing_ok=True)

    def verify_installation(self, version: str) -> bool:
        """Verify that installation works and version matches."""
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.error(f"{self.variant_name} binary not found at {binary_path}")
            return False

        try:
            from provide.foundation.process import run

            result = run(
                [str(binary_path), "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Check if version is in output
                if version in result.stdout or f"v{version}" in result.stdout:
                    logger.debug(f"{self.variant_name} {version} verification successful")
                    return True
                else:
                    logger.error(f"Version mismatch in {self.variant_name} output: {result.stdout}")
            else:
                logger.error(f"{self.variant_name} version command failed: {result.stderr}")

            return False

        except Exception as e:
            logger.error(f"Failed to verify {self.variant_name} installation: {e}")
            return False


__all__ = [
    "SubRosaManager",
]

# 🧰🌍🔚
