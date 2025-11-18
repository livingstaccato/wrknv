#!/usr/bin/env python3
"""
Test suite for CLI lock command.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import click.testing
from provide.testkit import FoundationTestCase
import pytest

from wrknv.cli.hub_cli import create_cli
from wrknv.lockfile import Lockfile, ResolvedTool


# Module-level shared CLI instance
_test_cli = None


def get_test_cli():
    """Get or create the test CLI instance."""
    global _test_cli
    if _test_cli is None:
        _test_cli = create_cli()
    return _test_cli


class TestLockGenerateCommand(FoundationTestCase):
    """Test lock generate command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.temp_dir = self.create_temp_dir()

    def test_generate_success(self) -> None:
        """Test generating lockfile successfully."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                mock_manager.lockfile_path.exists.return_value = False

                mock_lockfile = Mock()
                mock_lockfile.resolved_tools = {"go": Mock(), "terraform": Mock()}
                mock_manager.resolve_and_lock.return_value = mock_lockfile
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "generate"])

                assert result.exit_code == 0
                assert "Generating lockfile" in result.output
                assert "Lockfile generated with 2 resolved tools" in result.output
                mock_manager.resolve_and_lock.assert_called_once_with(mock_config)

    def test_generate_already_exists_no_force(self) -> None:
        """Test generating lockfile when it already exists without --force."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                mock_manager.lockfile_path.exists.return_value = True
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "generate"])

                assert result.exit_code == 1
                assert "Lockfile already exists" in result.output
                assert "Use --force to overwrite" in result.output
                mock_manager.resolve_and_lock.assert_not_called()

    def test_generate_with_force(self) -> None:
        """Test generating lockfile with --force flag."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                mock_manager.lockfile_path.exists.return_value = True

                mock_lockfile = Mock()
                mock_lockfile.resolved_tools = {"go": Mock()}
                mock_manager.resolve_and_lock.return_value = mock_lockfile
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "generate", "--force"])

                assert result.exit_code == 0
                assert "Generating lockfile" in result.output
                mock_manager.resolve_and_lock.assert_called_once_with(mock_config)

    def test_generate_error(self) -> None:
        """Test error during lockfile generation."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path.exists.return_value = False
                mock_manager.resolve_and_lock.side_effect = Exception("Resolution failed")
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "generate"])

                assert result.exit_code == 1
                assert "Failed to generate lockfile" in result.output
                assert "Resolution failed" in result.output


class TestLockCheckCommand(FoundationTestCase):
    """Test lock check command."""

    def test_check_no_lockfile(self) -> None:
        """Test checking when no lockfile exists."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                mock_manager.lockfile_path.exists.return_value = False
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "check"])

                assert result.exit_code == 1
                assert "No lockfile found" in result.output
                assert "wrknv lock generate" in result.output

    def test_check_valid_lockfile(self) -> None:
        """Test checking with valid lockfile."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                mock_manager.lockfile_path.exists.return_value = True
                mock_manager.is_lockfile_valid.return_value = True
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "check"])

                assert result.exit_code == 0
                assert "Lockfile is valid" in result.output

    def test_check_invalid_lockfile(self) -> None:
        """Test checking with invalid/outdated lockfile."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                mock_manager.lockfile_path.exists.return_value = True
                mock_manager.is_lockfile_valid.return_value = False
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "check"])

                assert result.exit_code == 1
                assert "Lockfile is outdated or invalid" in result.output
                assert "wrknv lock generate --force" in result.output

    def test_check_error(self) -> None:
        """Test error during lockfile check."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path.exists.return_value = True
                mock_manager.is_lockfile_valid.side_effect = Exception("Validation error")
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "check"])

                assert result.exit_code == 1
                assert "Failed to check lockfile" in result.output


