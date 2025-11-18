#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for command auto-detection in CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from wrknv.cli.hub_cli import _try_resolve_task_from_args, intercept_task_command
from wrknv.tasks.registry import TaskRegistry
from wrknv.tasks.schema import TaskConfig


class TestTryResolveTaskFromArgs:
    """Tests for _try_resolve_task_from_args helper function."""

    def test_resolve_flat_task(self, tmp_path: Path) -> None:
        """Test resolving a simple flat task."""
        # Create registry with flat task
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text("""
[tasks]
test = "pytest tests/"
""")

        registry = TaskRegistry.from_repo(tmp_path)

        # Try to resolve "test"
        result = _try_resolve_task_from_args(registry, ["test"])

        assert result == ("test", [])

    def test_resolve_flat_task_with_args(self, tmp_path: Path) -> None:
        """Test resolving flat task with arguments."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text("""
[tasks]
test = "pytest tests/"
""")

        registry = TaskRegistry.from_repo(tmp_path)

        # Try to resolve "test --verbose"
        result = _try_resolve_task_from_args(registry, ["test", "--verbose"])

        assert result == ("test", ["--verbose"])

    def test_resolve_nested_task(self, tmp_path: Path) -> None:
        """Test resolving a two-level nested task."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text("""
[tasks.test]
unit = "pytest tests/unit/"
integration = "pytest tests/integration/"
""")

        registry = TaskRegistry.from_repo(tmp_path)

        # Try to resolve "test unit"
        result = _try_resolve_task_from_args(registry, ["test", "unit"])

        assert result == ("test.unit", [])

    def test_resolve_nested_task_with_args(self, tmp_path: Path) -> None:
        """Test resolving nested task with arguments."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text("""
[tasks.test]
unit = "pytest tests/unit/"
""")

        registry = TaskRegistry.from_repo(tmp_path)

        # Try to resolve "test unit --verbose"
        result = _try_resolve_task_from_args(registry, ["test", "unit", "--verbose"])

        assert result == ("test.unit", ["--verbose"])

    def test_resolve_three_level_nested_task(self, tmp_path: Path) -> None:
        """Test resolving a three-level nested task."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text("""
[tasks.test.unit]
fast = "pytest tests/unit/ -x"
""")

        registry = TaskRegistry.from_repo(tmp_path)

        # Try to resolve "test unit fast"
        result = _try_resolve_task_from_args(registry, ["test", "unit", "fast"])

        assert result == ("test.unit.fast", [])

    def test_greedy_matching_finds_longest_valid_match(self, tmp_path: Path) -> None:
        """Test that greedy matching finds the longest valid task name."""
        config_path = tmp_path / "wrknv.toml"
        # Create only nested tasks without flat versions
        config_path.write_text("""
[tasks.test]
unit = "pytest tests/unit/"
integration = "pytest tests/integration/"
""")

        registry = TaskRegistry.from_repo(tmp_path)

        # Try to resolve "test unit extra" where only "test.unit" exists
        # Should match "test.unit" and pass "extra" as an arg
        result = _try_resolve_task_from_args(registry, ["test", "unit", "extra"])

        assert result == ("test.unit", ["extra"])

    def test_no_match_returns_none(self, tmp_path: Path) -> None:
        """Test that non-existent task returns None."""
        config_path = tmp_path / "wrknv.toml"
        config_path.write_text("""
