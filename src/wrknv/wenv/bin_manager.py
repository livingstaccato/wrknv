#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Workenv Bin Management
======================
General utilities for managing workenv bin directories and tool binaries."""

from __future__ import annotations

import os
import pathlib
import shutil
import sys
from typing import Any

from provide.foundation import logger


def get_workenv_bin_dir(config: Any | None) -> pathlib.Path:
    """Get the workenv bin directory (or fallback location).

    Priority:
    1. If in a workenv virtualenv -> workenv/bin
    2. If in a regular venv -> venv/bin
    3. If not in venv, find workenv relative to project root
    4. Fallback to ~/.local/bin
    """
    venv_path = pathlib.Path(sys.prefix)
    bin_dir = None

    # Check if we're in a virtual environment
    if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        # We're in a venv - determine bin directory based on platform
        bin_dir = venv_path / ("Scripts" if os.name == "nt" else "bin")
    else:
        # Not in a venv, check for workenv directory relative to project root
        project_root = find_project_root()
        if project_root:
            workenv_dir_name = None
            if config is not None:
                get_dir_name = getattr(config, "get_workenv_dir_name", None)
                if callable(get_dir_name):
                    workenv_dir_name = get_dir_name()
                else:
                    workenv_dir_name = getattr(config, "workenv_dir_name", None)

            if workenv_dir_name:
                bin_dir = project_root / workenv_dir_name / "bin"
                if bin_dir.exists():
                    return bin_dir

        # Fallback to .local/bin
        bin_dir = pathlib.Path.home() / ".local" / "bin"

    # Ensure directory exists
    bin_dir.mkdir(parents=True, exist_ok=True)
    return bin_dir


def find_project_root() -> pathlib.Path | None:
    """Find the project root by looking for pyproject.toml."""
    current = pathlib.Path.cwd()

    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent

    return None


def copy_tool_binary(source_path: pathlib.Path, target_name: str, bin_dir: pathlib.Path) -> bool:
    """Copy a tool binary to the bin directory.

    Args:
        source_path: Path to source binary
        target_name: Name for target binary (without .exe)
        bin_dir: Destination bin directory

    Returns:
        True if successful, False otherwise
    """
    if not source_path.exists():
        logger.warning(f"Source binary not found: {source_path}")
        return False

    # Add .exe extension on Windows
    if os.name == "nt":
        target_name += ".exe"

    target_path = bin_dir / target_name

    try:
        # Copy the binary
        shutil.copy2(source_path, target_path)

        # Make executable on Unix systems
        if os.name != "nt":
            target_path.chmod(0o755)

        logger.debug(f"Copied binary to {target_path}")
        return True

    except Exception as e:
        logger.warning(f"Failed to copy binary: {e}")
        return False


# 🧰🌍🔚
