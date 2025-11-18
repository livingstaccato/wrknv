#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test exec command for running commands in containers."""

from __future__ import annotations

from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.config import WorkenvConfig
from wrknv.container.shell_commands import exec_in_container
from wrknv.wenv.schema import ContainerConfig


@pytest.mark.container
class TestExecCommand:
    """Test exec command for running commands in containers."""

    @pytest.fixture
    def test_config(self) -> None:
        """Create test configuration."""
        return WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(enabled=True),
        )

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_exec_basic(self, mock_manager_class, mock_run, test_config) -> None:
        """Test basic command execution."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_run.return_value = Mock(returncode=0, stdout="command output", stderr="")

        result = exec_in_container(test_config, ["ls", "-la"])

        assert result.returncode == 0
        assert result.stdout == "command output"
        mock_run.assert_called_once_with(["docker", "exec", "test-project-dev", "ls", "-la"], check=False)

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_exec_with_working_dir(self, mock_manager_class, mock_run, test_config) -> None:
        """Test exec with working directory."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_run.return_value = Mock(returncode=0)

        exec_in_container(test_config, ["pwd"], working_dir="/app")

        mock_run.assert_called_once_with(
            ["docker", "exec", "-w", "/app", "test-project-dev", "pwd"],
            check=False,
        )

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_exec_with_environment(self, mock_manager_class, mock_run, test_config) -> None:
        """Test exec with environment variables."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_run.return_value = Mock(returncode=0)

        exec_in_container(test_config, ["echo", "$DEBUG"], environment={"DEBUG": "1"})

        mock_run.assert_called_once_with(
            ["docker", "exec", "-e", "DEBUG=1", "test-project-dev", "echo", "$DEBUG"],
            check=False,
        )

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_exec_interactive(self, mock_manager_class, mock_run, test_config) -> None:
        """Test interactive command execution."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_run.return_value = Mock(returncode=0)

        exec_in_container(test_config, ["python"], interactive=True)

        mock_run.assert_called_once_with(
            ["docker", "exec", "-it", "test-project-dev", "python"],
            check=False,
        )

    @patch("wrknv.container.shell_commands.run")
    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_exec_with_user(self, mock_manager_class, mock_run, test_config) -> None:
        """Test exec with specific user."""
        mock_manager = Mock()
        mock_manager.container_name = "test-project-dev"
        mock_manager.container_running.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_run.return_value = Mock(returncode=0)

        exec_in_container(test_config, ["whoami"], user="nobody")

        mock_run.assert_called_once_with(
            ["docker", "exec", "-u", "nobody", "test-project-dev", "whoami"],
            check=False,
        )

    @patch("wrknv.container.shell_commands.ContainerManager")
    def test_exec_container_not_running(self, mock_manager_class, test_config) -> None:
        """Test exec when container is not running."""
        mock_manager = Mock()
        mock_manager.container_running.return_value = False
        mock_manager_class.return_value = mock_manager

        result = exec_in_container(test_config, ["ls"])

        assert result is None
