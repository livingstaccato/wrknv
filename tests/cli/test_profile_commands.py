#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for CLI profile commands."""

from __future__ import annotations

import click.testing
from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch
import pytest
import tomli_w

from wrknv.cli.hub_cli import create_cli

# Module-level shared CLI instance
_test_cli = None


def get_test_cli():
    """Get or create the test CLI instance."""
    global _test_cli
    if _test_cli is None:
        _test_cli = create_cli()
    return _test_cli


class TestProfileCommands(FoundationTestCase):
    """Test profile save and load CLI commands."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.temp_dir = self.create_temp_dir()
        self.temp_path = self.temp_dir
        self.config_file = self.temp_path / "wrknv.toml"

    def test_profile_list_empty(self) -> None:
        """Test listing profiles when none exist."""
        # Create empty config file
        self.config_file.write_text("""
project_name = "test-project"
""")

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.list_profiles.return_value = []
            mock_config.get_current_profile.return_value = "default"
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["profile", "list"])

            assert result.exit_code == 0
            assert "No profiles found" in result.output

    def test_profile_list_with_profiles(self) -> None:
        """Test listing profiles when they exist."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.list_profiles.return_value = ["dev", "prod", "staging"]
            mock_config.get_current_profile.return_value = "default"
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["profile", "list"])

            assert result.exit_code == 0
            assert "dev" in result.output
            assert "prod" in result.output
            assert "staging" in result.output

    def test_profile_save_current_tools(self) -> None:
        """Test saving current tool versions as a profile."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {"terraform": "1.5.0", "go": "1.21.0", "uv": "0.4.0"}
            mock_config.save_profile.return_value = None
            mock_config.profile_exists.return_value = False
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["profile", "save", "dev"])

            assert result.exit_code == 0
            assert "Saved profile 'dev'" in result.output
            mock_config.save_profile.assert_called_once_with(
                "dev", {"terraform": "1.5.0", "go": "1.21.0", "uv": "0.4.0"}
            )

    def test_profile_save_overwrites_existing(self) -> None:
        """Test that saving a profile overwrites an existing one."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_all_tools.return_value = {"terraform": "1.6.0"}
            mock_config.profile_exists.return_value = True
            mock_config.save_profile.return_value = None
            mock_load.return_value = mock_config

            # Should prompt for confirmation
            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["profile", "save", "dev", "--force"], input="y\n")

            assert result.exit_code == 0
            mock_config.save_profile.assert_called_once()

    def test_profile_load_not_found(self) -> None:
        """Test loading a profile that doesn't exist."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_profile.return_value = None
            mock_config.list_profiles.return_value = []
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["profile", "load", "nonexistent"])

            assert result.exit_code == 1
            assert "Profile 'nonexistent' not found" in result.output

    def test_profile_load_success(self) -> None:
        """Test successfully loading a profile."""
        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.profile.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_profile.return_value = {"terraform": "1.5.0", "go": "1.21.0"}
            mock_load.return_value = mock_config

            mock_manager = Mock()
            mock_manager.install_version.return_value = None
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["profile", "load", "dev"])

            assert result.exit_code == 0
            assert "Loading profile 'dev'" in result.output
            assert "Successfully installed terraform 1.5.0" in result.output
            assert "Successfully installed go 1.21.0" in result.output

            # Verify install was called for each tool
            assert mock_manager.install_version.call_count == 2

    def test_profile_load_partial_failure(self) -> None:
        """Test loading a profile when some tools fail to install."""
        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("wrknv.cli.commands.profile.get_tool_manager") as mock_get_manager,
        ):
            mock_config = Mock()
            mock_config.get_profile.return_value = {"terraform": "1.5.0", "go": "1.21.0"}
            mock_load.return_value = mock_config

            # First tool succeeds, second fails
            mock_manager = Mock()
            mock_manager.install_version.side_effect = [
                None,  # terraform succeeds
                Exception("Failed to download Go"),  # go fails
            ]
            mock_get_manager.return_value = mock_manager

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["profile", "load", "dev"])

            # Should not exit with error, but show error message
            assert result.exit_code == 0
            assert "Successfully installed terraform 1.5.0" in result.output
            assert "Error installing go 1.21.0" in result.output

    def test_profile_delete(self) -> None:
        """Test deleting a profile."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.profile_exists.return_value = True
            mock_config.delete_profile.return_value = True
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(
                cli,
                ["profile", "delete", "dev"],
                input="y\n",  # Confirm deletion
            )

            assert result.exit_code == 0
            assert "Profile 'dev' deleted" in result.output
            mock_config.delete_profile.assert_called_once_with("dev")

    def test_profile_show(self) -> None:
        """Test showing details of a profile."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_profile.return_value = {"terraform": "1.5.0", "go": "1.21.0", "uv": "0.4.0"}
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["profile", "show", "dev"])

            assert result.exit_code == 0
            assert "Profile: dev" in result.output
            assert "terraform: 1.5.0" in result.output
            assert "go: 1.21.0" in result.output
            assert "uv: 0.4.0" in result.output

    def test_profile_export(self) -> None:
        """Test exporting a profile to a file."""
        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_profile.return_value = {"terraform": "1.5.0", "go": "1.21.0"}
            mock_load.return_value = mock_config

            output_file = self.temp_path / "profile.toml"

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            # Use positional arguments, not options
            result = runner.invoke(cli, ["profile", "export", "dev", str(output_file)])

            assert result.exit_code == 0
            assert f"Exported profile 'dev' to {output_file}" in result.output

            # Verify file was created with correct content
            assert output_file.exists()
            content = output_file.read_text()
            assert "terraform" in content
            assert "1.5.0" in content

    def test_profile_import(self) -> None:
        """Test importing a profile from a file."""
        # Create a profile file
        profile_file = self.temp_path / "profile.toml"
        profile_data = {"name": "imported", "tools": {"terraform": "1.6.0", "go": "1.22.0"}}
        profile_file.write_text(tomli_w.dumps(profile_data))

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.save_profile.return_value = None
            mock_load.return_value = mock_config

            runner = click.testing.CliRunner()
            cli = get_test_cli()
            # Command expects positional argument, not option
            result = runner.invoke(cli, ["profile", "import", str(profile_file)])

            assert result.exit_code == 0
            assert "Imported profile 'imported'" in result.output
            mock_config.save_profile.assert_called_once_with(
                "imported", {"terraform": "1.6.0", "go": "1.22.0"}
            )


class TestProfileCommandIntegration(FoundationTestCase):
    """Integration tests for profile commands with real config files."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.temp_dir = self.create_temp_dir()
        self.temp_path = self.temp_dir

    def test_profile_save_and_load_integration(self) -> None:
        """Test full save and load cycle with real config file."""
        config_file = self.temp_path / "wrknv.toml"
        config_file.write_text("""
project_name = "test-project"

[tools]
terraform = { version = "1.5.0" }
go = { version = "1.21.0" }
""")

        # Mock the config file location using pathlib.Path.cwd
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = self.temp_path

            # Save profile
            runner = click.testing.CliRunner()
            cli = get_test_cli()
            result = runner.invoke(cli, ["profile", "save", "test-profile"])
            assert result.exit_code == 0

            # Verify profile was saved to file
            config_content = config_file.read_text()
            assert "profiles" in config_content
            assert "test-profile" in config_content

            # Load profile
            with patch("wrknv.cli.commands.profile.get_tool_manager") as mock_get_manager:
                mock_manager = Mock()
                mock_manager.install_version.return_value = None
                mock_get_manager.return_value = mock_manager

                result = runner.invoke(cli, ["profile", "load", "test-profile"])
                assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# 🧰🌍🔚
