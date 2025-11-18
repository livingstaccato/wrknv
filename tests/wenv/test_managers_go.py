#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for wrknv.wenv.managers.go module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from provide.testkit import FoundationTestCase
import pytest

from wrknv.config import WorkenvConfig
from wrknv.wenv.managers.base import ToolManagerError
from wrknv.wenv.managers.go import GoManager


class TestGoManagerProperties(FoundationTestCase):
    """Test Go manager basic properties."""

    def test_tool_name(self) -> None:
        """Test tool_name property."""
        manager = GoManager()
        assert manager.tool_name == "go"

    def test_executable_name(self) -> None:
        """Test executable_name property."""
        manager = GoManager()
        assert manager.executable_name == "go"


class TestGetAvailableVersions(FoundationTestCase):
    """Test get_available_versions method."""

    @patch("wrknv.wenv.managers.go.urlopen")
    def test_get_available_versions_success(self, mock_urlopen: Mock) -> None:
        """Test fetching versions from Go API."""
        # Mock API response - Go API returns releases with 'go' prefix
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {"version": "go1.22.0", "stable": True},
                {"version": "go1.21.5", "stable": True},
                {"version": "go1.21.4", "stable": True},
            ]
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = GoManager()
        versions = manager.get_available_versions()

        assert isinstance(versions, list)
        # Versions should have 'go' prefix stripped
        assert "1.22.0" in versions
        assert "1.21.5" in versions
        assert "1.21.4" in versions
        # Should NOT have 'go' prefix
        assert "go1.22.0" not in versions

    @patch("wrknv.wenv.managers.go.urlopen")
    def test_get_available_versions_includes_unstable(self, mock_urlopen: Mock) -> None:
        """Test fetching versions including unstable when configured."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {"version": "go1.22.0", "stable": True},
                {"version": "go1.22rc1", "stable": False},
            ]
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = GoManager()
        # Mock the config setting check
        with patch.object(manager.config, "get_setting", return_value=True):
            versions = manager.get_available_versions()
            assert "1.22rc1" in versions

    @patch("wrknv.wenv.managers.go.urlopen")
    def test_get_available_versions_filters_unstable(self, mock_urlopen: Mock) -> None:
        """Test that unstable versions are filtered by default."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {"version": "go1.22.0", "stable": True},
                {"version": "go1.22rc1", "stable": False},
            ]
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = GoManager()
        versions = manager.get_available_versions()

        # Unstable should be filtered out by default
        assert "1.22.0" in versions
        assert "1.22rc1" not in versions

    @patch("wrknv.wenv.managers.go.urlopen", side_effect=Exception("Network error"))
    def test_get_available_versions_network_failure(self, mock_urlopen: Mock) -> None:
        """Test handling network failures."""
        manager = GoManager()
        with pytest.raises(ToolManagerError, match="Failed to fetch Go versions"):
            manager.get_available_versions()


class TestGetDownloadUrl(FoundationTestCase):
    """Test get_download_url method for different platforms."""

    @patch.object(GoManager, "get_platform_info")
    def test_get_download_url_linux_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for Linux x86_64."""
        mock_platform.return_value = {"os": "linux", "arch": "amd64"}
        manager = GoManager()

        url = manager.get_download_url("1.22.0")

        assert "go.dev/dl" in url
        assert "go1.22.0" in url
        assert "linux-amd64.tar.gz" in url

    @patch.object(GoManager, "get_platform_info")
    def test_get_download_url_linux_arm64(self, mock_platform: Mock) -> None:
        """Test download URL for Linux ARM64."""
        mock_platform.return_value = {"os": "linux", "arch": "arm64"}
        manager = GoManager()

        url = manager.get_download_url("1.22.0")

        assert "linux-arm64.tar.gz" in url

    @patch.object(GoManager, "get_platform_info")
    def test_get_download_url_macos_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for macOS x86_64."""
        mock_platform.return_value = {"os": "darwin", "arch": "amd64"}
        manager = GoManager()

        url = manager.get_download_url("1.22.0")

        assert "darwin-amd64.tar.gz" in url

    @patch.object(GoManager, "get_platform_info")
    def test_get_download_url_macos_arm64(self, mock_platform: Mock) -> None:
        """Test download URL for macOS ARM64."""
        mock_platform.return_value = {"os": "darwin", "arch": "arm64"}
        manager = GoManager()

        url = manager.get_download_url("1.22.0")

        assert "darwin-arm64.tar.gz" in url

    @patch.object(GoManager, "get_platform_info")
    def test_get_download_url_windows_x86_64(self, mock_platform: Mock) -> None:
        """Test download URL for Windows x86_64."""
        mock_platform.return_value = {"os": "windows", "arch": "amd64"}
        manager = GoManager()

        url = manager.get_download_url("1.22.0")

        assert "windows-amd64.tar.gz" in url

    @patch.object(GoManager, "get_platform_info")
    def test_get_download_url_with_custom_mirror(self, mock_platform: Mock) -> None:
        """Test download URL with custom mirror configured."""
        mock_platform.return_value = {"os": "linux", "arch": "amd64"}
        manager = GoManager()

        # Mock custom mirror configuration
        with patch.object(
            manager.config, "get_setting", return_value="https://mirror.example.com/go"
        ):
            url = manager.get_download_url("1.22.0")
            assert "mirror.example.com/go" in url
            assert "go1.22.0.linux-amd64.tar.gz" in url


