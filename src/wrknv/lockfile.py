#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Lockfile Management
==================
Manage wrknv.lock files for reproducible environments."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from attrs import define, field

from wrknv.config import WorkenvConfig


@define
class ResolvedTool:
    """A resolved tool with exact version and metadata."""

    name: str
    version: str
    resolved_from: str  # Original pattern like "1.11.x"
    checksum: str | None = None
    installed_at: str | None = None  # ISO timestamp
    install_path: str | None = None


@define
class Lockfile:
    """Represents a wrknv.lock file."""

    config_checksum: str  # Hash of the config that generated this lock
    resolved_tools: dict[str, ResolvedTool] = field(factory=dict)
    created_at: str | None = None  # ISO timestamp
    wrknv_version: str = "0.3.0"

    @classmethod
    def from_config(cls, config: WorkenvConfig) -> Lockfile:
        """Create a lockfile from a config."""
        from provide.foundation.time import provide_now

        # Calculate config checksum
        config_dict = config.to_dict()
        config_str = str(sorted(config_dict.items()))
        config_checksum = hashlib.sha256(config_str.encode()).hexdigest()[:12]

        return cls(
            config_checksum=config_checksum,
            created_at=provide_now().isoformat(),
        )

    def add_resolved_tool(
        self,
        name: str,
        version: str,
        resolved_from: str,
        checksum: str | None = None,
        install_path: str | None = None,
    ) -> None:
        """Add a resolved tool to the lockfile."""
        from provide.foundation.time import provide_now

        self.resolved_tools[name] = ResolvedTool(
            name=name,
            version=version,
            resolved_from=resolved_from,
            checksum=checksum,
            installed_at=provide_now().isoformat(),
            install_path=install_path,
        )

    def get_resolved_version(self, tool_name: str) -> str | None:
        """Get the resolved version for a tool."""
        tool = self.resolved_tools.get(tool_name)
        return tool.version if tool else None

    def is_tool_installed(self, tool_name: str) -> bool:
        """Check if a tool is marked as installed."""
        tool = self.resolved_tools.get(tool_name)
        return tool is not None and tool.installed_at is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "config_checksum": self.config_checksum,
            "created_at": self.created_at,
            "wrknv_version": self.wrknv_version,
            "resolved_tools": {
                name: {
                    "name": tool.name,
                    "version": tool.version,
                    "resolved_from": tool.resolved_from,
                    "checksum": tool.checksum,
                    "installed_at": tool.installed_at,
                    "install_path": tool.install_path,
                }
                for name, tool in self.resolved_tools.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Lockfile:
        """Create from dictionary."""
        resolved_tools = {}
        for name, tool_data in data.get("resolved_tools", {}).items():
            resolved_tools[name] = ResolvedTool(
                name=tool_data["name"],
                version=tool_data["version"],
                resolved_from=tool_data["resolved_from"],
                checksum=tool_data.get("checksum"),
                installed_at=tool_data.get("installed_at"),
                install_path=tool_data.get("install_path"),
            )

        return cls(
            config_checksum=data["config_checksum"],
            resolved_tools=resolved_tools,
            created_at=data.get("created_at"),
            wrknv_version=data.get("wrknv_version", "0.3.0"),
        )


class LockfileManager:
    """Manages wrknv.lock files."""

    def __init__(self, project_dir: Path = Path.cwd()) -> None:
        self.project_dir = project_dir
        self.lockfile_path = project_dir / "wrknv.lock"

    def load_lockfile(self) -> Lockfile | None:
        """Load existing lockfile."""
        if not self.lockfile_path.exists():
            return None

        try:
            import json

            with self.lockfile_path.open() as f:
                data = json.load(f)
            return Lockfile.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            # Corrupted lockfile - return None to regenerate
            return None

    def save_lockfile(self, lockfile: Lockfile) -> None:
        """Save lockfile to disk."""
        import json

        with self.lockfile_path.open("w") as f:
            json.dump(lockfile.to_dict(), f, indent=2)

    def create_lockfile(self, config: WorkenvConfig) -> Lockfile:
        """Create a new lockfile from config."""
        return Lockfile.from_config(config)

    def is_lockfile_valid(self, config: WorkenvConfig) -> bool:
        """Check if lockfile is valid for current config."""
        lockfile = self.load_lockfile()
        if not lockfile:
            return False

        # Check config checksum
        current_lockfile = self.create_lockfile(config)
        return lockfile.config_checksum == current_lockfile.config_checksum

    def resolve_and_lock(self, config: WorkenvConfig) -> Lockfile:
        """Resolve tool versions and create/update lockfile."""
        from wrknv.managers.factory import get_tool_manager
        from wrknv.utils.version_resolver import resolve_tool_versions

        # Load existing lockfile or create new one
        lockfile = self.load_lockfile()
        if not lockfile or not self.is_lockfile_valid(config):
            lockfile = self.create_lockfile(config)

        # Resolve each tool
        tools = config.get_all_tools()
        for tool_name, version_pattern in tools.items():
            try:
                manager = get_tool_manager(tool_name, config)

                # Handle matrix format (list of versions)
                if isinstance(version_pattern, list):
                    resolved_versions = resolve_tool_versions(manager, version_pattern)
                    for resolved_version in resolved_versions:
                        lockfile.add_resolved_tool(
                            name=f"{tool_name}@{resolved_version}",
                            version=resolved_version,
                            resolved_from=str(version_pattern),
                        )
                else:
                    # Single version pattern
                    resolved_versions = resolve_tool_versions(manager, version_pattern)
                    if resolved_versions:
                        resolved_version = resolved_versions[0]
                        lockfile.add_resolved_tool(
                            name=tool_name, version=resolved_version, resolved_from=version_pattern
                        )
            except Exception:
                # Skip tools that can't be resolved
                continue

        # Save lockfile
        self.save_lockfile(lockfile)
        return lockfile

    def get_locked_versions(self) -> dict[str, str]:
        """Get locked versions for all tools."""
        lockfile = self.load_lockfile()
        if not lockfile:
            return {}

        return {tool.name: tool.version for tool in lockfile.resolved_tools.values()}


# 🧰🌍🔚
