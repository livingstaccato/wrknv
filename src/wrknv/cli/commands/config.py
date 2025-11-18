#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Config Commands
===============
Commands for managing workenv configuration."""

from __future__ import annotations

import json
import sys
from typing import Any

from provide.foundation.cli import echo_error, echo_info, echo_success, echo_warning
from provide.foundation.console.output import pout
from provide.foundation.hub import register_command

from wrknv.cli.hub_cli import WrknvContext
from wrknv.errors import ProfileError


# Register the config group first
@register_command("config", group=True, description="Configuration management")
def config_group() -> None:
    """Configuration management commands."""
    pass


@register_command(
    "config.show",
    description="Show current configuration",
)
def config_show(
    output_json: bool = False,
    profile: str | None = None,
) -> None:
    """Show current configuration."""
    config = WrknvContext.get_config()

    if profile:
        # Show specific profile
        profile_data = config.get_profile(profile)
        if not profile_data:
            raise ProfileError(profile, available_profiles=config.list_profiles())

        if output_json:
            pout(json.dumps({"profile": profile, "tools": profile_data}, indent=2))
        else:
            echo_info(f"Profile: {profile}")
            for tool_name, version in profile_data.items():
                echo_info(f"  {tool_name}: {version}")
    elif output_json:
        # Output entire config as JSON
        config_data = config.to_dict()
        pout(json.dumps(config_data, indent=2))
    else:
        # Default formatted output
        config.show_config()


@register_command(
    "config.edit",
    description="Edit configuration file",
)
def config_edit() -> None:
    """Edit configuration file."""
    config = WrknvContext.get_config()
    try:
        config.edit_config()
    except RuntimeError as e:
        echo_error(f"Failed to edit config: {e}")
        sys.exit(1)


@register_command(
    "config.validate",
    description="Validate configuration file syntax and values",
)
def config_validate(strict: bool = False, verbose: bool = False) -> None:
    """Validate configuration file syntax and values."""
    try:
        config = WrknvContext.get_config()

        if not config.config_exists():
            echo_error("No configuration file found")
            echo_info("Create one with: wrknv config init")
            sys.exit(1)

        # Perform validation
        is_valid, errors = config.validate()

        if verbose:
            echo_info(f"📋 Validating configuration: {config.config_path}")
            echo_info("   Checking project metadata...")
            echo_info("   Checking tool configurations...")
            echo_info("   Checking profile configurations...")
            echo_info("   Checking workenv settings...")
            echo_info("   Checking environment variables...")

        if is_valid:
            if verbose:
                echo_info("   All checks passed")
            echo_success("✓ Configuration is valid")
        else:
            echo_error("❌ Configuration validation failed:")
            for error in errors:
                echo_error(f"  • {error}")

            if not strict:
                echo_warning("\n💡 These are validation warnings. Use --strict to fail on validation errors.")
                echo_info("   Fix these issues to ensure reliable operation.")
            else:
                sys.exit(1)

    except Exception as e:
        echo_error(f"Validation error: {e}")
        if verbose:
            import traceback

            echo_error(f"   Traceback: {traceback.format_exc()}")
        sys.exit(1)


@register_command(
    "config.init",
    description="Initialize a new configuration file interactively",
)
def config_init(force: bool = False) -> None:
    """Initialize a new configuration file interactively."""
    config = WrknvContext.get_config()

    if config.config_exists() and not force:
        echo_warning("Configuration file already exists")
        echo_info("Use --force to overwrite")
        sys.exit(1)

    try:
        # Interactive initialization
        echo_info("Creating new wrknv configuration...")

        # Prompt for basic settings
        project_name_input = input("Project name (leave empty to skip): ").strip()
        version_input = input("Version (leave empty to skip): ").strip()

        # Create default config structure
        config_data: dict[str, Any] = {
            "workenv": {
                "auto_install": True,
                "use_cache": True,
                "cache_ttl": "7d",
            },
            "tools": {},
            "profiles": {},
        }

        # Only add project metadata if provided
        if project_name_input:
            config_data["project_name"] = project_name_input
        if version_input:
            config_data["version"] = version_input

        # Write configuration
        config.write_config(config_data)

        echo_success(f"✓ Configuration created at {config.config_path}")

    except Exception as e:
        echo_error(f"Failed to create configuration: {e}")
        sys.exit(1)


@register_command(
    "config.path",
    description="Show path to configuration file",
)
def config_path() -> None:
    """Show path to configuration file."""
    config = WrknvContext.get_config()
    if config.config_exists():
        echo_info(str(config.config_path))
    else:
        echo_warning("No configuration file found")
        echo_info("Create one with: wrknv config init")


@register_command(
    "config.get",
    description="Get a specific configuration setting",
)
def config_get(key: str) -> None:
    """Get a specific configuration setting."""
    config = WrknvContext.get_config()

    try:
        value = config.get_setting(key)
        if value is not None:
            if isinstance(value, (dict, list)):
                echo_info(f"{key}: {json.dumps(value, indent=2)}")
            else:
                echo_info(f"{key}: {value}")
        else:
            echo_warning(f"Setting '{key}' not found")
    except Exception as e:
        echo_error(f"Error getting setting: {e}")
        sys.exit(1)


@register_command(
    "config.set",
    description="Set a configuration value",
)
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    config = WrknvContext.get_config()

    try:
        # Try to parse value as JSON first (for complex types)
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            # If not JSON, treat as string
            # Check for boolean strings
            if value.lower() in ("true", "yes", "on"):
                parsed_value = True
            elif value.lower() in ("false", "no", "off"):
                parsed_value = False
            else:
                parsed_value = value

        config.set_setting(key, parsed_value)
        echo_success(f"✓ Set {key} = {parsed_value}")
    except Exception as e:
        echo_error(f"Error setting value: {e}")
        sys.exit(1)


# 🧰🌍🔚
