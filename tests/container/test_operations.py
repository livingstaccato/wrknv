#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from provide.testkit import FoundationTestCase
from provide.testkit.mocking import patch
import pytest

from wrknv.config import WorkenvConfig
from wrknv.container.commands import (
    build_container,
    clean_container,
    container_logs,
    container_status,
    enter_container,
    rebuild_container,
    restart_container,
    start_container,
    stop_container,
)


@pytest.mark.container
class TestContainerManager(FoundationTestCase):
    @patch("wrknv.container.manager.ContainerManager.build_image")
    def test_build_container(self, mock_build_image) -> None:
        # Arrange
        mock_build_image.return_value = True
        config = WorkenvConfig(project_name="test-project")

        # Act
        result = build_container(config, rebuild=True)

        # Assert
        assert result
        mock_build_image.assert_called_once_with(rebuild=True)

    @patch("wrknv.container.manager.ContainerManager.start")
    def test_start_container(self, mock_start) -> None:
        # Arrange
        mock_start.return_value = True
        config = WorkenvConfig(project_name="test-project")

        # Act
        result = start_container(config, rebuild=True)

        # Assert
        assert result
        mock_start.assert_called_once_with(force_rebuild=True)

    @patch("wrknv.container.manager.ContainerManager.enter")
    def test_enter_container(self, mock_enter) -> None:
        # Arrange
        config = WorkenvConfig(project_name="test-project")

        # Act
        enter_container(config, command=["ls", "-l"])

        # Assert
        mock_enter.assert_called_once_with(
            command=["ls", "-l"], shell=None, working_dir=None, environment=None, user=None, auto_start=False
        )

    @patch("wrknv.container.manager.ContainerManager.stop")
    def test_stop_container(self, mock_stop) -> None:
        # Arrange
        mock_stop.return_value = True
        config = WorkenvConfig(project_name="test-project")

        # Act
        result = stop_container(config)

        # Assert
        assert result
        mock_stop.assert_called_once_with()

    @patch("wrknv.container.manager.ContainerManager.restart")
    def test_restart_container(self, mock_restart) -> None:
        # Arrange
        mock_restart.return_value = True
        config = WorkenvConfig(project_name="test-project")

        # Act
        result = restart_container(config)

        # Assert
        assert result
        mock_restart.assert_called_once_with()

    @patch("wrknv.container.manager.ContainerManager.status")
    def test_container_status(self, mock_status) -> None:
        # Arrange
        mock_status.return_value = {
            "docker_available": True,
            "image_found": True,
            "container_exists": True,
            "container_running": True,
            "container_info": {"id": "12345", "state": "running"},
        }
        config = WorkenvConfig(project_name="test-project")

        # Act
        container_status(config)

        # Assert
        mock_status.assert_called_once_with()

    @patch("wrknv.container.operations.logs.ContainerLogs.get_logs")
    def test_container_logs(self, mock_get_logs) -> None:
        # Arrange
        config = WorkenvConfig(project_name="test-project")

        # Act
        container_logs(config, follow=True, tail=100)

        # Assert
        # Note: details parameter is not passed to get_logs
        mock_get_logs.assert_called_once_with(follow=True, tail=100, since=None, timestamps=False)

    @patch("wrknv.container.manager.ContainerManager.clean")
    def test_clean_container(self, mock_clean) -> None:
        # Arrange
        mock_clean.return_value = True
        config = WorkenvConfig(project_name="test-project")

        # Act
        result = clean_container(config)

        # Assert
        assert result
        mock_clean.assert_called_once_with()

    @patch("wrknv.container.manager.ContainerManager.start")
    @patch("wrknv.container.manager.ContainerManager.build_image")
    @patch("wrknv.container.manager.ContainerManager.clean")
    def test_rebuild_container(self, mock_clean, mock_build_image, mock_start) -> None:
        # Arrange
        mock_clean.return_value = True
        mock_build_image.return_value = True
        mock_start.return_value = True
        config = WorkenvConfig(project_name="test-project")

        # Act
        result = rebuild_container(config)

        # Assert
        assert result
        mock_clean.assert_called_once_with()
        mock_build_image.assert_called_once_with(rebuild=True)
        mock_start.assert_called_once_with()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# 🧰🌍🔚
