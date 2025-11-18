#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Configuration Sources for wrknv
================================
Different sources for loading configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from provide.foundation.file import read_toml


class ConfigSource:
    """Base interface for configuration sources."""

    def get_tool_version(self, tool_name: str) -> str | None:
        """Get version for a specific tool."""
        return None

    def get_all_tools(self) -> dict[str, str]:
        """Get all tool versions."""
        return {}

    def get_profile(self, profile_name: str) -> dict[str, str]:
        """Get a configuration profile."""
        return {}

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting."""
        return default


class FileConfigSource(ConfigSource):
    """Configuration source that loads from TOML files."""

    def __init__(self, path: Path, section: str = "workenv") -> None:
        """Initialize with file path and optional section."""
        self.path = path
        self.section = section
        self._data = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        if self.path.exists():
            self._data = read_toml(self.path, default={})

    def get_tool_version(self, tool_name: str) -> str | None:
        """Get version for a specific tool."""
        tools = self._data.get(self.section, {}).get("tools", {})
        return tools.get(tool_name)

    def get_all_tools(self) -> dict[str, str]:
        """Get all tool versions."""
        return self._data.get(self.section, {}).get("tools", {})

    def get_profile(self, profile_name: str) -> dict[str, str]:
        """Get a configuration profile."""
        profiles = self._data.get(self.section, {}).get("profiles", {})
        return profiles.get(profile_name, {})

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting."""
        # First check in the section's settings
        settings = self._data.get(self.section, {}).get("settings", {})
        if key in settings:
            return settings[key]

        # Then try navigating from root
        parts = key.split(".")
        current = self._data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return default
            else:
                return default
        return current


class EnvironmentConfigSource(ConfigSource):
    """Configuration source that loads from environment variables."""

    def __init__(self, prefix: str = "WRKNV") -> None:
        """Initialize with environment variable prefix."""
        self.prefix = prefix

    def get_tool_version(self, tool_name: str) -> str | None:
        """Get version for a specific tool."""
        # Try both formats for compatibility
        env_var = f"{self.prefix}_{tool_name.upper()}_VERSION"
        value = os.environ.get(env_var)
        if value is None:
            # Also try with TOOL_ prefix
            env_var = f"{self.prefix}_TOOL_{tool_name.upper()}_VERSION"
            value = os.environ.get(env_var)
        return value

    def get_all_tools(self) -> dict[str, str]:
        """Get all tool versions from environment."""
        tools = {}
        # Check both formats
        for key, value in os.environ.items():
            if key.startswith(self.prefix) and key.endswith("_VERSION"):
                # Try to extract tool name from both formats
                if f"{self.prefix}_TOOL_" in key:
                    # Format: PREFIX_TOOL_TOOLNAME_VERSION
                    prefix = f"{self.prefix}_TOOL_"
                    tool_name = key[len(prefix) : -8].lower()
                else:
                    # Format: PREFIX_TOOLNAME_VERSION
                    prefix = f"{self.prefix}_"
                    tool_name = key[len(prefix) : -8].lower()
                    # Skip if it's not a tool (e.g., PROJECT_VERSION)
                    if tool_name in ("project", "wrknv"):
                        continue
                tools[tool_name] = value
        return tools

    def get_profile(self, profile_name: str) -> dict[str, str]:
        """Get a configuration profile from environment."""
        # Profiles from env vars are tool-specific overrides
        profile = {}
        prefix = f"{self.prefix}_PROFILE_{profile_name.upper()}_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                tool_name = key[len(prefix) :].lower()
                profile[tool_name] = value
        return profile

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting from environment."""
        env_var = f"{self.prefix}_{key.upper().replace('.', '_')}"
        value = os.environ.get(env_var)
        if value is None:
            return default
        # Try to parse boolean values
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        elif value.lower() in ("false", "0", "no", "off"):
            return False
        return value


# 🧰🌍🔚
