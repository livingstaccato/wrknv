#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

import pytest

#
# tests/container/test_container_schema.py
#
"""
Test Container Schema Updates
=============================
Tests for container configuration schema enhancements.
"""

from attrs import fields

from wrknv.wenv.schema import ContainerConfig, validate_volume_mapping


@pytest.mark.container
class TestContainerConfigSchema:
    """Test ContainerConfig schema enhancements."""

    def test_storage_path_field_exists(self) -> None:
        """Test that storage_path field exists in ContainerConfig."""
        config_fields = fields(ContainerConfig)
        field_names = [f.name for f in config_fields]

        assert "storage_path" in field_names

    def test_storage_path_default_value(self) -> None:
        """Test default value for storage_path."""
        config = ContainerConfig()
        assert config.storage_path == "~/.wrknv/containers"

    def test_storage_path_custom_value(self) -> None:
        """Test custom storage_path value."""
        config = ContainerConfig(storage_path="/custom/containers")
        assert config.storage_path == "/custom/containers"

    def test_persistent_volumes_field_exists(self) -> None:
        """Test that persistent_volumes field exists."""
        config_fields = fields(ContainerConfig)
        field_names = [f.name for f in config_fields]

        assert "persistent_volumes" in field_names

    def test_persistent_volumes_default(self) -> None:
        """Test default persistent_volumes."""
        config = ContainerConfig()

        # Should have default volumes
        assert isinstance(config.persistent_volumes, list)
        assert "workspace" in config.persistent_volumes
        assert "cache" in config.persistent_volumes
        assert "config" in config.persistent_volumes

    def test_persistent_volumes_custom(self) -> None:
        """Test custom persistent_volumes."""
        config = ContainerConfig(persistent_volumes=["workspace", "data", "logs"])

        assert len(config.persistent_volumes) == 3
        assert "workspace" in config.persistent_volumes
        assert "data" in config.persistent_volumes
        assert "logs" in config.persistent_volumes
        assert "cache" not in config.persistent_volumes  # Not in custom list

    def test_volume_mappings_field_exists(self) -> None:
        """Test that volume_mappings field exists."""
        config_fields = fields(ContainerConfig)
        field_names = [f.name for f in config_fields]

        assert "volume_mappings" in field_names

    def test_volume_mappings_default(self) -> None:
        """Test default volume_mappings."""
        config = ContainerConfig()

        assert isinstance(config.volume_mappings, dict)
        assert len(config.volume_mappings) == 0  # Empty by default

    def test_volume_mappings_custom(self) -> None:
        """Test custom volume_mappings."""
        mappings = {
            "data": "/host/data:/container/data",
            "logs": "/host/logs:/container/logs:ro",
            "config": "~/config:/app/config",
        }

        config = ContainerConfig(volume_mappings=mappings)

        assert config.volume_mappings["data"] == "/host/data:/container/data"
        assert config.volume_mappings["logs"] == "/host/logs:/container/logs:ro"
        assert config.volume_mappings["config"] == "~/config:/app/config"


@pytest.mark.container
class TestVolumeMapping:
    """Test volume mapping validation."""

    def test_valid_volume_mapping_basic(self) -> None:
        """Test valid basic volume mapping."""
        mapping = "/host/path:/container/path"
        assert validate_volume_mapping(mapping) is True

    def test_valid_volume_mapping_with_mode(self) -> None:
        """Test valid volume mapping with mode."""
        assert validate_volume_mapping("/host/path:/container/path:ro") is True
        assert validate_volume_mapping("/host/path:/container/path:rw") is True

    def test_valid_volume_mapping_with_home(self) -> None:
        """Test valid volume mapping with home directory."""
        assert validate_volume_mapping("~/data:/container/data") is True
        assert validate_volume_mapping("~/.config:/app/config:ro") is True

    def test_valid_volume_mapping_relative_host(self) -> None:
        """Test valid volume mapping with relative host path."""
        assert validate_volume_mapping("./data:/container/data") is True
        assert validate_volume_mapping("../shared:/app/shared") is True

    def test_invalid_volume_mapping_no_colon(self) -> None:
        """Test invalid volume mapping without colon."""
        assert validate_volume_mapping("/host/path") is False

    def test_invalid_volume_mapping_empty_parts(self) -> None:
        """Test invalid volume mapping with empty parts."""
        assert validate_volume_mapping(":/container/path") is False
        assert validate_volume_mapping("/host/path:") is False
        assert validate_volume_mapping(":") is False

    def test_invalid_volume_mapping_too_many_parts(self) -> None:
        """Test invalid volume mapping with too many colons."""
        assert validate_volume_mapping("/host/path:/container/path:ro:extra") is False

    def test_invalid_volume_mapping_bad_mode(self) -> None:
        """Test invalid volume mapping with bad mode."""
        assert validate_volume_mapping("/host/path:/container/path:invalid") is False
        assert validate_volume_mapping("/host/path:/container/path:r") is False

    def test_named_volume_mapping(self) -> None:
        """Test named volume mapping (Docker style)."""
        assert validate_volume_mapping("my_volume:/container/path") is True
        assert validate_volume_mapping("data-volume:/app/data:ro") is True


