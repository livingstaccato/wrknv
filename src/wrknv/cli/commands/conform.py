#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Conform Commands
================
Commands for enforcing SPDX headers and footer conformance."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys

from provide.foundation.cli import echo_error, echo_info, echo_success
from provide.foundation.hub import register_command

# --- Protocol Constants ---

HEADER_SHEBANG = "#!/usr/bin/env python3"
HEADER_LIBRARY = "# "
SPDX_BLOCK = [
    "# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.",
    "# SPDX-License-Identifier: Apache-2.0",
    "#",
]
PLACEHOLDER_DOCSTRING = '"""TODO: Add module docstring."""'

# Footer emojis to detect and strip
FOOTER_EMOJIS = [
    "\U0001f3d7\ufe0f",  # construction
    "\U0001f40d",  # snake
    "\U0001f9f1",  # brick
    "\U0001f41d",  # bee
    "\U0001f4c1",  # folder
    "\U0001f37d\ufe0f",  # plate
    "\U0001f4d6",  # book
    "\U0001f9ea",  # test tube
    "\u2705",  # check
    "\U0001f9e9",  # puzzle
    "\U0001f527",  # wrench
    "\U0001f30a",  # wave
    "\U0001faa2",  # knot
    "\U0001f50c",  # plug
    "\U0001f4de",  # phone
    "\U0001f4c4",  # page
    "\u2699\ufe0f",  # gear
    "\U0001f963",  # bowl
    "\U0001f52c",  # microscope
    "\U0001f53c",  # up triangle
    "\U0001f336\ufe0f",  # pepper
    "\U0001f4e6",  # package
    "\U0001f9f0",  # toolbox
    "\U0001f30d",  # globe
    "\U0001fa84",  # wand
    "\U0001f51a",  # end
]


def _detect_repo_name() -> str:
    """Auto-detect repository name from git remote or directory name."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        remote_url = result.stdout.strip()
        repo_name = remote_url.rstrip("/").split("/")[-1]
        repo_name = repo_name.removesuffix(".git")
        if repo_name:
            return repo_name
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
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


@register_command("conform", description="Enforce SPDX headers and footer conformance on Python files")
def conform_command(
    pattern: str | None = None,
    footer: str | None = None,
    check: bool = False,
) -> None:
    """Enforce SPDX headers and footer conformance on Python files.

    Args:
        pattern: Glob pattern for files (e.g., "src/**/*.py"). Defaults to src and tests directories.
        footer: Override footer pattern (auto-detects from repository by default)
        check: Only check, don't modify files (exit 1 if changes needed)
    """
    # Get footer (auto-detect unless overridden)
    if footer:
        effective_footer = footer
    else:
        effective_footer = _get_footer_for_current_repo()
        repo_name = _detect_repo_name()
        echo_info(f"Auto-detected repository: {repo_name}")
        echo_info(f"Using footer: {effective_footer}")

    # Collect files to process
    if pattern:
        filepaths = list(Path.cwd().glob(pattern))
    else:
        filepaths = []
        for default_pattern in ["src/**/*.py", "tests/**/*.py"]:
            filepaths.extend(Path.cwd().glob(default_pattern))

    if not filepaths:
        echo_info("No Python files found to process")
        return

    # Process each file
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
            if check:
                # In check mode, read and compare without writing
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
                    echo_info(f"Would fix: {filepath}")
                    modified_count += 1
                else:
                    echo_info(f"  OK: {filepath}")
            else:
                was_modified = _conform_file(filepath, effective_footer)
                if was_modified:
                    echo_success(f"Fixed: {filepath}")
                    modified_count += 1
                else:
                    echo_info(f"  OK: {filepath}")
        except Exception as e:
            echo_error(f"Error processing {filepath}: {e}")
            error_count += 1

    # Summary
    if error_count > 0:
        echo_error(f"\n{error_count} error(s) occurred")
        sys.exit(1)

    if modified_count > 0:
        if check:
            echo_error(f"\n{modified_count} file(s) need conformance fixes")
            sys.exit(1)
        else:
            echo_success(f"\n{modified_count} file(s) fixed")
    else:
        echo_success("\nAll files conform to standards")


# 🔧🌍🔚
