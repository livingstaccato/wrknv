#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for wrknv.wenv.managers.ibm_tf module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, Mock, patch

from provide.testkit import FoundationTestCase
import pytest

from wrknv.wenv.managers.base import ToolManagerError
from wrknv.wenv.managers.ibm_tf import IbmTfManager


class TestIbmTfManagerProperties(FoundationTestCase):
    """Test IBM Terraform manager basic properties."""

    def test_tool_name(self) -> None:
        """Test tool_name property."""
        manager = IbmTfManager()
        assert manager.tool_name == "ibmtf"

    def test_executable_name(self) -> None:
        """Test executable_name property."""
        manager = IbmTfManager()
        assert manager.executable_name == "ibmtf"

    def test_tool_prefix(self) -> None:
        """Test tool_prefix property."""
        manager = IbmTfManager()
        assert manager.tool_prefix == "terraform"


class TestGetAvailableVersions(FoundationTestCase):
    """Test get_available_versions method."""

    @patch("wrknv.wenv.managers.ibm_tf.urlopen")
    def test_get_available_versions_success(self, mock_urlopen: Mock) -> None:
        """Test fetching versions from HashiCorp releases API."""
        # Mock HashiCorp releases index.json format
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "versions": {
                    "1.6.0": {"version": "1.6.0"},
                    "1.5.7": {"version": "1.5.7"},
                    "1.5.0": {"version": "1.5.0"},
                    "1.5.0-rc1": {"version": "1.5.0-rc1"},
                }
            }
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = IbmTfManager()
        versions = manager.get_available_versions()

        assert isinstance(versions, list)
        assert "1.6.0" in versions
        assert "1.5.7" in versions
        assert "1.5.0" in versions
        # Prereleases should be filtered
        assert "1.5.0-rc1" not in versions

    @patch("wrknv.wenv.managers.ibm_tf.urlopen")
    def test_get_available_versions_includes_prereleases(self, mock_urlopen: Mock) -> None:
        """Test fetching versions including prereleases when configured."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "versions": {
                    "1.6.0": {"version": "1.6.0"},
                    "1.6.0-beta1": {"version": "1.6.0-beta1"},
                }
            }
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = IbmTfManager()

        # Mock get_setting to return appropriate values for different settings
        def mock_get_setting(key: str, default=None):
            if key == "include_prereleases":
                return True
            elif key == "terraform_mirror":
                return "https://releases.hashicorp.com/terraform"
            return default

        with patch.object(manager.config, "get_setting", side_effect=mock_get_setting):
            versions = manager.get_available_versions()
            assert "1.6.0-beta1" in versions

    @patch("wrknv.wenv.managers.ibm_tf.urlopen")
    def test_get_available_versions_sorted(self, mock_urlopen: Mock) -> None:
        """Test that versions are sorted newest first."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "versions": {
                    "1.5.0": {"version": "1.5.0"},
                    "1.6.0": {"version": "1.6.0"},
                    "1.5.7": {"version": "1.5.7"},
                }
            }
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = IbmTfManager()
        versions = manager.get_available_versions()

        # Should be sorted descending (newest first)
        assert versions[0] == "1.6.0"
        assert versions[1] == "1.5.7"
        assert versions[2] == "1.5.0"

    @patch("wrknv.wenv.managers.ibm_tf.urlopen")
    def test_get_available_versions_custom_mirror(self, mock_urlopen: Mock) -> None:
        """Test using custom mirror URL."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"versions": {"1.6.0": {"version": "1.6.0"}}}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = IbmTfManager()
        with patch.object(
            manager.config,
            "get_setting",
            return_value="https://mirror.example.com/terraform",
        ):
            manager.get_available_versions()

            # Verify custom mirror was used
            call_args = mock_urlopen.call_args[0][0]
            assert "mirror.example.com/terraform/index.json" in call_args

    @patch("wrknv.wenv.managers.ibm_tf.urlopen", side_effect=Exception("Network error"))
    def test_get_available_versions_network_failure(self, mock_urlopen: Mock) -> None:
        """Test handling network failures."""
        manager = IbmTfManager()
        with pytest.raises(ToolManagerError, match="Failed to fetch IBM Terraform versions"):
            manager.get_available_versions()


class TestPrereleaseDetection(FoundationTestCase):
    """Test prerelease version detection."""

    def test_is_prerelease_alpha(self) -> None:
        """Test detecting alpha versions."""
        manager = IbmTfManager()
        assert manager._is_prerelease("1.6.0-alpha1") is True

    def test_is_prerelease_beta(self) -> None:
        """Test detecting beta versions."""
        manager = IbmTfManager()
        assert manager._is_prerelease("1.6.0-beta2") is True

    def test_is_prerelease_rc(self) -> None:
        """Test detecting release candidate versions."""
        manager = IbmTfManager()
        assert manager._is_prerelease("1.6.0-rc1") is True

    def test_is_prerelease_stable(self) -> None:
        """Test stable versions are not prereleases."""
        manager = IbmTfManager()
        assert manager._is_prerelease("1.6.0") is False

    def test_is_prerelease_with_config_override(self) -> None:
        """Test prerelease detection with config override."""
        manager = IbmTfManager()
        with patch.object(manager.config, "get_setting", return_value=True):
            # When include_prereleases is True, nothing is a prerelease
            assert manager._is_prerelease("1.6.0-beta1") is False


class TestGetDownloadUrl(FoundationTestCase):
    """Test get_download_url method for different platforms."""

    @patch.object(IbmTfManager, "get_platform_info")
    def test_get_download_url_linux_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for Linux x86_64."""
        mock_platform.return_value = {"os": "linux", "arch": "amd64"}
        manager = IbmTfManager()

        url = manager.get_download_url("1.6.0")

        assert "releases.hashicorp.com/terraform" in url
        assert "1.6.0" in url
        assert "terraform_1.6.0_linux_amd64.zip" in url

    @patch.object(IbmTfManager, "get_platform_info")
    def test_get_download_url_linux_arm64(self, mock_platform: Mock) -> None:
        """Test download URL for Linux ARM64."""
        mock_platform.return_value = {"os": "linux", "arch": "arm64"}
        manager = IbmTfManager()

        url = manager.get_download_url("1.6.0")

        assert "linux_arm64.zip" in url

    @patch.object(IbmTfManager, "get_platform_info")
    def test_get_download_url_macos_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for macOS x86_64."""
        mock_platform.return_value = {"os": "darwin", "arch": "amd64"}
        manager = IbmTfManager()

        url = manager.get_download_url("1.6.0")

        assert "darwin_amd64.zip" in url

    @patch.object(IbmTfManager, "get_platform_info")
    def test_get_download_url_windows_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for Windows x86_64."""
        mock_platform.return_value = {"os": "windows", "arch": "amd64"}
        manager = IbmTfManager()

        url = manager.get_download_url("1.6.0")

        assert "windows_amd64.zip" in url

    @patch.object(IbmTfManager, "get_platform_info")
    def test_get_download_url_custom_mirror(self, mock_platform: Mock) -> None:
        """Test download URL with custom mirror."""
        mock_platform.return_value = {"os": "linux", "arch": "amd64"}
        manager = IbmTfManager()

        with patch.object(
            manager.config,
            "get_setting",
            return_value="https://mirror.example.com/terraform",
        ):
            url = manager.get_download_url("1.6.0")
            assert "mirror.example.com/terraform/1.6.0" in url