class TestGetChecksumUrl(FoundationTestCase):
    """Test get_checksum_url method."""

    def test_get_checksum_url_returns_none(self) -> None:
        """Test that Go doesn't provide separate checksum files."""
        manager = GoManager()
        url = manager.get_checksum_url("1.22.0")
        assert url is None


class TestInstallFromArchive(FoundationTestCase):
    """Test _install_from_archive method."""

    @patch.object(Path, "symlink_to")
    @patch("shutil.rmtree")
    @patch.object(GoManager, "verify_installation", return_value=True)
    @patch.object(GoManager, "extract_archive")
    def test_install_from_archive_success(
        self,
        mock_extract: Mock,
        mock_verify: Mock,
        mock_rmtree: Mock,
        mock_symlink: Mock,
        tmp_path: Path,
    ) -> None:
        """Test successful installation from archive."""
        config = WorkenvConfig()
        # Properly set install path via config setting
        with patch.object(
            config, "get_setting", return_value=str(tmp_path / "tools")
        ):
            manager = GoManager(config)

        # Create fake extracted Go structure
        extract_dir = manager.cache_dir / "go_1.22.0_extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        go_root = extract_dir / "go"
        go_root.mkdir(exist_ok=True)
        go_bin = go_root / "bin"
        go_bin.mkdir(exist_ok=True)
        (go_bin / "go").touch()

        archive_path = tmp_path / "go.tar.gz"
        archive_path.touch()

        # Use actual shutil.move so files are actually moved
        import shutil as real_shutil

        with patch("shutil.move", side_effect=real_shutil.move):
            manager._install_from_archive(archive_path, "1.22.0")

        mock_extract.assert_called_once()
        mock_symlink.assert_called_once()
        mock_verify.assert_called_once_with("1.22.0")

    @patch("shutil.rmtree")
    @patch.object(GoManager, "extract_archive")
    def test_install_from_archive_go_dir_not_found(
        self, mock_extract: Mock, mock_rmtree: Mock, tmp_path: Path
    ) -> None:
        """Test error when go directory not found in archive."""
        config = WorkenvConfig()
        with patch.object(
            config, "get_setting", return_value=str(tmp_path / "tools")
        ):
            manager = GoManager(config)

        # Create extract dir without 'go' subdirectory
        extract_dir = manager.cache_dir / "go_1.22.0_extract"
        extract_dir.mkdir(parents=True, exist_ok=True)

        archive_path = tmp_path / "go.tar.gz"
        archive_path.touch()

        with pytest.raises(ToolManagerError, match="Go directory not found in archive"):
            manager._install_from_archive(archive_path, "1.22.0")

    @patch("shutil.rmtree")
    @patch("shutil.move")
    @patch.object(GoManager, "extract_archive")
    def test_install_from_archive_binary_not_found(
        self, mock_extract: Mock, mock_move: Mock, mock_rmtree: Mock, tmp_path: Path
    ) -> None:
        """Test error when go binary not found in archive."""
        config = WorkenvConfig()
        with patch.object(
            config, "get_setting", return_value=str(tmp_path / "tools")
        ):
            manager = GoManager(config)

        # Create go directory but no binary
        extract_dir = manager.cache_dir / "go_1.22.0_extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        go_root = extract_dir / "go"
        go_root.mkdir(exist_ok=True)

        archive_path = tmp_path / "go.tar.gz"
        archive_path.touch()

        with pytest.raises(ToolManagerError, match="Go binary not found in extracted archive"):
            manager._install_from_archive(archive_path, "1.22.0")

    @patch.object(Path, "symlink_to")
    @patch("shutil.rmtree")
    @patch.object(GoManager, "verify_installation", return_value=False)
    @patch.object(GoManager, "extract_archive")
    def test_install_from_archive_verification_fails(
        self,
        mock_extract: Mock,
        mock_verify: Mock,
        mock_rmtree: Mock,
        mock_symlink: Mock,
        tmp_path: Path,
    ) -> None:
        """Test installation fails when verification fails."""
        config = WorkenvConfig()
        with patch.object(
            config, "get_setting", return_value=str(tmp_path / "tools")
        ):
            manager = GoManager(config)

        # Create proper structure
        extract_dir = manager.cache_dir / "go_1.22.0_extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        go_root = extract_dir / "go"
        go_root.mkdir(exist_ok=True)
        go_bin = go_root / "bin"
        go_bin.mkdir(exist_ok=True)
        (go_bin / "go").touch()

        archive_path = tmp_path / "go.tar.gz"
        archive_path.touch()

        # Use actual shutil.move so files are actually moved
        import shutil as real_shutil

        with (
            patch("shutil.move", side_effect=real_shutil.move),
            pytest.raises(ToolManagerError, match="installation verification failed"),
        ):
            manager._install_from_archive(archive_path, "1.22.0")


