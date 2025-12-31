#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Check Commands
==============
Commands for validating provide.io standards compliance."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

from provide.foundation.cli import echo_error, echo_info, echo_success, echo_warning
from provide.foundation.hub import register_command
from provide.foundation.process import run as process_run

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found]


# =============================================================================
# Check Group
# =============================================================================


@register_command("check", group=True, description="Validate provide.io standards compliance")
def check_group() -> None:
    """Check commands for validating standards compliance."""


# =============================================================================
# SPDX Command (headers + footers)
# =============================================================================

HEADER_SHEBANG = "#!/usr/bin/env python3"
HEADER_LIBRARY = "# "
SPDX_BLOCK = [
    "# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.",
    "# SPDX-License-Identifier: Apache-2.0",
    "#",
]
PLACEHOLDER_DOCSTRING = '"""TODO: Add module docstring."""'

FOOTER_EMOJIS = [
    "\U0001f3d7\ufe0f",
    "\U0001f40d",
    "\U0001f9f1",
    "\U0001f41d",
    "\U0001f4c1",
    "\U0001f37d\ufe0f",
    "\U0001f4d6",
    "\U0001f9ea",
    "\u2705",
    "\U0001f9e9",
    "\U0001f527",
    "\U0001f30a",
    "\U0001faa2",
    "\U0001f50c",
    "\U0001f4de",
    "\U0001f4c4",
    "\u2699\ufe0f",
    "\U0001f963",
    "\U0001f52c",
    "\U0001f53c",
    "\U0001f336\ufe0f",
    "\U0001f4e6",
    "\U0001f9f0",
    "\U0001f30d",
    "\U0001fa84",
    "\U0001f51a",
]


def _detect_repo_name() -> str:
    """Auto-detect repository name from git remote or directory name."""
    try:
        result = process_run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5.0,
        )
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            repo_name = remote_url.rstrip("/").split("/")[-1]
            repo_name = repo_name.removesuffix(".git")
            if repo_name:
                return repo_name
    except Exception:
        pass
    return Path.cwd().name


