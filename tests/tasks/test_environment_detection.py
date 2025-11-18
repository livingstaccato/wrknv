#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Comprehensive tests for task execution environment detection."""

from __future__ import annotations

import json
from pathlib import Path
import platform
from unittest.mock import MagicMock, patch

import pytest

from wrknv.tasks.environment import ExecutionEnvironment


class TestVenvDetection:
    """Tests for virtual environment detection."""

    def test_detect_workenv_pattern(self, tmp_path: Path) -> None:
        """Test detection of workenv/{package}_{os}_{arch} pattern."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        arch = (
            "amd64"
            if machine in ["x86_64", "amd64"]
            else "arm64"
            if machine in ["arm64", "aarch64"]
            else machine
        )

        workenv_dir = tmp_path / "workenv" / f"testpkg_{system}_{arch}"
        workenv_dir.mkdir(parents=True)
        (workenv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.venv_path == workenv_dir

    def test_detect_dot_venv(self, tmp_path: Path) -> None:
        """Test detection of .venv/ directory."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.venv_path == venv_dir

    def test_detect_venv(self, tmp_path: Path) -> None:
        """Test detection of venv/ directory."""
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.venv_path == venv_dir

    def test_priority_workenv_over_venv(self, tmp_path: Path) -> None:
        """Test that workenv/ has priority over .venv/ and venv/."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        arch = (
            "amd64"
            if machine in ["x86_64", "amd64"]
            else "arm64"
            if machine in ["arm64", "aarch64"]
            else machine
        )

        # Create all three
        workenv_dir = tmp_path / "workenv" / f"testpkg_{system}_{arch}"
        workenv_dir.mkdir(parents=True)
        (workenv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")

        dot_venv_dir = tmp_path / ".venv"
        dot_venv_dir.mkdir()
        (dot_venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")

        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.venv_path == workenv_dir

    def test_priority_dot_venv_over_venv(self, tmp_path: Path) -> None:
        """Test that .venv/ has priority over venv/."""
        dot_venv_dir = tmp_path / ".venv"
        dot_venv_dir.mkdir()
        (dot_venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")

        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.venv_path == dot_venv_dir

    def test_no_venv_found(self, tmp_path: Path) -> None:
        """Test behavior when no venv is found."""
        env = ExecutionEnvironment(tmp_path, "testpkg")
        # Will be None or sys.prefix if we're in a venv
        # Just check it doesn't crash
        assert env.venv_path is None or env.venv_path.exists()

    def test_venv_without_pyvenv_cfg_ignored(self, tmp_path: Path) -> None:
        """Test that directories without pyvenv.cfg are ignored."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        # No pyvenv.cfg

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.venv_path != venv_dir


class TestUVProjectDetection:
    """Tests for UV project detection."""

    def test_detect_via_uv_lock(self, tmp_path: Path) -> None:
        """Test UV project detection via uv.lock file."""
        (tmp_path / "uv.lock").write_text("# UV lockfile\n")

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.is_uv_project is True

    def test_detect_via_pyproject_toml(self, tmp_path: Path) -> None:
        """Test UV project detection via [tool.uv] in pyproject.toml."""
        pyproject_content = """
[project]
name = "testpkg"

[tool.uv]
dev-dependencies = ["pytest"]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.is_uv_project is True

    def test_not_uv_project_without_markers(self, tmp_path: Path) -> None:
        """Test non-UV project detection."""
        pyproject_content = """
[project]
name = "testpkg"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.is_uv_project is False

    def test_not_uv_project_no_pyproject(self, tmp_path: Path) -> None:
        """Test detection when no pyproject.toml exists."""
        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.is_uv_project is False

    def test_invalid_pyproject_toml(self, tmp_path: Path) -> None:
        """Test graceful handling of invalid TOML."""
        (tmp_path / "pyproject.toml").write_text("invalid [[ toml")

        env = ExecutionEnvironment(tmp_path, "testpkg")
        # Should not crash
        assert env.is_uv_project is False


