#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv Configuration Schema
===========================
Type-safe configuration models with validation for wrknv.toml using attrs."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING, Any

from attrs import Attribute, define, field, validators
import cattrs

from wrknv.config.defaults import (
    DEFAULT_AUTO_UPDATE,
    DEFAULT_CONTAINER_BASE_IMAGE,
    DEFAULT_CONTAINER_ENABLED,
    DEFAULT_CONTAINER_STORAGE_PATH,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PACKAGE_LICENSE,
    DEFAULT_PYTHON_VERSION,
    DEFAULT_REGISTRY_TIMEOUT,
    DEFAULT_REGISTRY_VERIFY_SSL,
    DEFAULT_REGISTRY_WRKNV_URL,
    DEFAULT_TELEMETRY_ENABLED,
    DEFAULT_TOOL_AUTO_DETECT,
    DEFAULT_TOOL_ENABLED,
    DEFAULT_VERSION,
    DEFAULT_WORKENV_CACHE_DIR,
    DEFAULT_WORKENV_INSTALL_DIR,
)

if TYPE_CHECKING:
    from wrknv.config.core import WorkenvConfig


def validate_version(instance: Any, attribute: Attribute[Any], value: str) -> None:
    """Validate version format."""
    if not value:
        raise ValueError("Version cannot be empty")
    # Basic version validation - must start with number or 'v'
    if not (value[0].isdigit() or value.startswith("v")):
        raise ValueError(f"Invalid version format: {value}")


def validate_python_version(instance: Any, attribute: Attribute[Any], value: str) -> None:
    """Validate Python version format."""
    parts = value.split(".")
    if len(parts) < 2:
        raise ValueError(f"Invalid Python version: {value}")
    try:
        major = int(parts[0])
        minor = int(parts[1])
        if major < 3 or (major == 3 and minor < 8):
            raise ValueError(f"Python version must be 3.8 or higher: {value}")
    except ValueError as e:
        raise ValueError(f"Invalid Python version format: {value}") from e


def validate_profile_name(instance: Any, attribute: Attribute[Any], value: str) -> None:
    """Validate profile name."""
    if not value:
        raise ValueError("Profile name cannot be empty")
    if not value.replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"Invalid profile name: {value}")


def validate_package_name_validator(instance: Any, attribute: Attribute[Any], value: str) -> None:
    """Validate package name."""
    if not value:
        raise ValueError("Package name cannot be empty")
    # Package names should follow Python naming conventions
    if not value.replace("-", "_").replace("_", "").isalnum():
        raise ValueError(f"Invalid package name: {value}")


def convert_package_name(value: str) -> str:
    """Convert package name to lowercase."""
    if not value:
        raise ValueError("Package name cannot be empty")
    # Package names should follow Python naming conventions
    if not value.replace("-", "_").replace("_", "").isalnum():
        raise ValueError(f"Invalid package name: {value}")
    return value.lower()


def convert_registry_url(value: str) -> str:
    """Convert registry URL by removing trailing slash."""
    if not value.startswith(("http://", "https://")):
        raise ValueError(f"Invalid registry URL: {value}")
    return value.rstrip("/")


def validate_timeout(instance: Any, attribute: Attribute[Any], value: int) -> None:
    """Validate timeout value."""
    if value <= 0:
        raise ValueError("Timeout must be positive")
    if value > 300:
        raise ValueError("Timeout cannot exceed 5 minutes")


def validate_volume_mapping(mapping: str) -> bool:
    """Validate a single volume mapping string."""
    if not mapping:
        return False

    parts = mapping.split(":")
    if len(parts) < 2 or len(parts) > 3:
        return False

    # Check host and container paths are not empty
    if not parts[0] or not parts[1]:
        return False

    # If mode is specified, check it's valid
    if len(parts) == 3:
        mode = parts[2]
        if mode not in ["ro", "rw"]:
            return False

    return True


def validate_volume_mappings(
    instance: Any,
    attribute: Attribute[Any],
    value: dict[str, str],
) -> None:
    """Validate volume mappings dictionary."""
    for name, mapping in value.items():
        if not validate_volume_mapping(mapping):
            raise ValueError(f"Invalid volume mapping for '{name}': {mapping}")


def validate_project_name(instance: Any, attribute: Attribute[Any], value: str) -> None:
    """Validate project name."""
    if not value:
        raise ValueError("Project name cannot be empty")


def convert_log_level(value: str) -> str:
    """Convert log level to uppercase and validate."""
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    value = value.upper()
    if value not in valid_levels:
        raise ValueError(f"Invalid log level: {value}")
    return value


@define
class GitignoreConfig:
    """Configuration for gitignore generation."""

    templates: list[str] = field(factory=list, validator=validators.instance_of(list))
    templates_path: str | None = field(
        default=None, validator=validators.optional(validators.instance_of(str))
    )
    auto_detect: bool = field(default=DEFAULT_TOOL_AUTO_DETECT, validator=validators.instance_of(bool))
    custom_rules: list[str] = field(factory=list, validator=validators.instance_of(list))
    exclude_patterns: list[str] = field(factory=list, validator=validators.instance_of(list))


