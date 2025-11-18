#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for wrknv.wenv.managers.tofu module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from provide.testkit import FoundationTestCase
import pytest

from wrknv.wenv.managers.base import ToolManagerError
from wrknv.wenv.managers.tofu import TofuManager


class TestTofuManagerProperties(FoundationTestCase):
    """Test Tofu manager basic properties."""

    def test_tool_name(self) -> None:
        """Test tool_name property."""
        manager = TofuManager()
        assert manager.tool_name == "tofu"

    def test_executable_name(self) -> None:
        """Test executable_name property."""
        manager = TofuManager()
        assert manager.executable_name == "tofu"

    def test_tool_prefix(self) -> None:
        """Test tool_prefix property."""
        manager = TofuManager()
        assert manager.tool_prefix == "opentofu"


class TestGetAvailableVersions(FoundationTestCase):
    """Test get_available_versions method."""

    @patch("wrknv.wenv.managers.tofu.urlopen")
    def test_get_available_versions_success(self, mock_urlopen: Mock) -> None:
        """Test fetching versions from GitHub API."""
        # Mock GitHub API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {"tag_name": "v1.6.0", "prerelease": False},
                {"tag_name": "v1.5.7", "prerelease": False},
                {"tag_name": "v1.5.0", "prerelease": False},
            ]
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = TofuManager()
        versions = manager.get_available_versions()

        assert isinstance(versions, list)
        # Versions should have 'v' prefix stripped
        assert "1.6.0" in versions
        assert "1.5.7" in versions
        assert "1.5.0" in versions
        # Should NOT have 'v' prefix
        assert "v1.6.0" not in versions

    @patch("wrknv.wenv.managers.tofu.urlopen")
    def test_get_available_versions_includes_prereleases(
        self, mock_urlopen: Mock
    ) -> None:
        """Test fetching versions including prereleases when configured."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {"tag_name": "v1.6.0", "prerelease": False},
                {"tag_name": "v1.6.0-rc1", "prerelease": True},
            ]
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = TofuManager()
        # Mock the config setting check
        with patch.object(manager.config, "get_setting", return_value=True):
            versions = manager.get_available_versions()
            assert "1.6.0-rc1" in versions

    @patch("wrknv.wenv.managers.tofu.urlopen")
    def test_get_available_versions_filters_prereleases(
        self, mock_urlopen: Mock
    ) -> None:
        """Test that prereleases are filtered by default."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {"tag_name": "v1.6.0", "prerelease": False},
                {"tag_name": "v1.6.0-rc1", "prerelease": True},
            ]
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = TofuManager()
        versions = manager.get_available_versions()

        # Prerelease should be filtered out by default
        assert "1.6.0" in versions
        assert "1.6.0-rc1" not in versions

    @patch("wrknv.wenv.managers.tofu.urlopen")
    def test_get_available_versions_sorted(self, mock_urlopen: Mock) -> None:
        """Test that versions are sorted newest first."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {"tag_name": "v1.5.0", "prerelease": False},
                {"tag_name": "v1.6.0", "prerelease": False},
                {"tag_name": "v1.5.7", "prerelease": False},
            ]
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = TofuManager()
        versions = manager.get_available_versions()

        # Should be sorted descending (newest first)
        assert versions[0] == "1.6.0"
        assert versions[1] == "1.5.7"
        assert versions[2] == "1.5.0"

    @patch("wrknv.wenv.managers.tofu.urlopen", side_effect=Exception("Network error"))
    def test_get_available_versions_network_failure(
        self, mock_urlopen: Mock
    ) -> None:
        """Test handling network failures."""
        manager = TofuManager()
        with pytest.raises(ToolManagerError, match="Failed to fetch OpenTofu versions"):
            manager.get_available_versions()


class TestGetDownloadUrl(FoundationTestCase):
    """Test get_download_url method for different platforms."""

    @patch.object(TofuManager, "get_platform_info")
    def test_get_download_url_linux_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for Linux x86_64."""
        mock_platform.return_value = {"os": "linux", "arch": "amd64"}
        manager = TofuManager()

        url = manager.get_download_url("1.6.0")

        assert "github.com/opentofu/opentofu/releases" in url
        assert "v1.6.0" in url
        assert "tofu_1.6.0_linux_amd64.zip" in url

    @patch.object(TofuManager, "get_platform_info")
    def test_get_download_url_linux_arm64(self, mock_platform: Mock) -> None:
        """Test download URL for Linux ARM64."""
        mock_platform.return_value = {"os": "linux", "arch": "arm64"}
        manager = TofuManager()

        url = manager.get_download_url("1.6.0")

        assert "linux_arm64.zip" in url

    @patch.object(TofuManager, "get_platform_info")
    def test_get_download_url_macos_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for macOS x86_64."""
        mock_platform.return_value = {"os": "darwin", "arch": "amd64"}
        manager = TofuManager()

        url = manager.get_download_url("1.6.0")

        assert "darwin_amd64.zip" in url

    @patch.object(TofuManager, "get_platform_info")
    def test_get_download_url_macos_arm64(self, mock_platform: Mock) -> None:
        """Test download URL for macOS ARM64."""
        mock_platform.return_value = {"os": "darwin", "arch": "arm64"}
        manager = TofuManager()

        url = manager.get_download_url("1.6.0")

        assert "darwin_arm64.zip" in url

    @patch.object(TofuManager, "get_platform_info")
    def test_get_download_url_windows_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for Windows x86_64."""
        mock_platform.return_value = {"os": "windows", "arch": "amd64"}
        manager = TofuManager()

        url = manager.get_download_url("1.6.0")

        assert "windows_amd64.zip" in url