class TestLockShowCommand(FoundationTestCase):
    """Test lock show command."""

    def test_show_no_lockfile(self) -> None:
        """Test showing lockfile when none exists."""
        with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
            mock_manager.lockfile_path.exists.return_value = False
            mock_manager_class.return_value = mock_manager

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["lock", "show"])

            assert result.exit_code == 0
            assert "No lockfile found" in result.output

    def test_show_corrupted_lockfile(self) -> None:
        """Test showing corrupted lockfile."""
        with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
            mock_manager.lockfile_path.exists.return_value = True
            mock_manager.load_lockfile.return_value = None
            mock_manager_class.return_value = mock_manager

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["lock", "show"])

            assert result.exit_code == 0
            assert "Failed to load lockfile (corrupted?)" in result.output

    def test_show_lockfile_with_tools(self) -> None:
        """Test showing lockfile with tools."""
        with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
            mock_manager.lockfile_path.exists.return_value = True

            # Create mock lockfile with tools
            tool1 = ResolvedTool(
                name="go",
                version="1.22.0",
                resolved_from="1.22.x",
                installed_at="2024-01-01T00:00:00",
            )
            tool2 = ResolvedTool(
                name="terraform",
                version="1.7.0",
                resolved_from="latest",
                installed_at=None,  # Not installed
            )

            mock_lockfile = Mock()
            mock_lockfile.config_checksum = "abc123def456"
            mock_lockfile.created_at = "2024-01-01T00:00:00"
            mock_lockfile.wrknv_version = "0.1.0"
            mock_lockfile.resolved_tools = {"go": tool1, "terraform": tool2}

            mock_manager.load_lockfile.return_value = mock_lockfile
            mock_manager_class.return_value = mock_manager

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["lock", "show"])

            assert result.exit_code == 0
            assert "Lockfile: /tmp/wrknv.lock" in result.output
            assert "Config checksum: abc123def456" in result.output
            assert "Tools: 2" in result.output
            assert "go: 1.22.0" in result.output
            assert "terraform: 1.7.0" in result.output
            assert "installed" in result.output
            assert "not installed" in result.output

    def test_show_lockfile_without_tools(self) -> None:
        """Test showing lockfile without any tools."""
        with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
            mock_manager.lockfile_path.exists.return_value = True

            mock_lockfile = Mock()
            mock_lockfile.config_checksum = "abc123"
            mock_lockfile.created_at = "2024-01-01T00:00:00"
            mock_lockfile.wrknv_version = "0.1.0"
            mock_lockfile.resolved_tools = {}

            mock_manager.load_lockfile.return_value = mock_lockfile
            mock_manager_class.return_value = mock_manager

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["lock", "show"])

            assert result.exit_code == 0
            assert "Tools: 0" in result.output

    def test_show_error(self) -> None:
        """Test error during lockfile show."""
        with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager.lockfile_path.exists.side_effect = Exception("Filesystem error")
            mock_manager_class.return_value = mock_manager

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["lock", "show"])

            assert result.exit_code == 1
            assert "Failed to show lockfile" in result.output


class TestLockCleanCommand(FoundationTestCase):
    """Test lock clean command."""

    def test_clean_no_lockfile(self) -> None:
        """Test cleaning when no lockfile exists."""
        with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
            mock_manager.lockfile_path.exists.return_value = False
            mock_manager_class.return_value = mock_manager

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["lock", "clean"])

            assert result.exit_code == 0
            assert "No lockfile to remove" in result.output

    def test_clean_success(self) -> None:
        """Test successfully removing lockfile."""
        with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
            mock_manager.lockfile_path.exists.return_value = True
            mock_manager.lockfile_path.unlink = Mock()
            mock_manager_class.return_value = mock_manager

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["lock", "clean"])

            assert result.exit_code == 0
            assert "Removed lockfile" in result.output
            mock_manager.lockfile_path.unlink.assert_called_once()

    def test_clean_error(self) -> None:
        """Test error during lockfile removal."""
        with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
            mock_manager.lockfile_path.exists.return_value = True
            mock_manager.lockfile_path.unlink.side_effect = Exception("Permission denied")
            mock_manager_class.return_value = mock_manager

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["lock", "clean"])

            assert result.exit_code == 1
            assert "Failed to remove lockfile" in result.output


