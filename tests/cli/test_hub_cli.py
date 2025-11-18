#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for hub CLI functionality."""

from __future__ import annotations

import sys

import click
from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.cli.hub_cli import (
    WrknvContext,
    _try_resolve_task_from_args,
    create_cli,
    intercept_task_command,
    load_commands,
)
from wrknv.config import WorkenvConfig


class TestWrknvContext(FoundationTestCase):
    """Test WrknvContext class."""

    def test_get_config_singleton(self) -> None:
        """Test that get_config returns singleton."""
        WrknvContext.reset()

        with patch("wrknv.cli.hub_cli.WorkenvConfig.load") as mock_load:
            mock_config = Mock(spec=WorkenvConfig)
            mock_load.return_value = mock_config

            config1 = WrknvContext.get_config()
            config2 = WrknvContext.get_config()

            assert config1 is config2
            mock_load.assert_called_once()

    def test_reset_clears_cache(self) -> None:
        """Test that reset clears config cache."""
        WrknvContext.reset()

        with patch("wrknv.cli.hub_cli.WorkenvConfig.load") as mock_load:
            mock_config1 = Mock(spec=WorkenvConfig)
            mock_config2 = Mock(spec=WorkenvConfig)
            mock_load.side_effect = [mock_config1, mock_config2]

            config1 = WrknvContext.get_config()
            WrknvContext.reset()
            config2 = WrknvContext.get_config()

            assert config1 is not config2
            assert mock_load.call_count == 2


class TestLoadCommands(FoundationTestCase):
    """Test load_commands function."""

    def test_load_commands_imports_modules(self) -> None:
        """Test that load_commands imports all command modules."""
        with patch("wrknv.cli.hub_cli.importlib.import_module") as mock_import:
            # Clear sys.modules to force fresh import
            command_modules = [
                "wrknv.cli.commands.config",
                "wrknv.cli.commands.container",
                "wrknv.cli.commands.doctor",
                "wrknv.cli.commands.gitignore",
                "wrknv.cli.commands.lock",
                "wrknv.cli.commands.profile",
                "wrknv.cli.commands.run",
                "wrknv.cli.commands.secrets",
                "wrknv.cli.commands.setup",
                "wrknv.cli.commands.terraform",
                "wrknv.cli.commands.tools",
                "wrknv.cli.commands.workspace",
            ]

            for module in command_modules:
                if module in sys.modules:
                    del sys.modules[module]

            load_commands()

            # Should import at least the command modules (may import more due to dependencies)
            assert mock_import.call_count >= len(command_modules)

    def test_load_commands_reloads_existing_modules(self) -> None:
        """Test that load_commands reloads already imported modules."""
        with patch("wrknv.cli.hub_cli.importlib.reload") as mock_reload:
            # Simulate one module already loaded
            import types

            mock_module = types.ModuleType("wrknv.cli.commands.config")
            sys.modules["wrknv.cli.commands.config"] = mock_module

            try:
                load_commands()

                # Should have called reload for the existing module
                assert mock_reload.call_count > 0
            finally:
                # Clean up
                if "wrknv.cli.commands.config" in sys.modules:
                    del sys.modules["wrknv.cli.commands.config"]


class TestCreateCli(FoundationTestCase):
    """Test create_cli function."""

    def test_create_cli_returns_command(self) -> None:
        """Test that create_cli returns a Click command."""
        cli = create_cli()

        assert isinstance(cli, click.Command)
        assert cli.name == "wrknv"

    def test_create_cli_resets_context(self) -> None:
        """Test that create_cli resets WrknvContext."""
        WrknvContext._config = Mock()

        create_cli()

        assert WrknvContext._config is None

    def test_create_cli_clears_registry(self) -> None:
        """Test that create_cli clears command registry."""
        with patch("wrknv.cli.hub_cli.get_hub") as mock_get_hub:
            mock_hub = Mock()
            mock_get_hub.return_value = mock_hub

            create_cli()

            mock_hub.clear.assert_called_once()


