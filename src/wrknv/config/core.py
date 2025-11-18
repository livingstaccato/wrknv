#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Core Configuration for wrknv
=============================
Main configuration classes using provide.foundation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from attrs import define, field
from provide.foundation.config import (
    ConfigManager,
    field as config_field,
)
from provide.foundation.config.env import RuntimeConfig
from provide.foundation.logger import get_logger

# Import container config from schema - will consolidate later
from wrknv.wenv.schema import ContainerConfig

logger = get_logger(__name__)


class WorkenvConfigError(Exception):
    """Raised when there's an error in workenv configuration."""

    pass


@define
class WorkenvToolConfig:
    """Configuration for a single tool."""

    version: str | None = None
    path: str | None = None
    env: dict[str, str] = field(factory=dict)


@define
class WorkenvSettings(RuntimeConfig):
    """Workenv-specific settings with WRKNV_ environment variable support."""

    auto_install: bool = config_field(
        default=True, description="Automatically install missing tools", env_var="WRKNV_AUTO_INSTALL"
    )
    use_cache: bool = config_field(
        default=True, description="Use cached tool installations", env_var="WRKNV_USE_CACHE"
    )
    cache_ttl: str = config_field(default="7d", description="Cache time-to-live", env_var="WRKNV_CACHE_TTL")
    log_level: str = config_field(default="WARNING", description="Logging level", env_var="WRKNV_LOG_LEVEL")
    container_runtime: str = config_field(
        default="docker", description="Container runtime to use", env_var="WRKNV_CONTAINER_RUNTIME"
    )
    container_registry: str = config_field(
        default="ghcr.io", description="Default container registry", env_var="WRKNV_CONTAINER_REGISTRY"
    )