def _load_footer_registry() -> dict[str, str]:
    """Load the footer registry from JSON file."""
    registry_path = Path(__file__).parent.parent.parent / "data" / "footer_registry.json"
    try:
        with registry_path.open() as f:
            data = json.load(f)
            return data.get("repositories", {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        echo_error(f"Warning: Could not load footer registry: {e}")
        return {}


def _get_footer_for_current_repo() -> str:
    """Get the correct footer pattern for the current repository."""
    repo_name = _detect_repo_name()
    registry = _load_footer_registry()
    return registry.get(repo_name, "# \U0001f51a")


def _find_module_docstring_and_body_start(content: str) -> tuple[str | None, int]:
    """Parse Python source to find module docstring and code body start."""
    try:
        tree = ast.parse(content)
        docstring = ast.get_docstring(tree)

        if not tree.body:
            return docstring, len(content.splitlines()) + 1

        first_node = tree.body[0]
        start_lineno = first_node.lineno

        if (
            isinstance(first_node, ast.Expr)
            and isinstance(first_node.value, ast.Constant)
            and isinstance(first_node.value.value, str)
        ):
            start_lineno = tree.body[1].lineno if len(tree.body) > 1 else len(content.splitlines()) + 1

        return docstring, start_lineno
    except SyntaxError:
        return None, 1


def _clean_header_lines(lines: list[str]) -> list[str]:
    """Remove shebang, SPDX headers, and placeholder docstrings from lines."""
    cleaned_lines = []
    skip_next_empty = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("#!"):
            skip_next_empty = True
            continue

        if stripped.startswith("# SPDX-") or stripped == "#":
            skip_next_empty = True
            continue

        if stripped == '"""TODO: Add module docstring."""':
            skip_next_empty = True
            continue

        if skip_next_empty and stripped == "":
            skip_next_empty = False
            continue

        skip_next_empty = False
        cleaned_lines.append(line)

    return cleaned_lines


def _remove_footer_emojis(body_content: str) -> str:
    """Remove lines containing footer emojis from body content."""
    body_lines_stripped = body_content.splitlines()
    cleaned_body_lines = []
    for line in body_lines_stripped:
        has_footer_emoji = any(emoji in line for emoji in FOOTER_EMOJIS)
        if not has_footer_emoji:
            cleaned_body_lines.append(line)
    return "\n".join(cleaned_body_lines).rstrip()


def _construct_file_content(header_first_line: str, docstring_str: str, body_content: str, footer: str) -> str:
    """Construct the final file content with header, docstring, body, and footer."""
    final_header = "\n".join([header_first_line, *SPDX_BLOCK])

    if body_content:
        return f"{final_header}\n\n{docstring_str}\n\n{body_content}\n\n{footer}\n"
    return f"{final_header}\n\n{docstring_str}\n\n{footer}\n"


def _conform_file(filepath: Path, footer: str) -> bool:
    """Apply header and footer conformance to a single Python file."""
    try:
        content = filepath.read_text(encoding="utf-8")
        original_content = content
        lines = content.splitlines(keepends=True)
    except (OSError, UnicodeDecodeError) as e:
        echo_error(f"Error reading {filepath}: {e}")
        return False

    if not lines:
        final_content = (
            "\n".join([HEADER_LIBRARY, *SPDX_BLOCK]) + "\n\n" + PLACEHOLDER_DOCSTRING + "\n\n" + footer + "\n"
        )
        filepath.write_text(final_content, encoding="utf-8")
        return True

    is_executable = lines[0].strip().startswith("#!")
    header_first_line = HEADER_SHEBANG if is_executable else HEADER_LIBRARY

    cleaned_lines = _clean_header_lines(lines)
    cleaned_content = "".join(cleaned_lines)

    docstring, body_start_lineno = _find_module_docstring_and_body_start(cleaned_content)
    docstring_str = PLACEHOLDER_DOCSTRING if docstring is None else f'"""{docstring}"""'

    cleaned_lines_list = cleaned_content.splitlines(keepends=True)
    body_lines = cleaned_lines_list[body_start_lineno - 1 :]
    body_content = "".join(body_lines).rstrip()

    body_content = _remove_footer_emojis(body_content)

    final_content = _construct_file_content(header_first_line, docstring_str, body_content, footer)

    try:
        if final_content != original_content:
            filepath.write_text(final_content, encoding="utf-8")
            return True
        return False
    except OSError as e:
        echo_error(f"Error writing {filepath}: {e}")
        return False


@register_command("check.spdx", description="Validate SPDX headers and emoji footers")
def check_spdx_command(
    pattern: str | None = None,
    footer: str | None = None,
    fix: bool = False,
) -> None:
    """Validate SPDX headers and emoji footers on Python files.

    Args:
        pattern: Glob pattern for files (e.g., "src/**/*.py"). Defaults to src and tests directories.
        footer: Override footer pattern (auto-detects from repository by default)
        fix: Fix files instead of just checking
    """
    if footer:
        effective_footer = footer
    else:
        effective_footer = _get_footer_for_current_repo()
        repo_name = _detect_repo_name()
        echo_info(f"Auto-detected repository: {repo_name}")
        echo_info(f"Using footer: {effective_footer}")

    if pattern:
        filepaths = list(Path.cwd().glob(pattern))
    else:
        filepaths = []
        for default_pattern in ["src/**/*.py", "tests/**/*.py"]:
            filepaths.extend(Path.cwd().glob(default_pattern))

    if not filepaths:
        echo_info("No Python files found to process")
        return

    modified_count = 0
    error_count = 0

    for filepath in filepaths:
        if not filepath.exists():
            echo_error(f"File not found: {filepath}")
            error_count += 1
            continue

        if filepath.suffix != ".py":
            continue

        try:
            if fix:
                was_modified = _conform_file(filepath, effective_footer)
                if was_modified:
                    echo_success(f"Fixed: {filepath}")
                    modified_count += 1
                else:
                    echo_info(f"  OK: {filepath}")
            else:
                content = filepath.read_text(encoding="utf-8")
                lines = content.splitlines(keepends=True)
                if not lines:
                    echo_info(f"Would fix: {filepath}")
                    modified_count += 1
                    continue

                is_executable = lines[0].strip().startswith("#!")
                header_first_line = HEADER_SHEBANG if is_executable else HEADER_LIBRARY
                cleaned_lines = _clean_header_lines(lines)
                cleaned_content = "".join(cleaned_lines)
                docstring, body_start_lineno = _find_module_docstring_and_body_start(cleaned_content)
                docstring_str = PLACEHOLDER_DOCSTRING if docstring is None else f'"""{docstring}"""'
                cleaned_lines_list = cleaned_content.splitlines(keepends=True)
                body_lines = cleaned_lines_list[body_start_lineno - 1 :]
                body_content = "".join(body_lines).rstrip()
                body_content = _remove_footer_emojis(body_content)
                final_content = _construct_file_content(
                    header_first_line, docstring_str, body_content, effective_footer
                )

                if final_content != content:
                    echo_error(f"Needs fix: {filepath}")
                    modified_count += 1
                else:
                    echo_info(f"  OK: {filepath}")
        except Exception as e:
            echo_error(f"Error processing {filepath}: {e}")
            error_count += 1

    if error_count > 0:
        echo_error(f"\n{error_count} error(s) occurred")
        sys.exit(1)

    if modified_count > 0:
        if fix:
            echo_success(f"\n{modified_count} file(s) fixed")
        else:
            echo_error(f"\n{modified_count} file(s) need fixes (use --fix to apply)")
            sys.exit(1)
    else:
        echo_success("\nAll files conform to SPDX standards")


# =============================================================================
# Pyproject Command
# =============================================================================

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


@register_command("check.pyproject", description="Validate pyproject.toml against provide.io standards")
def check_pyproject_command(
    path: str | None = None,
    strict: bool = False,
) -> None:
    """Validate pyproject.toml configuration matches provide.io standards.

    Args:
        path: Path to pyproject.toml. Defaults to ./pyproject.toml
        strict: Treat warnings as errors
    """
    if path:
        filepaths = [Path(path)]
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
