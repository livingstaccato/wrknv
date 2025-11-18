#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for version resolution utilities."""

from __future__ import annotations

from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock
import pytest
import semver

from wrknv.utils.version_resolver import (
    VersionResolver,
    resolve_tool_versions,
)


class TestVersionResolver(FoundationTestCase):
    """Test VersionResolver class."""

    def test_init(self) -> None:
        """Test VersionResolver initialization."""
        versions = ["1.11.5", "1.11.4", "1.10.0"]
        resolver = VersionResolver(versions)
        assert resolver.available_versions == versions

    def test_resolve_version_latest(self) -> None:
        """Test resolving 'latest' pattern."""
        versions = ["1.11.5", "1.11.4", "1.10.0"]
        resolver = VersionResolver(versions)
        result = resolver.resolve_version("latest")
        assert result == "1.11.5"

    def test_resolve_version_stable(self) -> None:
        """Test resolving 'stable' pattern."""
        versions = ["1.11.5", "1.11.4", "1.10.0"]
        resolver = VersionResolver(versions)
        result = resolver.resolve_version("stable")
        assert result == "1.11.5"

    def test_resolve_version_latest_no_versions(self) -> None:
        """Test resolving 'latest' with no available versions."""
        resolver = VersionResolver([])
        with pytest.raises(ValueError, match="No versions available"):
            resolver.resolve_version("latest")

    def test_resolve_version_exact(self) -> None:
        """Test resolving exact version."""
        versions = ["1.11.5", "1.11.4", "1.10.0"]
        resolver = VersionResolver(versions)
        result = resolver.resolve_version("1.11.4")
        assert result == "1.11.4"

    def test_resolve_version_exact_not_available(self) -> None:
        """Test resolving exact version that doesn't exist."""
        versions = ["1.11.5", "1.11.4"]
        resolver = VersionResolver(versions)
        with pytest.raises(ValueError, match=r"Version 1\.10\.0 not available"):
            resolver.resolve_version("1.10.0")

    def test_resolve_version_x_pattern(self) -> None:
        """Test resolving .x pattern like '1.11.x'."""
        versions = ["1.11.5", "1.11.4", "1.11.3", "1.10.0"]
        resolver = VersionResolver(versions)
        result = resolver.resolve_version("1.11.x")
        assert result == "1.11.5"

    def test_resolve_version_x_pattern_no_match(self) -> None:
        """Test resolving .x pattern with no matching versions."""
        versions = ["1.11.5", "1.10.0"]
        resolver = VersionResolver(versions)
        with pytest.raises(ValueError, match=r"No versions found matching pattern 1\.12\.x"):
            resolver.resolve_version("1.12.x")

    def test_resolve_version_major_minor(self) -> None:
        """Test resolving major.minor pattern."""
        versions = ["1.11.5", "1.11.4", "1.11.3", "1.10.0"]
        resolver = VersionResolver(versions)
        result = resolver.resolve_version("1.11")
        assert result == "1.11.5"

    def test_resolve_version_major_minor_no_match(self) -> None:
        """Test resolving major.minor with no matching versions."""
        versions = ["1.11.5", "1.10.0"]
        resolver = VersionResolver(versions)
        with pytest.raises(ValueError, match=r"No versions found for 1\.12"):
            resolver.resolve_version("1.12")

    def test_resolve_version_with_whitespace(self) -> None:
        """Test that whitespace is stripped from pattern."""
        versions = ["1.11.5", "1.11.4"]
        resolver = VersionResolver(versions)
        result = resolver.resolve_version("  1.11.5  ")
        assert result == "1.11.5"

    def test_resolve_version_unmatched_pattern(self) -> None:
        """Test that unmatched pattern raises error."""
        versions = ["1.11.5"]
        resolver = VersionResolver(versions)
        with pytest.raises(ValueError, match="Version pattern 'invalid' could not be resolved"):
            resolver.resolve_version("invalid")

    def test_is_exact_version_true(self) -> None:
        """Test _is_exact_version with valid semver."""
        resolver = VersionResolver([])
        assert resolver._is_exact_version("1.11.5") is True
        assert resolver._is_exact_version("0.0.1") is True
        assert resolver._is_exact_version("2.1.0") is True

    def test_is_exact_version_false(self) -> None:
        """Test _is_exact_version with invalid semver."""
        resolver = VersionResolver([])
        assert resolver._is_exact_version("1.11") is False
        assert resolver._is_exact_version("1.11.x") is False
        assert resolver._is_exact_version("latest") is False
        assert resolver._is_exact_version("invalid") is False

    def test_is_major_minor_only_true(self) -> None:
        """Test _is_major_minor_only with major.minor format."""
        resolver = VersionResolver([])
        assert resolver._is_major_minor_only("1.11") is True
        assert resolver._is_major_minor_only("0.1") is True
        assert resolver._is_major_minor_only("10.20") is True

    def test_is_major_minor_only_false(self) -> None:
        """Test _is_major_minor_only with other formats."""
        resolver = VersionResolver([])
        assert resolver._is_major_minor_only("1.11.5") is False
        assert resolver._is_major_minor_only("1") is False
        assert resolver._is_major_minor_only("1.11.x") is False
        assert resolver._is_major_minor_only("1.11a") is False

    def test_resolve_x_pattern(self) -> None:
        """Test _resolve_x_pattern method."""
        versions = ["1.11.5", "1.11.4", "1.11.3", "1.10.0"]
        resolver = VersionResolver(versions)
        result = resolver._resolve_x_pattern("1.11.x")
        assert result == "1.11.5"

    def test_resolve_x_pattern_sorting(self) -> None:
        """Test _resolve_x_pattern sorts correctly."""
        versions = ["1.11.3", "1.11.5", "1.11.4"]  # Unsorted
        resolver = VersionResolver(versions)
        result = resolver._resolve_x_pattern("1.11.x")
        assert result == "1.11.5"

    def test_resolve_major_minor(self) -> None:
        """Test _resolve_major_minor method."""
        versions = ["1.11.5", "1.11.4", "1.11.3", "1.10.0"]
        resolver = VersionResolver(versions)
        result = resolver._resolve_major_minor("1.11")
        assert result == "1.11.5"

    def test_resolve_major_minor_sorting(self) -> None:
        """Test _resolve_major_minor sorts correctly."""
        versions = ["1.11.3", "1.11.5", "1.11.4"]  # Unsorted
        resolver = VersionResolver(versions)
        result = resolver._resolve_major_minor("1.11")
        assert result == "1.11.5"

    def test_version_sort_key_valid_semver(self) -> None:
        """Test _version_sort_key with valid semver."""
        resolver = VersionResolver([])
        key1 = resolver._version_sort_key("1.11.5")
        key2 = resolver._version_sort_key("1.11.4")
        assert key1 > key2
        assert isinstance(key1, semver.VersionInfo)

    def test_version_sort_key_major_minor_only(self) -> None:
        """Test _version_sort_key with major.minor format."""
        resolver = VersionResolver([])
        key = resolver._version_sort_key("1.11")
        assert isinstance(key, semver.VersionInfo)
        assert key == semver.VersionInfo.parse("1.11.0")

    def test_version_sort_key_invalid_version(self) -> None:
        """Test _version_sort_key with invalid version."""
        resolver = VersionResolver([])
        key = resolver._version_sort_key("invalid.version")
        assert isinstance(key, semver.VersionInfo)
        assert key == semver.VersionInfo.parse("0.0.0")

    def test_resolve_versions_multiple(self) -> None:
        """Test resolve_versions with multiple patterns."""
        versions = ["1.11.5", "1.11.4", "1.10.0", "1.9.1"]
        resolver = VersionResolver(versions)
        patterns = ["latest", "1.11.x", "1.10.0"]
        results = resolver.resolve_versions(patterns)
        assert results == ["1.11.5", "1.11.5", "1.10.0"]

    def test_resolve_versions_with_failures(self) -> None:
        """Test resolve_versions ignores failures and logs warnings."""
        versions = ["1.11.5", "1.10.0"]
        resolver = VersionResolver(versions)
        patterns = ["1.11.5", "invalid", "1.10.0"]
        results = resolver.resolve_versions(patterns)
        # Invalid pattern is skipped
        assert results == ["1.11.5", "1.10.0"]

    def test_resolve_versions_empty_list(self) -> None:
        """Test resolve_versions with empty pattern list."""
        resolver = VersionResolver(["1.11.5"])
        results = resolver.resolve_versions([])
        assert results == []