class TestEditableInstallDetection:
    """Tests for editable install detection."""

    @patch("wrknv.tasks.environment.Distribution")
    def test_detect_editable_via_direct_url(self, mock_dist: MagicMock, tmp_path: Path) -> None:
        """Test editable install detection via direct_url.json."""
        direct_url_data = {
            "url": f"file://{tmp_path}",
            "dir_info": {"editable": True},
        }

        mock_instance = MagicMock()
        mock_instance.read_text.return_value = json.dumps(direct_url_data)
        mock_dist.from_name.return_value = mock_instance

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.package_is_editable is True

    @patch("wrknv.tasks.environment.Distribution")
    def test_detect_editable_via_src_structure(self, mock_dist: MagicMock, tmp_path: Path) -> None:
        """Test editable install detection via src/ directory structure."""
        # Mock distribution to raise exception (fallback to src/ detection)
        mock_dist.from_name.side_effect = FileNotFoundError

        # Create src/ structure
        src_dir = tmp_path / "src" / "testpkg"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("# testpkg")

        # Mock import to return our test module
        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.__file__ = str(src_dir / "__init__.py")
            mock_import.return_value = mock_module

            env = ExecutionEnvironment(tmp_path, "testpkg")
            assert env.package_is_editable is True

    @patch("wrknv.tasks.environment.Distribution")
    def test_not_editable_regular_install(self, mock_dist: MagicMock, tmp_path: Path) -> None:
        """Test non-editable install detection."""
        direct_url_data = {
            "url": "https://pypi.org/testpkg",
            "dir_info": {"editable": False},
        }

        mock_instance = MagicMock()
        mock_instance.read_text.return_value = json.dumps(direct_url_data)
        mock_dist.from_name.return_value = mock_instance

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.package_is_editable is False

    @patch("wrknv.tasks.environment.Distribution")
    def test_package_not_found(self, mock_dist: MagicMock, tmp_path: Path) -> None:
        """Test handling when package is not installed."""
        from importlib.metadata import PackageNotFoundError

        mock_dist.from_name.side_effect = PackageNotFoundError

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.package_is_editable is False


class TestAutoDetectionLogic:
    """Tests for auto-detection decision matrix."""

    @patch("wrknv.tasks.environment.ExecutionEnvironment._is_editable_install")
    @patch("wrknv.tasks.environment.ExecutionEnvironment._is_uv_project")
    def test_editable_install_uses_direct_execution(
        self, mock_uv: MagicMock, mock_editable: MagicMock, tmp_path: Path
    ) -> None:
        """Test that editable installs use direct execution (not uv run)."""
        mock_editable.return_value = True
        mock_uv.return_value = True  # Even in UV project

        env = ExecutionEnvironment(tmp_path, "testpkg", mode="auto")
        assert env.use_uv_run is False  # Should use direct to preserve editable

    @patch("wrknv.tasks.environment.ExecutionEnvironment._is_editable_install")
    @patch("wrknv.tasks.environment.ExecutionEnvironment._is_uv_project")
    def test_uv_project_non_editable_uses_uv_run(
        self, mock_uv: MagicMock, mock_editable: MagicMock, tmp_path: Path
    ) -> None:
        """Test that UV projects use uv run when not editable."""
        mock_editable.return_value = False
        mock_uv.return_value = True

        env = ExecutionEnvironment(tmp_path, "testpkg", mode="auto")
        assert env.use_uv_run is True

    @patch("wrknv.tasks.environment.ExecutionEnvironment._is_editable_install")
    @patch("wrknv.tasks.environment.ExecutionEnvironment._is_uv_project")
    def test_non_uv_project_uses_direct(
        self, mock_uv: MagicMock, mock_editable: MagicMock, tmp_path: Path
    ) -> None:
        """Test that non-UV projects use direct execution."""
        mock_editable.return_value = False
        mock_uv.return_value = False

        env = ExecutionEnvironment(tmp_path, "testpkg", mode="auto")
        assert env.use_uv_run is False


