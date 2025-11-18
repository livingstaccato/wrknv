#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for wrknv.wenv.managers.base module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

from provide.testkit import FoundationTestCase
import pytest

from wrknv.config import WorkenvConfig, WorkenvConfigError
from wrknv.wenv.managers.base import BaseToolManager, ToolManagerError


class ConcreteToolManager(BaseToolManager):
    """Concrete implementation for testing."""

    @property
    def tool_name(self) -> str:
        return "testtool"

    @property
    def executable_name(self) -> str:
        return "testtool"

    def get_available_versions(self) -> list[str]:
        return ["2.0.0", "1.1.0", "1.0.0"]

    def get_download_url(self, version: str) -> str:
        return f"https://example.com/testtool/{version}/testtool.tar.gz"

    def get_checksum_url(self, version: str) -> str | None:
        return f"https://example.com/testtool/{version}/checksums.txt"

    def _install_from_archive(self, archive_path: Path, version: str) -> None:
        # Simulate installation
        version_dir = self.install_path / self.tool_name / version / "bin"
        version_dir.mkdir(parents=True, exist_ok=True)
        binary = version_dir / self.executable_name
        binary.touch()
        binary.chmod(0o755)


class TestBaseToolManagerInit(FoundationTestCase):
    """Test BaseToolManager initialization."""

    def test_init_with_config(self, tmp_path: Path) -> None:
        """Test initialization with provided config."""
        config = WorkenvConfig()
        manager = ConcreteToolManager(config)
        assert manager.config == config

    def test_init_without_config(self) -> None:
        """Test initialization creates default config."""
        manager = ConcreteToolManager()
        assert isinstance(manager.config, WorkenvConfig)

    def test_init_creates_directories(self, tmp_path: Path) -> None:
        """Test that initialization creates necessary directories."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = ConcreteToolManager(config)
        assert manager.install_path.exists()
        assert manager.cache_dir.exists()


class TestBaseToolManagerProperties(FoundationTestCase):
    """Test BaseToolManager properties and basic methods."""

    def test_tool_name_property(self) -> None:
        """Test tool_name property."""
        manager = ConcreteToolManager()
        assert manager.tool_name == "testtool"

    def test_executable_name_property(self) -> None:
        """Test executable_name property."""
        manager = ConcreteToolManager()
        assert manager.executable_name == "testtool"

    def test_get_platform_info(self) -> None:
        """Test get_platform_info method."""
        manager = ConcreteToolManager()
        platform_info = manager.get_platform_info()
        assert isinstance(platform_info, dict)
        assert "os" in platform_info
        assert "arch" in platform_info


class TestVersionManagement(FoundationTestCase):
    """Test version management methods."""

    def test_get_installed_version_none_when_not_set(self) -> None:
        """Test getting installed version when none is set."""
        manager = ConcreteToolManager()
        version = manager.get_installed_version()
        assert version is None or version == ""

    @patch.object(WorkenvConfig, "set_tool_version")
    def test_set_installed_version(self, mock_set: Mock) -> None:
        """Test setting installed version."""
        manager = ConcreteToolManager()
        manager.set_installed_version("1.0.0")
        mock_set.assert_called_once_with("testtool", "1.0.0")

    @patch.object(WorkenvConfig, "set_tool_version", side_effect=WorkenvConfigError("test"))
    @patch("wrknv.wenv.managers.base.logger")
    def test_set_installed_version_handles_error(self, mock_logger: Mock, mock_set: Mock) -> None:
        """Test that set_installed_version handles errors gracefully."""
        manager = ConcreteToolManager()
        manager.set_installed_version("1.0.0")
        assert mock_logger.warning.called


class TestBinaryPaths(FoundationTestCase):
    """Test binary path methods."""

    def test_get_binary_path(self, tmp_path: Path) -> None:
        """Test getting binary path for a version."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = ConcreteToolManager(config)

        binary_path = manager.get_binary_path("1.0.0")
        assert binary_path == manager.install_path / "testtool" / "1.0.0" / "bin" / "testtool"

    @patch("platform.system", return_value="Windows")
    def test_get_binary_path_windows(self, mock_platform: Mock, tmp_path: Path) -> None:
        """Test binary path adds .exe on Windows."""
        config = WorkenvConfig()
        config.workenv_cache_dir = str(tmp_path / "cache")
        manager = ConcreteToolManager(config)

        binary_path = manager.get_binary_path("1.0.0")
        assert binary_path.name == "testtool.exe"

    @patch.object(ConcreteToolManager, "get_installed_version", return_value="1.0.0")
    def test_get_current_binary_path(self, mock_version: Mock) -> None:
        """Test getting current binary path."""
        manager = ConcreteToolManager()
        binary_path = manager.get_current_binary_path()
        assert binary_path is not None
        assert "1.0.0" in str(binary_path)

    @patch.object(ConcreteToolManager, "get_installed_version", return_value=None)
    def test_get_current_binary_path_none_when_no_version(self, mock_version: Mock) -> None:
        """Test getting current binary path when no version installed."""
        manager = ConcreteToolManager()
        binary_path = manager.get_current_binary_path()
        assert binary_path is None