[tasks]
test = "pytest tests/"
""")

        registry = TaskRegistry.from_repo(tmp_path)

        # Try to resolve non-existent task
        result = _try_resolve_task_from_args(registry, ["build", "docker"])

        assert result is None

    def test_empty_args_returns_none(self, tmp_path: Path) -> None:
        """Test that empty args returns None."""
        registry = TaskRegistry.from_repo(tmp_path)

        result = _try_resolve_task_from_args(registry, [])

        assert result is None


class TestInterceptTaskCommand:
    """Tests for intercept_task_command function."""

    def test_built_in_commands_not_intercepted(self) -> None:
        """Test that built-in commands are not intercepted."""
        built_in_commands = [
            "config",
            "setup",
            "run",
            "tasks",
            "doctor",
            "--help",
            "-h",
        ]

        for cmd in built_in_commands:
            with patch("sys.argv", ["wrknv", cmd]):
                result = intercept_task_command()
                assert result is False, f"Built-in command '{cmd}' should not be intercepted"

    def test_empty_args_not_intercepted(self) -> None:
        """Test that empty args are not intercepted."""
        with patch("sys.argv", ["wrknv"]):
            result = intercept_task_command()
            assert result is False

    @patch("wrknv.tasks.registry.TaskRegistry.from_repo")
    @patch("wrknv.cli.hub_cli.asyncio.run")
    @patch("wrknv.cli.hub_cli.Path.cwd")
    def test_flat_task_intercepted_and_run(
        self,
        mock_cwd: MagicMock,
        mock_asyncio_run: MagicMock,
        mock_from_repo: MagicMock,
    ) -> None:
        """Test that a flat task is intercepted and run."""
        # Setup mocks
        mock_cwd.return_value = Path("/fake/repo")

        mock_registry = MagicMock()
        task = TaskConfig(name="test", run="pytest tests/")
        mock_registry.get_task.return_value = task
        mock_from_repo.return_value = mock_registry

        # Simulate: we test
        with patch("sys.argv", ["we", "test"]):
            result = intercept_task_command()

        assert result is True
        mock_asyncio_run.assert_called_once()

    @patch("wrknv.tasks.registry.TaskRegistry.from_repo")
    @patch("wrknv.cli.hub_cli.asyncio.run")
    @patch("wrknv.cli.hub_cli.Path.cwd")
    def test_nested_task_intercepted(
        self,
        mock_cwd: MagicMock,
        mock_asyncio_run: MagicMock,
        mock_from_repo: MagicMock,
    ) -> None:
        """Test that a nested task is intercepted."""
        # Setup mocks
        mock_cwd.return_value = Path("/fake/repo")

        mock_registry = MagicMock()
        # First call for "test.unit" returns None, second for "test.unit" returns task
        test_unit_task = TaskConfig(name="unit", namespace="test", run="pytest tests/unit/")
        mock_registry.get_task.side_effect = [None, test_unit_task]
        mock_from_repo.return_value = mock_registry

        # Simulate: we test unit
        with patch("sys.argv", ["we", "test", "unit"]):
            result = intercept_task_command()

        assert result is True
        mock_asyncio_run.assert_called_once()

    @patch("wrknv.tasks.registry.TaskRegistry.from_repo")
    @patch("wrknv.cli.hub_cli.Path.cwd")
    def test_non_existent_task_not_intercepted(
        self,
        mock_cwd: MagicMock,
        mock_from_repo: MagicMock,
    ) -> None:
        """Test that non-existent tasks are not intercepted."""
        # Setup mocks
        mock_cwd.return_value = Path("/fake/repo")

        mock_registry = MagicMock()
        mock_registry.get_task.return_value = None
        mock_from_repo.return_value = mock_registry

        # Simulate: we nonexistent
        with patch("sys.argv", ["we", "nonexistent"]):
            result = intercept_task_command()

        assert result is False

    @patch("wrknv.tasks.registry.TaskRegistry.from_repo")
    @patch("wrknv.cli.hub_cli.asyncio.run")
    @patch("wrknv.cli.hub_cli.Path.cwd")
    def test_task_with_args_intercepted(
        self,
        mock_cwd: MagicMock,
        mock_asyncio_run: MagicMock,
        mock_from_repo: MagicMock,
    ) -> None:
        """Test that tasks with arguments are intercepted."""
        # Setup mocks
        mock_cwd.return_value = Path("/fake/repo")

        mock_registry = MagicMock()
        task = TaskConfig(name="test", run="pytest tests/")
        mock_registry.get_task.return_value = task
        mock_from_repo.return_value = mock_registry

        # Simulate: we test --verbose --color=yes
        with patch("sys.argv", ["we", "test", "--verbose", "--color=yes"]):
            result = intercept_task_command()

        assert result is True
        mock_asyncio_run.assert_called_once()