class TestResolveToolVersions(FoundationTestCase):
    """Test resolve_tool_versions convenience function."""

    def test_resolve_tool_versions_single_pattern(self) -> None:
        """Test resolve_tool_versions with single pattern string."""
        mock_manager = Mock()
        mock_manager.get_available_versions.return_value = ["1.11.5", "1.11.4", "1.10.0"]
        mock_manager.tool_name = "uv"

        result = resolve_tool_versions(mock_manager, "latest")
        assert result == ["1.11.5"]
        mock_manager.get_available_versions.assert_called_once()

    def test_resolve_tool_versions_list_patterns(self) -> None:
        """Test resolve_tool_versions with list of patterns."""
        mock_manager = Mock()
        mock_manager.get_available_versions.return_value = ["1.11.5", "1.11.4", "1.10.0"]
        mock_manager.tool_name = "uv"

        result = resolve_tool_versions(mock_manager, ["latest", "1.10.0"])
        assert result == ["1.11.5", "1.10.0"]

    def test_resolve_tool_versions_manager_failure(self) -> None:
        """Test resolve_tool_versions when manager fails."""
        mock_manager = Mock()
        mock_manager.get_available_versions.side_effect = Exception("Network error")
        mock_manager.tool_name = "uv"

        result = resolve_tool_versions(mock_manager, "latest")
        assert result == []

    def test_resolve_tool_versions_empty_patterns(self) -> None:
        """Test resolve_tool_versions with empty pattern list."""
        mock_manager = Mock()
        mock_manager.get_available_versions.return_value = ["1.11.5"]
        mock_manager.tool_name = "uv"

        result = resolve_tool_versions(mock_manager, [])
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
