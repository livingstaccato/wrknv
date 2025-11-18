#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for wrknv.wenv.managers.uv module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from provide.testkit import FoundationTestCase
import pytest

from wrknv.config import WorkenvConfig
from wrknv.wenv.managers.base import ToolManagerError
from wrknv.wenv.managers.uv import UvManager


class TestUvManagerProperties(FoundationTestCase):
    """Test UV manager basic properties."""

    def test_tool_name(self) -> None:
        """Test tool_name property."""
        manager = UvManager()
        assert manager.tool_name == "uv"

    def test_executable_name(self) -> None:
        """Test executable_name property."""
        manager = UvManager()
        assert manager.executable_name == "uv"


class TestGetAvailableVersions(FoundationTestCase):
    """Test get_available_versions method."""

    @patch("wrknv.wenv.managers.uv.urlopen")
    def test_get_available_versions_success(self, mock_urlopen: Mock) -> None:
        """Test fetching versions from GitHub API."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {"tag_name": "0.4.15", "prerelease": False},
                {"tag_name": "0.4.14", "prerelease": False},
                {"tag_name": "0.4.13-beta", "prerelease": True},
            ]
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = UvManager()
        versions = manager.get_available_versions()

        assert isinstance(versions, list)
        assert "0.4.15" in versions
        assert "0.4.14" in versions
        # Prerelease should be filtered out by default
        assert "0.4.13-beta" not in versions

    @patch("wrknv.wenv.managers.uv.urlopen")
    def test_get_available_versions_includes_prereleases(self, mock_urlopen: Mock) -> None:
        """Test fetching versions including prereleases when configured."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {"tag_name": "0.4.15", "prerelease": False},
                {"tag_name": "0.4.13-beta", "prerelease": True},
            ]
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = UvManager()
        # Mock the config setting check
        with patch.object(manager.config, "get_setting", return_value=True):
            versions = manager.get_available_versions()
            assert "0.4.13-beta" in versions

    @patch("wrknv.wenv.managers.uv.urlopen", side_effect=Exception("Network error"))
    def test_get_available_versions_network_failure(self, mock_urlopen: Mock) -> None:
        """Test handling network failures."""
        manager = UvManager()
        with pytest.raises(ToolManagerError, match="Failed to fetch UV versions"):
            manager.get_available_versions()


class TestGetDownloadUrl(FoundationTestCase):
    """Test get_download_url method for different platforms."""

    @patch.object(UvManager, "get_platform_info")
    def test_get_download_url_linux_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for Linux x86_64."""
        mock_platform.return_value = {"os": "linux", "arch": "amd64"}
        manager = UvManager()

        url = manager.get_download_url("0.4.15")

        assert "github.com/astral-sh/uv/releases" in url
        assert "0.4.15" in url
        assert "x86_64-unknown-linux-gnu.tar.gz" in url

    @patch.object(UvManager, "get_platform_info")
    def test_get_download_url_linux_arm64(self, mock_platform: Mock) -> None:
        """Test download URL for Linux ARM64."""
        mock_platform.return_value = {"os": "linux", "arch": "arm64"}
        manager = UvManager()

        url = manager.get_download_url("0.4.15")

        assert "arm64-unknown-linux-gnu.tar.gz" in url

    @patch.object(UvManager, "get_platform_info")
    def test_get_download_url_macos_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for macOS x86_64."""
        mock_platform.return_value = {"os": "darwin", "arch": "amd64"}
        manager = UvManager()

        url = manager.get_download_url("0.4.15")

        assert "x86_64-apple-darwin.tar.gz" in url

    @patch.object(UvManager, "get_platform_info")
    def test_get_download_url_macos_arm64(self, mock_platform: Mock) -> None:
        """Test download URL for macOS ARM64."""
        mock_platform.return_value = {"os": "darwin", "arch": "arm64"}
        manager = UvManager()

        url = manager.get_download_url("0.4.15")

        assert "arm64-apple-darwin.tar.gz" in url

    @patch.object(UvManager, "get_platform_info")
    def test_get_download_url_windows_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for Windows x86_64."""
        mock_platform.return_value = {"os": "windows", "arch": "amd64"}
        manager = UvManager()

        url = manager.get_download_url("0.4.15")

        assert "amd64-pc-windows-msvc.zip" in url

    @patch.object(UvManager, "get_platform_info")
    def test_get_download_url_unsupported_platform(self, mock_platform: Mock) -> None:
        """Test error handling for unsupported platforms."""
        mock_platform.return_value = {"os": "freebsd", "arch": "amd64"}
        manager = UvManager()

        with pytest.raises(ToolManagerError, match="Unsupported platform"):
            manager.get_download_url("0.4.15")


class TestGetChecksumUrl(FoundationTestCase):
    """Test get_checksum_url method."""

    def test_get_checksum_url_returns_none(self) -> None:
        """Test that UV doesn't provide checksum files."""
        manager = UvManager()
        url = manager.get_checksum_url("0.4.15")
        assert url is None


