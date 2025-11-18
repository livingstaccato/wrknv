#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Secret Management Commands
===========================
Commands for managing secret management tools (OpenBao, IBM Vault)."""

from __future__ import annotations

import sys
from typing import Annotated

from provide.foundation.cli import echo_error, echo_info
from provide.foundation.hub import register_command

from wrknv.cli.hub_cli import WrknvContext
from wrknv.managers.factory import get_tool_manager


@register_command("secrets", description="Manage secret management tools (Bao, Vault)", category="tools")
def secrets_command(
    variant_or_version: Annotated[str, "argument"] = "",
    version: Annotated[str, "argument"] = "",
    list: bool = False,
    list_variants: bool = False,
    dry_run: bool = False,
) -> None:
    """Manage secret management tools (OpenBao, IBM Vault).

    Switch to a specific variant and version of secret management tools.
    This command will install the version if needed and activate it in your workenv.

    Examples:
        wrknv secrets bao 2.1.0      # Switch to OpenBao 2.1.0
        wrknv secrets vault 1.15.0   # Switch to IBM Vault 1.15.0
        wrknv secrets 2.1.0          # Switch to default variant (from config)
        wrknv secrets --list-variants
        wrknv secrets bao --list     # List available Bao versions

    Args:
        variant_or_version: Variant name (bao/vault) or version if using default
        version: Version to switch to (if first arg was variant)
        list: List available versions
        list_variants: List available variants
        dry_run: Show what would be done without doing it
    """
    config = WrknvContext.get_config()

    if list_variants:
        echo_info("🔐 Available secret management variants:")
        echo_info("  • bao    - OpenBao (open source Vault fork)")
        echo_info("  • vault  - IBM Vault (HashiCorp Vault)")
        return

    # Get default variant for list/install operations
    default_variant = config.get_setting("tools.secrets.default_variant", "bao")

    # Smart parsing: determine variant and version
    if not variant_or_version or variant_or_version == "":
        # No args: only valid with --list or --list-variants
        if not list and not list_variants:
            echo_error("Error: Version required. Use 'wrknv secrets --list' to see available versions.")
            sys.exit(1)
        actual_variant = default_variant
        actual_version = ""
    elif not version or version == "":
        # Single arg: use default variant from config
        actual_variant = default_variant
        actual_version = variant_or_version

        if not list and not list_variants:
            echo_info(f"Using default variant: {actual_variant}")
    else:
        # Two args: explicit variant specified
        actual_variant = variant_or_version
        actual_version = version

    # Map variant to manager name
    variant_map = {
        "bao": "bao",
        "vault": "vault",
        "ibm": "vault",  # Alias for convenience
    }

    manager_name = variant_map.get(actual_variant.lower())
    if not manager_name:
        echo_error(f"Unknown secrets variant: {actual_variant}")
        echo_info("Available variants: bao, vault")
        sys.exit(1)

    # Variant display names
    variant_display = {
        "bao": "OpenBao",
        "vault": "IBM Vault",
    }
    display_name = variant_display.get(manager_name, manager_name)

    if list:
        # List available versions for this variant
        try:
            manager = get_tool_manager(manager_name, config)
            echo_info(f"🔐 Available {display_name} versions:")
            versions = manager.get_available_versions()
            for v in versions[:20]:  # Show first 20
                echo_info(f"  • {v}")
            if len(versions) > 20:
                echo_info(f"  ... and {len(versions) - 20} more")
            echo_info(f"\nTotal: {len(versions)} versions available")
        except Exception as e:
            echo_error(f"Error listing versions: {e}")
            sys.exit(1)
        return

    # Switch to the specified version
    try:
        manager = get_tool_manager(manager_name, config)

        if dry_run:
            echo_info(f"[DRY-RUN] Would switch to {display_name} {actual_version}")
        else:
            echo_info(
                f"🔐 Switching to {display_name} {actual_version}...",
            )

        manager.switch_version(actual_version, dry_run=dry_run)

        if not dry_run:
            echo_info("💡 Run 'source env.sh' to activate in current shell")
            echo_info("💡 Or restart your terminal")
    except Exception as e:
        echo_error(f"Error: {e}")
        import traceback

        echo_error(traceback.format_exc())
        sys.exit(1)


# 🧰🌍🔚
