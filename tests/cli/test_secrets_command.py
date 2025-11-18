#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for CLI secrets command."""

from __future__ import annotations

import click.testing
from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch

from wrknv.cli.hub_cli import create_cli


def get_test_cli():
    """Get or create the test CLI instance."""
    # Always create a fresh CLI to ensure module reloading works with mocks
    return create_cli()


class TestSecretsCommand(FoundationTestCase):
    """Test secrets command for managing secret management tools."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.temp_dir = self.create_temp_dir()
        self.temp_path = self.temp_dir
        self.config_file = self.temp_path / "wrknv.toml"

    def test_list_variants(self) -> None:
        """Test listing available secret management variants."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["secrets", "--list-variants"])

            assert result.exit_code == 0
            assert "bao" in result.output
            assert "vault" in result.output
            assert "OpenBao" in result.output

    def test_no_args_error(self) -> None:
        """Test that calling without args shows error."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_setting.return_value = "bao"
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["secrets"])

            assert result.exit_code == 1
            assert "Version required" in result.output

    def test_list_versions_default_variant(self) -> None:
        """Test listing versions for default variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.secrets.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "bao"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.get_available_versions.return_value = ["2.1.0", "2.0.0", "1.9.0"]
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["secrets", "--list"])

            assert result.exit_code == 0
            assert "OpenBao" in result.output
            assert "2.1.0" in result.output
            assert "Total: 3 versions" in result.output

    def test_list_versions_explicit_variant(self) -> None:
        """Test listing versions for explicit variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.secrets.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            # Mock get_setting to return default variant (used in single-arg mode)
            mock_config.get_setting.return_value = "vault"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.get_available_versions.return_value = ["1.15.0", "1.14.0"]
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["secrets", "vault", "--list"])

            assert result.exit_code == 0
            assert "IBM Vault" in result.output
            assert "1.15.0" in result.output
            mock_get_manager.assert_called_once_with("vault", mock_config)

    def test_list_many_versions(self) -> None:
        """Test listing truncates to 20 versions."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.secrets.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "bao"
            mock_load.return_value = mock_config

            # Create 25 versions
            versions = [f"2.{i}.0" for i in range(25)]
            mock_manager = Mock()
            mock_manager.get_available_versions.return_value = versions
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["secrets", "--list"])

            assert result.exit_code == 0
            assert "and 5 more" in result.output
            assert "Total: 25 versions" in result.output

    def test_switch_version_default_variant(self) -> None:
        """Test switching to a version using default variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.secrets.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "bao"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["secrets", "2.1.0"])

            assert result.exit_code == 0
            assert "Using default variant: bao" in result.output
            assert "Switching to OpenBao 2.1.0" in result.output
            mock_manager.switch_version.assert_called_once_with("2.1.0", dry_run=False)

    def test_switch_version_explicit_variant(self) -> None:
        """Test switching to a version with explicit variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.secrets.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["secrets", "vault", "1.15.0"])

            assert result.exit_code == 0
            assert "Switching to IBM Vault 1.15.0" in result.output
            mock_manager.switch_version.assert_called_once_with("1.15.0", dry_run=False)

    def test_switch_version_dry_run(self) -> None:
        """Test dry-run mode."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.secrets.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "bao"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["secrets", "2.1.0", "--dry-run"])

            assert result.exit_code == 0
            assert "[DRY-RUN] Would switch to OpenBao 2.1.0" in result.output
            mock_manager.switch_version.assert_called_once_with("2.1.0", dry_run=True)

    def test_unknown_variant(self) -> None:
        """Test error for unknown variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["secrets", "unknown", "1.0.0"])

            assert result.exit_code == 1
            assert "Unknown secrets variant: unknown" in result.output
            assert "Available variants: bao, vault" in result.output

    def test_ibm_alias(self) -> None:
        """Test that 'ibm' is an alias for 'vault'."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.secrets.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["secrets", "ibm", "1.15.0"])

            assert result.exit_code == 0
            assert "IBM Vault" in result.output
            mock_get_manager.assert_called_once_with("vault", mock_config)

    def test_switch_version_error(self) -> None:
        """Test error handling during version switch."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.secrets.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "bao"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.side_effect = Exception("Version not found")
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["secrets", "2.1.0"])

            assert result.exit_code == 1
            assert "Error" in result.output

    def test_list_versions_error(self) -> None:
        """Test error handling during version listing."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.secrets.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "bao"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.get_available_versions.side_effect = Exception("Network error")
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["secrets", "--list"])

            assert result.exit_code == 1
            assert "Error listing versions" in result.output


# 🧰🌍🔚
