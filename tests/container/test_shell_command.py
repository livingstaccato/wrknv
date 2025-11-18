#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test shell command for interactive container access."""

from __future__ import annotations

from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.config import WorkenvConfig
from wrknv.container.manager import ContainerManager
from wrknv.container.shell_commands import shell_into_container
from wrknv.wenv.schema import ContainerConfig


@pytest.mark.container
class TestShellCommand:
    """Test shell command for interactive container access."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock container manager."""
        manager = Mock(spec=ContainerManager)
        manager.container_name = "test-project-dev"
        manager.container_running = Mock(return_value=True)
        manager.container_exists = Mock(return_value=True)
        return manager

    @pytest.fixture
    def test_config(self) -> None:
        """Create test configuration."""
        return WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(enabled=True),
        )

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_shell_basic(self, mock_manager_class, mock_run, test_config) -> None:
        """Test basic shell command execution."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = True
        mock_manager_class.return_value = mock_manager

        # Mock run_command to return successful result
        mock_run.return_value = Mock(returncode=0)

        result = shell_into_container(test_config)

        assert result is True
        mock_run.assert_called_once_with(
            ["docker", "exec", "-it", "test-project-dev", "/bin/bash"], check=False
        )

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_shell_with_custom_shell(self, mock_manager_class, mock_run, test_config) -> None:
        """Test shell command with custom shell."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = True
        mock_manager_class.return_value = mock_manager

        # Mock run_command to return successful result
        mock_run.return_value = Mock(returncode=0)

        result = shell_into_container(test_config, shell="/bin/zsh")

        assert result is True
        mock_run.assert_called_once_with(
            ["docker", "exec", "-it", "test-project-dev", "/bin/zsh"], check=False
        )

    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_shell_container_not_running(self, mock_manager_class, test_config) -> None:
        """Test shell when container is not running."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = False
        mock_manager.container_exists.return_value = True
        mock_manager.start.return_value = False
        mock_manager_class.return_value = mock_manager

        result = shell_into_container(test_config)

        assert result is False

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_shell_auto_start(self, mock_manager_class, mock_run, test_config) -> None:
        """Test shell with auto-start when container is stopped."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = False
        mock_manager.container_exists.return_value = True
        mock_manager.start.return_value = True
        mock_manager_class.return_value = mock_manager

        # After start, container is running
        mock_manager.container_running.side_effect = [False, True]

        # Mock run_command to return successful result
        mock_run.return_value = Mock(returncode=0)

        result = shell_into_container(test_config, auto_start=True)

        assert result is True
        mock_manager.start.assert_called_once()
        mock_run.assert_called_once()

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_shell_with_working_dir(self, mock_manager_class, mock_run, test_config) -> None:
        """Test shell with custom working directory."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = True
        mock_manager_class.return_value = mock_manager

        # Mock run_command to return successful result
        mock_run.return_value = Mock(returncode=0)

        result = shell_into_container(test_config, working_dir="/app")

        assert result is True
        mock_run.assert_called_once_with(
            ["docker", "exec", "-it", "-w", "/app", "test-project-dev", "/bin/bash"], check=False
        )

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_shell_with_environment(self, mock_manager_class, mock_run, test_config) -> None:
        """Test shell with environment variables."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = True
        mock_manager_class.return_value = mock_manager

        # Mock run_command to return successful result
        mock_run.return_value = Mock(returncode=0)

        env_vars = {"DEBUG": "true", "APP_ENV": "development"}
        result = shell_into_container(test_config, environment=env_vars)

        assert result is True
        expected_cmd = [
            "docker",
            "exec",
            "-it",
            "-e",
            "DEBUG=true",
            "-e",
            "APP_ENV=development",
            "test-project-dev",
            "/bin/bash",
        ]
        mock_run.assert_called_once_with(expected_cmd, check=False)
