#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Lock Commands
=============
Commands for managing wrknv.lock files."""

from __future__ import annotations

import sys

from provide.foundation.cli import echo_error, echo_info, echo_success, echo_warning
from provide.foundation.hub import register_command

from wrknv.cli.hub_cli import WrknvContext
from wrknv.lockfile import LockfileManager


# Register the lock group first
@register_command("lock", group=True, description="Manage version lockfiles")
def lock_group() -> None:
    """Commands for managing lockfiles."""
    pass


@register_command("lock.generate", description="Generate lockfile from current configuration")
def lock_generate(force: bool = False) -> None:
    """Generate lockfile from current configuration."""
    try:
        config = WrknvContext.get_config()
        lockfile_manager = LockfileManager()

        if lockfile_manager.lockfile_path.exists() and not force:
            echo_warning("Lockfile already exists. Use --force to overwrite.")
            echo_info(f"Existing lockfile: {lockfile_manager.lockfile_path}")
            sys.exit(1)

        echo_info("🔒 Generating lockfile from configuration...")
        lockfile_manager.resolve_and_lock(config)

    except Exception as e:
        echo_error(f"Failed to generate lockfile: {e}")
        sys.exit(1)


@register_command("lock.check", description="Check if lockfile is valid for current config")
def lock_check() -> None:
    """Check if lockfile is valid for current configuration."""
    try:
        config = WrknvContext.get_config()
        lockfile_manager = LockfileManager()

        if not lockfile_manager.lockfile_path.exists():
            echo_warning("No lockfile found")
            echo_info("Generate one with: wrknv lock generate")
            sys.exit(1)

        is_valid = lockfile_manager.is_lockfile_valid(config)

        if is_valid:
            echo_success("✅ Lockfile is valid and up to date")
        else:
            echo_error("❌ Lockfile is outdated or invalid")
            echo_info("Regenerate with: wrknv lock generate --force")
            sys.exit(1)

    except Exception as e:
        echo_error(f"Failed to check lockfile: {e}")
        sys.exit(1)


@register_command("lock.show", description="Show lockfile contents")
def lock_show() -> None:
    """Show lockfile contents."""
    try:
        lockfile_manager = LockfileManager()

        if not lockfile_manager.lockfile_path.exists():
            echo_warning("No lockfile found")
            echo_info("Generate one with: wrknv lock generate")
            return

        lockfile = lockfile_manager.load_lockfile()
        if not lockfile:
            echo_error("Failed to load lockfile (corrupted?)")
            return

        echo_info(f"🔐 Config checksum: {lockfile.config_checksum}")
        echo_info(f"📅 Created: {lockfile.created_at}")
        echo_info(f"🛠️  Tools: {len(lockfile.resolved_tools)}")

        if lockfile.resolved_tools:
            echo_info("\nResolved tools:")
            for tool in lockfile.resolved_tools.values():
                status = "🟢 installed" if tool.installed_at else "⚪ not installed"
                echo_info(f"  • {tool.name}: {tool.version} (from {tool.resolved_from}) - {status}")

    except Exception as e:
        echo_error(f"Failed to show lockfile: {e}")
        sys.exit(1)


@register_command("lock.clean", description="Remove lockfile")
def lock_clean() -> None:
    """Remove lockfile."""
    try:
        lockfile_manager = LockfileManager()

        if not lockfile_manager.lockfile_path.exists():
            echo_info("No lockfile to remove")
            return

        lockfile_manager.lockfile_path.unlink()

    except Exception as e:
        echo_error(f"Failed to remove lockfile: {e}")
        sys.exit(1)


@register_command("lock.sync", description="Install tools using locked versions")
def lock_sync() -> None:
    """Install tools using locked versions."""
    try:
        config = WrknvContext.get_config()
        lockfile_manager = LockfileManager()

        if not lockfile_manager.lockfile_path.exists():
            echo_error("No lockfile found")
            echo_info("Generate one with: wrknv lock generate")
            sys.exit(1)

        if not lockfile_manager.is_lockfile_valid(config):
            echo_error("Lockfile is outdated for current configuration")
            echo_info("Update with: wrknv lock generate --force")
            sys.exit(1)

        lockfile = lockfile_manager.load_lockfile()
        if not lockfile:
            echo_error("Failed to load lockfile")
            sys.exit(1)

        echo_info("🔒 Installing tools from lockfile...")

        from wrknv.managers.factory import get_tool_manager

        installed_count = 0
        for tool in lockfile.resolved_tools.values():
            try:
                # Skip matrix entries (they have @ in the name)
                if "@" in tool.name:
                    continue

                manager = get_tool_manager(tool.name, config)
                echo_info(f"Installing {tool.name} {tool.version}...")
                manager.install_version(tool.version, dry_run=False)
                installed_count += 1

            except Exception as e:
                echo_error(f"❌ Error installing {tool.name} {tool.version}: {e}")

    except Exception as e:
        echo_error(f"Failed to sync from lockfile: {e}")
        sys.exit(1)


# 🧰🌍🔚
