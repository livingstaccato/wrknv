#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test the new foundation-based config system
===========================================
Tests for the WorkenvConfig implementation using provide.foundation."""

from __future__ import annotations

import pathlib
import tempfile

from provide.testkit.mocking import patch

from wrknv.config import WorkenvConfig


class TestWorkenvConfig:
    """Test the new WorkenvConfig implementation."""

    def test_load_with_defaults(self) -> None:
        """Should load with sensible defaults."""
        # Isolate test by mocking config file discovery to return non-existent file
        with patch.object(
            WorkenvConfig, "_find_config_file", return_value=pathlib.Path("/nonexistent/.wrknv.toml")
        ):
            config = WorkenvConfig.load()

            assert config.project_name == "my-project"
            assert config.version == "1.0.0"
            assert config.workenv.log_level == "WARNING"
            assert config.workenv.auto_install is True

    def test_load_from_file(self) -> None:
        """Should load configuration from TOML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = pathlib.Path(tmpdir) / ".wrknv.toml"
            config_file.write_text("""
project_name = "test-project"
version = "2.0.0"

[tools]
terraform = "1.5.7"
go = "1.21.0"

[workenv]
log_level = "DEBUG"
auto_install = false
""")

            with patch("wrknv.config.core.Path.cwd", return_value=pathlib.Path(tmpdir)):
                config = WorkenvConfig.load()

                assert config.project_name == "test-project"
                assert config.version == "2.0.0"
                assert config.get_tool_version("terraform") == "1.5.7"
                assert config.get_tool_version("go") == "1.21.0"
                assert config.workenv.log_level == "DEBUG"
                assert config.workenv.auto_install is False

    def test_environment_variables(self) -> None:
        """Should support WRKNV_ environment variables."""
        with patch.dict(
            "os.environ",
            {
                "WRKNV_PROJECT_NAME": "env-project",
                "WRKNV_VERSION": "3.0.0",
                "WRKNV_LOG_LEVEL": "INFO",
                "WRKNV_AUTO_INSTALL": "false",
            },
        ):
            config = WorkenvConfig.load()

            # Environment variables should override defaults
            assert config.project_name == "env-project"
            assert config.version == "3.0.0"
            assert config.workenv.log_level == "INFO"
            assert config.workenv.auto_install is False

    def test_tool_management(self) -> None:
        """Should manage tool versions correctly."""
        # Isolate test by mocking config file discovery
        with patch.object(
            WorkenvConfig, "_find_config_file", return_value=pathlib.Path("/nonexistent/.wrknv.toml")
        ):
            config = WorkenvConfig.load()

            # Initially no tools
            assert config.get_all_tools() == {}
            assert config.get_tool_version("terraform") is None

            # Add some tools
            config.tools = {
                "terraform": "1.5.7",
                "go": {"version": "1.21.0", "path": "/usr/local/go"},
            }

            # Should retrieve tool versions
            assert config.get_tool_version("terraform") == "1.5.7"
            assert config.get_tool_version("go") == "1.21.0"

            all_tools = config.get_all_tools()
            assert all_tools["terraform"] == "1.5.7"
            assert all_tools["go"] == "1.21.0"

    def test_profile_management(self) -> None:
        """Should manage profiles correctly."""
        # Isolate test by mocking config file discovery
        with patch.object(
            WorkenvConfig, "_find_config_file", return_value=pathlib.Path("/nonexistent/.wrknv.toml")
        ):
            config = WorkenvConfig.load()

            # Initially no profiles
            assert config.list_profiles() == []
            assert config.get_profile("dev") is None

            # Add profiles
            config.profiles = {
                "dev": {"terraform": "1.6.0", "go": "1.21.0"},
                "prod": {"terraform": "1.5.7", "go": "1.20.0"},
            }

            # Should list profiles
            profiles = config.list_profiles()
            assert "dev" in profiles
            assert "prod" in profiles

            # Should get profile data
            dev_profile = config.get_profile("dev")
            assert dev_profile["terraform"] == "1.6.0"
            assert dev_profile["go"] == "1.21.0"


class TestWorkenvConfigMethods:
    """Test WorkenvConfig utility methods."""

    def test_get_setting(self) -> None:
        """Should retrieve settings with dot notation."""
        # Isolate test by mocking config file discovery
        with patch.object(
            WorkenvConfig, "_find_config_file", return_value=pathlib.Path("/nonexistent/.wrknv.toml")
        ):
            config = WorkenvConfig.load()

            # Should get direct attributes
            assert config.get_setting("project_name") == "my-project"

            # Should get nested attributes
            assert config.get_setting("workenv.log_level") == "WARNING"
            assert config.get_setting("workenv.auto_install") is True

            # Should return default for missing
            assert config.get_setting("missing", "default") == "default"

    def test_validation(self) -> None:
        """Should validate configuration correctly."""
        # Isolate test by mocking config file discovery
        with patch.object(
            WorkenvConfig, "_find_config_file", return_value=pathlib.Path("/nonexistent/.wrknv.toml")
        ):
            config = WorkenvConfig.load()

            # Default config should be valid
            is_valid, errors = config.validate()
            assert is_valid
            assert errors == []

            # Invalid tool version should fail
            config.tools = {"terraform": {"version": "invalid.version"}}
            is_valid, errors = config.validate()
            assert not is_valid
            assert any("Invalid version" in error for error in errors)

    def test_to_dict(self) -> None:
        """Should convert to dictionary correctly."""
        config = WorkenvConfig.load()
        config.project_name = "test"
        config.tools = {"terraform": "1.5.7"}

        data = config.to_dict()

        assert data["project_name"] == "test"
        assert data["tools"]["terraform"] == "1.5.7"
        assert data["workenv"]["log_level"] == "WARNING"


# 🧰🌍🔚
