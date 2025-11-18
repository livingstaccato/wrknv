#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""UV Tool Manager for wrknv
============================
Manages UV (Python package manager) versions for development."""

from __future__ import annotations

import asyncio
import pathlib
from typing import TYPE_CHECKING

from provide.foundation import logger

from wrknv.managers.base import BaseToolManager, ToolManagerError
from wrknv.managers.github import GitHubReleasesClient

if TYPE_CHECKING:
    from wrknv.config import WorkenvConfig


class UvManager(BaseToolManager):
    """Manages UV versions using GitHub releases API."""

    def __init__(self, config: WorkenvConfig | None = None) -> None:
        super().__init__(config)
        self._github_client: GitHubReleasesClient | None = None

    @property
    def github_client(self) -> GitHubReleasesClient:
        """Get or create GitHub client for UV repository."""
        if self._github_client is None:
            self._github_client = GitHubReleasesClient("astral-sh/uv")
        return self._github_client

    @property
    def tool_name(self) -> str:
        return "uv"

    @property
    def executable_name(self) -> str:
        return "uv"

    def get_available_versions(self) -> list[str]:
        """Get available UV versions from GitHub releases."""
        try:
            logger.debug("Fetching UV versions from GitHub")

            include_prereleases = self.config.get_setting("include_prereleases", False)

            # Use GitHub client to fetch versions
            versions = asyncio.run(self.github_client.get_versions(include_prereleases=include_prereleases))

            logger.debug(f"Found {len(versions)} UV versions")
            return versions

        except Exception as e:
            raise ToolManagerError(f"Failed to fetch UV versions: {e}") from e

    def get_download_url(self, version: str) -> str:
        """Get download URL for UV version."""
        platform_info = self.get_platform_info()
        os_name = platform_info["os"]
        arch = platform_info["arch"]

        # UV uses different naming convention
        if os_name == "darwin":
            platform_name = "apple-darwin"
        elif os_name == "linux":
            platform_name = "unknown-linux-gnu"
        elif os_name == "windows":
            platform_name = "pc-windows-msvc"
        else:
            raise ToolManagerError(f"Unsupported platform for UV: {os_name}")

        # UV uses specific architecture names
        if arch == "amd64":
            arch = "x86_64"
        elif arch == "arm64":
            arch = "aarch64"

        # Return appropriate archive format
        if os_name == "windows":
            return f"https://github.com/astral-sh/uv/releases/download/{version}/uv-{arch}-{platform_name}.zip"
        else:
            return (
                f"https://github.com/astral-sh/uv/releases/download/{version}/uv-{arch}-{platform_name}.tar.gz"
            )

    def get_checksum_url(self, version: str) -> str | None:
        """UV doesn't provide separate checksum files."""
        return None

    def _install_from_archive(self, archive_path: pathlib.Path, version: str) -> None:
        """Install UV from downloaded archive."""
        # Create version-specific directory
        version_dir = self.install_path / self.tool_name / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Create bin subdirectory
        bin_dir = version_dir / "bin"
        bin_dir.mkdir(exist_ok=True)

        # Extract archive
        extract_dir = self.cache_dir / f"uv_{version}_extract"
        extract_dir.mkdir(exist_ok=True)

        try:
            self.extract_archive(archive_path, extract_dir)

            # Find uv binary in extracted files
            uv_binary = None
            for file_path in extract_dir.rglob("uv*"):
                if file_path.is_file() and file_path.name in ["uv", "uv.exe"]:
                    uv_binary = file_path
                    break

            if not uv_binary:
                raise ToolManagerError("UV binary not found in archive")

            # Copy to bin directory
            target_path = bin_dir / uv_binary.name
            from provide.foundation.file import safe_copy, safe_rmtree

            safe_copy(uv_binary, target_path, overwrite=True)

            # Make executable (Unix systems)
            self.make_executable(target_path)

            logger.info(f"Installed UV binary to: {target_path}")

            # Verify installation
            if not self.verify_installation(version):
                raise ToolManagerError(f"UV {version} installation verification failed")

        finally:
            # Clean up extraction directory
            from provide.foundation.file import safe_copy, safe_rmtree

            safe_rmtree(extract_dir, missing_ok=True)

    def verify_installation(self, version: str) -> bool:
        """Verify that UV installation works and version matches."""
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.error(f"UV binary not found at {binary_path}")
            return False

        try:
            from provide.foundation.process import run

            result = run(
                [str(binary_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Check if version matches (UV outputs "uv 0.4.15")
                if version in result.stdout:
                    logger.debug(f"UV {version} verification successful")
                    return True
                else:
                    logger.error(f"Version mismatch in UV output: {result.stdout}")
            else:
                logger.error(f"UV version command failed: {result.stderr}")

            return False

        except Exception as e:
            logger.error(f"Failed to verify UV installation: {e}")
            return False

    def get_harness_compatibility(self) -> dict:
        """Get compatibility information for Python tools."""
        version = self.get_installed_version()
        if not version:
            return {"status": "not_installed"}

        # Check compatibility with Python tools
        compatibility = {
            "status": "compatible",
            "version": version,
            "harness": {
                "python.cty": self._check_python_cty_compatibility(version),
                "python.hcl": self._check_python_hcl_compatibility(version),
                "python.wire": self._check_python_wire_compatibility(version),
            },
        }

        return compatibility

    def _check_python_cty_compatibility(self, version: str) -> dict:
        """Check compatibility with Python CTY tools."""
        return {
            "compatible": True,
            "notes": "Python CTY tools compatible with all UV versions",
        }

    def _check_python_hcl_compatibility(self, version: str) -> dict:
        """Check compatibility with Python HCL tools."""
        return {
            "compatible": True,
            "notes": "Python HCL tools compatible with all UV versions",
        }

    def _check_python_wire_compatibility(self, version: str) -> dict:
        """Check compatibility with Python wire protocol tools."""
        return {
            "compatible": True,
            "notes": "Python wire protocol tools compatible with all UV versions",
        }


# 🧰🌍🔚