class TestGetChecksumUrl(FoundationTestCase):
    """Test get_checksum_url method."""

    def test_get_checksum_url(self) -> None:
        """Test that OpenTofu provides checksum files."""
        manager = TofuManager()
        url = manager.get_checksum_url("1.6.0")

        assert url is not None
        assert "github.com/opentofu/opentofu/releases" in url
        assert "v1.6.0" in url
        assert "tofu_1.6.0_SHA256SUMS" in url


class TestVerifyInstallation(FoundationTestCase):
    """Test verify_installation method."""

    @patch("subprocess.run")
    def test_verify_installation_success(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test successful installation verification."""
        manager = TofuManager()

        # Create fake binary path
        binary_path = manager.get_binary_path("1.6.0")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        # Mock subprocess to return successful version check
        mock_run.return_value = Mock(
            returncode=0, stdout="OpenTofu v1.6.0\n", stderr=""
        )

        result = manager.verify_installation("1.6.0")

        assert result is True
        # Verify -version flag was used
        assert mock_run.call_args[0][0][1] == "-version"

    @patch("subprocess.run")
    def test_verify_installation_version_mismatch(
        self, mock_run: Mock, tmp_path: Path
    ) -> None:
        """Test verification fails on version mismatch."""
        manager = TofuManager()

        binary_path = manager.get_binary_path("1.6.0")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        # Mock subprocess with wrong version
        mock_run.return_value = Mock(
            returncode=0, stdout="OpenTofu v1.5.0\n", stderr=""
        )

        result = manager.verify_installation("1.6.0")
        assert result is False

    def test_verify_installation_binary_missing(self) -> None:
        """Test verification fails when binary doesn't exist."""
        manager = TofuManager()

        result = manager.verify_installation("1.6.0")
        assert result is False

    @patch("subprocess.run", side_effect=Exception("Command failed"))
    def test_verify_installation_subprocess_error(
        self, mock_run: Mock, tmp_path: Path
    ) -> None:
        """Test verification handles subprocess errors."""
        manager = TofuManager()

        binary_path = manager.get_binary_path("1.6.0")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        result = manager.verify_installation("1.6.0")
        assert result is False


class TestVersionSorting(FoundationTestCase):
    """Test version sorting logic."""

    def test_version_sort_key_valid_semver(self) -> None:
        """Test version sorting with valid semver."""
        manager = TofuManager()

        key_160 = manager._version_sort_key("1.6.0")
        key_157 = manager._version_sort_key("1.5.7")

        assert key_160 > key_157

    def test_version_sort_key_incomplete_version(self) -> None:
        """Test version sorting with incomplete versions like 1.0."""
        manager = TofuManager()

        # Should handle incomplete versions
        key = manager._version_sort_key("1.0")
        assert key is not None

    def test_version_sort_key_invalid_version(self) -> None:
        """Test version sorting with invalid version strings."""
        manager = TofuManager()

        # Should return fallback for invalid versions
        key = manager._version_sort_key("invalid")
        assert key is not None


class TestHarnessCompatibility(FoundationTestCase):
    """Test harness compatibility methods."""

    @patch.object(TofuManager, "get_installed_version", return_value="1.6.0")
    def test_get_harness_compatibility_installed(self, mock_version: Mock) -> None:
        """Test harness compatibility when OpenTofu is installed."""
        manager = TofuManager()
        compat = manager.get_harness_compatibility()

        assert compat["status"] == "compatible"
        assert compat["version"] == "1.6.0"
        assert "harness" in compat
        assert compat["harness"]["go.cty"]["compatible"] is True
        assert compat["harness"]["go.wire"]["compatible"] is True
        assert compat["harness"]["conformance"]["compatible"] is True

    @patch.object(TofuManager, "get_installed_version", return_value=None)
    def test_get_harness_compatibility_not_installed(self, mock_version: Mock) -> None:
        """Test harness compatibility when OpenTofu is not installed."""
        manager = TofuManager()
        compat = manager.get_harness_compatibility()

        assert compat["status"] == "not_installed"

    def test_check_cty_compatibility(self) -> None:
        """Test CTY compatibility check."""
        manager = TofuManager()
        result = manager._check_cty_compatibility("1.6.0")

        assert result["compatible"] is True
        assert "notes" in result

    def test_check_wire_compatibility_compatible(self) -> None:
        """Test wire protocol compatibility check with compatible version."""
        manager = TofuManager()
        result = manager._check_wire_compatibility("1.6.0")

        assert result["compatible"] is True
        assert "1.6+" in result["notes"]

    def test_check_wire_compatibility_incompatible(self) -> None:
        """Test wire protocol compatibility check with incompatible version."""
        manager = TofuManager()
        result = manager._check_wire_compatibility("1.5.0")

        assert result["compatible"] is False
        assert "1.6+" in result["notes"]

    def test_check_wire_compatibility_edge_case(self) -> None:
        """Test wire protocol compatibility at exact threshold."""
        manager = TofuManager()

        # 1.6 should be compatible
        result = manager._check_wire_compatibility("1.6.0")
        assert result["compatible"] is True

        # 1.5.9 should not be compatible
        result = manager._check_wire_compatibility("1.5.9")
        assert result["compatible"] is False

    def test_check_wire_compatibility_invalid_version(self) -> None:
        """Test wire protocol compatibility with invalid version."""
        manager = TofuManager()
        result = manager._check_wire_compatibility("invalid")

        assert result["compatible"] is False

    def test_check_conformance_compatibility(self) -> None:
        """Test conformance testing compatibility check."""
        manager = TofuManager()
        result = manager._check_conformance_compatibility("1.6.0")

        assert result["compatible"] is True
        assert "notes" in result


class TestBinaryPath(FoundationTestCase):
    """Test binary path generation."""

    def test_get_binary_path(self) -> None:
        """Test binary path uses opentofu prefix."""
        manager = TofuManager()
        path = manager.get_binary_path("1.6.0")

        # Should use opentofu prefix, not tofu
        assert "opentofu_1.6.0" in str(path)
        assert path == manager.install_path / "opentofu_1.6.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
