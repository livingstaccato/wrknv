#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for CLI config commands."""

from __future__ import annotations

import os

import click.testing
from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.cli.hub_cli import create_cli

# Create CLI once at module level and reuse across all tests
_test_cli = None


def get_test_cli():
    """Get or create the test CLI instance."""
    global _test_cli
    if _test_cli is None:
        _test_cli = create_cli()
    return _test_cli


@pytest.mark.cli
@pytest.mark.config
class TestConfigCommands(FoundationTestCase):
    """Test config show and edit CLI commands."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.temp_dir = self.create_temp_dir()
        self.temp_path = self.temp_dir
        self.config_file = self.temp_path / "wrknv.toml"

    def test_config_show_no_config(self) -> None:
        """Test showing config when no config file exists."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.show_config.return_value = None
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 0
            mock_config.show_config.assert_called_once()

    def test_config_show_with_config(self) -> None:
        """Test showing existing configuration."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.show_config.return_value = None
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 0
            mock_config.show_config.assert_called_once()

    def test_config_show_json_format(self) -> None:
        """Test showing config in JSON format."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.to_dict.return_value = {
                "project_name": "test-project",
                "tools": {"terraform": {"version": "1.5.0", "enabled": True}},
            }
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "show", "--output-json"])

            assert result.exit_code == 0
            # Output should be valid JSON
            import json

            output_data = json.loads(result.output)
            assert output_data["project_name"] == "test-project"

    def test_config_show_with_profile_filter(self) -> None:
        """Test showing only specific profile configuration."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_profile.return_value = {"terraform": "1.5.0", "go": "1.21.0"}
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "show", "--profile", "dev"])

            assert result.exit_code == 0
            assert "Profile: dev" in result.output
            assert "terraform: 1.5.0" in result.output

    def test_config_edit_with_editor(self) -> None:
        """Test editing config file with default editor."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        self.config_file.write_text('project_name = "test-project"')

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_config_path.return_value = self.config_file
            mock_config.edit_config.return_value = None
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "edit"])

            assert result.exit_code == 0
            mock_config.edit_config.assert_called_once()

    def test_config_edit_no_editor_set(self) -> None:
        """Test editing config when no EDITOR is set."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        self.config_file.write_text('project_name = "test-project"')

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch.dict(os.environ, {}, clear=True),
        ):
            # Remove EDITOR from environment
            if "EDITOR" in os.environ:
                del os.environ["EDITOR"]

            mock_config = Mock()
            mock_config.get_config_path.return_value = self.config_file
            mock_config.edit_config.side_effect = RuntimeError(
                "No editor configured. Set EDITOR or VISUAL environment variable."
            )
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "edit"])

            # The command catches the exception and shows error message
            assert "No editor configured" in result.output

    def test_config_edit_creates_file_if_missing(self) -> None:
        """Test that edit creates a config file if it doesn't exist."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load,
            patch("provide.foundation.process.run") as mock_run,
            patch.dict(os.environ, {"EDITOR": "nano"}),
        ):
            mock_config = Mock()
            mock_config.get_config_path.return_value = self.config_file
            mock_config.config_exists.return_value = False
            mock_config.edit_config.return_value = None
            mock_load.return_value = mock_config
            mock_run.return_value = Mock(returncode=0)

            result = runner.invoke(cli, ["config", "edit"])

            assert result.exit_code == 0
            mock_config.edit_config.assert_called_once()

    def test_config_validate(self) -> None:
        """Test validating configuration file."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        self.config_file.write_text("""
project_name = "test-project"
version = "1.0.0"

[tools]
terraform = { version = "1.5.0" }
""")

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.config_exists.return_value = True
            mock_config.get_config_path.return_value = self.config_file
            mock_config.validate.return_value = (True, [])
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "validate"])

            assert result.exit_code == 0
            assert "Configuration is valid" in result.output

    def test_config_validate_with_errors(self) -> None:
        """Test validating invalid configuration."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        self.config_file.write_text("""
# Missing project_name
version = "1.0.0"
""")

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.config_exists.return_value = True
            mock_config.get_config_path.return_value = self.config_file
            mock_config.validate.return_value = (
                False,
                ["Missing required field: project_name", "Invalid version format"],
            )
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "validate", "--strict"])

            assert result.exit_code == 1
            assert "Configuration validation failed" in result.output
            assert "Missing required field: project_name" in result.output

    def test_config_init(self) -> None:
        """Test initializing a new configuration file."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.config_path = self.config_file
            mock_config.get_config_path.return_value = self.config_file
            mock_config.config_exists.return_value = False
            mock_config.write_config.return_value = None
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "init"], input="my-project\n1.0.0\n")

            assert result.exit_code == 0
            assert "Configuration created" in result.output

    def test_config_init_already_exists(self) -> None:
        """Test initializing when config already exists."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        self.config_file.write_text('project_name = "existing"')

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_config_path.return_value = self.config_file
            mock_config.config_exists.return_value = True
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "init"])

            assert result.exit_code == 1
            assert "Configuration file already exists" in result.output

    def test_config_get_setting(self) -> None:
        """Test getting a specific configuration setting."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.get_setting.return_value = "INFO"
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "get", "log_level"])

            assert result.exit_code == 0
            assert "log_level: INFO" in result.output

    def test_config_set_setting(self) -> None:
        """Test setting a configuration value."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.set_setting.return_value = True
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "set", "log_level", "DEBUG"])

            assert result.exit_code == 0
            assert "Set log_level" in result.output
            mock_config.set_setting.assert_called_once_with("log_level", "DEBUG")

    def test_config_path(self) -> None:
        """Test showing configuration file path."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        with patch("wrknv.cli.hub_cli.WrknvContext.get_config") as mock_load:
            mock_config = Mock()
            mock_config.config_exists.return_value = True
            mock_config.config_path = self.config_file
            mock_config.get_config_path.return_value = self.config_file
            mock_load.return_value = mock_config

            result = runner.invoke(cli, ["config", "path"])

            assert result.exit_code == 0
            assert str(self.config_file) in result.output


class TestConfigCommandIntegration(FoundationTestCase):
    """Integration tests for config commands."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.temp_dir = self.create_temp_dir()
        self.temp_path = self.temp_dir

    def test_config_init_and_validate_integration(self) -> None:
        """Test creating and validating a config file."""
        runner = click.testing.CliRunner()
        cli = get_test_cli()

        config_file = self.temp_path / ".wrknv.toml"

        with patch("wrknv.config.core.Path.cwd") as mock_cwd:
            mock_cwd.return_value = self.temp_path

            # Initialize config (provide both project name and version inputs)
            result = runner.invoke(cli, ["config", "init"], input="test-project\n\n")
            assert result.exit_code == 0

            # Verify file was created
            assert config_file.exists()

            # Validate the config
            result = runner.invoke(cli, ["config", "validate"])
            assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# 🧰🌍🔚