class TestLockSyncCommand(FoundationTestCase):
    """Test lock sync command."""

    def test_sync_no_lockfile(self) -> None:
        """Test syncing when no lockfile exists."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                mock_manager.lockfile_path.exists.return_value = False
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "sync"])

                assert result.exit_code == 1
                assert "No lockfile found" in result.output

    def test_sync_outdated_lockfile(self) -> None:
        """Test syncing with outdated lockfile."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                mock_manager.lockfile_path.exists.return_value = True
                mock_manager.is_lockfile_valid.return_value = False
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "sync"])

                assert result.exit_code == 1
                assert "Lockfile is outdated" in result.output

    def test_sync_corrupted_lockfile(self) -> None:
        """Test syncing with corrupted lockfile."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                mock_manager.lockfile_path.exists.return_value = True
                mock_manager.is_lockfile_valid.return_value = True
                mock_manager.load_lockfile.return_value = None
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "sync"])

                assert result.exit_code == 1
                assert "Failed to load lockfile" in result.output

    def test_sync_success(self) -> None:
        """Test successful sync with tools."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                with patch("wrknv.cli.commands.lock.get_tool_manager") as mock_get_manager:
                    mock_config = Mock()
                    mock_load.return_value = mock_config

                    # Create tools
                    tool1 = ResolvedTool(
                        name="go",
                        version="1.22.0",
                        resolved_from="1.22.x",
                    )
                    tool2 = ResolvedTool(
                        name="terraform",
                        version="1.7.0",
                        resolved_from="latest",
                    )

                    mock_lockfile = Mock()
                    mock_lockfile.resolved_tools = {"go": tool1, "terraform": tool2}

                    mock_manager = Mock()
                    mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                    mock_manager.lockfile_path.exists.return_value = True
                    mock_manager.is_lockfile_valid.return_value = True
                    mock_manager.load_lockfile.return_value = mock_lockfile
                    mock_manager_class.return_value = mock_manager

                    # Mock tool managers
                    mock_tool_manager = Mock()
                    mock_tool_manager.install_version = Mock()
                    mock_get_manager.return_value = mock_tool_manager

                    runner = click.testing.CliRunner()
                    cli = get_test_cli()
                    result = runner.invoke(cli, ["lock", "sync"])

                    assert result.exit_code == 0
                    assert "Installing tools from lockfile" in result.output
                    assert "Installing go 1.22.0" in result.output
                    assert "Installing terraform 1.7.0" in result.output
                    assert "Sync completed: 2 tools installed" in result.output

    def test_sync_skip_matrix_entries(self) -> None:
        """Test that sync skips matrix entries (tools with @ in name)."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                with patch("wrknv.cli.commands.lock.get_tool_manager") as mock_get_manager:
                    mock_config = Mock()
                    mock_load.return_value = mock_config

                    # Create tools including matrix entry
                    tool1 = ResolvedTool(
                        name="go",
                        version="1.22.0",
                        resolved_from="1.22.x",
                    )
                    tool2 = ResolvedTool(
                        name="terraform@linux",  # Matrix entry - should be skipped
                        version="1.7.0",
                        resolved_from="latest",
                    )

                    mock_lockfile = Mock()
                    mock_lockfile.resolved_tools = {"go": tool1, "terraform@linux": tool2}

                    mock_manager = Mock()
                    mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                    mock_manager.lockfile_path.exists.return_value = True
                    mock_manager.is_lockfile_valid.return_value = True
                    mock_manager.load_lockfile.return_value = mock_lockfile
                    mock_manager_class.return_value = mock_manager

                    # Mock tool manager - should only be called once for 'go'
                    mock_tool_manager = Mock()
                    mock_tool_manager.install_version = Mock()
                    mock_get_manager.return_value = mock_tool_manager

                    runner = click.testing.CliRunner()
                    cli = get_test_cli()
                    result = runner.invoke(cli, ["lock", "sync"])

                    assert result.exit_code == 0
                    assert "Installing go 1.22.0" in result.output
                    assert "terraform@linux" not in result.output
                    assert "Sync completed: 1 tools installed" in result.output
                    # get_tool_manager should only be called once for 'go'
                    mock_get_manager.assert_called_once_with("go", mock_config)

    def test_sync_partial_failure(self) -> None:
        """Test sync with partial installation failure."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                with patch("wrknv.cli.commands.lock.get_tool_manager") as mock_get_manager:
                    mock_config = Mock()
                    mock_load.return_value = mock_config

                    # Create tools
                    tool1 = ResolvedTool(
                        name="go",
                        version="1.22.0",
                        resolved_from="1.22.x",
                    )
                    tool2 = ResolvedTool(
                        name="terraform",
                        version="1.7.0",
                        resolved_from="latest",
                    )

                    mock_lockfile = Mock()
                    mock_lockfile.resolved_tools = {"go": tool1, "terraform": tool2}

                    mock_manager = Mock()
                    mock_manager.lockfile_path = Path("/tmp/wrknv.lock")
                    mock_manager.lockfile_path.exists.return_value = True
                    mock_manager.is_lockfile_valid.return_value = True
                    mock_manager.load_lockfile.return_value = mock_lockfile
                    mock_manager_class.return_value = mock_manager

                    # Mock tool managers - second one fails
                    def side_effect(tool_name, config):
                        mock_tool_manager = Mock()
                        if tool_name == "go":
                            mock_tool_manager.install_version = Mock()
                        else:
                            mock_tool_manager.install_version.side_effect = Exception("Install failed")
                        return mock_tool_manager

                    mock_get_manager.side_effect = side_effect

                    runner = click.testing.CliRunner()
                    cli = get_test_cli()
                    result = runner.invoke(cli, ["lock", "sync"])

                    assert result.exit_code == 0
                    assert "Installing go 1.22.0" in result.output
                    assert "Successfully installed go 1.22.0" in result.output
                    assert "Error installing terraform 1.7.0" in result.output
                    assert "Sync completed: 1 tools installed" in result.output

    def test_sync_general_error(self) -> None:
        """Test error during sync."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            with patch("wrknv.cli.commands.lock.LockfileManager") as mock_manager_class:
                mock_config = Mock()
                mock_load.return_value = mock_config

                mock_manager = Mock()
                mock_manager.lockfile_path.exists.side_effect = Exception("Filesystem error")
                mock_manager_class.return_value = mock_manager

                runner = click.testing.CliRunner()
                cli = get_test_cli()
                result = runner.invoke(cli, ["lock", "sync"])

                assert result.exit_code == 1
                assert "Failed to sync from lockfile" in result.output
