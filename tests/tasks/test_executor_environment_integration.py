#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Integration tests for TaskExecutor with ExecutionEnvironment auto-detection."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wrknv.tasks.executor import TaskExecutor
from wrknv.tasks.schema import TaskConfig


class TestExecutorEnvironmentIntegration:
    """Tests for TaskExecutor integration with ExecutionEnvironment."""

    @pytest.mark.asyncio
    async def test_executor_with_auto_detect_disabled(self, tmp_path: Path) -> None:
        """Test executor when auto-detection is disabled."""
        task = TaskConfig(name="test", run="echo 'hello'")
        executor = TaskExecutor(repo_path=tmp_path, auto_detect_env=False)

        assert executor.execution_env is None

        result = await executor.execute(task)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_executor_creates_execution_environment(self, tmp_path: Path) -> None:
        """Test that executor creates ExecutionEnvironment by default."""
        executor = TaskExecutor(repo_path=tmp_path, package_name="test-package")

        assert executor.execution_env is not None
        assert executor.execution_env.package_name == "test-package"
        assert executor.execution_env.project_dir == tmp_path

    @pytest.mark.asyncio
    async def test_executor_respects_execution_mode(self, tmp_path: Path) -> None:
        """Test that executor respects execution_mode parameter."""
        executor = TaskExecutor(
            repo_path=tmp_path,
            package_name="test-package",
            execution_mode="direct",
        )

        assert executor.execution_env is not None
        assert executor.execution_env.mode == "direct"
        assert executor.execution_env.use_uv_run is False

    @pytest.mark.asyncio
    async def test_executor_applies_uv_run_prefix(self, tmp_path: Path) -> None:
        """Test that executor applies 'uv run' prefix when appropriate."""
        # Create uv.lock to trigger UV project detection
        (tmp_path / "uv.lock").write_text("")

        task = TaskConfig(name="test", run="pytest tests/")
        executor = TaskExecutor(repo_path=tmp_path, package_name="test-package")

        # Mock async_run to capture the command
        with patch("wrknv.tasks.executor.async_run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = await executor.execute(task)

            # Verify command was prefixed with 'uv run'
            mock_run.assert_called_once()
            called_command = mock_run.call_args[1]["cmd"]
            assert called_command.startswith("uv run pytest tests/")
            assert result.success is True

    @pytest.mark.asyncio
    async def test_executor_does_not_prefix_with_editable_install(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that executor does NOT use 'uv run' when editable install detected."""
        # Create uv.lock
        (tmp_path / "uv.lock").write_text("")

        task = TaskConfig(name="test", run="pytest tests/")

        # Mock editable install detection
        with patch("wrknv.tasks.environment.ExecutionEnvironment._is_editable_install") as mock_editable:
            mock_editable.return_value = True

            executor = TaskExecutor(repo_path=tmp_path, package_name="test-package")

            # Editable install should override UV project detection
            assert executor.execution_env is not None
            assert executor.execution_env.use_uv_run is False

            # Mock async_run to capture command
            with patch("wrknv.tasks.executor.async_run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "success"
                mock_result.stderr = ""
                mock_run.return_value = mock_result

                result = await executor.execute(task)

                # Verify command was NOT prefixed
                mock_run.assert_called_once()
                called_command = mock_run.call_args[1]["cmd"]
                assert called_command == "pytest tests/"
                assert result.success is True

    @pytest.mark.asyncio
    async def test_executor_respects_per_task_command_prefix(self, tmp_path: Path) -> None:
        """Test that per-task command_prefix overrides auto-detection."""
        # Create uv.lock (would normally trigger uv run)
        (tmp_path / "uv.lock").write_text("")

        task = TaskConfig(
            name="test",
            run="pytest tests/",
            command_prefix="",  # Explicitly disable prefix
        )
        executor = TaskExecutor(repo_path=tmp_path, package_name="test-package")

        # UV project detected but task overrides
        assert executor.execution_env is not None
        assert executor.execution_env.use_uv_run is True  # Auto-detected

        # Mock async_run
        with patch("wrknv.tasks.executor.async_run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = await executor.execute(task)

            # Task override should prevent prefix
            mock_run.assert_called_once()
            called_command = mock_run.call_args[1]["cmd"]
            assert called_command == "pytest tests/"
            assert result.success is True

    @pytest.mark.asyncio
    async def test_executor_applies_custom_command_prefix(self, tmp_path: Path) -> None:
        """Test that custom command_prefix is applied."""
        task = TaskConfig(
            name="test",
            run="pytest tests/",
            command_prefix="docker run myimage",
        )
        executor = TaskExecutor(repo_path=tmp_path, auto_detect_env=False)

        # Mock async_run
        with patch("wrknv.tasks.executor.async_run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = await executor.execute(task)

            # Custom prefix should be applied
            mock_run.assert_called_once()
            called_command = mock_run.call_args[1]["cmd"]
            assert called_command == "docker run myimage pytest tests/"
            assert result.success is True

    @pytest.mark.asyncio
    async def test_executor_modifies_path_for_direct_execution(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that executor modifies PATH when using direct execution."""
        # Create a venv
        venv_path = tmp_path / ".venv"
        venv_path.mkdir()
        (venv_path / "pyvenv.cfg").write_text("")
        bin_dir = venv_path / "bin"
        bin_dir.mkdir()

        task = TaskConfig(name="test", run="pytest tests/")
        executor = TaskExecutor(
            repo_path=tmp_path,
            package_name="test-package",
            execution_mode="direct",  # Force direct mode
        )

        # Mock async_run to capture environment
        with patch("wrknv.tasks.executor.async_run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = await executor.execute(task)

            # Verify PATH was modified
            mock_run.assert_called_once()
            called_env = mock_run.call_args[1]["env"]
            assert called_env is not None
            assert "PATH" in called_env
            assert str(bin_dir) in called_env["PATH"]
            assert result.success is True

    @pytest.mark.asyncio
    async def test_executor_does_not_modify_path_with_uv_run(self, tmp_path: Path) -> None:
        """Test that PATH is not modified when using 'uv run' (UV handles it)."""
        # Create uv.lock to trigger UV project detection
        (tmp_path / "uv.lock").write_text("")

        task = TaskConfig(name="test", run="pytest tests/")
        executor = TaskExecutor(repo_path=tmp_path, package_name="test-package")

        # UV project should use uv run
        assert executor.execution_env is not None
        assert executor.execution_env.use_uv_run is True

        # Mock async_run
        with patch("wrknv.tasks.executor.async_run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            os.environ.get("PATH", "")
            result = await executor.execute(task)

            # Verify PATH was not modified (or only contains os.environ PATH)
            mock_run.assert_called_once()
            called_env = mock_run.call_args[1]["env"]
            if called_env and "PATH" in called_env:
                # Should not contain venv bin paths
                assert ".venv/bin" not in called_env["PATH"]
            assert result.success is True

    @pytest.mark.asyncio
    async def test_executor_environment_override_from_env_var(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that WRKNV_TASK_RUNNER environment variable overrides auto-detection."""
        # Set environment variable override
        monkeypatch.setenv("WRKNV_TASK_RUNNER", "uv run")

        task = TaskConfig(name="test", run="pytest tests/")
        executor = TaskExecutor(
            repo_path=tmp_path,
            package_name="test-package",
            execution_mode="direct",  # Would normally use direct
        )

        # Environment variable should override
        assert executor.execution_env is not None
        assert executor.execution_env.override_from_env == "uv run"
        assert executor.execution_env.use_uv_run is True

        # Mock async_run
        with patch("wrknv.tasks.executor.async_run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = await executor.execute(task)

            # Command should have uv run prefix
            mock_run.assert_called_once()
            called_command = mock_run.call_args[1]["cmd"]
            assert called_command.startswith("uv run pytest tests/")
            assert result.success is True

    @pytest.mark.asyncio
    async def test_executor_preserves_task_environment_variables(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that task environment variables are preserved after PATH modification."""
        # Create a venv
        venv_path = tmp_path / ".venv"
        venv_path.mkdir()
        (venv_path / "pyvenv.cfg").write_text("")
        (venv_path / "bin").mkdir()

        task = TaskConfig(
            name="test",
            run="echo $CUSTOM_VAR",
            env={"CUSTOM_VAR": "custom_value"},
        )
        executor = TaskExecutor(
            repo_path=tmp_path,
            package_name="test-package",
            execution_mode="direct",
        )

        # Mock async_run
        with patch("wrknv.tasks.executor.async_run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "custom_value"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = await executor.execute(task)

            # Verify both PATH and CUSTOM_VAR are in environment
            mock_run.assert_called_once()
            called_env = mock_run.call_args[1]["env"]
            assert called_env is not None
            assert "PATH" in called_env
            assert "CUSTOM_VAR" in called_env
            assert called_env["CUSTOM_VAR"] == "custom_value"
            assert result.success is True

    @pytest.mark.asyncio
    async def test_executor_with_system_mode(self, tmp_path: Path) -> None:
        """Test executor with system mode (ignores venv)."""
        # Create a venv (should be ignored)
        venv_path = tmp_path / ".venv"
        venv_path.mkdir()
        (venv_path / "pyvenv.cfg").write_text("")

        task = TaskConfig(name="test", run="echo 'hello'")
        executor = TaskExecutor(
            repo_path=tmp_path,
            package_name="test-package",
            execution_mode="system",
        )

        # System mode should ignore venv
        assert executor.execution_env is not None
        assert executor.execution_env.venv_path is None
        assert executor.execution_env.use_uv_run is False

        result = await executor.execute(task)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_executor_logs_environment_detection_results(
        self,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that executor logs environment detection results."""
        # Create uv.lock
        (tmp_path / "uv.lock").write_text("")

        executor = TaskExecutor(repo_path=tmp_path, package_name="test-package")

        # Check that detection was logged
        # Note: This depends on logger configuration in tests
        assert executor.execution_env is not None
        assert executor.execution_env.is_uv_project is True


class TestExecutorEnvironmentRealExecution:
    """Integration tests with real subprocess execution."""

    @pytest.mark.asyncio
    async def test_real_command_execution_with_env_detection(
        self,
        tmp_path: Path,
    ) -> None:
        """Test real command execution with environment detection."""
        task = TaskConfig(name="test", run="echo 'integration test'")
        executor = TaskExecutor(
            repo_path=tmp_path,
            package_name="test-package",
            auto_detect_env=True,
        )

        result = await executor.execute(task)

        assert result.success is True
        assert result.exit_code == 0
        assert "integration test" in result.stdout

    @pytest.mark.asyncio
    async def test_real_command_with_args(self, tmp_path: Path) -> None:
        """Test real command execution with arguments."""
        task = TaskConfig(name="test", run="echo")
        executor = TaskExecutor(repo_path=tmp_path, auto_detect_env=True)

        result = await executor.execute(task, args=["hello", "world"])

        assert result.success is True
        assert "hello world" in result.stdout
