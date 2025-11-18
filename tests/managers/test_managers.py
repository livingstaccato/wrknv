#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from pathlib import Path

from provide.testkit import FoundationTestCase
from provide.testkit.mocking import MagicMock, patch
import pytest

from wrknv.config import WorkenvConfig
from wrknv.managers.base import BaseToolManager


class ConcreteToolManager(BaseToolManager):
    tool_name = "test"
    executable_name = "test"

    def get_download_url(self, version: str) -> str:
        return f"https://example.com/{self.tool_name}/{version}"

    def get_available_versions(self) -> list[str]:
        return ["1.0.0", "1.1.0"]

    def _install_from_archive(self, archive_path: str, version: str) -> None:
        pass

    def get_checksum_url(self, version: str) -> str | None:
        return f"https://example.com/{self.tool_name}/{version}/checksums.txt"


class TestManagers(FoundationTestCase):
    def test_base_tool_manager_init(self) -> None:
        # Arrange
        config = WorkenvConfig()

        # Act
        manager = ConcreteToolManager(config)

        # Assert
        assert manager.config == config

    def test_get_binary_path(self) -> None:
        # Arrange
        config = WorkenvConfig()
        manager = ConcreteToolManager(config)
        expected_path = manager.install_path / manager.tool_name / "1.0.0" / "bin" / manager.executable_name

        # Act
        binary_path = manager.get_binary_path("1.0.0")

        # Assert
        assert binary_path == expected_path

    @patch("pathlib.Path.iterdir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_get_installed_versions(self, mock_exists, mock_iterdir) -> None:
        # Arrange
        config = WorkenvConfig()
        manager = ConcreteToolManager(config)

        # Create dummy directories for mocking
        mock_install_path = MagicMock(spec=Path)
        mock_tool_install_dir = MagicMock(spec=Path)

        # Create proper mock Path objects with name attributes
        mock_dir_1_0_0 = MagicMock(spec=Path)
        mock_dir_1_0_0.name = "1.0.0"
        mock_dir_1_0_0.is_dir.return_value = True

        mock_dir_1_1_0 = MagicMock(spec=Path)
        mock_dir_1_1_0.name = "1.1.0"
        mock_dir_1_1_0.is_dir.return_value = True

        mock_dir_invalid = MagicMock(spec=Path)
        mock_dir_invalid.name = "invalid"
        mock_dir_invalid.is_dir.return_value = True

        mock_dir_2_0_0 = MagicMock(spec=Path)
        mock_dir_2_0_0.name = "2.0.0"
        mock_dir_2_0_0.is_dir.return_value = True

        mock_tool_install_dir.iterdir.return_value = [
            mock_dir_1_0_0,
            mock_dir_1_1_0,
            mock_dir_invalid,
            mock_dir_2_0_0,
        ]
        mock_install_path.__truediv__.return_value = mock_tool_install_dir
        manager.install_path = mock_install_path

        # Act
        versions = manager.get_installed_versions()

        # Assert
        assert versions == ["2.0.0", "1.1.0", "1.0.0"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# 🧰🌍🔚
