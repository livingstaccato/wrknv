#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Security Configuration
======================
Configuration loading and resolution for security scanning."""

from __future__ import annotations

import tomllib
from pathlib import Path

from attrs import define, field
from provide.foundation import logger


@define
class SecurityConfig:
    """Security scanning configuration."""

    description: str = "Allowlisted paths for secret scanning"
    allowed_paths: list[str] = field(factory=list)


def load_security_config(
    project_dir: Path | None = None,
    pyproject_path: Path | None = None,
    wrknv_path: Path | None = None,
) -> SecurityConfig | None:
    """Load security configuration from pyproject.toml or wrknv.toml.

    Resolution order:
    1. pyproject.toml [tool.security]
    2. wrknv.toml [security]

    Args:
        project_dir: Project directory to search in
        pyproject_path: Explicit path to pyproject.toml
        wrknv_path: Explicit path to wrknv.toml

    Returns:
        SecurityConfig if found, None otherwise
    """
    project_dir = Path(project_dir) if project_dir else Path.cwd()

    # Try pyproject.toml first
    pyproject_file = pyproject_path or project_dir / "pyproject.toml"
    if pyproject_file.exists():
        config = _load_from_pyproject(pyproject_file)
        if config:
            logger.debug(f"Loaded security config from {pyproject_file}")
            return config

    # Try wrknv.toml
    wrknv_file = wrknv_path or project_dir / "wrknv.toml"
    if wrknv_file.exists():
        config = _load_from_wrknv(wrknv_file)
        if config:
            logger.debug(f"Loaded security config from {wrknv_file}")
            return config

    # Try .wrknv.toml (hidden)
    wrknv_hidden = project_dir / ".wrknv.toml"
    if wrknv_hidden.exists():
        config = _load_from_wrknv(wrknv_hidden)
        if config:
            logger.debug(f"Loaded security config from {wrknv_hidden}")
            return config

    logger.debug("No security configuration found")
    return None


def _load_from_pyproject(path: Path) -> SecurityConfig | None:
    """Load security config from pyproject.toml [tool.security].

    Args:
        path: Path to pyproject.toml

    Returns:
        SecurityConfig if found, None otherwise
    """
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)

        security_data = data.get("tool", {}).get("security", {})
        if not security_data:
            return None

        return SecurityConfig(
            description=security_data.get("description", "Allowlisted paths for secret scanning"),
            allowed_paths=security_data.get("allowed_paths", []),
        )
    except (OSError, tomllib.TOMLDecodeError) as e:
        logger.warning(f"Failed to load {path}: {e}")
        return None


def _load_from_wrknv(path: Path) -> SecurityConfig | None:
    """Load security config from wrknv.toml [security].

    Args:
        path: Path to wrknv.toml

    Returns:
        SecurityConfig if found, None otherwise
    """
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)

        security_data = data.get("security", {})
        if not security_data:
            return None

        return SecurityConfig(
            description=security_data.get("description", "Allowlisted paths for secret scanning"),
            allowed_paths=security_data.get("allowed_paths", []),
        )
    except (OSError, tomllib.TOMLDecodeError) as e:
        logger.warning(f"Failed to load {path}: {e}")
        return None


# 🧰🌍🔚
