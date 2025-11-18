#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test logs command for viewing container logs."""

from __future__ import annotations

from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.config import WorkenvConfig
from wrknv.container.shell_commands import get_container_logs
from wrknv.wenv.schema import ContainerConfig


@pytest.mark.container
class TestLogsCommand:
    """Test logs command for viewing container logs."""

    @pytest.fixture
    def test_config(self) -> None:
        """Create test configuration."""
        return WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(enabled=True),
        )

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_logs_basic(self, mock_manager_class, mock_run, test_config) -> None:
        """Test basic logs retrieval."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_exists.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_run.return_value = Mock(returncode=0, stdout="container logs here", stderr="")

        result = get_container_logs(test_config)

        assert result == "container logs here"
        mock_run.assert_called_once_with(["docker", "logs", "test-project-dev"], check=False)

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_logs_with_follow(self, mock_manager_class, mock_run, test_config) -> None:
        """Test logs with follow option."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_exists.return_value = True
        mock_manager_class.return_value = mock_manager

        # For follow mode, we don't capture output
        get_container_logs(test_config, follow=True)

        mock_run.assert_called_once_with(["docker", "logs", "-f", "test-project-dev"], check=False)

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_logs_with_tail(self, mock_manager_class, mock_run, test_config) -> None:
        """Test logs with tail option."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_exists.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_run.return_value = Mock(returncode=0, stdout="last lines")

        result = get_container_logs(test_config, tail=50)

        assert result == "last lines"
        mock_run.assert_called_once_with(["docker", "logs", "--tail", "50", "test-project-dev"], check=False)

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_logs_with_timestamps(self, mock_manager_class, mock_run, test_config) -> None:
        """Test logs with timestamps."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_exists.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_run.return_value = Mock(returncode=0, stdout="timestamped logs")

        result = get_container_logs(test_config, timestamps=True)

        assert result == "timestamped logs"
        mock_run.assert_called_once_with(["docker", "logs", "-t", "test-project-dev"], check=False)

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_logs_with_since(self, mock_manager_class, mock_run, test_config) -> None:
        """Test logs with since option."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_exists.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_run.return_value = Mock(returncode=0, stdout="recent logs")

        result = get_container_logs(test_config, since="1h")

        assert result == "recent logs"
        mock_run.assert_called_once_with(
            ["docker", "logs", "--since", "1h", "test-project-dev"],
            check=False,
        )

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_logs_combined_options(self, mock_manager_class, mock_run, test_config) -> None:
        """Test logs with multiple options combined."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_exists.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_run.return_value = Mock(returncode=0, stdout="filtered logs")

        result = get_container_logs(test_config, tail=100, timestamps=True, since="30m")

        assert result == "filtered logs"
        mock_run.assert_called_once_with(
            ["docker", "logs", "-t", "--tail", "100", "--since", "30m", "test-project-dev"],
            check=False,
        )

    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_logs_container_not_exists(self, mock_manager_class, test_config) -> None:
        """Test logs when container doesn't exist."""
        mock_manager = Mock()
        mock_manager.container_exists.return_value = False
        mock_manager_class.return_value = mock_manager

        result = get_container_logs(test_config)

        assert result is None