class TestGetChecksumUrl(FoundationTestCase):
    """Test get_checksum_url method."""

    def test_get_checksum_url(self) -> None:
        """Test that IBM Terraform provides checksum files."""
        manager = IbmTfManager()
        url = manager.get_checksum_url("1.6.0")

        assert url is not None
        assert "releases.hashicorp.com/terraform" in url
        assert "1.6.0" in url
        assert "terraform_1.6.0_SHA256SUMS" in url

    def test_get_checksum_url_custom_mirror(self) -> None:
        """Test checksum URL with custom mirror."""
        manager = IbmTfManager()

        with patch.object(
            manager.config,
            "get_setting",
            return_value="https://mirror.example.com/terraform",
        ):
            url = manager.get_checksum_url("1.6.0")
            assert "mirror.example.com/terraform/1.6.0" in url


class TestVerifyInstallation(FoundationTestCase):
    """Test verify_installation method."""

    @patch("subprocess.run")
    def test_verify_installation_success(self, mock_run: Mock) -> None:
        """Test successful installation verification."""
        manager = IbmTfManager()

        binary_path = manager.get_binary_path("1.6.0")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        mock_run.return_value = Mock(returncode=0, stdout="Terraform v1.6.0\n", stderr="")

        result = manager.verify_installation("1.6.0")

        assert result is True
        assert mock_run.call_args[0][0][1] == "-version"

    @patch("subprocess.run")
    def test_verify_installation_version_mismatch(self, mock_run: Mock) -> None:
        """Test verification fails on version mismatch."""
        manager = IbmTfManager()

        binary_path = manager.get_binary_path("1.6.0")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        mock_run.return_value = Mock(returncode=0, stdout="Terraform v1.5.0\n", stderr="")

        result = manager.verify_installation("1.6.0")
        assert result is False

    def test_verify_installation_binary_missing(self) -> None:
        """Test verification fails when binary doesn't exist."""
        manager = IbmTfManager()

        result = manager.verify_installation("1.6.0")
        assert result is False

    @patch("subprocess.run", side_effect=Exception("Command failed"))
    def test_verify_installation_subprocess_error(self, mock_run: Mock) -> None:
        """Test verification handles subprocess errors."""
        manager = IbmTfManager()

        binary_path = manager.get_binary_path("1.6.0")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        result = manager.verify_installation("1.6.0")
        assert result is False


