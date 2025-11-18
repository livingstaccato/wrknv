#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for CLI terraform command."""

from __future__ import annotations

import click.testing
from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch

from wrknv.cli.hub_cli import create_cli


def get_test_cli():
    """Get or create the test CLI instance."""
    # Always create a fresh CLI to ensure module reloading works with mocks
    return create_cli()


class TestTerraformCommand(FoundationTestCase):
    """Test tf command for managing Terraform/OpenTofu."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.temp_dir = self.create_temp_dir()
        self.temp_path = self.temp_dir
        self.config_file = self.temp_path / "wrknv.toml"

    def test_list_variants(self) -> None:
        """Test listing available Terraform variants."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["tf", "--list-variants"])

            assert result.exit_code == 0
            assert "tofu" in result.output
            assert "ibm" in result.output
            assert "OpenTofu" in result.output

    def test_no_args_error(self) -> None:
        """Test that calling without args shows error."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_setting.return_value = "tofu"
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["tf"])

            assert result.exit_code == 1
            assert "Version required" in result.output

    def test_list_versions_default_variant(self) -> None:
        """Test listing versions for default variant (tofu)."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "tofu"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.get_available_versions.return_value = ["1.9.0", "1.8.0", "1.7.0"]
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "--list"])

            assert result.exit_code == 0
            assert "OpenTofu" in result.output
            assert "1.9.0" in result.output
            assert "Total: 3 versions" in result.output

    def test_list_versions_explicit_variant_tofu(self) -> None:
        """Test listing versions for explicit tofu variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            # Mock get_setting to return tofu as default variant (used in single-arg mode)
            mock_config.get_setting.return_value = "tofu"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.get_available_versions.return_value = ["1.9.0", "1.8.0"]
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "tofu", "--list"])

            assert result.exit_code == 0
            assert "OpenTofu" in result.output
            assert "1.9.0" in result.output
            mock_get_manager.assert_called_once_with("tofu", mock_config)

    def test_list_versions_explicit_variant_ibm(self) -> None:
        """Test listing versions for explicit IBM variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            # Mock get_setting to return ibm as default variant (used in single-arg mode)
            mock_config.get_setting.return_value = "ibm"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.get_available_versions.return_value = ["1.6.2", "1.5.0"]
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "ibm", "--list"])

            assert result.exit_code == 0
            assert "IBM Terraform" in result.output
            assert "1.6.2" in result.output
            mock_get_manager.assert_called_once_with("ibmtf", mock_config)

    def test_list_many_versions(self) -> None:
        """Test listing truncates to 20 versions."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "tofu"
            mock_load.return_value = mock_config

            # Create 25 versions
            versions = [f"1.{i}.0" for i in range(25)]
            mock_manager = Mock()
            mock_manager.get_available_versions.return_value = versions
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "--list"])

            assert result.exit_code == 0
            assert "and 5 more" in result.output
            assert "Total: 25 versions" in result.output

    def test_switch_version_default_variant(self) -> None:
        """Test switching to a version using default variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "tofu"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "1.9.0"])

            assert result.exit_code == 0
            assert "Using default variant: tofu" in result.output
            assert "Switching to OpenTofu 1.9.0" in result.output
            mock_manager.switch_version.assert_called_once_with("1.9.0", dry_run=False)

    def test_switch_version_explicit_variant_tofu(self) -> None:
        """Test switching to OpenTofu with explicit variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "tofu", "1.9.0"])

            assert result.exit_code == 0
            assert "Switching to OpenTofu 1.9.0" in result.output
            mock_manager.switch_version.assert_called_once_with("1.9.0", dry_run=False)

    def test_switch_version_explicit_variant_ibm(self) -> None:
        """Test switching to IBM Terraform with explicit variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "ibm", "1.6.2"])

            assert result.exit_code == 0
            assert "Switching to IBM Terraform 1.6.2" in result.output
            mock_manager.switch_version.assert_called_once_with("1.6.2", dry_run=False)

    def test_switch_version_dry_run(self) -> None:
        """Test dry-run mode."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "tofu"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "1.9.0", "--dry-run"])

            assert result.exit_code == 0
            assert "[DRY-RUN] Would switch to OpenTofu 1.9.0" in result.output
            mock_manager.switch_version.assert_called_once_with("1.9.0", dry_run=True)

    def test_unknown_variant(self) -> None:
        """Test error for unknown variant."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["tf", "unknown", "1.0.0"])

            assert result.exit_code == 1
            assert "Unknown Terraform variant: unknown" in result.output
            assert "Available variants: tofu, ibm" in result.output

    def test_opentofu_alias(self) -> None:
        """Test that 'opentofu' is an alias for 'tofu'."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "opentofu", "1.9.0"])

            assert result.exit_code == 0
            assert "OpenTofu" in result.output
            mock_get_manager.assert_called_once_with("tofu", mock_config)

    def test_terraform_alias(self) -> None:
        """Test that 'terraform' is an alias for 'ibmtf'."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "terraform", "1.6.2"])

            assert result.exit_code == 0
            assert "IBM Terraform" in result.output
            mock_get_manager.assert_called_once_with("ibmtf", mock_config)

    def test_switch_version_error(self) -> None:
        """Test error handling during version switch."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "tofu"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.switch_version.side_effect = Exception("Version not found")
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "1.9.0"])

            assert result.exit_code == 1
            assert "Error" in result.output

    def test_list_versions_error(self) -> None:
        """Test error handling during version listing."""
        # Create CLI before patching to ensure module reload happens first
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.terraform.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_setting.return_value = "tofu"
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.get_available_versions.side_effect = Exception("Network error")
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tf", "--list"])

            assert result.exit_code == 1
            assert "Error listing versions" in result.output


# 🧰🌍🔚
