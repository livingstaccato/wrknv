#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""OpenBao Tool Manager for wrknv
===============================
Manages OpenBao (open source Vault fork) versions for development."""

from __future__ import annotations

import asyncio
import pathlib
from typing import TYPE_CHECKING

from provide.foundation import logger

from wrknv.managers.base import BaseToolManager, ToolManagerError
from wrknv.managers.github import GitHubReleasesClient

if TYPE_CHECKING:
    from wrknv.config import WorkenvConfig


class BaoManager(BaseToolManager):
    """Manages OpenBao versions using GitHub releases API."""

    def __init__(self, config: WorkenvConfig | None = None) -> None:
        super().__init__(config)
        self._github_client: GitHubReleasesClient | None = None

    @property
    def github_client(self) -> GitHubReleasesClient:
        """Get or create GitHub client for OpenBao repository."""
        if self._github_client is None:
            self._github_client = GitHubReleasesClient("openbao/openbao")
        return self._github_client

    @property
    def tool_name(self) -> str:
        return "bao"

    @property
    def executable_name(self) -> str:
        return "bao"

    def get_available_versions(self) -> list[str]:
        """Get available OpenBao versions from GitHub releases."""
        try:
            logger.debug("Fetching OpenBao versions from GitHub")

            include_prereleases = self.config.get_setting("include_prereleases", False)

            # Use GitHub client to fetch versions
            versions = asyncio.run(self.github_client.get_versions(include_prereleases=include_prereleases))

            # OpenBao versions have 'v' prefix in tags, already stripped by client
            logger.debug(f"Found {len(versions)} OpenBao versions")
            return versions

        except Exception as e:
            raise ToolManagerError(f"Failed to fetch OpenBao versions: {e}") from e

    def get_download_url(self, version: str) -> str:
        """Get download URL for OpenBao version."""
        platform_info = self.get_platform_info()
        os_name = platform_info["os"]
        arch = platform_info["arch"]

        # OpenBao uses capitalized OS names: Darwin, Linux, Windows
        os_capitalized = os_name.capitalize()

        # OpenBao naming: bao_2.1.0_Darwin_arm64.tar.gz
        # Note: They use tar.gz for all platforms
        return f"https://github.com/openbao/openbao/releases/download/v{version}/bao_{version}_{os_capitalized}_{arch}.tar.gz"

    def get_checksum_url(self, version: str) -> str | None:
        """Get checksum URL for OpenBao version."""
        # OpenBao provides SHA256SUMS file
        return f"https://github.com/openbao/openbao/releases/download/v{version}/bao_{version}_SHA256SUMS"

    def _install_from_archive(self, archive_path: pathlib.Path, version: str) -> None:
        """Install OpenBao from downloaded archive."""
        # Create version-specific directory
        version_dir = self.install_path / self.tool_name / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Create bin subdirectory
        bin_dir = version_dir / "bin"
        bin_dir.mkdir(exist_ok=True)

        # Extract archive
        extract_dir = self.cache_dir / f"bao_{version}_extract"
        extract_dir.mkdir(exist_ok=True)

        try:
            self.extract_archive(archive_path, extract_dir)

            # Find bao binary in extracted files
            bao_binary = None
            for file_path in extract_dir.rglob("bao*"):
                if file_path.is_file() and file_path.name in ["bao", "bao.exe"]:
                    bao_binary = file_path
                    break

            if not bao_binary:
                raise ToolManagerError("OpenBao binary not found in archive")

            # Copy to bin directory
            target_path = bin_dir / bao_binary.name
            from provide.foundation.file import safe_copy, safe_rmtree

            safe_copy(bao_binary, target_path, overwrite=True)

            # Make executable (Unix systems)
            self.make_executable(target_path)

            logger.info(f"Installed OpenBao binary to: {target_path}")

            # Verify installation
            if not self.verify_installation(version):
                raise ToolManagerError(f"OpenBao {version} installation verification failed")

        finally:
            # Clean up extraction directory
            from provide.foundation.file import safe_copy, safe_rmtree

            safe_rmtree(extract_dir, missing_ok=True)

    def verify_installation(self, version: str) -> bool:
        """Verify that OpenBao installation works and version matches."""
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.error(f"OpenBao binary not found at {binary_path}")
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
                # OpenBao version output: "Bao v2.1.0 (1234abcd), built 2024-01-01T00:00:00Z"
                if version in result.stdout or f"v{version}" in result.stdout:
                    logger.debug(f"OpenBao {version} verification successful")
                    return True
                else:
                    logger.error(f"Version mismatch in OpenBao output: {result.stdout}")
            else:
                logger.error(f"OpenBao version command failed: {result.stderr}")

            return False

        except Exception as e:
            logger.error(f"Failed to verify OpenBao installation: {e}")
            return False


__all__ = [
    "BaoManager",
]

# 🧰🌍🔚
