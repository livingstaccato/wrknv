#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test CLI integration for shell commands."""

from __future__ import annotations

from click.testing import CliRunner
from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.config import WorkenvConfig
from wrknv.wenv.schema import ContainerConfig


@pytest.mark.container
class TestCLIIntegration:
    """Test CLI integration for shell commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def mock_config(self):
        """Mock WorkenvConfig."""
        config = WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(enabled=True),
        )
        with patch("wrknv.config.WorkenvConfig", return_value=config):
            yield config

    @pytest.fixture
    def mock_container_manager(self):
        """Mock ContainerManager."""
        with patch("wrknv.container.manager.ContainerManager") as mock_class:
            manager = Mock()
            manager.container_name = "test-project-dev"
            manager.container_running.return_value = True
            manager.container_exists.return_value = True
            manager.enter.return_value = True
            manager.logs.return_value = None
            manager.status.return_value = {
                "docker_available": True,
                "image_exists": True,
                "container_exists": True,
                "container_running": True,
                "container_info": {"id": "abc123", "state": "running"},
            }
            mock_class.return_value = manager
            # Also patch in commands module where it's imported
            with patch("wrknv.container.commands.ContainerManager", return_value=manager):
                yield manager

    def test_cli_enter_command(self, runner, mock_config, mock_container_manager) -> None:
        """Test CLI enter command."""
        from wrknv.cli.hub_cli import create_cli

        result = runner.invoke(create_cli(), ["container", "enter"])

        assert result.exit_code == 0
        mock_container_manager.enter.assert_called_once()

    @pytest.mark.skip(reason="Hub CLI parameter duplication bug when tests run in sequence")
    def test_cli_exec_command(self, runner, mock_config, mock_container_manager) -> None:
        """Test CLI exec command."""
        from wrknv.cli.hub_cli import create_cli

        # Mock enter_container at the source (exec command calls this)
        with patch("wrknv.cli.commands.container.enter_container") as mock_enter:
            mock_enter.return_value = None

            result = runner.invoke(create_cli(), ["container", "exec", "ls -la"])

            if result.exit_code != 0:
                pass
            assert result.exit_code == 0
            # Verify enter_container was called with the command
            mock_enter.assert_called_once()

    def test_cli_logs_command(self, runner, mock_config, mock_container_manager) -> None:
        """Test CLI logs command."""
        from wrknv.cli.hub_cli import create_cli

        result = runner.invoke(create_cli(), ["container", "logs"])

        assert result.exit_code == 0
        mock_container_manager.logs.get_logs.assert_called_once()

    def test_cli_logs_with_options(self, runner, mock_config, mock_container_manager) -> None:
        """Test CLI logs command with options."""
        from wrknv.cli.hub_cli import create_cli

        result = runner.invoke(create_cli(), ["container", "logs", "--tail", "50", "--timestamps"])

        assert result.exit_code == 0
        # Check that options were passed through
        mock_container_manager.logs.get_logs.assert_called_once_with(
            follow=False, tail=50, since=None, timestamps=True
        )

    @pytest.mark.skip(reason="stats command not implemented yet")
    def test_cli_stats_command(self, runner, mock_config, mock_container_manager) -> None:
        """Test CLI stats command."""
        from wrknv.cli.hub_cli import create_cli

        # Mock get_container_stats at the source
        with patch("wrknv.container.shell_commands.get_container_stats") as mock_stats:
            mock_stats.return_value = {
                "name": "test-project-dev",
                "cpu": "5.2%",
                "memory": {"usage": "256MB / 1GB", "percent": "25%"},
                "network": "1KB / 2KB",
                "disk": "10MB / 20MB",
                "pids": "10",
            }

            result = runner.invoke(create_cli(), ["container", "stats"])

            assert result.exit_code == 0
            assert "Container Resource Usage" in result.output
            mock_stats.assert_called_once()