class TestExecutionModes:
    """Tests for explicit execution mode overrides."""

    def test_mode_uv_run(self, tmp_path: Path) -> None:
        """Test forced uv run mode."""
        env = ExecutionEnvironment(tmp_path, "testpkg", mode="uv_run")
        assert env.use_uv_run is True

    def test_mode_direct(self, tmp_path: Path) -> None:
        """Test forced direct execution mode."""
        env = ExecutionEnvironment(tmp_path, "testpkg", mode="direct")
        assert env.use_uv_run is False

    def test_mode_system(self, tmp_path: Path) -> None:
        """Test system mode (ignore venv)."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")

        env = ExecutionEnvironment(tmp_path, "testpkg", mode="system")
        assert env.use_uv_run is False
        assert env.venv_path is None  # Venv ignored in system mode


class TestEnvironmentVariableOverride:
    """Tests for WRKNV_TASK_RUNNER environment variable override."""

    def test_override_to_uv_run(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test override to use uv run."""
        monkeypatch.setenv("WRKNV_TASK_RUNNER", "uv run")

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.override_from_env == "uv run"
        assert env.use_uv_run is True

    def test_override_to_empty_string(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test override to no runner (empty string)."""
        monkeypatch.setenv("WRKNV_TASK_RUNNER", "")

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.override_from_env == ""
        assert env.use_uv_run is False

    def test_no_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test behavior without override."""
        monkeypatch.delenv("WRKNV_TASK_RUNNER", raising=False)

        env = ExecutionEnvironment(tmp_path, "testpkg")
        assert env.override_from_env is None


class TestCommandPreparation:
    """Tests for command preparation with prefixes."""

    def test_prepare_command_with_uv_run(self, tmp_path: Path) -> None:
        """Test command preparation when using uv run."""
        env = ExecutionEnvironment(tmp_path, "testpkg", mode="uv_run")
        command = env.prepare_command("pytest tests/")
        assert command == "uv run pytest tests/"

    def test_prepare_command_direct(self, tmp_path: Path) -> None:
        """Test command preparation for direct execution."""
        env = ExecutionEnvironment(tmp_path, "testpkg", mode="direct")
        command = env.prepare_command("pytest tests/")
        assert command == "pytest tests/"

    def test_prepare_command_with_task_override(self, tmp_path: Path) -> None:
        """Test per-task prefix override."""
        env = ExecutionEnvironment(tmp_path, "testpkg", mode="direct")
        command = env.prepare_command("pytest tests/", prefix_override="custom prefix")
        assert command == "custom prefix pytest tests/"

    def test_prepare_command_empty_override_disables_prefix(self, tmp_path: Path) -> None:
        """Test that empty string override disables prefix."""
        env = ExecutionEnvironment(tmp_path, "testpkg", mode="uv_run")
        command = env.prepare_command("pytest tests/", prefix_override="")
        assert command == "pytest tests/"  # No prefix

    def test_prepare_command_with_env_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test command preparation with environment variable override."""
        monkeypatch.setenv("WRKNV_TASK_RUNNER", "poetry run")

        env = ExecutionEnvironment(tmp_path, "testpkg")
        command = env.prepare_command("pytest tests/")
        assert command == "poetry run pytest tests/"


class TestEnvironmentPreparation:
    """Tests for environment dictionary preparation with PATH modification."""

    def test_prepare_environment_direct_execution(self, tmp_path: Path) -> None:
        """Test PATH modification for direct execution."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")
        bin_dir = venv_dir / ("Scripts" if platform.system() == "Windows" else "bin")
        bin_dir.mkdir()

        env = ExecutionEnvironment(tmp_path, "testpkg", mode="direct")
        exec_env = env.prepare_environment({"FOO": "bar"})

        assert "PATH" in exec_env
        assert str(bin_dir) in exec_env["PATH"]
        assert exec_env["FOO"] == "bar"

    def test_prepare_environment_uv_run_no_modification(self, tmp_path: Path) -> None:
        """Test that PATH is not modified when using uv run."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")

        env = ExecutionEnvironment(tmp_path, "testpkg", mode="uv_run")
        exec_env = env.prepare_environment({"FOO": "bar"})

        # PATH should not be modified for uv run
        assert exec_env == {"FOO": "bar"}

    def test_prepare_environment_no_venv(self, tmp_path: Path) -> None:
        """Test environment preparation when no venv found."""
        env = ExecutionEnvironment(tmp_path, "testpkg", mode="direct")
        exec_env = env.prepare_environment({"FOO": "bar"})

        # Should contain FOO - PATH may be added if we're running in a venv
        assert exec_env["FOO"] == "bar"
        # If a venv was detected (sys.prefix), PATH will be modified
        # If not, it should match the base env
        if env.venv_path:
            assert "PATH" in exec_env
        else:
            assert exec_env == {"FOO": "bar"}

    def test_prepare_environment_preserves_existing_path(self, tmp_path: Path) -> None:
        """Test that existing PATH is preserved and extended."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")
        bin_dir = venv_dir / ("Scripts" if platform.system() == "Windows" else "bin")
        bin_dir.mkdir()

        env = ExecutionEnvironment(tmp_path, "testpkg", mode="direct")
        exec_env = env.prepare_environment({"PATH": "/existing/path"})

        assert str(bin_dir) in exec_env["PATH"]
        assert "/existing/path" in exec_env["PATH"]

    def test_prepare_environment_empty_base(self, tmp_path: Path) -> None:
        """Test environment preparation with None base."""
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("[virtualenv]\n")
        bin_dir = venv_dir / ("Scripts" if platform.system() == "Windows" else "bin")
        bin_dir.mkdir()

        env = ExecutionEnvironment(tmp_path, "testpkg", mode="direct")
        exec_env = env.prepare_environment(None)

        assert "PATH" in exec_env
        assert str(bin_dir) in exec_env["PATH"]


class TestPlatformSpecificBehavior:
    """Tests for platform-specific functionality."""

    @patch("platform.system")
    def test_get_bin_dir_windows(self, mock_system: MagicMock, tmp_path: Path) -> None:
        """Test bin directory detection on Windows."""
        mock_system.return_value = "Windows"

        venv_path = tmp_path / ".venv"
        bin_dir = ExecutionEnvironment._get_bin_dir(venv_path)

        assert bin_dir == venv_path / "Scripts"

    @patch("platform.system")
    def test_get_bin_dir_unix(self, mock_system: MagicMock, tmp_path: Path) -> None:
        """Test bin directory detection on Unix/Linux/macOS."""
        mock_system.return_value = "Linux"

        venv_path = tmp_path / ".venv"
        bin_dir = ExecutionEnvironment._get_bin_dir(venv_path)

        assert bin_dir == venv_path / "bin"


# 🧰🌍🔚
