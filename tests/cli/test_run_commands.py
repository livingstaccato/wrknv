#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for CLI run/tasks commands."""

from __future__ import annotations

import click.testing
from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.cli.hub_cli import create_cli


def get_test_cli():
    """Get or create the test CLI instance."""
    return create_cli()


class TestRunCommand(FoundationTestCase):
    """Test run command."""

    def test_run_task_success(self) -> None:
        """Test running a task successfully."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            # Mock successful task result
            result_mock = Mock()
            result_mock.success = True
            result_mock.stdout = "Test output\n"
            result_mock.stderr = ""
            result_mock.duration = 1.5
            result_mock.exit_code = 0

            async def mock_run_task(*args, **kwargs):
                return result_mock

            mock_registry.run_task = mock_run_task

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["run", "test"])

            assert result.exit_code == 0
            assert "Running task: test" in result.output
            assert "completed" in result.output

    def test_run_task_with_info_flag(self) -> None:
        """Test running task with --info flag."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            task_mock = Mock()
            task_mock.name = "test"
            task_mock.description = "Run tests"
            task_mock.run = "pytest"
            task_mock.depends_on = []
            task_mock.env = {}
            mock_registry.get_task.return_value = task_mock

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["run", "test", "--info"])

            assert result.exit_code == 0
            assert "Task: test" in result.output
            assert "Run tests" in result.output
            assert "Command: pytest" in result.output

    def test_run_task_with_dependencies(self) -> None:
        """Test task info shows dependencies."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            task_mock = Mock()
            task_mock.name = "build"
            task_mock.description = "Build project"
            task_mock.run = "make build"
            task_mock.depends_on = ["test", "lint"]
            task_mock.env = {"NODE_ENV": "production"}
            mock_registry.get_task.return_value = task_mock

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["run", "build", "--info"])

            assert result.exit_code == 0
            assert "Depends on: test, lint" in result.output
            assert "Environment:" in result.output

    def test_run_task_not_found(self) -> None:
        """Test running non-existent task with info."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry
            mock_registry.get_task.return_value = None

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["run", "nonexistent", "--info"])

            assert result.exit_code == 0
            assert "Task not found" in result.output

    @pytest.mark.skip(
        reason="--env parameter doesn't work due to foundation hub not converting tuple[str, ...] to multiple=True"
    )
    def test_run_task_with_env_vars(self) -> None:
        """Test running task with environment variables."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            result_mock = Mock()
            result_mock.success = True
            result_mock.stdout = ""
            result_mock.stderr = ""
            result_mock.duration = 1.0
            result_mock.exit_code = 0

            env_captured = {}

            async def mock_run_task(*args, **kwargs):
                env_captured.update(kwargs.get("env", {}))
                return result_mock

            mock_registry.run_task = mock_run_task

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["run", "test", "--env", "FOO=bar"])

            assert result.exit_code == 0
            assert env_captured.get("FOO") == "bar"

    def test_run_task_invalid_env_format(self) -> None:
        """Test running task with invalid env format."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry"):
            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["run", "test", "--env", "INVALID"])

            assert result.exit_code == 1
            assert "Invalid env format" in result.output

    def test_run_task_dry_run(self) -> None:
        """Test running task in dry-run mode."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            result_mock = Mock()
            result_mock.success = True
            result_mock.stdout = "[DRY RUN] Would execute: pytest\n"
            result_mock.stderr = ""
            result_mock.duration = 0.1
            result_mock.exit_code = 0

            dry_run_captured = None

            async def mock_run_task(*args, **kwargs):
                nonlocal dry_run_captured
                dry_run_captured = kwargs.get("dry_run")
                return result_mock

            mock_registry.run_task = mock_run_task

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["run", "test", "--dry-run"])

            assert result.exit_code == 0
            assert dry_run_captured is True
            assert "DRY RUN" in result.output

    def test_run_task_failure(self) -> None:
        """Test running task that fails."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            result_mock = Mock()
            result_mock.success = False
            result_mock.stdout = ""
            result_mock.stderr = "Error: test failed\n"
            result_mock.duration = 2.0
            result_mock.exit_code = 1

            async def mock_run_task(*args, **kwargs):
                return result_mock

            mock_registry.run_task = mock_run_task

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["run", "test"])

            assert result.exit_code == 1
            assert "failed" in result.output

    def test_run_task_value_error(self) -> None:
        """Test running task that raises ValueError."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            async def mock_run_task(*args, **kwargs):
                raise ValueError("Task configuration invalid")

            mock_registry.run_task = mock_run_task

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["run", "test"])

            assert result.exit_code == 1
            assert "Task configuration invalid" in result.output


class TestTasksCommand(FoundationTestCase):
    """Test tasks command."""

    def test_list_tasks(self) -> None:
        """Test listing available tasks."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            # Create mock tasks
            task1 = Mock()
            task1.name = "test"
            task1.description = "Run tests"
            task1.namespace = "dev"
            task1.is_default = False
            task1.is_composite = False
            task1.run = "pytest"

            task2 = Mock()
            task2.name = "build"
            task2.description = "Build project"
            task2.namespace = "dev"
            task2.is_default = False
            task2.is_composite = False
            task2.run = "make build"

            mock_registry.list_tasks.return_value = [task1, task2]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tasks"])

            assert result.exit_code == 0
            assert "Available tasks" in result.output
            assert "test" in result.output
            assert "build" in result.output

    def test_list_tasks_verbose(self) -> None:
        """Test listing tasks in verbose mode."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            task = Mock()
            task.name = "test"
            task.description = "Run tests"
            task.namespace = "dev"
            task.is_default = False
            task.is_composite = False
            task.run = "pytest tests/"

            mock_registry.list_tasks.return_value = [task]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tasks", "--verbose"])

            assert result.exit_code == 0
            assert "Command: pytest tests/" in result.output

    def test_list_tasks_with_composite(self) -> None:
        """Test listing composite tasks."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            task = Mock()
            task.name = "ci"
            task.description = "Run CI pipeline"
            task.namespace = "dev"
            task.is_default = False
            task.is_composite = True
            task.run = ["lint", "test", "build"]

            mock_registry.list_tasks.return_value = [task]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tasks", "--verbose"])

            assert result.exit_code == 0
            assert "Runs: lint, test, build" in result.output

    def test_list_tasks_with_default(self) -> None:
        """Test listing tasks shows default marker."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            task = Mock()
            task.name = "test"
            task.description = "Run tests"
            task.namespace = "dev"
            task.is_default = True
            task.is_composite = False
            task.run = "pytest"

            mock_registry.list_tasks.return_value = [task]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tasks"])

            assert result.exit_code == 0
            assert "(default)" in result.output

    def test_list_tasks_flat(self) -> None:
        """Test listing flat (non-namespaced) tasks."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            task = Mock()
            task.name = "quick"
            task.description = "Quick task"
            task.namespace = None
            task.is_default = False
            task.is_composite = False
            task.run = "echo quick"

            mock_registry.list_tasks.return_value = [task]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tasks"])

            assert result.exit_code == 0
            assert "Flat tasks" in result.output
            assert "quick" in result.output

    def test_list_tasks_none_defined(self) -> None:
        """Test listing when no tasks are defined."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry
            mock_registry.list_tasks.return_value = []

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tasks"])

            assert result.exit_code == 0
            assert "No tasks defined" in result.output

    def test_list_tasks_long_command_truncated(self) -> None:
        """Test that long commands are truncated in verbose mode."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            task = Mock()
            task.name = "long"
            task.description = "Long command"
            task.namespace = None
            task.is_default = False
            task.is_composite = False
            task.run = "a" * 100  # Very long command

            mock_registry.list_tasks.return_value = [task]

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["tasks", "--verbose"])

            assert result.exit_code == 0
            assert "..." in result.output  # Truncation marker


