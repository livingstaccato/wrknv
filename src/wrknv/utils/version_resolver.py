#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Version Resolution Utilities
============================
Handles resolution of version patterns like "1.11.x" to specific versions."""

from __future__ import annotations

from provide.foundation.logger import get_logger
import semver

from wrknv.managers.base import BaseToolManager

logger = get_logger(__name__)


class VersionResolver:
    """Resolves version patterns to specific versions from available versions list."""

    def __init__(self, available_versions: list[str]) -> None:
        """Initialize with list of available versions."""
        self.available_versions = available_versions

    def resolve_version(self, version_pattern: str) -> str:
        """
        Resolve a version pattern to a specific version.

        Examples:
            "1.11.x" -> "1.11.5" (latest patch in 1.11 series)
            "1.13" -> "1.13.7" (latest patch in 1.13 series)
            "1.15.0" -> "1.15.0" (exact version)
            "latest" -> "1.16.2" (latest overall version)

        Args:
            version_pattern: Version pattern to resolve

        Returns:
            Resolved specific version string

        Raises:
            ValueError: If pattern cannot be resolved
        """
        version_pattern = version_pattern.strip()

        # Handle special cases
        if version_pattern in ("latest", "stable"):
            if not self.available_versions:
                raise ValueError("No versions available")
            return self.available_versions[0]  # Assuming sorted with latest first

        # Handle exact version (already specific)
        if self._is_exact_version(version_pattern):
            if version_pattern in self.available_versions:
                return version_pattern
            else:
                raise ValueError(f"Version {version_pattern} not available")

        # Handle .x suffix patterns like "1.11.x"
        if version_pattern.endswith(".x"):
            return self._resolve_x_pattern(version_pattern)

        # Handle major.minor patterns like "1.11" (no patch specified)
        if self._is_major_minor_only(version_pattern):
            return self._resolve_major_minor(version_pattern)

        # If no pattern matches, treat as exact version
        if version_pattern in self.available_versions:
            return version_pattern
        else:
            raise ValueError(f"Version pattern '{version_pattern}' could not be resolved")

    def _is_exact_version(self, version: str) -> bool:
        """Check if version string is an exact semantic version."""
        try:
            semver.VersionInfo.parse(version)
            return True
        except ValueError:
            return False

    def _is_major_minor_only(self, version: str) -> bool:
        """Check if version is in major.minor format (no patch)."""
        parts = version.split(".")
        return len(parts) == 2 and all(part.isdigit() for part in parts)

    def _resolve_x_pattern(self, pattern: str) -> str:
        """Resolve patterns like '1.11.x' to latest patch version."""
        # Extract major.minor from pattern
        prefix = pattern[:-2]  # Remove ".x"

        # Find all versions matching the prefix
        matching_versions = [v for v in self.available_versions if v.startswith(prefix + ".")]

        if not matching_versions:
            raise ValueError(f"No versions found matching pattern {pattern}")

        # Sort and return latest (first in sorted list)
        matching_versions.sort(key=self._version_sort_key, reverse=True)
        resolved = matching_versions[0]

        logger.debug(f"Resolved {pattern} to {resolved}")
        return resolved

    def _resolve_major_minor(self, version: str) -> str:
        """Resolve major.minor to latest patch version."""
        # Find all versions matching major.minor
        matching_versions = [v for v in self.available_versions if v.startswith(version + ".")]

        if not matching_versions:
            raise ValueError(f"No versions found for {version}")

        # Sort and return latest
        matching_versions.sort(key=self._version_sort_key, reverse=True)
        resolved = matching_versions[0]

        logger.debug(f"Resolved {version} to {resolved}")
        return resolved

    def _version_sort_key(self, version: str) -> semver.VersionInfo:
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

    def resolve_versions(self, version_patterns: list[str]) -> list[str]:
        """Resolve multiple version patterns."""
        resolved_versions = []
        for pattern in version_patterns:
            try:
                resolved = self.resolve_version(pattern)
                resolved_versions.append(resolved)
            except ValueError as e:
                logger.warning(f"Failed to resolve version pattern '{pattern}': {e}")
        return resolved_versions


def resolve_tool_versions(
    tool_manager: BaseToolManager,
    version_patterns: str | list[str],
) -> list[str]:
    """
    Convenience function to resolve version patterns using a tool manager.

    Args:
        tool_manager: Tool manager instance with get_available_versions() method
        version_patterns: Single pattern string or list of patterns

    Returns:
        List of resolved specific versions
    """
    if isinstance(version_patterns, str):
        version_patterns = [version_patterns]

    # Get available versions from tool manager
    try:
        available_versions = tool_manager.get_available_versions()
    except Exception as e:
        logger.error(f"Failed to get available versions for {tool_manager.tool_name}: {e}")
        return []

    # Create resolver and resolve patterns
    resolver = VersionResolver(available_versions)
    return resolver.resolve_versions(version_patterns)


# 🧰🌍🔚
