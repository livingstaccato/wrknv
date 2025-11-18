#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from pathlib import Path
import sys
import tomllib

from packaging.specifiers import SpecifierSet
from packaging.version import Version
from provide.foundation.process import run
from provide.foundation.serialization import json


def get_venv_python_version(venv_dir: Path) -> dict[str, any] | None:
    """Get Python version information from a virtual environment.

    Args:
        venv_dir: Path to the virtual environment directory

    Returns:
        Dict with version info or None if venv doesn't exist
    """
    python_bin = venv_dir / "bin" / "python"
    if sys.platform.startswith("win"):
        python_bin = venv_dir / "Scripts" / "python.exe"

    if not python_bin.exists():
        return None

    try:
        # Get version info as JSON for easy parsing
        cmd = [
            str(python_bin),
            "-c",
            "import sys, json; print(json.dumps({'version': '.'.join(map(str, sys.version_info[:3])), 'major': sys.version_info.major, 'minor': sys.version_info.minor, 'micro': sys.version_info.micro}))",
        ]
        result = run(cmd, check=False)

        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass

    return None


def get_project_python_requirement() -> str | None:
    """Get Python version requirement from pyproject.toml.

    Returns:
        Python version specifier string or None
    """
    pyproject_path = Path.cwd() / "pyproject.toml"

    if not pyproject_path.exists():
        return None

    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)

        # Check for requires-python in [project] section
        if "project" in data and "requires-python" in data["project"]:
            return data["project"]["requires-python"]
    except Exception:
        pass

    return None


def check_python_version_compatibility(version: str, requirement: str) -> bool:
    """Check if a Python version meets the requirement.

    Args:
        version: Python version string (e.g., "3.11.5")
        requirement: PEP 440 version specifier (e.g., ">=3.11")

    Returns:
        True if version meets requirement
    """
    try:
        version_obj = Version(version)
        spec = SpecifierSet(requirement)
        return version_obj in spec
    except Exception:
        # If we can't parse, assume it's compatible
        return True


def should_recreate_venv(venv_dir: Path, project_requirement: str | None) -> tuple[bool, str | None]:
    """Determine if virtual environment should be recreated.

    Args:
        venv_dir: Path to virtual environment
        project_requirement: Python version requirement from project

    Returns:
        Tuple of (should_recreate, reason_message)
    """
    if not project_requirement:
        # No requirement specified, don't recreate
        return (False, None)

    version_info = get_venv_python_version(venv_dir)

    if not version_info:
        # No existing venv
        return (False, None)

    venv_version = version_info["version"]

    if not check_python_version_compatibility(venv_version, project_requirement):
        return (
            True,
            f"Virtual environment has Python {venv_version} but project requires {project_requirement}",
        )

    return (False, None)


def save_venv_python_version(venv_dir: Path) -> None:
    """Save current Python version to a marker file in venv.

    This is used by the generated shell script to track the Python
    version used to create the venv.
    """
    version_file = venv_dir / ".python-version"
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    version_file.write_text(version)


def read_venv_python_version(venv_dir: Path) -> str | None:
    """Read Python version from marker file in venv."""
    version_file = venv_dir / ".python-version"
    if version_file.exists():
        return version_file.read_text().strip()
    return None


def get_python_version() -> str:
    """Get current Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


# 🧰🌍🔚
