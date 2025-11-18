#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test config/defaults.py module"""

from __future__ import annotations

from pathlib import Path

from wrknv.config.defaults import (
    DEFAULT_ACTIVATE,
    DEFAULT_AUTO_DISCOVER,
    DEFAULT_CLI_HELP,
    DEFAULT_CLI_NAME,
    DEFAULT_CLI_VERSION,
    DEFAULT_CONTAINER_PLATFORM,
    DEFAULT_CONTAINER_RUNTIME,
    DEFAULT_DRY_RUN,
    DEFAULT_FORCE,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PACKAGE_FORMAT,
    DEFAULT_PYTHON_VERSION,
    DEFAULT_REGISTRY_URL,
    DEFAULT_SEARCH_LIMIT,
    DEFAULT_SHORT_TIMEOUT,
    DEFAULT_SYNC_STRATEGY,
    DEFAULT_TEMPLATE_BRANCH,
    DEFAULT_TEMPLATE_VERSION,
    DEFAULT_TIMEOUT,
    DEFAULT_TOOL_TIMEOUT,
    DEFAULT_VERIFY,
    DEFAULT_VERSION,
    DEFAULT_WORKSPACE_VERSION,
    default_config_dir,
    default_custom_values,
    default_empty_dict,
    default_empty_list,
    default_workenv_cache_dir,
    default_workenv_dir,
)


class TestDefaults:
    """Test default values are correct types and reasonable."""

    def test_boolean_defaults(self) -> None:
        """Test boolean defaults are booleans."""
        assert isinstance(DEFAULT_DRY_RUN, bool)
        assert isinstance(DEFAULT_FORCE, bool)
        assert isinstance(DEFAULT_VERIFY, bool)
        assert isinstance(DEFAULT_ACTIVATE, bool)
        assert isinstance(DEFAULT_AUTO_DISCOVER, bool)

        assert DEFAULT_DRY_RUN is False
        assert DEFAULT_FORCE is False
        assert DEFAULT_VERIFY is True
        assert DEFAULT_ACTIVATE is True
        assert DEFAULT_AUTO_DISCOVER is True

    def test_timeout_defaults(self) -> None:
        """Test timeout defaults are positive integers."""
        assert isinstance(DEFAULT_TIMEOUT, int)
        assert isinstance(DEFAULT_SHORT_TIMEOUT, int)
        assert isinstance(DEFAULT_TOOL_TIMEOUT, int)

        assert DEFAULT_TIMEOUT > 0
        assert DEFAULT_SHORT_TIMEOUT > 0
        assert DEFAULT_TOOL_TIMEOUT > 0

    def test_string_defaults(self) -> None:
        """Test string defaults are strings and not empty."""
        assert isinstance(DEFAULT_VERSION, str)
        assert isinstance(DEFAULT_WORKSPACE_VERSION, str)
        assert isinstance(DEFAULT_SYNC_STRATEGY, str)
        assert isinstance(DEFAULT_CONTAINER_RUNTIME, str)
        assert isinstance(DEFAULT_CONTAINER_PLATFORM, str)
        assert isinstance(DEFAULT_PACKAGE_FORMAT, str)
        assert isinstance(DEFAULT_PYTHON_VERSION, str)
        assert isinstance(DEFAULT_LOG_LEVEL, str)
        assert isinstance(DEFAULT_CLI_NAME, str)
        assert isinstance(DEFAULT_CLI_VERSION, str)
        assert isinstance(DEFAULT_CLI_HELP, str)

        assert DEFAULT_VERSION
        assert DEFAULT_WORKSPACE_VERSION
        assert DEFAULT_SYNC_STRATEGY
        assert DEFAULT_CONTAINER_RUNTIME
        assert DEFAULT_CONTAINER_PLATFORM
        assert DEFAULT_PACKAGE_FORMAT
        assert DEFAULT_PYTHON_VERSION
        assert DEFAULT_LOG_LEVEL
        assert DEFAULT_CLI_NAME
        assert DEFAULT_CLI_VERSION
        assert DEFAULT_CLI_HELP

    def test_none_defaults(self) -> None:
        """Test None defaults are None."""
        assert DEFAULT_REGISTRY_URL is None
        assert DEFAULT_TEMPLATE_VERSION is None
        assert DEFAULT_TEMPLATE_BRANCH is None

    def test_numeric_defaults(self) -> None:
        """Test numeric defaults are correct types."""
        assert isinstance(DEFAULT_SEARCH_LIMIT, int)
        assert DEFAULT_SEARCH_LIMIT > 0


class TestFactoryFunctions:
    """Test factory functions for mutable defaults."""

    def test_default_workenv_cache_dir(self) -> None:
        """Test workenv cache directory factory."""
        result = default_workenv_cache_dir()
        assert isinstance(result, Path)
        assert ".wrknv" in str(result)
        assert "cache" in str(result)
        assert "packages" in str(result)

    def test_default_config_dir(self) -> None:
        """Test config directory factory."""
        result = default_config_dir()
        assert isinstance(result, Path)
        assert ".wrknv" in str(result)

    def test_default_workenv_dir(self) -> None:
        """Test workenv directory factory."""
        result = default_workenv_dir()
        assert isinstance(result, Path)
        assert str(result) == "workenv"

    def test_default_empty_list(self) -> None:
        """Test empty list factory returns new instance each time."""
        list1 = default_empty_list()
        list2 = default_empty_list()

        assert isinstance(list1, list)
        assert isinstance(list2, list)
        assert list1 == []
        assert list2 == []
        assert list1 is not list2  # Different instances

    def test_default_empty_dict(self) -> None:
        """Test empty dict factory returns new instance each time."""
        dict1 = default_empty_dict()
        dict2 = default_empty_dict()

        assert isinstance(dict1, dict)
        assert isinstance(dict2, dict)
        assert dict1 == {}
        assert dict2 == {}
        assert dict1 is not dict2  # Different instances

    def test_default_custom_values(self) -> None:
        """Test custom values factory returns new instance each time."""
        values1 = default_custom_values()
        values2 = default_custom_values()

        assert isinstance(values1, dict)
        assert isinstance(values2, dict)
        assert values1 == {}
        assert values2 == {}
        assert values1 is not values2  # Different instances


class TestValueConstraints:
    """Test that default values meet expected constraints."""

    def test_sync_strategy_valid(self) -> None:
        """Test sync strategy is a valid option."""
        valid_strategies = {"manual", "auto", "check"}
        assert DEFAULT_SYNC_STRATEGY in valid_strategies

    def test_container_runtime_valid(self) -> None:
        """Test container runtime is a known value."""
        valid_runtimes = {"docker", "podman"}
        assert DEFAULT_CONTAINER_RUNTIME in valid_runtimes

    def test_package_format_valid(self) -> None:
        """Test package format is known."""
        valid_formats = {"tar", "zip"}
        assert DEFAULT_PACKAGE_FORMAT in valid_formats

    def test_log_level_valid(self) -> None:
        """Test log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert DEFAULT_LOG_LEVEL in valid_levels

    def test_cli_name_valid(self) -> None:
        """Test CLI name is reasonable."""
        assert DEFAULT_CLI_NAME == "wrknv"
        assert DEFAULT_CLI_NAME.isalnum()

    def test_python_version_format(self) -> None:
        """Test Python version format is reasonable."""
        assert "." in DEFAULT_PYTHON_VERSION
        parts = DEFAULT_PYTHON_VERSION.split(".")
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts)


# 🧰🌍🔚
