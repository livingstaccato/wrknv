#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import pytest

#
# tests/container/test_container_volume_commands.py
#
"""
Test Container Volume Commands
==============================
Tests for container volume management commands.
"""

import tarfile

from click.testing import CliRunner
from provide.testkit.mocking import Mock, patch

from wrknv.cli.hub_cli import create_cli
from wrknv.config import WorkenvConfig
from wrknv.container.commands import (
    backup_volumes,
    clean_volumes,
    list_volumes,
    restore_volumes,
)
from wrknv.wenv.schema import ContainerConfig


@pytest.mark.container
class TestVolumeCommands:
    """Test volume management commands."""

    @pytest.fixture
    def mock_home(self, tmp_path):
        """Mock home directory for testing."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        with patch("pathlib.Path.home", return_value=mock_home):
            yield mock_home

    @pytest.fixture
    def test_config(self) -> None:
        """Create test configuration."""
        return WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(enabled=True),
        )

    @pytest.fixture
    def mock_manager(self, mock_home, test_config):
        """Create mock container manager."""
        with patch("wrknv.container.commands.ContainerManager") as MockManager:
            manager = MockManager.return_value
            manager.container_name = "test-project-dev"
            manager.get_container_path = Mock(
                side_effect=lambda p="": mock_home / ".wrknv" / "containers" / "test-project-dev" / p
            )

            # Setup mock storage
            container_dir = mock_home / ".wrknv" / "containers" / "test-project-dev"
            container_dir.mkdir(parents=True, exist_ok=True)
            (container_dir / "volumes").mkdir(exist_ok=True)
            (container_dir / "volumes" / "workspace").mkdir(exist_ok=True)
            (container_dir / "volumes" / "cache").mkdir(exist_ok=True)
            (container_dir / "volumes" / "config").mkdir(exist_ok=True)

            yield manager

    def test_list_volumes_command(self, mock_manager, test_config, capsys) -> None:
        """Test list_volumes command output."""
        # Setup mock volumes
        mock_volumes = [
            {
                "name": "workspace",
                "path": "/home/.wrknv/containers/test-project-dev/volumes/workspace",
                "exists": True,
                "size": 1024 * 1024,  # 1MB
                "files": 10,
            },
            {
                "name": "cache",
                "path": "/home/.wrknv/containers/test-project-dev/volumes/cache",
                "exists": True,
                "size": 5 * 1024 * 1024,  # 5MB
                "files": 50,
            },
            {
                "name": "config",
                "path": "/home/.wrknv/containers/test-project-dev/volumes/config",
                "exists": False,
                "size": 0,
                "files": 0,
            },
        ]
        mock_manager.list_volumes.return_value = mock_volumes

        # Run command
        list_volumes(test_config)

        # Check output
        captured = capsys.readouterr()
        assert "Container Volumes" in captured.out
        assert "workspace" in captured.out
        # Check that table is rendered
        assert "cache" in captured.out
        assert "5.0 MB" in captured.out
        assert "50 files" in captured.out
        assert "config" in captured.out
        assert "Not Mounted" in captured.out

    def test_list_volumes_empty(self, mock_manager, test_config, capsys) -> None:
        """Test list_volumes with no volumes."""
        mock_manager.list_volumes.return_value = []

        list_volumes(test_config)

        captured = capsys.readouterr()
        assert "No volumes found" in captured.out

    def test_backup_volumes_command(self, mock_manager, test_config, mock_home, capsys) -> None:
        """Test backup_volumes command."""
        # Setup mock backup
        backup_path = (
            mock_home
            / ".wrknv"
            / "containers"
            / "test-project-dev"
            / "backups"
            / "backup-20250831-150000.tar.gz"
        )
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a real tar file for testing
        with tarfile.open(backup_path, "w:gz") as tar:
            # Add a test file
            test_file = mock_home / "test.txt"
            test_file.write_text("test")
            tar.add(test_file, arcname="volumes/workspace/test.txt")

        mock_manager.backup_volumes.return_value = backup_path

        # Run command
        result = backup_volumes(test_config)

        # Check result
        assert result is True
        mock_manager.backup_volumes.assert_called_once_with(compress=True, include_metadata=True, name=None)

        # Check output
        captured = capsys.readouterr()
        assert "Backup created successfully" in captured.out
        assert "backup-20250831-150000.tar.gz" in captured.out

    def test_backup_volumes_with_name(self, mock_manager, test_config, mock_home, capsys) -> None:
        """Test backup_volumes with custom name."""
        backup_path = (
            mock_home / ".wrknv" / "containers" / "test-project-dev" / "backups" / "custom-backup.tar.gz"
        )
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text("")  # Create empty file

        mock_manager.backup_volumes.return_value = backup_path

        # Run command with custom name
        result = backup_volumes(test_config, name="custom-backup")

        assert result is True
        mock_manager.backup_volumes.assert_called_once_with(
            compress=True, include_metadata=True, name="custom-backup"
        )

    def test_backup_volumes_failure(self, mock_manager, test_config, capsys) -> None:
        """Test backup_volumes command failure."""
        mock_manager.backup_volumes.side_effect = Exception("Backup failed")

        result = backup_volumes(test_config)

        assert result is False
        captured = capsys.readouterr()
        assert "Failed to create backup" in captured.out
        assert "Backup failed" in captured.out

    def test_restore_volumes_command(self, mock_manager, test_config, mock_home, capsys) -> None:
        """Test restore_volumes command."""
        # Create backup file
        backup_path = mock_home / ".wrknv" / "containers" / "test-project-dev" / "backups" / "backup.tar.gz"
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with tarfile.open(backup_path, "w:gz") as tar:
            test_file = mock_home / "test.txt"
            test_file.write_text("restored data")
            tar.add(test_file, arcname="volumes/workspace/test.txt")

        mock_manager.restore_volumes.return_value = True

        # Run command
        result = restore_volumes(test_config, backup_path=str(backup_path))

        assert result is True
        mock_manager.restore_volumes.assert_called_once_with(backup_path, force=False)

        captured = capsys.readouterr()
        assert "Volumes restored successfully" in captured.out
        assert "backup.tar.gz" in captured.out

    def test_restore_volumes_latest(self, mock_manager, test_config, mock_home, capsys) -> None:
        """Test restore_volumes with latest backup."""
        # Create multiple backups
        backups_dir = mock_home / ".wrknv" / "containers" / "test-project-dev" / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)

        older_backup = backups_dir / "backup-20250830-120000.tar.gz"
        latest_backup = backups_dir / "backup-20250831-150000.tar.gz"

        for backup in [older_backup, latest_backup]:
            with tarfile.open(backup, "w:gz") as tar:
                test_file = mock_home / "test.txt"
                test_file.write_text("data")
                tar.add(test_file, arcname="test.txt")

        mock_manager.get_latest_backup.return_value = latest_backup
        mock_manager.restore_volumes.return_value = True

        # Run without specifying backup
        result = restore_volumes(test_config)

        assert result is True
        mock_manager.restore_volumes.assert_called_once_with(latest_backup, force=False)

    def test_restore_volumes_no_backups(self, mock_manager, test_config, capsys) -> None:
        """Test restore_volumes with no backups available."""
        mock_manager.get_latest_backup.return_value = None

        result = restore_volumes(test_config)

        assert result is False
        captured = capsys.readouterr()
        assert "No backups found" in captured.out

    def test_restore_volumes_force(self, mock_manager, test_config, mock_home) -> None:
        """Test restore_volumes with force flag."""
        backup_path = mock_home / ".wrknv" / "containers" / "test-project-dev" / "backups" / "backup.tar.gz"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text("")

        mock_manager.restore_volumes.return_value = True

        result = restore_volumes(test_config, backup_path=str(backup_path), force=True)

        assert result is True
        mock_manager.restore_volumes.assert_called_once_with(backup_path, force=True)

    def test_clean_volumes_command(self, mock_manager, test_config, capsys) -> None:
        """Test clean_volumes command."""
        mock_manager.clean_volumes.return_value = True

        # Mock user confirmation
        with patch("click.confirm", return_value=True):
            result = clean_volumes(test_config)

        assert result is True
        mock_manager.clean_volumes.assert_called_once_with(preserve=[])

        captured = capsys.readouterr()
        assert "Volumes cleaned successfully" in captured.out

    def test_clean_volumes_with_preserve(self, mock_manager, test_config) -> None:
        """Test clean_volumes with preserved volumes."""
        mock_manager.clean_volumes.return_value = True

        with patch("click.confirm", return_value=True):
            result = clean_volumes(test_config, preserve=["workspace", "config"])

        assert result is True
        mock_manager.clean_volumes.assert_called_once_with(preserve=["workspace", "config"])

    def test_clean_volumes_cancelled(self, mock_manager, test_config, capsys) -> None:
        """Test clean_volumes when user cancels."""
        with patch("click.confirm", return_value=False):
            result = clean_volumes(test_config)

        assert result is False
        mock_manager.clean_volumes.assert_not_called()

        captured = capsys.readouterr()
        assert "Cancelled" in captured.out

    def test_clean_volumes_failure(self, mock_manager, test_config, capsys) -> None:
        """Test clean_volumes command failure."""
        mock_manager.clean_volumes.side_effect = Exception("Clean failed")

        with patch("click.confirm", return_value=True):
            result = clean_volumes(test_config)

        assert result is False
        captured = capsys.readouterr()
        assert "Failed to clean volumes" in captured.out


@pytest.mark.container
class TestVolumeCommandsCLI:
    """Test volume commands CLI integration."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def mock_load_config(self):
        """Mock WorkenvConfig constructor."""
        with patch("wrknv.config.WorkenvConfig") as mock:
            mock.return_value = WorkenvConfig(
                project_name="test-project",
                container=ContainerConfig(enabled=True),
            )
            yield mock

    @pytest.fixture
    def mock_container_manager(self, tmp_path):
        """Mock ContainerManager."""
        with patch("wrknv.container.commands.ContainerManager") as mock:
            manager = mock.return_value
            # Setup backup return value
            backup_path = tmp_path / "backup.tar.gz"
            backup_path.write_text("")
            manager.backup_volumes.return_value = backup_path
            # Setup other methods
            manager.get_latest_backup.return_value = backup_path
            manager.restore_volumes.return_value = True
            manager.clean_volumes.return_value = True
            manager.list_volumes.return_value = []
            yield mock

    def test_cli_volumes_list(self, runner, mock_load_config, mock_container_manager) -> None:
        """Test CLI volumes list command."""
        cli = create_cli()

        result = runner.invoke(cli, ["container", "volumes", "list"])

        assert result.exit_code == 0

    def test_cli_volumes_backup(self, runner, mock_load_config, mock_container_manager) -> None:
        """Test CLI volumes backup command."""
        cli = create_cli()

        result = runner.invoke(cli, ["container", "volumes", "backup"])

        # Debug output
        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            if result.exception:
                print(f"Exception: {result.exception}")

        assert result.exit_code == 0

    def test_cli_volumes_backup_with_name(self, runner, mock_load_config, mock_container_manager) -> None:
        """Test CLI volumes backup command with name."""
        cli = create_cli()

        result = runner.invoke(cli, ["container", "volumes", "backup", "--name", "my-backup"])

        assert result.exit_code == 0

    def test_cli_volumes_restore(self, runner, mock_load_config, mock_container_manager) -> None:
        """Test CLI volumes restore command."""
        cli = create_cli()

        result = runner.invoke(cli, ["container", "volumes", "restore"])

        assert result.exit_code == 0

    def test_cli_volumes_restore_with_path(self, runner, mock_load_config, mock_container_manager) -> None:
        """Test CLI volumes restore command with path."""
        cli = create_cli()

        backup_path = "/path/to/backup.tar.gz"
        # backup_path is a positional argument, not an option
        result = runner.invoke(cli, ["container", "volumes", "restore", backup_path])

        assert result.exit_code == 0

    def test_cli_volumes_clean(self, runner, mock_load_config, mock_container_manager) -> None:
        """Test CLI volumes clean command."""
        cli = create_cli()

        # Auto-confirm for testing
        result = runner.invoke(cli, ["container", "volumes", "clean"], input="y\n")

        assert result.exit_code == 0

    def test_cli_volumes_clean_with_preserve(self, runner, mock_load_config, mock_container_manager) -> None:
        """Test CLI volumes clean command with preserve."""
        cli = create_cli()

        result = runner.invoke(
            cli,
            ["container", "volumes", "clean", "--preserve", "workspace", "--preserve", "config"],
            input="y\n",
        )

        assert result.exit_code == 0


# 🧰🌍🔚