@define
class ToolConfig:
    """Configuration for a specific tool."""

    version: str = field(validator=[validators.instance_of(str), validate_version])
    enabled: bool = field(default=DEFAULT_TOOL_ENABLED, validator=validators.instance_of(bool))
    source_url: str | None = field(default=None, validator=validators.optional(validators.instance_of(str)))
    install_path: str | None = field(default=None, validator=validators.optional(validators.instance_of(str)))
    environment: dict[str, str] = field(factory=dict, validator=validators.instance_of(dict))


@define
class ContainerConfig:
    """Configuration for container operations."""

    enabled: bool = field(default=DEFAULT_CONTAINER_ENABLED, validator=validators.instance_of(bool))
    base_image: str = field(default=DEFAULT_CONTAINER_BASE_IMAGE, validator=validators.instance_of(str))
    python_version: str = field(
        default=DEFAULT_PYTHON_VERSION, validator=[validators.instance_of(str), validate_python_version]
    )
    additional_packages: list[str] = field(factory=list, validator=validators.instance_of(list))
    environment: dict[str, str] = field(factory=dict, validator=validators.instance_of(dict))
    volumes: list[str] = field(factory=list, validator=validators.instance_of(list))
    ports: list[str] = field(factory=list, validator=validators.instance_of(list))

    # New storage-related fields
    storage_path: str = field(default=DEFAULT_CONTAINER_STORAGE_PATH, validator=validators.instance_of(str))
    persistent_volumes: list[str] = field(
        factory=lambda: ["workspace", "cache", "config"], validator=validators.instance_of(list)
    )
    volume_mappings: dict[str, str] = field(
        factory=dict, validator=[validators.instance_of(dict), validate_volume_mappings]
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert ContainerConfig to dictionary."""
        return cattrs.unstructure(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContainerConfig:
        """Create ContainerConfig from dictionary."""
        return cattrs.structure(data, cls)


@define
class ProfileConfig:
    """Configuration for a workenv profile."""

    name: str = field(validator=[validators.instance_of(str), validate_profile_name])
    description: str = field(default="", validator=validators.instance_of(str))
    tools: dict[str, ToolConfig] = field(factory=dict, validator=validators.instance_of(dict))
    container: ContainerConfig | None = field(
        default=None,
        validator=validators.optional(validators.instance_of(ContainerConfig)),
    )
    environment: dict[str, str] = field(factory=dict, validator=validators.instance_of(dict))
    scripts: dict[str, str] = field(factory=dict, validator=validators.instance_of(dict))

    def model_dump(self) -> dict[str, Any]:
        """Convert to dictionary (compatibility method)."""
        return cattrs.unstructure(self)


@define
class PackageConfig:
    """Configuration for package operations."""

    name: str = field(validator=validators.instance_of(str), converter=convert_package_name)
    version: str = field(validator=validators.instance_of(str))
    entry_point: str = field(validator=validators.instance_of(str))
    author: str = field(default="", validator=validators.instance_of(str))
    description: str = field(default="", validator=validators.instance_of(str))
    license: str = field(default=DEFAULT_PACKAGE_LICENSE, validator=validators.instance_of(str))
    dependencies: list[str] = field(factory=list, validator=validators.instance_of(list))
    metadata: dict[str, Any] = field(factory=dict, validator=validators.instance_of(dict))


@define
class RegistryConfig:
    """Configuration for package registry."""

    url: str = field(default=DEFAULT_REGISTRY_WRKNV_URL, converter=convert_registry_url)
    username: str | None = field(default=None, validator=validators.optional(validators.instance_of(str)))
    token: str | None = field(default=None, validator=validators.optional(validators.instance_of(str)))
    verify_ssl: bool = field(default=DEFAULT_REGISTRY_VERIFY_SSL, validator=validators.instance_of(bool))
    timeout: int = field(
        default=DEFAULT_REGISTRY_TIMEOUT, validator=[validators.instance_of(int), validate_timeout]
    )


@define
class WorkenvSchema:
    """Schema for wrknv configuration validation (use wrknv.config.WorkenvConfig for runtime)."""

    project_name: str = field(validator=[validators.instance_of(str), validate_project_name])
    version: str = field(default=DEFAULT_VERSION, validator=validators.instance_of(str))
    description: str = field(default="", validator=validators.instance_of(str))

    # Tool configurations
    tools: dict[str, ToolConfig] = field(factory=dict, validator=validators.instance_of(dict))

    # Container configuration
    container: ContainerConfig | None = field(
        default=None,
        validator=validators.optional(validators.instance_of(ContainerConfig)),
    )

    # Package configuration
    package: PackageConfig | None = field(
        default=None,
        validator=validators.optional(validators.instance_of(PackageConfig)),
    )

    # Registry configuration
    registry: RegistryConfig | None = field(
        default=None,
        validator=validators.optional(validators.instance_of(RegistryConfig)),
    )

    # Profiles
    profiles: dict[str, ProfileConfig] = field(factory=dict, validator=validators.instance_of(dict))

    # Global settings
    install_dir: str = field(default=DEFAULT_WORKENV_INSTALL_DIR, validator=validators.instance_of(str))
    cache_dir: str = field(default=DEFAULT_WORKENV_CACHE_DIR, validator=validators.instance_of(str))
    log_level: str = field(default=DEFAULT_LOG_LEVEL, converter=convert_log_level)
    telemetry_enabled: bool = field(default=DEFAULT_TELEMETRY_ENABLED, validator=validators.instance_of(bool))
    auto_update: bool = field(default=DEFAULT_AUTO_UPDATE, validator=validators.instance_of(bool))

    # Task execution settings
    task_runner_prefix: str | None = field(
        default=None, validator=validators.optional(validators.instance_of(str))
    )
    task_auto_detect: bool = field(default=True, validator=validators.instance_of(bool))

    # Environment variables
    environment: dict[str, str] = field(factory=dict, validator=validators.instance_of(dict))

    # Custom scripts
    scripts: dict[str, str] = field(factory=dict, validator=validators.instance_of(dict))

    # Gitignore configuration
    gitignore: GitignoreConfig | None = field(
        default=None,
        validator=validators.optional(validators.instance_of(GitignoreConfig)),
    )

    def __attrs_post_init__(self) -> None:
        """Post-initialization processing."""
        # Expand user home directory
        self.install_dir = str(pathlib.Path(self.install_dir).expanduser())
        self.cache_dir = str(pathlib.Path(self.cache_dir).expanduser())

    def get_tool_config(self, tool_name: str) -> ToolConfig | None:
        """Get configuration for a specific tool."""
        return self.tools.get(tool_name)

    def get_profile(self, profile_name: str) -> ProfileConfig | None:
        """Get a specific profile configuration."""
        return self.profiles.get(profile_name)

    def merge_with_profile(self, profile_name: str) -> WorkenvSchema:
        """Create a new config merged with a profile."""
        profile = self.get_profile(profile_name)
        if not profile:
            return self

        # Create a copy of the current config
        merged_dict = cattrs.unstructure(self)

        # Merge tool configurations
        for tool_name, tool_config in profile.tools.items():
            merged_dict["tools"][tool_name] = cattrs.unstructure(tool_config)

        # Merge container config if present
        if profile.container:
            merged_dict["container"] = cattrs.unstructure(profile.container)

        # Merge environment variables
        merged_dict["environment"].update(profile.environment)

        # Merge scripts
        merged_dict["scripts"].update(profile.scripts)

        # Create new instance from merged dict
        return cattrs.structure(merged_dict, WorkenvSchema)

    def model_dump(self, exclude_none: bool = False) -> dict[str, Any]:
        """Convert to dictionary (compatibility method)."""
        data = cattrs.unstructure(self)
        if exclude_none:
            data = remove_none_values(data)
        return data


def remove_none_values(data: Any) -> Any:
    """Recursively remove None values from dictionary."""
    if isinstance(data, dict):
        return {k: remove_none_values(v) for k, v in data.items() if v is not None}
    if isinstance(data, list):
        return [remove_none_values(item) for item in data]
    return data


def validate_config_dict(config_dict: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate a configuration dictionary.

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    try:
        converter = cattrs.Converter()
        converter.structure(config_dict, WorkenvSchema)
        return True, []
    except Exception as e:
        if hasattr(e, "__cause__") and e.__cause__:
            # Extract validation errors from attrs/cattrs
            errors.append(str(e.__cause__))
        else:
            errors.append(str(e))

        return False, errors


def load_config_from_dict(config_dict: dict[str, Any]) -> WorkenvSchema:
    """
    Load configuration from a dictionary with validation.

    Raises:
        ValueError: If configuration is invalid
    """
    is_valid, errors = validate_config_dict(config_dict)
    if not is_valid:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

    converter = cattrs.Converter()
    return converter.structure(config_dict, WorkenvSchema)


def get_default_config(project_name: str = "my-project") -> WorkenvSchema:
    """Get a default configuration schema."""
    return WorkenvSchema(
        project_name=project_name,
        tools={
            "terraform": ToolConfig(version="1.5.0"),
            "tofu": ToolConfig(version="1.6.0", enabled=False),
            "go": ToolConfig(version="1.21.0"),
            "uv": ToolConfig(version="0.4.0"),
        },
        container=ContainerConfig(
            enabled=False,
            base_image="ubuntu:22.04",
            python_version="3.11",
        ),
    )


def config_to_toml(config: WorkenvConfig) -> str:
    """Convert configuration to TOML format."""
    from provide.foundation.file.formats import toml_dumps

    # Convert to dictionary
    config_dict = config.model_dump(exclude_none=True)

    # Remove empty collections
    def remove_empty(data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: remove_empty(v) for k, v in data.items() if v and (not isinstance(v, (dict, list)) or v)
            }
        if isinstance(data, list):
            return [remove_empty(item) for item in data if item]
        return data

    config_dict = remove_empty(config_dict)

    # Convert to TOML
    return toml_dumps(config_dict)


# 🧰🌍🔚