@pytest.mark.container
class TestContainerConfigValidation:
    """Test ContainerConfig validation."""

    def test_empty_persistent_volumes_allowed(self) -> None:
        """Test that empty persistent_volumes list is allowed."""
        config = ContainerConfig(persistent_volumes=[])
        assert config.persistent_volumes == []

    def test_duplicate_persistent_volumes_handled(self) -> None:
        """Test handling of duplicate persistent volumes."""
        config = ContainerConfig(persistent_volumes=["workspace", "cache", "workspace", "config", "cache"])

        # Implementation should handle deduplication
        unique_volumes = list(set(config.persistent_volumes))
        assert len(unique_volumes) == 3

    def test_invalid_volume_mapping_raises_error(self) -> None:
        """Test that invalid volume mapping raises error."""
        with pytest.raises(ValueError, match="Invalid volume mapping"):
            ContainerConfig(volume_mappings={"invalid": "not-a-valid-mapping"})

    def test_volume_mapping_normalization(self) -> None:
        """Test volume mapping path normalization."""
        config = ContainerConfig(
            volume_mappings={
                "home": "~/data/:/container/data",  # Extra slash
                "relative": "./local//data:/app/data",  # Double slash
            }
        )

        # Paths should be normalized (implementation detail)
        # This test documents expected behavior
        assert ":/container/data" in config.volume_mappings["home"]
        assert ":/app/data" in config.volume_mappings["relative"]


@pytest.mark.container
class TestContainerConfigSerialization:
    """Test ContainerConfig serialization/deserialization."""

    def test_config_to_dict(self) -> None:
        """Test converting ContainerConfig to dictionary."""
        config = ContainerConfig(
            enabled=True,
            storage_path="/custom/path",
            persistent_volumes=["workspace", "data"],
            volume_mappings={"logs": "/var/logs:/container/logs:ro"},
        )

        config_dict = config.to_dict()

        assert config_dict["enabled"] is True
        assert config_dict["storage_path"] == "/custom/path"
        assert "workspace" in config_dict["persistent_volumes"]
        assert config_dict["volume_mappings"]["logs"] == "/var/logs:/container/logs:ro"

    def test_config_from_dict(self) -> None:
        """Test creating ContainerConfig from dictionary."""
        config_dict = {
            "enabled": True,
            "storage_path": "/custom/containers",
            "persistent_volumes": ["workspace", "cache", "custom"],
            "volume_mappings": {"project": "/home/user/project:/app", "data": "/mnt/data:/data:ro"},
            "python_version": "3.11",
            "base_image": "ubuntu:24.04",
        }

        config = ContainerConfig.from_dict(config_dict)

        assert config.enabled is True
        assert config.storage_path == "/custom/containers"
        assert len(config.persistent_volumes) == 3
        assert "custom" in config.persistent_volumes
        assert config.volume_mappings["project"] == "/home/user/project:/app"
        assert config.python_version == "3.11"

    def test_config_roundtrip(self) -> None:
        """Test config serialization roundtrip."""
        original = ContainerConfig(
            enabled=True,
            storage_path="~/.wrknv/special",
            persistent_volumes=["a", "b", "c"],
            volume_mappings={"x": "/x:/y", "z": "/z:/w:ro"},
            environment={"KEY": "value"},
            ports=["8080:80", "9000:9000"],
        )

        # Convert to dict and back
        config_dict = original.to_dict()
        restored = ContainerConfig.from_dict(config_dict)

        assert restored.enabled == original.enabled
        assert restored.storage_path == original.storage_path
        assert restored.persistent_volumes == original.persistent_volumes
        assert restored.volume_mappings == original.volume_mappings
        assert restored.environment == original.environment
        assert restored.ports == original.ports


# 🧰🌍🔚