class TestInstallFromArchive(FoundationTestCase):
    """Test _install_from_archive method."""

    @patch("shutil.copy2")
    @patch("shutil.rmtree")
    @patch.object(UvManager, "verify_installation", return_value=True)
    @patch.object(UvManager, "make_executable")
    @patch.object(UvManager, "extract_archive")
    def test_install_from_archive_success(
        self,
        mock_extract: Mock,
        mock_make_exec: Mock,
        mock_verify: Mock,
        mock_rmtree: Mock,
        mock_copy: Mock,
        tmp_path: Path,
    ) -> None:
        """Test successful installation from archive."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = UvManager(config)

        # Create fake extracted binary
        extract_dir = manager.cache_dir / "uv_0.4.15_extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        fake_binary = extract_dir / "uv"
        fake_binary.touch()

        archive_path = tmp_path / "uv.tar.gz"
        archive_path.touch()

        manager._install_from_archive(archive_path, "0.4.15")

        mock_extract.assert_called_once()
        mock_make_exec.assert_called_once()
        mock_verify.assert_called_once_with("0.4.15")

    @patch("shutil.copy2")
    @patch("shutil.rmtree")
    @patch.object(UvManager, "verify_installation", return_value=False)
    @patch.object(UvManager, "make_executable")
    @patch.object(UvManager, "extract_archive")
    def test_install_from_archive_verification_fails(
        self,
        mock_extract: Mock,
        mock_make_exec: Mock,
        mock_verify: Mock,
        mock_rmtree: Mock,
        mock_copy: Mock,
        tmp_path: Path,
    ) -> None:
        """Test installation fails when verification fails."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = UvManager(config)

        extract_dir = manager.cache_dir / "uv_0.4.15_extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        fake_binary = extract_dir / "uv"
        fake_binary.touch()

        archive_path = tmp_path / "uv.tar.gz"
        archive_path.touch()

        with pytest.raises(ToolManagerError, match="verification failed"):
            manager._install_from_archive(archive_path, "0.4.15")

    @patch("shutil.rmtree")
    @patch.object(UvManager, "extract_archive")
    def test_install_from_archive_binary_not_found(
        self, mock_extract: Mock, mock_rmtree: Mock, tmp_path: Path
    ) -> None:
        """Test error when UV binary not found in archive."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = UvManager(config)

        # Create extract dir with no uv binary
        extract_dir = manager.cache_dir / "uv_0.4.15_extract"
        extract_dir.mkdir(parents=True, exist_ok=True)

        archive_path = tmp_path / "uv.tar.gz"
        archive_path.touch()

        # Mock rglob to return empty list (no uv binary found)
        with (
            patch.object(Path, "rglob", return_value=iter([])),
            pytest.raises(ToolManagerError, match="UV binary not found"),
        ):
            manager._install_from_archive(archive_path, "0.4.15")


class TestVerifyInstallation(FoundationTestCase):
    """Test verify_installation method."""

    @patch("subprocess.run")
    def test_verify_installation_success(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test successful installation verification."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = UvManager(config)

        # Create fake binary
        binary_path = manager.get_binary_path("0.4.15")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        # Mock subprocess to return successful version check
        mock_run.return_value = Mock(returncode=0, stdout="uv 0.4.15\n", stderr="")

        result = manager.verify_installation("0.4.15")

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_verify_installation_version_mismatch(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test verification fails on version mismatch."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = UvManager(config)

        binary_path = manager.get_binary_path("0.4.15")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        # Mock subprocess with wrong version
        mock_run.return_value = Mock(returncode=0, stdout="uv 0.4.14\n", stderr="")

        result = manager.verify_installation("0.4.15")
        assert result is False

    def test_verify_installation_binary_missing(self, tmp_path: Path) -> None:
        """Test verification fails when binary doesn't exist."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = UvManager(config)

        result = manager.verify_installation("0.4.15")
        assert result is False

    @patch("subprocess.run", side_effect=Exception("Command failed"))
    def test_verify_installation_subprocess_error(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test verification handles subprocess errors."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = UvManager(config)

        binary_path = manager.get_binary_path("0.4.15")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        result = manager.verify_installation("0.4.15")
        assert result is False


class TestHarnessCompatibility(FoundationTestCase):
    """Test harness compatibility methods."""

    @patch.object(UvManager, "get_installed_version", return_value="0.4.15")
    def test_get_harness_compatibility_installed(self, mock_version: Mock) -> None:
        """Test harness compatibility when UV is installed."""
        manager = UvManager()
        compat = manager.get_harness_compatibility()

        assert compat["status"] == "compatible"
        assert compat["version"] == "0.4.15"
        assert "harness" in compat
        assert compat["harness"]["python.cty"]["compatible"] is True
        assert compat["harness"]["python.hcl"]["compatible"] is True
        assert compat["harness"]["python.wire"]["compatible"] is True

    @patch.object(UvManager, "get_installed_version", return_value=None)
    def test_get_harness_compatibility_not_installed(self, mock_version: Mock) -> None:
        """Test harness compatibility when UV is not installed."""
        manager = UvManager()
        compat = manager.get_harness_compatibility()

        assert compat["status"] == "not_installed"

    def test_check_python_cty_compatibility(self) -> None:
        """Test Python CTY compatibility check."""
        manager = UvManager()
        result = manager._check_python_cty_compatibility("0.4.15")

        assert result["compatible"] is True
        assert "notes" in result

    def test_check_python_hcl_compatibility(self) -> None:
        """Test Python HCL compatibility check."""
        manager = UvManager()
        result = manager._check_python_hcl_compatibility("0.4.15")

        assert result["compatible"] is True
        assert "notes" in result

    def test_check_python_wire_compatibility(self) -> None:
        """Test Python wire protocol compatibility check."""
        manager = UvManager()
        result = manager._check_python_wire_compatibility("0.4.15")

        assert result["compatible"] is True
        assert "notes" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
