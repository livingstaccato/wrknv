#
# wrknv/workenv/managers/ibm_tf.py
#
"""
IBM Terraform Tool Manager for wrknv
=====================================
Manages IBM Terraform (formerly HashiCorp Terraform) versions for development environment.
"""

import json
import re
from urllib.request import urlopen

from provide.foundation import logger
from provide.foundation.process import run as process_run
import semver

from .tf_base import TfVersionsManager, ToolManagerError


class IbmTfManager(TfVersionsManager):
    """Manages IBM Terraform (formerly HashiCorp Terraform) versions using HashiCorp's releases API."""

    @property
    def tool_name(self) -> str:
        return "ibmtf"

    @property
    def executable_name(self) -> str:
        return "ibmtf"

    @property
    def tool_prefix(self) -> str:
        return "terraform"

    def get_available_versions(self) -> list[str]:
        """Get available IBM Terraform versions from HashiCorp releases API."""
        try:
            # Use custom mirror if configured
            mirror_url = self.config.get_setting(
                "terraform_mirror", "https://releases.hashicorp.com/terraform"
            )
            api_url = f"{mirror_url.rstrip('/')}/index.json"

            logger.debug(f"Fetching IBM Terraform versions from {api_url}")

            with urlopen(api_url) as response:
                data = json.loads(response.read())

            versions = []
            for version_info in data.get("versions", {}).values():
                version = version_info.get("version")
                if version and not self._is_prerelease(version):
                    versions.append(version)

            # Sort versions in descending order (latest first)
            versions.sort(key=self._version_sort_key, reverse=True)

            logger.debug(f"Found {len(versions)} IBM Terraform versions")
            # Log the first few versions to debug
            if versions:
                logger.debug(f"Latest versions: {versions[:5]}")

            return versions

        except Exception as e:
            raise ToolManagerError(f"Failed to fetch IBM Terraform versions: {e}") from e

    def _is_prerelease(self, version: str) -> bool:
        """Check if version is a prerelease."""
        include_prereleases = self.config.get_setting("include_prereleases", False)
        if include_prereleases:
            return False

        # Check for prerelease indicators
        prerelease_patterns = ["alpha", "beta", "rc", "pre"]
        version_lower = version.lower()
        return any(pattern in version_lower for pattern in prerelease_patterns)

    def _version_sort_key(self, version: str) -> tuple[int, ...]:
        """Generate sort key for semantic versioning using semver module."""
        try:
            # Try to parse as a semantic version
            return semver.VersionInfo.parse(version)
        except ValueError:
            # If it fails, try to make it semver-compliant
            # Handle versions like "1.0" by adding ".0"
            parts = version.split(".")
            while len(parts) < 3:
                parts.append("0")
            try:
                normalized = ".".join(parts[:3])
                return semver.VersionInfo.parse(normalized)
            except ValueError:
                # Last resort: return a very old version
                return semver.VersionInfo.parse("0.0.0")

    def get_download_url(self, version: str) -> str:
        """Get download URL for IBM Terraform version."""
        platform_info = self.get_platform_info()
        os_name = platform_info["os"]
        arch = platform_info["arch"]

        # Use custom mirror if configured
        mirror_url = self.config.get_setting("terraform_mirror", "https://releases.hashicorp.com/terraform")

        return f"{mirror_url.rstrip('/')}/{version}/terraform_{version}_{os_name}_{arch}.zip"

    def get_checksum_url(self, version: str) -> str | None:
        """Get checksum URL for IBM Terraform version."""
        mirror_url = self.config.get_setting("terraform_mirror", "https://releases.hashicorp.com/terraform")
        return f"{mirror_url.rstrip('/')}/{version}/terraform_{version}_SHA256SUMS"

    # _install_from_archive is inherited from TfVersionsManager

    def verify_installation(self, version: str) -> bool:
        """Verify that IBM Terraform installation works and version matches."""
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.error(f"IBM Terraform binary not found at {binary_path}")
            return False

        try:
            result = process_run(
                [str(binary_path), "-version"],
                capture_output=True,
                text=True,
                timeout=10.0,
                check=False,
            )

            if result.returncode == 0:
                # Check if version matches
                version_pattern = rf"Terraform v{re.escape(version)}"
                if re.search(version_pattern, result.stdout):
                    logger.debug(f"IBM Terraform {version} verification successful")
                    return True
                else:
                    logger.error(f"Version mismatch in IBM Terraform output: {result.stdout}")
            else:
                logger.error(f"IBM Terraform version command failed: {result.stderr}")

            return False

        except Exception as e:
            logger.error(f"Failed to verify IBM Terraform installation: {e}")
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
        # CTY tools work with most Terraform versions
        return {
            "compatible": True,
            "notes": "CTY testing compatible with all IBM Terraform versions",
        }

    def _check_wire_compatibility(self, version: str) -> dict:
        """Check compatibility with wire protocol tools."""
        # Wire protocol compatibility depends on Terraform version
        major_minor = ".".join(version.split(".")[:2])

        compatible_versions = ["1.5", "1.6", "1.7"]
        is_compatible = major_minor in compatible_versions

        return {
            "compatible": is_compatible,
            "notes": f"Wire protocol testing requires IBM Terraform 1.5+ (current: {version})",
        }

    def _check_conformance_compatibility(self, version: str) -> dict:
        """Check compatibility with conformance testing."""
        return {
            "compatible": True,
            "notes": "Conformance testing supports all IBM Terraform versions",
        }


# 🍲🥄📄🪄
