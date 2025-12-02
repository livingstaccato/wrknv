#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for CLI tools commands."""

from __future__ import annotations

from pathlib import Path

import click.testing
from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch

from wrknv.cli.hub_cli import create_cli


def get_test_cli():
    """Get or create the test CLI instance."""
    # Always create a fresh CLI to ensure module reloading works with mocks
    return create_cli()


class TestStatusCommand(FoundationTestCase):
    """Test status command for showing tool status."""

    def test_status_no_tools_configured(self) -> None:
        """Test status when no tools are configured."""
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {}
            mock_get_config.return_value = mock_config

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "No tools configured" in result.output

    def test_status_with_simple_tools(self) -> None:
        """Test status with simple tool versions."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "uv": "0.5.0",
                "go": "1.22.0",
            }
            mock_get_config.return_value = mock_config

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            mock_resolve.return_value = ["0.5.0"]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Tool Status" in result.output
            assert "uv" in result.output
            assert "go" in result.output
            assert "Configured" in result.output

    def test_status_with_list_versions(self) -> None:
        """Test status with list (matrix) of versions."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "go": ["1.22.0", "1.21.0"],
            }
            mock_get_config.return_value = mock_config

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            mock_resolve.return_value = ["1.22.0", "1.21.0"]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "go" in result.output
            assert "1.22.0" in result.output

    def test_status_with_version_pattern_resolution(self) -> None:
        """Test status with version pattern that resolves."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "go": "1.22.*",
            }
            mock_get_config.return_value = mock_config

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            # Pattern resolves to specific version
            mock_resolve.return_value = ["1.22.5"]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "go" in result.output
            # Should show pattern → resolved
            assert "1.22.*" in result.output or "1.22.5" in result.output

    def test_status_handles_resolution_errors(self) -> None:
        """Test status gracefully handles resolution errors."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "uv": "0.5.0",
            }
            mock_get_config.return_value = mock_config

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            # Resolution fails
            mock_resolve.side_effect = Exception("Network error")

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["status"])

            # Should still succeed, just show version without resolution
            assert result.exit_code == 0
            assert "uv" in result.output
            assert "0.5.0" in result.output


class TestSyncCommand(FoundationTestCase):
    """Test sync command for installing tools."""

    def test_sync_no_tools_configured(self) -> None:
        """Test sync when no tools are configured."""
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {}
            mock_get_config.return_value = mock_config

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["sync"])

            assert result.exit_code == 0
            assert "No tools configured" in result.output

    def test_sync_with_lock(self) -> None:
        """Test sync with lockfile creation."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.LockfileManager") as mock_lockfile_cls,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "uv": "0.5.0",
            }
            mock_get_config.return_value = mock_config

            mock_lockfile = Mock()
            mock_lockfile_cls.return_value = mock_lockfile

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            mock_resolve.return_value = ["0.5.0"]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["sync"])

            assert result.exit_code == 0
            # Should call resolve_and_lock
            mock_lockfile.resolve_and_lock.assert_called_once_with(mock_config)
            # Should install version
            mock_manager.install_version.assert_called_with("0.5.0", dry_run=False)

    def test_sync_basic(self) -> None:
        """Test basic sync functionality."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.LockfileManager") as mock_lockfile_cls,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "uv": "0.5.0",
            }
            mock_get_config.return_value = mock_config

            mock_lockfile = Mock()
            mock_lockfile_cls.return_value = mock_lockfile

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            mock_resolve.return_value = ["0.5.0"]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["sync"])

            assert result.exit_code == 0
            # Should install the tool
            mock_manager.install_version.assert_called_with("0.5.0", dry_run=False)

    def test_sync_with_list_versions(self) -> None:
        """Test sync with list (matrix) of versions."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.LockfileManager") as mock_lockfile_cls,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "go": ["1.22.0", "1.21.0"],
            }
            mock_get_config.return_value = mock_config

            mock_lockfile = Mock()
            mock_lockfile_cls.return_value = mock_lockfile

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            mock_resolve.return_value = ["1.22.0", "1.21.0"]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["sync"])

            assert result.exit_code == 0
            # Should install both versions
            assert mock_manager.install_version.call_count == 2

    def test_sync_with_version_pattern(self) -> None:
        """Test sync with version pattern that resolves."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.LockfileManager") as mock_lockfile_cls,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "go": "1.22.*",
            }
            mock_get_config.return_value = mock_config

            mock_lockfile = Mock()
            mock_lockfile_cls.return_value = mock_lockfile

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            # Pattern resolves to specific version
            mock_resolve.return_value = ["1.22.5"]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["sync"])

            assert result.exit_code == 0
            # Should show resolution message
            assert "Resolved" in result.output or "Installing" in result.output
            mock_manager.install_version.assert_called_with("1.22.5", dry_run=False)

    def test_sync_unresolved_version_pattern(self) -> None:
        """Test sync when version pattern cannot be resolved."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.LockfileManager") as mock_lockfile_cls,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "go": "99.99.*",
            }
            mock_get_config.return_value = mock_config

            mock_lockfile = Mock()
            mock_lockfile_cls.return_value = mock_lockfile

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            # Cannot resolve pattern
            mock_resolve.return_value = []

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["sync"])

            # Should show error but not crash
            assert "Could not resolve" in result.output or "Error" in result.output
            # Should NOT install
            mock_manager.install_version.assert_not_called()

    def test_sync_handles_installation_errors(self) -> None:
        """Test sync gracefully handles installation errors."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.LockfileManager") as mock_lockfile_cls,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "uv": "0.5.0",
            }
            mock_get_config.return_value = mock_config

            mock_lockfile = Mock()
            mock_lockfile_cls.return_value = mock_lockfile

            mock_manager = Mock()
            mock_manager.install_version.side_effect = Exception("Download failed")
            mock_get_manager.return_value = mock_manager
            mock_resolve.return_value = ["0.5.0"]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["sync"])

            # Should show error message
            assert "Error installing" in result.output or "Download failed" in result.output