class TestTryResolveTaskFromArgs(FoundationTestCase):
    """Test _try_resolve_task_from_args function."""

    def test_resolve_simple_task(self) -> None:
        """Test resolving a simple task name."""
        mock_registry = Mock()
        mock_registry.get_task.side_effect = lambda name: name == "test"

        result = _try_resolve_task_from_args(mock_registry, ["test", "--verbose"])

        assert result is not None
        assert result[0] == "test"
        assert result[1] == ["--verbose"]

    def test_resolve_namespaced_task(self) -> None:
        """Test resolving a namespaced task."""
        mock_registry = Mock()
        mock_registry.get_task.side_effect = lambda name: name == "test.unit"

        result = _try_resolve_task_from_args(mock_registry, ["test", "unit", "--verbose"])

        assert result is not None
        assert result[0] == "test.unit"
        assert result[1] == ["--verbose"]

    def test_resolve_greedy_matching(self) -> None:
        """Test that matching is greedy (longest match wins)."""
        mock_registry = Mock()

        def get_task_side_effect(name):
            return name in ["test", "test.unit"]

        mock_registry.get_task.side_effect = get_task_side_effect

        result = _try_resolve_task_from_args(mock_registry, ["test", "unit", "--verbose"])

        # Should match the longer "test.unit" instead of just "test"
        assert result is not None
        assert result[0] == "test.unit"
        assert result[1] == ["--verbose"]

    def test_resolve_no_match(self) -> None:
        """Test when no task matches."""
        mock_registry = Mock()
        mock_registry.get_task.return_value = None

        result = _try_resolve_task_from_args(mock_registry, ["unknown", "--verbose"])

        assert result is None

    def test_resolve_empty_args(self) -> None:
        """Test with empty args."""
        mock_registry = Mock()

        result = _try_resolve_task_from_args(mock_registry, [])

        assert result is None


class TestInterceptTaskCommand(FoundationTestCase):
    """Test intercept_task_command function."""

    def test_intercept_returns_false_for_builtin_commands(self) -> None:
        """Test that built-in commands are not intercepted."""
        with patch("wrknv.cli.hub_cli.sys.argv", ["we", "config"]):
            result = intercept_task_command()
            assert result is False

        with patch("wrknv.cli.hub_cli.sys.argv", ["we", "tools"]):
            result = intercept_task_command()
            assert result is False

        with patch("wrknv.cli.hub_cli.sys.argv", ["we", "--help"]):
            result = intercept_task_command()
            assert result is False

    def test_intercept_returns_false_for_no_args(self) -> None:
        """Test that no args returns False."""
        with patch("wrknv.cli.hub_cli.sys.argv", ["we"]):
            result = intercept_task_command()
            assert result is False

    def test_intercept_runs_task_when_found(self) -> None:
        """Test that task is intercepted and run when found."""
        mock_registry = Mock()
        mock_task = Mock()
        mock_registry.get_task.return_value = mock_task

        with (
            patch("wrknv.cli.hub_cli.sys.argv", ["we", "test"]),
            patch("wrknv.tasks.registry.TaskRegistry.from_repo") as mock_from_repo,
            patch("wrknv.cli.hub_cli.asyncio.run") as mock_async_run,
        ):
            mock_from_repo.return_value = mock_registry

            result = intercept_task_command()

            assert result is True
            mock_async_run.assert_called_once()

    def test_intercept_returns_false_when_task_not_found(self) -> None:
        """Test that returns False when task not found."""
        mock_registry = Mock()
        mock_registry.get_task.return_value = None

        with (
            patch("wrknv.cli.hub_cli.sys.argv", ["we", "unknown"]),
            patch("wrknv.tasks.registry.TaskRegistry.from_repo") as mock_from_repo,
        ):
            mock_from_repo.return_value = mock_registry

            result = intercept_task_command()

            assert result is False

    def test_intercept_handles_exceptions(self) -> None:
        """Test that exceptions during task resolution are handled."""
        with (
            patch("wrknv.cli.hub_cli.sys.argv", ["we", "test"]),
            patch("wrknv.tasks.registry.TaskRegistry.from_repo") as mock_from_repo,
        ):
            mock_from_repo.side_effect = Exception("Registry error")

            result = intercept_task_command()

            assert result is False


class TestIntegration(FoundationTestCase):
    """Integration tests for hub CLI."""

    def test_create_cli_has_standard_commands(self) -> None:
        """Test that created CLI has standard commands."""
        cli = create_cli()

        # Check that commands were loaded
        assert hasattr(cli, "commands")
        assert len(cli.commands) > 0

        # Check for some expected commands (use only commands we know exist)
        expected_commands = ["run", "tasks"]
        for cmd in expected_commands:
            assert cmd in cli.commands, f"Command '{cmd}' not found in CLI"

    def test_wrknv_context_config_lifecycle(self) -> None:
        """Test full lifecycle of WrknvContext config."""
        WrknvContext.reset()

        with patch("wrknv.cli.hub_cli.WorkenvConfig.load") as mock_load:
            mock_config = Mock(spec=WorkenvConfig)
            mock_load.return_value = mock_config

            # Get config
            config1 = WrknvContext.get_config()
            assert config1 is mock_config

            # Get again - should be cached
            config2 = WrknvContext.get_config()
            assert config2 is config1
            mock_load.assert_called_once()

            # Reset and get again - should reload
            WrknvContext.reset()
            config3 = WrknvContext.get_config()
            assert config3 is not None
            assert mock_load.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
