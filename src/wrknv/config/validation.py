#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Configuration Validation for wrknv
===================================
Validation methods for configuration data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from wrknv.config.core import WorkenvConfig


class WorkenvConfigValidator:
    """Validator for WorkenvConfig instances."""

    def __init__(self, config: WorkenvConfig) -> None:
        """Initialize validator with config instance."""
        self.config = config

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the entire configuration.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Basic validation
        if not isinstance(self.config.project_name, str):
            errors.append(f"project_name must be string, got {type(self.config.project_name)}")
        elif not self.config.project_name.strip():
            errors.append("project_name cannot be empty")
        elif not self._is_valid_project_name(self.config.project_name):
            errors.append(f"Invalid project_name: {self.config.project_name}")

        if not isinstance(self.config.version, str):
            errors.append(f"version must be string, got {type(self.config.version)}")
        elif not self._is_valid_version(self.config.version):
            errors.append(f"Invalid version: {self.config.version}")

        # Validate tools
        if not isinstance(self.config.tools, dict):
            errors.append(f"tools must be dictionary, got {type(self.config.tools)}")
        else:
            for tool_name, tool_config in self.config.tools.items():
                tool_errors = self._validate_tool_config(tool_name, tool_config)
                errors.extend(tool_errors)

        # Validate profiles
        if not isinstance(self.config.profiles, dict):
            errors.append(f"profiles must be dictionary, got {type(self.config.profiles)}")
        else:
            for profile_name, profile_config in self.config.profiles.items():
                profile_errors = self._validate_profile_config(profile_name, profile_config)
                errors.extend(profile_errors)

        # Validate workenv settings
        workenv_errors = self._validate_workenv_settings()
        errors.extend(workenv_errors)

        # Validate env configuration
        if not isinstance(self.config.env, dict):
            errors.append(f"env must be dictionary, got {type(self.config.env)}")
        else:
            env_errors = self._validate_env_config()
            errors.extend(env_errors)

        return len(errors) == 0, errors

    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is valid."""
        if not isinstance(version, str):
            return False

        if version in ("latest", "stable", "dev", "main", "master"):
            return True

        # Basic semver check (supports X.Y, X.Y.Z, X.Y.Z-suffix)
        if version.startswith("v"):
            version = version[1:]  # Remove 'v' prefix

        # Handle pre-release versions (e.g., 1.2.3-beta.1)
        base_version = version.split("-")[0]
        parts = base_version.split(".")

        if len(parts) < 2 or len(parts) > 4:
            return False

        # Check that major and minor versions are numeric
        try:
            for i, part in enumerate(parts):
                if i < 2:  # Major and minor must be numeric
                    int(part)
                else:  # Patch and build can be numeric or alphanumeric
                    if not (part.isdigit() or part.replace("_", "").replace("-", "").isalnum()):
                        return False
            return True
        except ValueError:
            return False

    def _is_valid_project_name(self, name: str) -> bool:
        """Check if project name follows valid naming conventions."""
        import re

        # Allow letters, numbers, hyphens, underscores, and dots
        pattern = r"^[a-zA-Z0-9._-]+$"
        return bool(re.match(pattern, name)) and len(name) <= 100

    def _validate_tool_config(self, tool_name: str, tool_config: Any) -> list[str]:
        """Validate individual tool configuration."""
        errors = []

        if not isinstance(tool_name, str):
            errors.append(f"Tool name must be string, got {type(tool_name)}")
            return errors

        if not tool_name.strip():
            errors.append("Tool name cannot be empty")
            return errors

        # Tool config can be string (version), dict (detailed config), or list (matrix config)
        if isinstance(tool_config, str):
            if not self._is_valid_version(tool_config):
                errors.append(f"Invalid version for tool '{tool_name}': {tool_config}")
        elif isinstance(tool_config, list):
            # Matrix configuration - validate each version in the list
            if not tool_config:
                errors.append(f"Tool '{tool_name}' has empty version list")
            else:
                for i, version in enumerate(tool_config):
                    if not isinstance(version, str):
                        errors.append(f"Version {i} for tool '{tool_name}' must be string")
                    elif not self._is_valid_version(version):
                        errors.append(f"Invalid version {i} for tool '{tool_name}': {version}")
        elif isinstance(tool_config, dict):
            # Validate version if present
            version = tool_config.get("version")
            if version is not None:
                if not isinstance(version, str):
                    errors.append(f"Version for tool '{tool_name}' must be string")
                elif not self._is_valid_version(version):
                    errors.append(f"Invalid version for tool '{tool_name}': {version}")

            # Validate path if present
            path = tool_config.get("path")
            if path is not None and not isinstance(path, str):
                errors.append(f"Path for tool '{tool_name}' must be string")

            # Validate env if present
            env = tool_config.get("env")
            if env is not None:
                if not isinstance(env, dict):
                    errors.append(f"Environment for tool '{tool_name}' must be dictionary")
                else:
                    for env_key, env_value in env.items():
                        if not isinstance(env_key, str):
                            errors.append(f"Environment key for tool '{tool_name}' must be string")
                        if not isinstance(env_value, str):
                            errors.append(f"Environment value for tool '{tool_name}' must be string")
        else:
            errors.append(f"Tool configuration for '{tool_name}' must be string, list, or dictionary")

        return errors

    def _validate_profile_config(self, profile_name: str, profile_config: Any) -> list[str]:
        """Validate individual profile configuration."""
        errors = []

        if not isinstance(profile_name, str):
            errors.append(f"Profile name must be string, got {type(profile_name)}")
            return errors

        if not profile_name.strip():
            errors.append("Profile name cannot be empty")
            return errors

        if not isinstance(profile_config, dict):
            errors.append(f"Profile '{profile_name}' must be a dictionary")
            return errors

        # Validate profile tools
        for tool_name, tool_version in profile_config.items():
            if not isinstance(tool_name, str):
                errors.append(f"Tool name in profile '{profile_name}' must be string")
            elif not isinstance(tool_version, str):
                errors.append(f"Tool version for '{tool_name}' in profile '{profile_name}' must be string")
            elif not self._is_valid_version(tool_version):
                errors.append(
                    f"Invalid version '{tool_version}' for tool '{tool_name}' in profile '{profile_name}'"
                )

        return errors

    def _validate_workenv_settings(self) -> list[str]:
        """Validate workenv settings."""
        errors = []

        # Import here to avoid circular import
        from wrknv.config.core import WorkenvSettings

        if not isinstance(self.config.workenv, WorkenvSettings):
            errors.append("workenv must be WorkenvSettings instance")
            return errors

        # Validate boolean settings
        if not isinstance(self.config.workenv.auto_install, bool):
            errors.append("workenv.auto_install must be boolean")

        if not isinstance(self.config.workenv.use_cache, bool):
            errors.append("workenv.use_cache must be boolean")

        # Validate string settings
        if not isinstance(self.config.workenv.cache_ttl, str):
            errors.append("workenv.cache_ttl must be string")
        elif not self._is_valid_duration(self.config.workenv.cache_ttl):
            errors.append(f"Invalid cache_ttl format: {self.config.workenv.cache_ttl}")

        if not isinstance(self.config.workenv.log_level, str):
            errors.append("workenv.log_level must be string")
        elif self.config.workenv.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            errors.append(f"Invalid log_level: {self.config.workenv.log_level}")

        if not isinstance(self.config.workenv.container_runtime, str):
            errors.append("workenv.container_runtime must be string")
        elif self.config.workenv.container_runtime not in ("docker", "podman", "nerdctl"):
            errors.append(f"Unsupported container_runtime: {self.config.workenv.container_runtime}")

        if not isinstance(self.config.workenv.container_registry, str):
            errors.append("workenv.container_registry must be string")
        elif not self._is_valid_registry_url(self.config.workenv.container_registry):
            errors.append(f"Invalid container_registry URL: {self.config.workenv.container_registry}")

        return errors

    def _validate_env_config(self) -> list[str]:
        """Validate environment configuration."""
        errors = []

        for key, value in self.config.env.items():
            if not isinstance(key, str):
                errors.append(f"Environment key must be string, got {type(key)}")
            elif not key.strip():
                errors.append("Environment key cannot be empty")
            elif not key.replace("_", "").isalnum():
                errors.append(
                    f"Invalid environment key '{key}': must contain only letters, numbers, and underscores"
                )

            # Values can be string, number, boolean, or list
            if not isinstance(value, (str, int, float, bool, list)):
                errors.append(f"Environment value for '{key}' must be string, number, boolean, or list")
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if not isinstance(item, (str, int, float, bool)):
                        errors.append(
                            f"Environment list item {i} for '{key}' must be string, number, or boolean"
                        )

        return errors

    def _is_valid_duration(self, duration: str) -> bool:
        """Check if duration string is valid (e.g., '7d', '2h', '30m')."""
        import re

        pattern = r"^\d+[smhdw]$"
        return bool(re.match(pattern, duration))

    def _is_valid_registry_url(self, url: str) -> bool:
        """Check if registry URL is valid."""
        import re

        # Basic URL validation for container registries
        pattern = r"^[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})?(/[a-zA-Z0-9._-]+)*$"
        return bool(re.match(pattern, url))


# 🧰🌍🔚
