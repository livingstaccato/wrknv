#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""OpenTofu Tool Manager for wrknv
==================================
Manages OpenTofu versions for development environment."""

from __future__ import annotations

import re

from provide.foundation.logger import get_logger
from provide.foundation.transport import get

from wrknv.managers.base import ToolManagerError
from wrknv.managers.tf.base import TfManager
from wrknv.managers.tf.utils import version_sort_key

logger = get_logger(__name__)


class TofuTfVariant(TfManager):
    """OpenTofu Tf variant - manages OpenTofu versions using GitHub releases API with wrknv's directory structure."""

    @property
    def tool_name(self) -> str:
        return "tofu"

    @property
    def executable_name(self) -> str:
        return "tofu"

    @property
    def tool_prefix(self) -> str:
        return "opentofu"

    def get_available_versions(self) -> list[str]:
        """Get available OpenTofu versions from GitHub releases."""
        try:
            # Use custom mirror if configured
            api_url = "https://api.github.com/repos/opentofu/opentofu/releases"

            logger.debug(f"Fetching OpenTofu versions from {api_url}")

            response = get(api_url)
            data = response.json()

            versions = []
            for release in data:
                tag_name = release.get("tag_name", "")
                if tag_name.startswith("v"):
                    version = tag_name[1:]  # Remove 'v' prefix

                    # Skip prereleases unless configured to include them
                    if release.get("prerelease", False) and not self.config.get_setting(
                        "include_prereleases", False
                    ):
                        continue

                    versions.append(version)

            # Sort versions in descending order (latest first)
            versions.sort(key=version_sort_key, reverse=True)

            logger.debug(f"Found {len(versions)} OpenTofu versions")
            return versions

        except Exception as e:
            raise ToolManagerError(f"Failed to fetch OpenTofu versions: {e}") from e

    def get_download_url(self, version: str) -> str:
        """Get download URL for OpenTofu version."""
        platform_info = self.get_platform_info()
        os_name = platform_info["os"]
        arch = platform_info["arch"]

        return f"https://github.com/opentofu/opentofu/releases/download/v{version}/tofu_{version}_{os_name}_{arch}.zip"

    def get_checksum_url(self, version: str) -> str | None:
        """Get checksum URL for OpenTofu version."""
        return f"https://github.com/opentofu/opentofu/releases/download/v{version}/tofu_{version}_SHA256SUMS"

    # _install_from_archive is inherited from TfVersionsManager

    def verify_installation(self, version: str) -> bool:
        """Verify that OpenTofu installation works and version matches."""
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.error(f"OpenTofu binary not found at {binary_path}")
            return False

        try:
            from provide.foundation.process import run

            result = run(
                [str(binary_path), "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Check if version matches
                version_pattern = rf"OpenTofu v{re.escape(version)}"
                if re.search(version_pattern, result.stdout):
                    logger.debug(f"OpenTofu {version} verification successful")
                    return True
                else:
                    logger.error(f"Version mismatch in OpenTofu output: {result.stdout}")
            else:
                logger.error(f"OpenTofu version command failed: {result.stderr}")

            return False

        except Exception as e:
            logger.error(f"Failed to verify OpenTofu installation: {e}")
            return False

    def get_harness_compatibility(self) -> dict:
        """Get compatibility information for development tools."""
        version = self.get_installed_version()
        if not version:
            return {"status": "not_installed"}

        # Check compatibility with development tools
        compatibility = {
            "status": "compatible",
            "version": version,
            "harness": {
                "go.cty": self._check_cty_compatibility(version),
                "go.wire": self._check_wire_compatibility(version),
                "conformance": self._check_conformance_compatibility(version),
            },
        }

        return compatibility

    def _check_cty_compatibility(self, version: str) -> dict:
        """Check compatibility with CTY tools."""
        return {
            "compatible": True,
            "notes": "CTY testing compatible with all OpenTofu versions",
        }

    def _check_wire_compatibility(self, version: str) -> dict:
        """Check compatibility with wire protocol tools."""
        # OpenTofu 1.6+ is compatible with Terraform wire protocol
        major_minor = ".".join(version.split(".")[:2])

        try:
            major, minor = map(int, major_minor.split("."))
            is_compatible = major > 1 or (major == 1 and minor >= 6)
        except (ValueError, TypeError):
            is_compatible = False

        return {
            "compatible": is_compatible,
            "notes": f"Wire protocol testing requires OpenTofu 1.6+ (current: {version})",
        }

    def _check_conformance_compatibility(self, version: str) -> dict:
        """Check compatibility with conformance testing."""
        return {
            "compatible": True,
            "notes": "Conformance testing supports all OpenTofu versions",
        }


# 🧰🌍🔚
