#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Go Tool Manager for wrknv
============================
Manages Go versions for development."""

from __future__ import annotations

import asyncio
import pathlib
import re

from provide.foundation import logger
from provide.foundation.transport import get

from .base import BaseToolManager, ToolManagerError


class GoManager(BaseToolManager):
    """Manages Go versions using official Go download API."""

    @property
    def tool_name(self) -> str:
        return "go"

    @property
    def executable_name(self) -> str:
        return "go"

    def get_available_versions(self) -> list[str]:
        """Get available Go versions from official API."""
        try:
            api_url = "https://go.dev/dl/?mode=json"

            logger.debug(f"Fetching Go versions from {api_url}")

            # Use foundation transport for unified HTTP handling
            response = asyncio.run(get(api_url))
            data = response.json()

            versions = []
            for release in data:
                version = release.get("version", "")
                if version.startswith("go"):
                    version = version[2:]  # Remove 'go' prefix

                    # Skip unstable versions unless configured to include them
                    if not release.get("stable", True) and not self.config.get_setting(
                        "include_prereleases", False
                    ):
                        continue

                    versions.append(version)

            logger.debug(f"Found {len(versions)} Go versions")
            return versions

        except Exception as e:
            raise ToolManagerError(f"Failed to fetch Go versions: {e}") from e

    def get_download_url(self, version: str) -> str:
        """Get download URL for Go version."""
        platform_info = self.get_platform_info()
        os_name = platform_info["os"]
        arch = platform_info["arch"]

        # Use custom mirror if configured
        mirror_url = self.config.get_setting("go_mirror", "https://go.dev/dl")

        return f"{mirror_url.rstrip('/')}/go{version}.{os_name}-{arch}.tar.gz"

    def get_checksum_url(self, version: str) -> str | None:
        """Go doesn't provide separate checksum files, checksums are in the main API."""
        return None

    def _install_from_archive(self, archive_path: pathlib.Path, version: str) -> None:
        """Install Go from downloaded tar.gz archive."""
        # Create version-specific directory
        version_dir = self.install_path / self.tool_name / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Extract tar.gz file
        extract_dir = self.cache_dir / f"go_{version}_extract"
        extract_dir.mkdir(exist_ok=True)

        try:
            self.extract_archive(archive_path, extract_dir)

            # Go archive contains 'go' directory with bin/go inside
            go_root = extract_dir / "go"
            if not go_root.exists():
                raise ToolManagerError("Go directory not found in archive")

            # Move the entire Go installation to version directory
            from provide.foundation.file import safe_move, safe_rmtree

            safe_move(go_root, version_dir / "go")

            # Create a bin directory in version_dir for consistency
            bin_dir = version_dir / "bin"
            bin_dir.mkdir(exist_ok=True)

            # Create symlink to go binary
            go_binary = version_dir / "go" / "bin" / "go"
            if go_binary.exists():
                target_path = bin_dir / "go"
                target_path.symlink_to(go_binary)
                logger.info(f"Installed Go to: {version_dir}")
            else:
                raise ToolManagerError("Go binary not found in extracted archive")

            # Verify installation
            if not self.verify_installation(version):
                raise ToolManagerError(f"Go {version} installation verification failed")

        finally:
            # Clean up extraction directory
            from provide.foundation.file import safe_rmtree

            safe_rmtree(extract_dir, missing_ok=True)

    def verify_installation(self, version: str) -> bool:
        """Verify that Go installation works and version matches."""
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.error(f"Go binary not found at {binary_path}")
            return False

        try:
            from provide.foundation.process import run

            # Set GOROOT for this Go installation
            go_root = binary_path.parent.parent / "go"
            env = {"GOROOT": str(go_root)}

            result = run(
                [str(binary_path), "version"],
                timeout=10,
                env=env,
            )

            if result.returncode == 0:
                # Check if version matches
                version_pattern = rf"go{re.escape(version)}"
                if re.search(version_pattern, result.stdout):
                    logger.debug(f"Go {version} verification successful")
                    return True
                else:
                    logger.error(f"Version mismatch in Go output: {result.stdout}")
            else:
                logger.error(f"Go version command failed: {result.stderr}")

            return False

        except Exception as e:
            logger.error(f"Failed to verify Go installation: {e}")
            return False

    def get_harness_compatibility(self) -> dict:
        """Get compatibility information for Go-based tools."""
        version = self.get_installed_version()
        if not version:
            return {"status": "not_installed"}

        # Check compatibility with Go-based tools
        compatibility = {
            "status": "compatible",
            "version": version,
            "harness": {
                "go.cty": self._check_go_cty_compatibility(version),
                "go.rpc": self._check_go_rpc_compatibility(version),
                "go.wire": self._check_go_wire_compatibility(version),
                "go.hcl": self._check_go_hcl_compatibility(version),
            },
        }

        return compatibility

    def _check_go_cty_compatibility(self, version: str) -> dict:
        """Check compatibility with go-cty tools."""
        # go-cty requires Go 1.18+
        is_compatible = self._version_compare(version, "1.18.0") >= 0

        return {
            "compatible": is_compatible,
            "notes": f"go-cty tools require Go 1.18+ (current: {version})",
        }

    def _check_go_rpc_compatibility(self, version: str) -> dict:
        """Check compatibility with go-rpc tools."""
        # go-rpc requires Go 1.19+ for generics
        is_compatible = self._version_compare(version, "1.19.0") >= 0

        return {
            "compatible": is_compatible,
            "notes": f"go-rpc tools require Go 1.19+ (current: {version})",
        }

    def _check_go_wire_compatibility(self, version: str) -> dict:
        """Check compatibility with go-wire tools."""
        # go-wire requires Go 1.18+
        is_compatible = self._version_compare(version, "1.18.0") >= 0

        return {
            "compatible": is_compatible,
            "notes": f"go-wire tools require Go 1.18+ (current: {version})",
        }

    def _check_go_hcl_compatibility(self, version: str) -> dict:
        """Check compatibility with go-hcl tools."""
        # go-hcl requires Go 1.18+
        is_compatible = self._version_compare(version, "1.18.0") >= 0

        return {
            "compatible": is_compatible,
            "notes": f"go-hcl tools require Go 1.18+ (current: {version})",
        }

    def _version_compare(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns -1, 0, or 1."""

        def version_tuple(v: str) -> tuple[int, ...]:
            return tuple(map(int, v.split(".")))

        v1_tuple = version_tuple(version1)
        v2_tuple = version_tuple(version2)

        if v1_tuple < v2_tuple:
            return -1
        elif v1_tuple > v2_tuple:
            return 1
        else:
            return 0

    def get_goroot(self, version: str) -> pathlib.Path:
        """Get GOROOT path for a specific Go version."""
        return self.install_path / self.tool_name / version / "go"

    def get_gopath(self, version: str) -> pathlib.Path:
        """Get default GOPATH for a specific Go version."""
        return self.install_path / self.tool_name / version / "gopath"


# 🧰🌍🔚