class TestRunCommandIntegration(FoundationTestCase):
    """Integration tests for run/tasks commands."""

    def test_list_then_run_workflow(self) -> None:
        """Test workflow of listing tasks then running one."""
        cli = get_test_cli()

        with patch("wrknv.cli.commands.run.TaskRegistry") as mock_registry_cls:
            mock_registry = Mock()
            mock_registry_cls.from_repo.return_value = mock_registry

            # Setup for list
            task = Mock()
            task.name = "test"
            task.description = "Run tests"
            task.namespace = "dev"
            task.is_default = False
            task.is_composite = False
            task.run = "pytest"
            mock_registry.list_tasks.return_value = [task]

            # Setup for run
            result_mock = Mock()
            result_mock.success = True
            result_mock.stdout = "All tests passed\n"
            result_mock.stderr = ""
            result_mock.duration = 5.0
            result_mock.exit_code = 0

            async def mock_run_task(*args, **kwargs):
                return result_mock

            mock_registry.run_task = mock_run_task

            runner = click.testing.CliRunner()

            # List tasks
            result1 = runner.invoke(cli, ["tasks"])
            assert result1.exit_code == 0
            assert "test" in result1.output

            # Run task
            result2 = runner.invoke(cli, ["run", "test"])
            assert result2.exit_code == 0
            assert "completed" in result2.output


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
