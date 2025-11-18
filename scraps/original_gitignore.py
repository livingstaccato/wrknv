#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Gitignore Commands
==================
Commands for managing .gitignore files."""

import sys
from pathlib import Path

from provide.foundation.cli import echo_error, echo_info, echo_success, echo_warning
from provide.foundation.hub import register_command
from wrknv.wenv.config import WorkenvConfig

from wrknv.gitignore import GitignoreManager, ProjectDetector


@register_command(
    "gitignore-list",
    description="List available gitignore templates",
    category="gitignore",
)
def gitignore_list(category: str | None = None) -> None:
    """List available gitignore templates."""
    manager = GitignoreManager()
    templates = manager.list_available_templates(category=category)

    if not templates:
        echo_info("No templates found")
        return

    if category:
        echo_info(f"Templates in category '{category}':")
    else:
        echo_info("Available templates:")

    for template in templates:
        echo_info(f"  • {template}")

    echo_info(f"\nTotal: {len(templates)} templates")


@register_command(
    "gitignore-search",
    description="Search for gitignore templates",
    category="gitignore",
)
def gitignore_search(pattern: str) -> None:
    """Search for gitignore templates matching a pattern."""
    manager = GitignoreManager()
    results = manager.search_templates(pattern)

    if not results:
        echo_info(f"No templates found matching '{pattern}'")
        return

    echo_info(f"Templates matching '{pattern}':")
    for template in results:
        echo_info(f"  • {template}")

    echo_info(f"\nFound: {len(results)} templates")


@register_command(
    "gitignore-detect",
    description="Detect project types and suggest templates",
    category="gitignore",
)
def gitignore_detect(path: str | None = None) -> None:
    """Detect project types and suggest appropriate gitignore templates."""
    target_path = Path(path) if path else Path.cwd()

    if not target_path.exists():
        echo_error(f"Path does not exist: {target_path}")
        sys.exit(1)

    detector = ProjectDetector()
    detected = detector.detect_project_types(target_path)

    if not detected:
        echo_info("No specific project types detected")
        echo_info("Consider using 'Global' template for general patterns")
        return

    echo_info("Detected project types:")
    for project_type in detected:
        echo_info(f"  • {project_type}")

    echo_info("\nSuggested templates:")
    manager = GitignoreManager()
    for project_type in detected:
        if manager.template_exists(project_type):
            echo_success(f"  ✓ {project_type}")
        else:
            # Try to find similar templates
            similar = manager.search_templates(project_type)
            if similar:
                echo_warning(f"  ? {project_type} → {', '.join(similar[:3])}")
            else:
                echo_warning(f"  ? {project_type} (no template found)")


@register_command(
    "gitignore-build",
    description="Build a .gitignore file from templates",
    category="gitignore",
)
def gitignore_build(
    templates: list[str] | None = None,
    output: str | None = None,
    append: bool = False,
    auto_detect: bool = False,
) -> None:
    """Build a .gitignore file from templates."""
    config = WorkenvConfig()
    manager = GitignoreManager(config)

    # Determine templates to use
    template_list = []

    if auto_detect:
        detector = ProjectDetector()
        detected = detector.detect_project_types(Path.cwd())
        if detected:
            template_list.extend(detected)
            echo_info(f"Auto-detected: {', '.join(detected)}")

    if templates:
        template_list.extend(templates)

    if not template_list:
        # Try to get from config
        gitignore_config = config.get_setting("gitignore", {})
        template_list = gitignore_config.get("templates", [])

    if not template_list:
        echo_warning("No gitignore templates specified in config or via --templates.")
        echo_info("Use --templates or configure in wrknv.toml")
        sys.exit(0)

    # Build gitignore content
    try:
        builder = manager.create_builder()

        # Add templates
        for template_name in template_list:
            added = builder.add_template(template_name)
            if added:
                echo_success(f"  ✓ Added template: {template_name}")
            else:
                echo_warning(f"  ? Template not found: {template_name}")

        # Build the content
        content = builder.build()

        if not content:
            echo_error("No content generated")
            sys.exit(1)

        # Write to output
        output_path = Path(output) if output else Path(".gitignore")

        if append and output_path.exists():
            existing = output_path.read_text()
            content = existing + "\n" + content

        output_path.write_text(content)

    except Exception as e:
        echo_error(f"Failed to build .gitignore: {e}")
        sys.exit(1)


@register_command(
    "gitignore-show",
    description="Show content of a gitignore template",
    category="gitignore",
)
def gitignore_show(template: str) -> None:
    """Show the content of a specific gitignore template."""
    manager = GitignoreManager()

    content = manager.get_template_content(template)

    if content:
        echo_info(f"# Template: {template}")
        echo_info(content)
    else:
        echo_error(f"Template not found: {template}")

        # Suggest similar templates
        similar = manager.search_templates(template)
        if similar:
            echo_info(f"Did you mean: {', '.join(similar[:3])}?")
        sys.exit(1)


@register_command(
    "gitignore-update",
    description="Update gitignore template cache",
    category="gitignore",
)
def gitignore_update() -> None:
    """Update the local gitignore template cache from GitHub."""
    manager = GitignoreManager()

    echo_info("Updating gitignore templates from GitHub...")

    try:
        count = manager.update_templates()
    except Exception as e:
        echo_error(f"Failed to update templates: {e}")
        sys.exit(1)

# 🧰🌍🔚
