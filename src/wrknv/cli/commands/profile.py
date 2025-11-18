#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Profile Commands
================
Commands for managing workenv profiles."""

from __future__ import annotations

from pathlib import Path
import sys

from provide.foundation import logger
from provide.foundation.cli import echo_error, echo_info, echo_success, echo_warning
from provide.foundation.hub import register_command

from wrknv.cli.hub_cli import WrknvContext
from wrknv.managers.factory import get_tool_manager


# Register the profile group first
@register_command("profile", group=True, description="Manage tool version profiles")
def profile_group() -> None:
    """Commands for managing profiles."""
    pass


@register_command(
    "profile.list",
    description="List available profiles",
)
def profile_list() -> None:
    """List available profiles."""
    config = WrknvContext.get_config()
    profiles = config.list_profiles()

    if profiles:
        echo_info("Available profiles:")
        for name in profiles:
            if name == config.get_current_profile():
                echo_info(f"  * {name} (active)")
            else:
                echo_info(f"    {name}")
    else:
        echo_info("No profiles found")


@register_command(
    "profile.save",
    description="Save current tool versions as a profile",
)
def profile_save(name: str, force: bool = False) -> None:
    """Save current tool versions as a profile."""
    config = WrknvContext.get_config()

    if config.profile_exists(name) and not force:
        echo_warning(f"Profile '{name}' already exists")
        echo_info("Use --force to overwrite")
        sys.exit(1)

    # Get current tool versions
    tools = config.get_all_tools()

    if not tools:
        echo_warning("No tools configured to save")
        sys.exit(1)

    # Save profile
    config.save_profile(name, tools)
    echo_success(f"Saved profile '{name}'")


@register_command(
    "profile.load",
    description="Load and apply a profile",
)
def profile_load(name: str) -> None:
    """Load and apply a profile."""
    config = WrknvContext.get_config()

    profile_data = config.get_profile(name)
    if not profile_data:
        echo_error(f"Profile '{name}' not found")
        available = config.list_profiles()
        if available:
            echo_info(f"Available profiles: {', '.join(available)}")
        sys.exit(1)

    echo_info(f"Loading profile '{name}'...")

    failed_tools = []
    for tool_name, version in profile_data.items():
        try:
            manager = get_tool_manager(tool_name, config)
            manager.install_version(version)
            echo_success(f"Successfully installed {tool_name} {version}")
        except Exception as e:
            logger.error(f"Failed to install {tool_name} {version}: {e}")
            failed_tools.append((tool_name, version, str(e)))
            echo_error(f"❌ Error installing {tool_name} {version}: {e}")

    if failed_tools:
        echo_warning(f"Failed to install {len(failed_tools)} tools")
        for tool, version, error in failed_tools:
            echo_error(f"  - {tool} {version}: {error}")
    else:
        echo_success("✅ All tools installed successfully")


@register_command(
    "profile.delete",
    description="Delete a profile",
)
def profile_delete(name: str) -> None:
    """Delete a profile."""
    config = WrknvContext.get_config()

    if not config.profile_exists(name):
        echo_error(f"Profile '{name}' not found")
        sys.exit(1)

    # Confirm deletion
    response = input(f"Delete profile '{name}'? [y/N]: ").strip().lower()
    if response != "y":
        echo_info("Cancelled")
        sys.exit(0)

    config.delete_profile(name)
    echo_success(f"Profile '{name}' deleted")


@register_command(
    "profile.show",
    description="Show profile details",
)
def profile_show(name: str) -> None:
    """Show profile details."""
    config = WrknvContext.get_config()

    profile_data = config.get_profile(name)
    if not profile_data:
        echo_error(f"Profile '{name}' not found")
        sys.exit(1)

    echo_info(f"Profile: {name}")
    for tool_name, version in profile_data.items():
        echo_info(f"  {tool_name}: {version}")


@register_command(
    "profile.export",
    description="Export a profile to a file",
)
def profile_export(name: str, output: str) -> None:
    """Export a profile to a file."""
    import json

    from provide.foundation.file.formats import toml_dumps

    config = WrknvContext.get_config()

    profile_data = config.get_profile(name)
    if not profile_data:
        echo_error(f"Profile '{name}' not found")
        sys.exit(1)

    output_path = Path(output)

    # Determine format from extension
    if output_path.suffix == ".json":
        output_path.write_text(json.dumps({"name": name, "tools": profile_data}, indent=2))
    else:
        # Default to TOML
        output_path.write_text(toml_dumps({"name": name, "tools": profile_data}))

    echo_success(f"Exported profile '{name}' to {output_path}")


@register_command(
    "profile.import",
    description="Import a profile from a file",
)
def profile_import(file: str) -> None:
    """Import a profile from a file."""
    import json

    from provide.foundation.file.formats import toml_loads

    file_path = Path(file)

    if not file_path.exists():
        echo_error(f"File not found: {file_path}")
        sys.exit(1)

    try:
        content = file_path.read_text()

        # Try to parse as JSON first
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try TOML
            data = toml_loads(content)

        name = data.get("name")
        tools = data.get("tools")

        if not name or not tools:
            echo_error("Invalid profile format: missing 'name' or 'tools'")
            sys.exit(1)

        config = WrknvContext.get_config()
        config.save_profile(name, tools)
        echo_success(f"Imported profile '{name}'")

    except Exception as e:
        echo_error(f"Failed to import profile: {e}")
        sys.exit(1)


# 🧰🌍🔚
