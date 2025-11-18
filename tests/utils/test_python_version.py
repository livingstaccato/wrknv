#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for Python version utilities."""

from __future__ import annotations

from pathlib import Path
import sys

from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.utils.python_version import (
    check_python_version_compatibility,
    get_project_python_requirement,
    get_python_version,
    get_venv_python_version,
    read_venv_python_version,
    save_venv_python_version,
    should_recreate_venv,
)


class TestGetVenvPythonVersion(FoundationTestCase):
    """Test get_venv_python_version function."""

    def test_get_venv_python_version_not_exists(self, tmp_path: Path) -> None:
        """Test when venv Python binary doesn't exist."""
        venv_dir = tmp_path / "venv"
        result = get_venv_python_version(venv_dir)
        assert result is None

    def test_get_venv_python_version_command_fails(self, tmp_path: Path) -> None:
        """Test when Python command fails."""
        venv_dir = tmp_path / "venv"
        # Create correct binary based on platform
        if sys.platform.startswith("win"):
            venv_bin = venv_dir / "Scripts" / "python.exe"
        else:
            venv_bin = venv_dir / "bin" / "python"
        venv_bin.parent.mkdir(parents=True)
        venv_bin.write_text("#!/usr/bin/env python3")
        venv_bin.chmod(0o755)

        with patch("wrknv.utils.python_version.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            result = get_venv_python_version(venv_dir)

        assert result is None

    def test_get_venv_python_version_exception(self, tmp_path: Path) -> None:
        """Test when run raises an exception."""
        venv_dir = tmp_path / "venv"
        # Create correct binary based on platform
        if sys.platform.startswith("win"):
            venv_bin = venv_dir / "Scripts" / "python.exe"
        else:
            venv_bin = venv_dir / "bin" / "python"
        venv_bin.parent.mkdir(parents=True)
        venv_bin.write_text("#!/usr/bin/env python3")
        venv_bin.chmod(0o755)

        with patch("wrknv.utils.python_version.run", side_effect=Exception("run failed")):
            result = get_venv_python_version(venv_dir)

        assert result is None


class TestGetProjectPythonRequirement(FoundationTestCase):
    """Test get_project_python_requirement function."""

    def test_get_project_python_requirement_exists(self, tmp_path: Path) -> None:
        """Test getting requires-python from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"')

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = get_project_python_requirement()

        assert result == ">=3.11"

    def test_get_project_python_requirement_no_file(self, tmp_path: Path) -> None:
        """Test when pyproject.toml doesn't exist."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = get_project_python_requirement()

        assert result is None

    def test_get_project_python_requirement_no_requires_python(self, tmp_path: Path) -> None:
        """Test when pyproject.toml has no requires-python."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test-project'")

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = get_project_python_requirement()

        assert result is None

    def test_get_project_python_requirement_no_project_section(self, tmp_path: Path) -> None:
        """Test when pyproject.toml has no [project] section."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.pytest]\nminversion = '7.0'")

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = get_project_python_requirement()

        assert result is None

    def test_get_project_python_requirement_invalid_toml(self, tmp_path: Path) -> None:
        """Test when pyproject.toml is invalid."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("invalid toml content [[[")

        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = get_project_python_requirement()

        assert result is None


class TestCheckPythonVersionCompatibility(FoundationTestCase):
    """Test check_python_version_compatibility function."""

    def test_version_compatible_exact(self) -> None:
        """Test exact version match."""
        result = check_python_version_compatibility("3.11.5", "==3.11.5")
        assert result is True

    def test_version_compatible_greater_than(self) -> None:
        """Test greater than requirement."""
        result = check_python_version_compatibility("3.12.0", ">=3.11")
        assert result is True

    def test_version_compatible_range(self) -> None:
        """Test version in range."""
        result = check_python_version_compatibility("3.11.5", ">=3.11,<3.13")
        assert result is True

    def test_version_not_compatible(self) -> None:
        """Test version not compatible."""
        result = check_python_version_compatibility("3.10.0", ">=3.11")
        assert result is False

    def test_version_parsing_error_returns_true(self) -> None:
        """Test that parsing errors default to compatible."""
        result = check_python_version_compatibility("invalid", ">=3.11")
        assert result is True

    def test_requirement_parsing_error_returns_true(self) -> None:
        """Test that invalid requirement defaults to compatible."""
        result = check_python_version_compatibility("3.11.5", "invalid requirement")
        assert result is True


class TestShouldRecreateVenv(FoundationTestCase):
    """Test should_recreate_venv function."""

    def test_should_recreate_no_requirement(self, tmp_path: Path) -> None:
        """Test when no project requirement is specified."""
        venv_dir = tmp_path / "venv"
        should_recreate, reason = should_recreate_venv(venv_dir, None)
        assert should_recreate is False
        assert reason is None

    def test_should_recreate_no_venv(self, tmp_path: Path) -> None:
        """Test when venv doesn't exist."""
        venv_dir = tmp_path / "venv"
        should_recreate, reason = should_recreate_venv(venv_dir, ">=3.11")
        assert should_recreate is False
        assert reason is None

    def test_should_recreate_incompatible_version(self, tmp_path: Path) -> None:
        """Test when venv has incompatible Python version."""
        venv_dir = tmp_path / "venv"

        with patch(
            "wrknv.utils.python_version.get_venv_python_version",
            return_value={"version": "3.10.0", "major": 3, "minor": 10, "micro": 0},
        ):
            should_recreate, reason = should_recreate_venv(venv_dir, ">=3.11")

        assert should_recreate is True
        assert reason is not None
        assert "3.10.0" in reason
        assert ">=3.11" in reason

    def test_should_recreate_compatible_version(self, tmp_path: Path) -> None:
        """Test when venv has compatible Python version."""
        venv_dir = tmp_path / "venv"

        with patch(
            "wrknv.utils.python_version.get_venv_python_version",
            return_value={"version": "3.11.5", "major": 3, "minor": 11, "micro": 5},
        ):
            should_recreate, reason = should_recreate_venv(venv_dir, ">=3.11")

        assert should_recreate is False
        assert reason is None


class TestSaveVenvPythonVersion(FoundationTestCase):
    """Test save_venv_python_version function."""

    def test_save_venv_python_version(self, tmp_path: Path) -> None:
        """Test saving Python version to marker file."""
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()

        save_venv_python_version(venv_dir)

        version_file = venv_dir / ".python-version"
        assert version_file.exists()
        content = version_file.read_text()
        assert content == f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


class TestReadVenvPythonVersion(FoundationTestCase):
    """Test read_venv_python_version function."""

    def test_read_venv_python_version_exists(self, tmp_path: Path) -> None:
        """Test reading Python version from marker file."""
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        version_file = venv_dir / ".python-version"
        version_file.write_text("3.11.5")

        result = read_venv_python_version(venv_dir)
        assert result == "3.11.5"

    def test_read_venv_python_version_not_exists(self, tmp_path: Path) -> None:
        """Test when marker file doesn't exist."""
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()

        result = read_venv_python_version(venv_dir)
        assert result is None

    def test_read_venv_python_version_with_whitespace(self, tmp_path: Path) -> None:
        """Test reading version with whitespace."""
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        version_file = venv_dir / ".python-version"
        version_file.write_text("  3.11.5\n")

        result = read_venv_python_version(venv_dir)
        assert result == "3.11.5"


class TestGetPythonVersion(FoundationTestCase):
    """Test get_python_version function."""

    def test_get_python_version(self) -> None:
        """Test getting current Python version."""
        result = get_python_version()
        expected = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
