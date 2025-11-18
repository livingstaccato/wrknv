#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""IBM Vault Variant for SubRosaManager
=====================================
Manages IBM Vault (HashiCorp Vault) versions for development."""

from __future__ import annotations

import pathlib

from provide.foundation import logger
from provide.foundation.file import safe_copy, safe_rmtree
from provide.foundation.transport import get

from wrknv.managers.base import ToolManagerError
from wrknv.managers.subrosa.base import SubRosaManager


class IbmVaultVariant(SubRosaManager):
    """IBM Vault (HashiCorp Vault) variant of secret management tools."""

    @property
    def variant_name(self) -> str:
        """Variant name for this secret manager."""
        return "vault"

    def get_available_versions(self) -> list[str]:
        """Get available HashiCorp Vault versions from releases API."""
        try:
            # HashiCorp provides a JSON API for releases
            api_url = "https://releases.hashicorp.com/vault/index.json"

            logger.debug(f"Fetching Vault versions from {api_url}")

            response = get(api_url)
            data = response.json()

            versions = []
            include_prereleases = self.config.get_setting("include_prereleases", False)

            # Parse versions from release data
            for version_str, _version_data in data.get("versions", {}).items():
                # Skip pre-releases unless configured
                if not include_prereleases and any(
                    tag in version_str for tag in ["-rc", "-beta", "-alpha", "-dev"]
                ):
                    continue

                versions.append(version_str)

            logger.debug(f"Found {len(versions)} Vault versions")

            # Sort versions
            try:
                from packaging.version import parse as parse_version

                versions.sort(key=lambda v: parse_version(v), reverse=True)
            except Exception:
                versions.sort(reverse=True)

            return versions

        except Exception as e:
            raise ToolManagerError(f"Failed to fetch Vault versions: {e}") from e

    def get_download_url(self, version: str) -> str:
        """Get download URL for HashiCorp Vault version."""
        platform_info = self.get_platform_info()
        os_name = platform_info["os"]  # darwin, linux, windows
        arch = platform_info["arch"]  # amd64, arm64, etc.

        # HashiCorp uses different arch naming for ARM
        if arch == "arm64":
            hc_arch = "arm64"
        elif arch == "amd64" or arch == "x86_64":
            hc_arch = "amd64"
        else:
            hc_arch = arch

        # HashiCorp naming: vault_1.15.0_darwin_arm64.zip
        return f"https://releases.hashicorp.com/vault/{version}/vault_{version}_{os_name}_{hc_arch}.zip"

    def get_checksum_url(self, version: str) -> str | None:
        """Get checksum URL for HashiCorp Vault version."""
        # HashiCorp provides SHA256SUMS file
        return f"https://releases.hashicorp.com/vault/{version}/vault_{version}_SHA256SUMS"

    def _install_from_archive(self, archive_path: pathlib.Path, version: str) -> None:
        """Install Vault from downloaded ZIP archive.

        HashiCorp uses .zip format, not .tar.gz like OpenBao.
        """
        # Create extraction directory
        extract_dir = self.cache_dir / f"vault_{version}_extract"
        extract_dir.mkdir(exist_ok=True)

        try:
            # Extract ZIP archive
            self.extract_archive(archive_path, extract_dir)

            # Find vault binary in extracted files
            binary_path = None
            for file_path in extract_dir.rglob("vault*"):
                if file_path.is_file() and file_path.name in ["vault", "vault.exe"]:
                    binary_path = file_path
                    break

            if not binary_path:
                raise ToolManagerError("Vault binary not found in archive")

            # Copy to target location with variant-specific naming
            target_path = self.get_binary_path(version)
            safe_copy(binary_path, target_path, overwrite=True)

            # Make executable (Unix systems)
            self.make_executable(target_path)

            logger.info(f"Installed Vault binary to: {target_path}")

            # Verify installation
            if not self.verify_installation(version):
                raise ToolManagerError(f"Vault {version} installation verification failed")

        finally:
            # Clean up extraction directory
            safe_rmtree(extract_dir, missing_ok=True)


__all__ = [
    "IbmVaultVariant",
]

# 🧰🌍🔚