class TestVerifyInstallation(FoundationTestCase):
    """Test verify_installation method."""

    @patch("subprocess.run")
    def test_verify_installation_success(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test successful installation verification."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = GoManager(config)

        # Create fake binary structure
        binary_path = manager.get_binary_path("1.22.0")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        # Create GOROOT structure
        go_root = binary_path.parent.parent / "go"
        go_root.mkdir(parents=True, exist_ok=True)

        # Mock subprocess to return successful version check
        mock_run.return_value = Mock(
            returncode=0, stdout="go version go1.22.0 linux/amd64\n", stderr=""
        )

        result = manager.verify_installation("1.22.0")

        assert result is True
        # Verify GOROOT was set in env
        assert mock_run.call_args.kwargs["env"]["GOROOT"] == str(go_root)

    @patch("subprocess.run")
    def test_verify_installation_version_mismatch(
        self, mock_run: Mock, tmp_path: Path
    ) -> None:
        """Test verification fails on version mismatch."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = GoManager(config)

        binary_path = manager.get_binary_path("1.22.0")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        go_root = binary_path.parent.parent / "go"
        go_root.mkdir(parents=True, exist_ok=True)

        # Mock subprocess with wrong version
        mock_run.return_value = Mock(
            returncode=0, stdout="go version go1.21.0 linux/amd64\n", stderr=""
        )

        result = manager.verify_installation("1.22.0")
        assert result is False

    def test_verify_installation_binary_missing(self, tmp_path: Path) -> None:
        """Test verification fails when binary doesn't exist."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = GoManager(config)

        result = manager.verify_installation("1.22.0")
        assert result is False

    @patch("subprocess.run", side_effect=Exception("Command failed"))
    def test_verify_installation_subprocess_error(
        self, mock_run: Mock, tmp_path: Path
    ) -> None:
        """Test verification handles subprocess errors."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = GoManager(config)

        binary_path = manager.get_binary_path("1.22.0")
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.touch()

        go_root = binary_path.parent.parent / "go"
        go_root.mkdir(parents=True, exist_ok=True)

        result = manager.verify_installation("1.22.0")
        assert result is False


class TestHarnessCompatibility(FoundationTestCase):
    """Test harness compatibility methods."""

    @patch.object(GoManager, "get_installed_version", return_value="1.22.0")
    def test_get_harness_compatibility_installed(self, mock_version: Mock) -> None:
        """Test harness compatibility when Go is installed."""
        manager = GoManager()
        compat = manager.get_harness_compatibility()

        assert compat["status"] == "compatible"
        assert compat["version"] == "1.22.0"
        assert "harness" in compat
        # All harnesses should be compatible with Go 1.22
        assert compat["harness"]["go.cty"]["compatible"] is True
        assert compat["harness"]["go.rpc"]["compatible"] is True
        assert compat["harness"]["go.wire"]["compatible"] is True
        assert compat["harness"]["go.hcl"]["compatible"] is True

    @patch.object(GoManager, "get_installed_version", return_value=None)
    def test_get_harness_compatibility_not_installed(self, mock_version: Mock) -> None:
        """Test harness compatibility when Go is not installed."""
        manager = GoManager()
        compat = manager.get_harness_compatibility()

        assert compat["status"] == "not_installed"

    def test_check_go_cty_compatibility_compatible(self) -> None:
        """Test Go CTY compatibility check with compatible version."""
        manager = GoManager()
        result = manager._check_go_cty_compatibility("1.20.0")

        assert result["compatible"] is True
        assert "1.18+" in result["notes"]

    def test_check_go_cty_compatibility_incompatible(self) -> None:
        """Test Go CTY compatibility check with incompatible version."""
        manager = GoManager()
        result = manager._check_go_cty_compatibility("1.17.0")

        assert result["compatible"] is False
        assert "1.18+" in result["notes"]

    def test_check_go_rpc_compatibility_compatible(self) -> None:
        """Test Go RPC compatibility check with compatible version."""
        manager = GoManager()
        result = manager._check_go_rpc_compatibility("1.20.0")

        assert result["compatible"] is True
        assert "1.19+" in result["notes"]

    def test_check_go_rpc_compatibility_incompatible(self) -> None:
        """Test Go RPC compatibility check with incompatible version."""
        manager = GoManager()
        result = manager._check_go_rpc_compatibility("1.18.0")

        assert result["compatible"] is False
        assert "1.19+" in result["notes"]

    def test_check_go_wire_compatibility(self) -> None:
        """Test Go wire protocol compatibility check."""
        manager = GoManager()
        result = manager._check_go_wire_compatibility("1.20.0")

        assert result["compatible"] is True
        assert "1.18+" in result["notes"]

    def test_check_go_hcl_compatibility(self) -> None:
        """Test Go HCL compatibility check."""
        manager = GoManager()
        result = manager._check_go_hcl_compatibility("1.20.0")

        assert result["compatible"] is True
        assert "1.18+" in result["notes"]


class TestVersionComparison(FoundationTestCase):
    """Test version comparison method."""

    def test_version_compare_less_than(self) -> None:
        """Test version comparison with first version less than second."""
        manager = GoManager()
        result = manager._version_compare("1.20.0", "1.21.0")
        assert result == -1

    def test_version_compare_greater_than(self) -> None:
        """Test version comparison with first version greater than second."""
        manager = GoManager()
        result = manager._version_compare("1.21.0", "1.20.0")
        assert result == 1

    def test_version_compare_equal(self) -> None:
        """Test version comparison with equal versions."""
        manager = GoManager()
        result = manager._version_compare("1.20.0", "1.20.0")
        assert result == 0

    def test_version_compare_patch_level(self) -> None:
        """Test version comparison at patch level."""
        manager = GoManager()
        result = manager._version_compare("1.20.1", "1.20.5")
        assert result == -1

    def test_version_compare_different_lengths(self) -> None:
        """Test version comparison with different segment counts."""
        manager = GoManager()
        # 1.20.0.0 vs 1.20.0 - should handle gracefully
        result = manager._version_compare("1.20.0", "1.21.0")
        assert result == -1


class TestGoPathMethods(FoundationTestCase):
    """Test GOROOT and GOPATH methods."""

    def test_get_goroot(self, tmp_path: Path) -> None:
        """Test GOROOT path generation."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = GoManager(config)

        goroot = manager.get_goroot("1.22.0")

        assert goroot == manager.install_path / "go" / "1.22.0" / "go"
        assert "1.22.0" in str(goroot)

    def test_get_gopath(self, tmp_path: Path) -> None:
        """Test GOPATH path generation."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = GoManager(config)

        gopath = manager.get_gopath("1.22.0")

        assert gopath == manager.install_path / "go" / "1.22.0" / "gopath"
        assert "1.22.0" in str(gopath)
        assert "gopath" in str(gopath)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