@define
class WorkenvConfig(RuntimeConfig):
    """Main workenv configuration with WRKNV_ environment variable support."""

    # Project metadata
    project_name: str | None = config_field(
        default="my-project", description="Project name", env_var="WRKNV_PROJECT_NAME"
    )
    version: str | None = config_field(default="1.0.0", description="Project version", env_var="WRKNV_VERSION")
    description: str | None = config_field(
        default=None, description="Project description", env_var="WRKNV_DESCRIPTION"
    )

    # Tool configurations
    tools: dict[str, dict[str, Any]] = field(factory=dict)

    # Container configuration (matching WorkenvSchema)
    container: ContainerConfig | None = field(default=None)

    # Profiles
    profiles: dict[str, dict[str, str]] = field(factory=dict)

    # Settings
    workenv: WorkenvSettings = field(factory=WorkenvSettings)

    # Env configuration
    env: dict[str, Any] = field(factory=dict)

    # Gitignore configuration
    gitignore: dict[str, Any] = field(factory=dict)

    # Internal state
    config_path: Path | None = field(init=False, repr=False, default=None)
    _manager: ConfigManager | None = field(init=False, repr=False, default=None)

    # Helper instances for delegation
    _validator: Any = field(init=False, repr=False, default=None)
    _persistence: Any = field(init=False, repr=False, default=None)
    _display: Any = field(init=False, repr=False, default=None)

    def __attrs_post_init__(self) -> None:
        """Initialize helper instances after attrs initialization."""
        from wrknv.config.display import WorkenvConfigDisplay
        from wrknv.config.persistence import WorkenvConfigPersistence
        from wrknv.config.validation import WorkenvConfigValidator

        self._validator = WorkenvConfigValidator(self)
        self._persistence = WorkenvConfigPersistence(self)
        self._display = WorkenvConfigDisplay(self)

    @classmethod
    def load(cls, config_file: Path | None = None) -> WorkenvConfig:
        """Load configuration from file and environment variables."""
        from provide.foundation.config.types import ConfigSource

        instance = cls()
        instance.config_path = config_file or instance._find_config_file()
        instance._manager = instance._create_manager()
        instance._load_config()

        # Load environment config using foundation's from_env
        env_config = cls.from_env(prefix="WRKNV")

        # Merge only values that came from environment (not defaults)
        if env_config.get_source("project_name") == ConfigSource.ENV:
            instance.project_name = env_config.project_name
        if env_config.get_source("version") == ConfigSource.ENV:
            instance.version = env_config.version
        if env_config.get_source("description") == ConfigSource.ENV:
            instance.description = env_config.description

        # Merge workenv settings from environment
        env_settings = WorkenvSettings.from_env(prefix="WRKNV")
        for field_name in [
            "log_level",
            "auto_install",
            "use_cache",
            "cache_ttl",
            "container_runtime",
            "container_registry",
        ]:
            if env_settings.get_source(field_name) == ConfigSource.ENV:
                setattr(instance.workenv, field_name, getattr(env_settings, field_name))

        return instance

    def _find_config_file(self) -> Path:
        """Find configuration file in standard locations."""
        # Check standard locations
        locations = [
            Path.cwd() / ".wrknv.toml",
            Path.cwd() / "wrknv.toml",
            Path.cwd() / "pyproject.toml",
            Path.home() / ".config" / "wrknv" / "config.toml",
            Path.home() / ".wrknv.toml",
        ]

        for path in locations:
            if path.exists():
                logger.debug(f"Found config file at {path}")
                return path

        # Return default location for new configs
        return Path.cwd() / ".wrknv.toml"

    def _create_manager(self) -> ConfigManager:
        """Create configuration manager."""
        # For now, just create a basic manager
        # We'll load files manually to avoid complexity
        return ConfigManager()

    def _load_config(self) -> None:
        """Load configuration from file."""
        self._persistence.load_config()

    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        if self._persistence is None:
            return False
        return self._persistence.config_exists()  # type: ignore[no-any-return]

    def get_config_path(self) -> Path:
        """Get path to configuration file."""
        if self._persistence is None:
            msg = "Persistence handler not initialized"
            raise RuntimeError(msg)
        return self._persistence.get_config_path()  # type: ignore[no-any-return]

    def get_tool_version(self, tool_name: str) -> str | None:
        """Get version for a specific tool."""
        tool_config = self.tools.get(tool_name, {})
        if isinstance(tool_config, dict):
            return tool_config.get("version")
        return tool_config if isinstance(tool_config, str) else None

    def set_tool_version(self, tool_name: str, version: str) -> None:
        """Set version for a specific tool."""
        # Ensure tool entry exists
        if tool_name not in self.tools:
            self.tools[tool_name] = {}

        # If it's a dict, set the version key
        if isinstance(self.tools[tool_name], dict):
            self.tools[tool_name]["version"] = version
        else:
            # If it's a string, replace with dict
            self.tools[tool_name] = {"version": version}

        # Save configuration
        self.save_config()

    def get_all_tools(self) -> dict[str, str | list[str]]:
        """Get all tool versions."""
        result = {}
        for tool_name, config in self.tools.items():
            version = config.get("version") if isinstance(config, dict) else config
            if version:
                result[tool_name] = version
        return result

    def get_profile(self, profile_name: str) -> dict[str, str] | None:
        """Get a configuration profile."""
        return self.profiles.get(profile_name)

    def list_profiles(self) -> list[str]:
        """List all available profiles."""
        return list(self.profiles.keys())

    def profile_exists(self, profile_name: str) -> bool:
        """Check if a profile exists."""
        return profile_name in self.profiles

    def save_profile(self, profile_name: str, tools: dict[str, str]) -> None:
        """Save a profile."""
        self.profiles[profile_name] = tools
        self.save_config()

    def delete_profile(self, profile_name: str) -> bool:
        """Delete a profile."""
        if profile_name in self.profiles:
            del self.profiles[profile_name]
            self.save_config()
            return True
        return False

    def get_current_profile(self) -> str:
        """Get the current active profile name."""
        # For now, always return "default"
        # TODO: Add support for tracking active profile
        return "default"

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting using dot notation."""
        parts = key.split(".")
        current = self

        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def get_env_config(self) -> dict[str, Any]:
        """Get environment configuration for env generation."""
        return self.env

    def set_setting(self, key: str, value: Any) -> None:
        """Set a configuration setting using dot notation."""
        parts = key.split(".")

        # Navigate to the parent
        current = self
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                if part not in current:
                    current[part] = {}
                current = current[part]
            else:
                raise WorkenvConfigError(f"Cannot set {key}: parent doesn't exist")

        # Set the value
        last_part = parts[-1]
        if hasattr(current, last_part):
            setattr(current, last_part, value)
        elif isinstance(current, dict):
            current[last_part] = value
        else:
            raise WorkenvConfigError(f"Cannot set {key}: invalid target")

        # Save to file
        self.save_config()

    # Delegation methods to helper classes
    def save_config(self) -> None:
        """Save configuration to file."""
        self._persistence.save_config()

    def to_dict(self, include_sensitive: bool = True) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        if self._persistence is None:
            return {}
        return self._persistence.to_dict()  # type: ignore[no-any-return]

    def write_config(self, config_data: dict[str, Any]) -> None:
        """Write configuration data to file."""
        self._persistence.write_config(config_data)

    def edit_config(self) -> None:
        """Open configuration file in editor."""
        self._persistence.edit_config()

    def show_config(self) -> None:
        """Display configuration in a readable format."""
        self._display.show_config()

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate configuration comprehensively.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        if self._validator is None:
            return True, []
        return self._validator.validate()  # type: ignore[no-any-return]

    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration comprehensively.

        This is an alias for validate_config() to match the interface expected by tests.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        return self.validate_config()

    def validate_version(self, tool_name: str, version: str) -> bool:
        """Validate a tool version format.

        Args:
            tool_name: Name of the tool
            version: Version string to validate

        Returns:
            True if version is valid, False otherwise
        """
        import re

        if not version:
            return False

        # Allow "latest" as a special case
        if version.lower() in ["latest", "stable"]:
            return True

        # Check semantic versioning format (X.Y.Z with optional suffixes)
        semver_pattern = r"^\d+\.\d+(\.\d+)?(-[a-zA-Z0-9\.\-]+)?(\+[a-zA-Z0-9\.\-]+)?$"
        if re.match(semver_pattern, version):
            return True

        # Allow version patterns (for matrix testing)
        return bool("*" in version or "~" in version or "^" in version)


# 🧰🌍🔚
