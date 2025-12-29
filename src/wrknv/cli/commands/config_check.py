#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Config Check Commands
=====================
Commands for validating pyproject.toml configuration standardization."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Annotated

from provide.foundation.cli import echo_error, echo_info, echo_success, echo_warning
from provide.foundation.hub import register_command

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found]

# --- Canonical Configuration Standards ---

CANONICAL_RUFF = {
    "line-length": 111,
    "indent-width": 4,
    "target-version": "py311",
}

CANONICAL_RUFF_LINT_SELECT = ["E", "F", "W", "I", "UP", "ANN", "B", "C90", "SIM", "PTH", "RUF"]
CANONICAL_RUFF_LINT_IGNORE = ["ANN401", "B008", "E501"]

CANONICAL_RUFF_FORMAT = {
    "quote-style": "double",
    "indent-style": "space",
    "skip-magic-trailing-comma": False,
    "line-ending": "auto",
}

CANONICAL_MYPY = {
    "python_version": "3.11",
    "strict": True,
    "pretty": True,
    "show_error_codes": True,
    "show_column_numbers": True,
    "warn_unused_ignores": True,
    "warn_unused_configs": True,
}

REQUIRED_PYTEST_SETTINGS = {
    "log_cli": True,
    "testpaths": ["tests"],
    "python_files": ["test_*.py", "*_test.py"],
}


def _check_ruff_config(config: dict) -> list[str]:
    """Validate ruff configuration matches canonical standards."""
    errors = []
    ruff = config.get("tool", {}).get("ruff", {})

    for key, expected_value in CANONICAL_RUFF.items():
        actual_value = ruff.get(key)
        if actual_value != expected_value:
            errors.append(f"[tool.ruff] {key} should be {expected_value!r}, got {actual_value!r}")

    lint = ruff.get("lint", {})
    select = lint.get("select", [])
    if set(select) != set(CANONICAL_RUFF_LINT_SELECT):
        errors.append(f"[tool.ruff.lint] select should be {CANONICAL_RUFF_LINT_SELECT}, got {select}")

    ignore = lint.get("ignore", [])
    if set(ignore) != set(CANONICAL_RUFF_LINT_IGNORE):
        errors.append(f"[tool.ruff.lint] ignore should be {CANONICAL_RUFF_LINT_IGNORE}, got {ignore}")

    fmt = ruff.get("format", {})
    for key, expected_value in CANONICAL_RUFF_FORMAT.items():
        actual_value = fmt.get(key)
        if actual_value != expected_value:
            errors.append(f"[tool.ruff.format] {key} should be {expected_value!r}, got {actual_value!r}")

    return errors


def _check_mypy_config(config: dict) -> list[str]:
    """Validate mypy configuration matches canonical standards."""
    errors = []
    mypy = config.get("tool", {}).get("mypy", {})

    for key, expected_value in CANONICAL_MYPY.items():
        actual_value = mypy.get(key)
        if actual_value != expected_value:
            errors.append(f"[tool.mypy] {key} should be {expected_value!r}, got {actual_value!r}")

    return errors


def _check_pytest_config(config: dict) -> list[str]:
    """Validate pytest configuration has required settings."""
    errors = []
    pytest = config.get("tool", {}).get("pytest", {}).get("ini_options", {})

    for key, expected_value in REQUIRED_PYTEST_SETTINGS.items():
        actual_value = pytest.get(key)
        if actual_value != expected_value:
            errors.append(
                f"[tool.pytest.ini_options] {key} should be {expected_value!r}, got {actual_value!r}"
            )

    return errors


def _check_project_metadata(config: dict) -> list[str]:
    """Validate project metadata has required fields."""
    warnings = []
    project = config.get("project", {})

    license_val = project.get("license")
    if license_val != "Apache-2.0":
        warnings.append(f"[project] license should be 'Apache-2.0', got {license_val!r}")

    requires_python = project.get("requires-python", "")
    if not requires_python.startswith(">=3.11"):
        warnings.append(f"[project] requires-python should be '>=3.11', got {requires_python!r}")

    return warnings


def _validate_pyproject(filepath: Path) -> tuple[list[str], list[str]]:
    """Validate a pyproject.toml file."""
    try:
        with filepath.open("rb") as f:
            config = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        return ([f"Failed to parse {filepath}: {e}"], [])

    errors = []
    warnings = []

    errors.extend(_check_ruff_config(config))
    errors.extend(_check_mypy_config(config))
    errors.extend(_check_pytest_config(config))
    warnings.extend(_check_project_metadata(config))

    return errors, warnings


@register_command("config-check", description="Validate pyproject.toml configuration standardization")
def config_check_command(
    files: Annotated[tuple[str, ...], "argument"] = (),
    strict: bool = False,
) -> None:
    """Validate pyproject.toml configuration matches provide.io standards.

    Checks that ruff, mypy, and pytest configurations match the canonical
    standards for the provide.io ecosystem.

    Args:
        files: pyproject.toml files to check. If not provided, checks ./pyproject.toml
        strict: Treat warnings as errors
    """
    # Collect files to check
    if files:
        filepaths = [Path(f) for f in files]
    else:
        pyproject = Path.cwd() / "pyproject.toml"
        if pyproject.exists():
            filepaths = [pyproject]
        else:
            echo_error("No pyproject.toml found in current directory")
            sys.exit(1)

    all_valid = True

    for filepath in filepaths:
        if filepath.name != "pyproject.toml":
            continue

        if not filepath.exists():
            echo_error(f"File not found: {filepath}")
            all_valid = False
            continue

        echo_info(f"\nChecking {filepath}...")
        errors, warnings = _validate_pyproject(filepath)

        if errors:
            echo_error(f"\n{len(errors)} error(s) found:")
            for error in errors:
                echo_error(f"  - {error}")
            all_valid = False
            continue

        if warnings:
            echo_warning(f"\n{len(warnings)} warning(s):")
            for warning in warnings:
                echo_warning(f"  - {warning}")
            if strict:
                all_valid = False
                continue

        if not errors and (not warnings or not strict):
            echo_success("Configuration valid")

    if not all_valid:
        sys.exit(1)


# 🔧🌍🔚