class TestInstalledVersions(FoundationTestCase):
    """Test get_installed_versions method."""

    def test_get_installed_versions_empty(self, tmp_path: Path) -> None:
        """Test getting installed versions when none exist."""
        config = WorkenvConfig()
        with patch.object(config, "get_setting", return_value=str(tmp_path / "tools")):
            manager = ConcreteToolManager(config)

            versions = manager.get_installed_versions()
            assert versions == []

    def test_get_installed_versions_with_versions(self, tmp_path: Path) -> None:
        """Test getting installed versions when some exist."""
        config = WorkenvConfig()
        with patch.object(config, "get_setting", return_value=str(tmp_path / "tools")):
            manager = ConcreteToolManager(config)

            # Create fake version directories
            tool_dir = manager.install_path / "testtool"
            (tool_dir / "1.0.0").mkdir(parents=True)
            (tool_dir / "2.0.0").mkdir(parents=True)
            (tool_dir / "1.5.0").mkdir(parents=True)
            (tool_dir / "invalid").mkdir(parents=True)  # Should be ignored

            versions = manager.get_installed_versions()
            assert "1.0.0" in versions
            assert "2.0.0" in versions
            assert "1.5.0" in versions
            assert "invalid" not in versions
            # Should be sorted in reverse order
            assert versions[0] > versions[-1]


class TestVersionDirCheck(FoundationTestCase):
    """Test _is_version_dir method."""

    def test_is_version_dir_valid(self) -> None:
        """Test version directory validation with valid versions."""
        manager = ConcreteToolManager()
        assert manager._is_version_dir("1.0.0")
        assert manager._is_version_dir("2.1.3")
        assert manager._is_version_dir("10.20.30")

    def test_is_version_dir_invalid(self) -> None:
        """Test version directory validation with invalid names."""
        manager = ConcreteToolManager()
        assert not manager._is_version_dir("invalid")
        assert not manager._is_version_dir("v1.0.0")
        assert not manager._is_version_dir("latest")
        assert not manager._is_version_dir("1.0")


class TestAvailableVersions(FoundationTestCase):
    """Test get_available_versions method."""

    def test_get_available_versions(self) -> None:
        """Test getting available versions."""
        manager = ConcreteToolManager()
        versions = manager.get_available_versions()
        assert isinstance(versions, list)
        assert "1.0.0" in versions
        assert "2.0.0" in versions


class TestDownloadUrl(FoundationTestCase):
    """Test get_download_url method."""

    def test_get_download_url(self) -> None:
        """Test getting download URL."""
        manager = ConcreteToolManager()
        url = manager.get_download_url("1.0.0")
        assert "1.0.0" in url
        assert "testtool" in url


class TestChecksumUrl(FoundationTestCase):
    """Test get_checksum_url method."""

    def test_get_checksum_url(self) -> None:
        """Test getting checksum URL."""
        manager = ConcreteToolManager()
        url = manager.get_checksum_url("1.0.0")
        assert url is not None
        assert "1.0.0" in url


class TestListVersions(FoundationTestCase):
    """Test list_versions method."""

    @patch("builtins.print")
    @patch.object(ConcreteToolManager, "get_installed_version", return_value="1.0.0")
    def test_list_versions(self, mock_version: Mock, mock_print: Mock) -> None:
        """Test listing versions."""
        manager = ConcreteToolManager()
        manager.list_versions(limit=10)
        assert mock_print.called

    @patch("builtins.print")
    @patch.object(ConcreteToolManager, "get_available_versions", side_effect=Exception("API Error"))
    def test_list_versions_error(self, mock_versions: Mock, mock_print: Mock) -> None:
        """Test list_versions handles errors."""
        manager = ConcreteToolManager()
        with pytest.raises(ToolManagerError):
            manager.list_versions()


class TestShowCurrent(FoundationTestCase):
    """Test show_current method."""

    @patch("builtins.print")
    @patch.object(ConcreteToolManager, "get_installed_version", return_value="1.0.0")
    @patch.object(ConcreteToolManager, "get_current_binary_path")
    def test_show_current_installed(
        self, mock_binary: Mock, mock_version: Mock, mock_print: Mock, tmp_path: Path
    ) -> None:
        """Test showing current version when installed."""
        binary_path = tmp_path / "testtool"
        binary_path.touch()
        mock_binary.return_value = binary_path

        manager = ConcreteToolManager()
        manager.show_current()
        mock_print.assert_called_once()
        assert "1.0.0" in mock_print.call_args[0][0]

    @patch("builtins.print")
    @patch.object(ConcreteToolManager, "get_installed_version", return_value=None)
    def test_show_current_not_installed(self, mock_version: Mock, mock_print: Mock) -> None:
        """Test showing current version when not installed."""
        manager = ConcreteToolManager()
        manager.show_current()
        mock_print.assert_called_once()
        assert "not installed" in mock_print.call_args[0][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