class TestVersionSorting(FoundationTestCase):
    """Test version sorting logic."""

    def test_version_sort_key_valid_semver(self) -> None:
        """Test version sorting with valid semver."""
        manager = IbmTfManager()

        key_160 = manager._version_sort_key("1.6.0")
        key_157 = manager._version_sort_key("1.5.7")

        assert key_160 > key_157

    def test_version_sort_key_incomplete_version(self) -> None:
        """Test version sorting with incomplete versions."""
        manager = IbmTfManager()

        key = manager._version_sort_key("1.0")
        assert key is not None

    def test_version_sort_key_invalid_version(self) -> None:
        """Test version sorting with invalid version strings."""
        manager = IbmTfManager()

        key = manager._version_sort_key("invalid")
        assert key is not None


class TestHarnessCompatibility(FoundationTestCase):
    """Test harness compatibility methods."""

    @patch.object(IbmTfManager, "get_installed_version", return_value="1.6.0")
    def test_get_harness_compatibility_installed(self, mock_version: Mock) -> None:
        """Test harness compatibility when IBM Terraform is installed."""
        manager = IbmTfManager()
        compat = manager.get_harness_compatibility()

        assert compat["status"] == "compatible"
        assert compat["version"] == "1.6.0"
        assert "harness" in compat
        assert compat["harness"]["go.cty"]["compatible"] is True
        assert compat["harness"]["go.wire"]["compatible"] is True
        assert compat["harness"]["conformance"]["compatible"] is True

    @patch.object(IbmTfManager, "get_installed_version", return_value=None)
    def test_get_harness_compatibility_not_installed(self, mock_version: Mock) -> None:
        """Test harness compatibility when IBM Terraform is not installed."""
        manager = IbmTfManager()
        compat = manager.get_harness_compatibility()

        assert compat["status"] == "not_installed"

    def test_check_cty_compatibility(self) -> None:
        """Test CTY compatibility check."""
        manager = IbmTfManager()
        result = manager._check_cty_compatibility("1.6.0")

        assert result["compatible"] is True
        assert "notes" in result

    def test_check_wire_compatibility_compatible_versions(self) -> None:
        """Test wire protocol compatibility with compatible versions."""
        manager = IbmTfManager()

        # 1.5, 1.6, 1.7 should be compatible
        for version in ["1.5.0", "1.6.0", "1.7.0"]:
            result = manager._check_wire_compatibility(version)
            assert result["compatible"] is True, f"Version {version} should be compatible"

    def test_check_wire_compatibility_incompatible_versions(self) -> None:
        """Test wire protocol compatibility with incompatible versions."""
        manager = IbmTfManager()

        # 1.4, 1.8 should be incompatible
        for version in ["1.4.0", "1.8.0"]:
            result = manager._check_wire_compatibility(version)
            assert result["compatible"] is False, f"Version {version} should be incompatible"

    def test_check_conformance_compatibility(self) -> None:
        """Test conformance testing compatibility check."""
        manager = IbmTfManager()
        result = manager._check_conformance_compatibility("1.6.0")

        assert result["compatible"] is True
        assert "notes" in result


class TestBinaryPath(FoundationTestCase):
    """Test binary path generation."""

    def test_get_binary_path(self) -> None:
        """Test binary path uses terraform prefix."""
        manager = IbmTfManager()
        path = manager.get_binary_path("1.6.0")

        # Should use terraform prefix
        assert "terraform_1.6.0" in str(path)
        assert path == manager.install_path / "terraform_1.6.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