class TestGenerateEnvCommand(FoundationTestCase):
    """Test generate-env command."""

    def test_generate_env_default_shell(self, tmp_path: Path) -> None:
        """Test generating env script with default shell."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.create_project_env_scripts") as mock_create,
            patch("wrknv.cli.commands.tools.safe_move"),
        ):
            mock_config = Mock()
            mock_get_config.return_value = mock_config

            sh_path = tmp_path / "env.sh"
            ps1_path = tmp_path / "env.ps1"

            mock_create.return_value = (sh_path, ps1_path)

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["generate-env"])

            assert result.exit_code == 0
            assert "To use the environment" in result.output
            mock_create.assert_called_once()

    def test_generate_env_powershell(self, tmp_path: Path) -> None:
        """Test generating env script for PowerShell."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.create_project_env_scripts") as mock_create,
            patch("wrknv.cli.commands.tools.safe_move") as mock_move,
        ):
            mock_config = Mock()
            mock_get_config.return_value = mock_config

            sh_path = tmp_path / "env.sh"
            ps1_path = tmp_path / "env.ps1"
            output_path = tmp_path / "custom.ps1"
            sh_path.touch()
            ps1_path.touch()

            mock_create.return_value = (sh_path, ps1_path)

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["generate-env", "--shell", "powershell", str(output_path)])

            assert result.exit_code == 0
            # Should move ps1 file to custom location
            mock_move.assert_called_once()

    def test_generate_env_custom_output(self, tmp_path: Path) -> None:
        """Test generating env script to custom output path."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.create_project_env_scripts") as mock_create,
            patch("wrknv.cli.commands.tools.safe_move") as mock_move,
        ):
            mock_config = Mock()
            mock_get_config.return_value = mock_config

            sh_path = tmp_path / "env.sh"
            ps1_path = tmp_path / "env.ps1"
            output_path = tmp_path / "custom-env.sh"
            sh_path.touch()
            ps1_path.touch()

            mock_create.return_value = (sh_path, ps1_path)

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["generate-env", str(output_path)])

            assert result.exit_code == 0
            # Should move sh file to custom location
            mock_move.assert_called_once()

    def test_generate_env_file_not_found(self) -> None:
        """Test generate-env handles missing project file."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.create_project_env_scripts") as mock_create,
        ):
            mock_config = Mock()
            mock_get_config.return_value = mock_config

            # Simulate missing pyproject.toml
            mock_create.side_effect = FileNotFoundError("pyproject.toml not found")

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["generate-env"])

            assert "Error" in result.output
            assert "pyproject.toml" in result.output


class TestDoctorCommand(FoundationTestCase):
    """Test doctor command for diagnostics."""

    def test_doctor_success(self) -> None:
        """Test doctor command when all checks pass."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.run_doctor") as mock_run_doctor,
        ):
            mock_config = Mock()
            mock_get_config.return_value = mock_config

            # Doctor returns 0 for success
            mock_run_doctor.return_value = 0

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["doctor"])

            assert result.exit_code == 0
            mock_run_doctor.assert_called_once_with(False)

    def test_doctor_with_verbose(self) -> None:
        """Test doctor command with verbose flag."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.run_doctor") as mock_run_doctor,
        ):
            mock_config = Mock()
            mock_get_config.return_value = mock_config

            mock_run_doctor.return_value = 0

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["doctor", "--verbose"])

            assert result.exit_code == 0
            # Should pass verbose=True
            mock_run_doctor.assert_called_once_with(True)

    def test_doctor_with_issues(self) -> None:
        """Test doctor command when issues are found."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.run_doctor") as mock_run_doctor,
        ):
            mock_config = Mock()
            mock_get_config.return_value = mock_config

            # Doctor returns 1 for issues found
            mock_run_doctor.return_value = 1

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["doctor"])

            assert result.exit_code == 1
            mock_run_doctor.assert_called_once()


class TestToolsCommandIntegration(FoundationTestCase):
    """Integration tests for tools commands."""

    def test_status_then_sync_workflow(self) -> None:
        """Test workflow of checking status then syncing tools."""
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_get_config,
            patch("wrknv.cli.commands.tools.get_tool_manager") as mock_get_manager,
            patch("wrknv.cli.commands.tools.resolve_tool_versions") as mock_resolve,
            patch("wrknv.cli.commands.tools.LockfileManager") as mock_lockfile_cls,
        ):
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {
                "uv": "0.5.0",
            }
            mock_get_config.return_value = mock_config

            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            mock_resolve.return_value = ["0.5.0"]

            mock_lockfile = Mock()
            mock_lockfile_cls.return_value = mock_lockfile

            runner = click.testing.CliRunner()

            # First check status
            result1 = runner.invoke(cli, ["status"])
            assert result1.exit_code == 0
            assert "uv" in result1.output

            # Then sync
            result2 = runner.invoke(cli, ["sync"])
            assert result2.exit_code == 0
            mock_manager.install_version.assert_called_with("0.5.0", dry_run=False)


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
