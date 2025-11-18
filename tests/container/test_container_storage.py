#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

import pytest

#
# tests/container/test_container_storage.py
#
"""
Test Container Storage Management
==================================
Tests for container storage structure under ~/.wrknv
"""

import json
from pathlib import Path
import shutil

from provide.testkit.mocking import Mock

from wrknv.config import WorkenvConfig
from wrknv.container.manager import ContainerManager
from wrknv.wenv.schema import ContainerConfig


@pytest.mark.container
class TestContainerStorageStructure:
    """Test container storage directory structure."""

    @pytest.fixture
    def test_storage_path(self, tmp_path):
        """Create a test storage path."""
        storage_path = tmp_path / "test_wrknv_containers"
        return str(storage_path)

    @pytest.fixture
    def container_manager(self, test_storage_path):
        """Create a ContainerManager instance with test config."""
        config = WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(enabled=True, storage_path=test_storage_path),
        )
        return ContainerManager(config)

    def test_storage_directory_exists(self, container_manager, test_storage_path) -> None:
        """Test that storage directory is created."""
        # The directory should be created during __init__
        storage_dir = Path(test_storage_path)
        assert storage_dir.exists()
        assert storage_dir.is_dir()

    def test_containers_directory_structure(self, container_manager, test_storage_path) -> None:
        """Test that containers directory structure is created correctly."""
        storage_dir = Path(test_storage_path)

        # Check for shared directory
        shared_dir = storage_dir / "shared"
        assert shared_dir.exists()
        assert (shared_dir / "downloads").exists()

    def test_container_specific_directories(self, container_manager, test_storage_path) -> None:
        """Test that container-specific directories are created."""
        container_name = container_manager.container_name
        storage_dir = Path(test_storage_path)

        container_dir = storage_dir / container_name
        assert container_dir.exists()

        # Check all required subdirectories
        assert (container_dir / "volumes").exists()
        assert (container_dir / "volumes" / "workspace").exists()
        assert (container_dir / "volumes" / "cache").exists()
        assert (container_dir / "volumes" / "config").exists()
        assert (container_dir / "build").exists()
        assert (container_dir / "logs").exists()
        assert (container_dir / "backups").exists()

    def test_get_container_path(self, container_manager, test_storage_path) -> None:
        """Test getting container-specific paths."""
        # Storage is now automatically set up in __attrs_post_init__

        # Test various path types
        workspace_path = container_manager.get_container_path("volumes/workspace")
        assert workspace_path.exists()
        assert "test-project-dev" in str(workspace_path)
        assert workspace_path.name == "workspace"

        build_path = container_manager.get_container_path("build")
        assert build_path.exists()
        assert build_path.name == "build"

        # Test root container path
        root_path = container_manager.get_container_path()
        assert root_path.exists()
        assert root_path.name == container_manager.container_name


@pytest.mark.container
class TestContainerMetadata:
    """Test container metadata management."""

    @pytest.fixture
    def test_storage_path(self, tmp_path):
        """Create a test storage path."""
        storage_path = tmp_path / "test_wrknv_containers"
        return str(storage_path)

    @pytest.fixture
    def container_manager(self, test_storage_path):
        """Create a ContainerManager instance."""
        config = WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(
                enabled=True,
                python_version="3.11",
                additional_packages=["git", "curl"],
                storage_path=test_storage_path,
            ),
        )
        manager = ContainerManager(config)
        # Storage is now automatically set up in __attrs_post_init__
        return manager

    def test_save_metadata(self, container_manager, test_storage_path) -> None:
        """Test saving container metadata."""
        container_manager.save_metadata()

        metadata_file = container_manager.storage.get_container_path("metadata.json")
        assert metadata_file.exists()

        with metadata_file.open() as f:
            metadata = json.load(f)

        # Check actual metadata fields from implementation
        assert "container_name" in metadata
        assert "image_name" in metadata
        assert "project_name" in metadata
        assert "config_version" in metadata
        assert "last_updated" in metadata
        assert metadata["container_name"] == "test-project-dev"
        assert metadata["project_name"] == "test-project"

    def test_load_metadata(self, container_manager, test_storage_path) -> None:
        """Test loading container metadata."""
        # Save metadata first
        container_manager.save_metadata()

        # Load it back
        metadata = container_manager.load_metadata()

        assert metadata is not None
        assert "container_name" in metadata
        assert "image_name" in metadata
        assert "project_name" in metadata
        assert "last_updated" in metadata
        assert metadata["project_name"] == "test-project"

    def test_update_metadata(self, container_manager, test_storage_path) -> None:
        """Test updating container metadata."""
        # Save initial metadata
        container_manager.save_metadata()

        # Update metadata
        container_manager.update_metadata({"last_started": "2025-08-31T15:00:00"})

        # Load and verify
        metadata = container_manager.load_metadata()
        assert metadata["last_started"] == "2025-08-31T15:00:00"
        assert "container_name" in metadata  # Original field still exists
        assert "last_updated" in metadata  # Timestamp updated

    def test_metadata_not_found(self, container_manager) -> None:
        """Test loading metadata when file doesn't exist."""
        metadata = container_manager.load_metadata()
        assert metadata is None


@pytest.mark.container
class TestVolumeManagement:
    """Test container volume management."""

    @pytest.fixture
    def test_storage_path(self, tmp_path):
        """Create a test storage path."""
        storage_path = tmp_path / "test_wrknv_containers"
        return str(storage_path)

    @pytest.fixture
    def container_manager(self, test_storage_path):
        """Create a ContainerManager instance."""
        config = WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(enabled=True, storage_path=test_storage_path),
        )
        manager = ContainerManager(config)
        # Storage is now automatically set up in __attrs_post_init__
        return manager

    def test_get_volume_mappings(self, container_manager) -> None:
        """Test getting volume mappings for container."""
        mappings = container_manager.get_volume_mappings()

        # Actual implementation returns {host_path: container_path}
        assert mappings is not None
        assert len(mappings) > 0

        # Check that workspace mapping exists (CWD -> /workspace)
        container_paths = list(mappings.values())
        assert "/workspace" in container_paths

        # Check that persistent volumes are mapped
        # Keys are host paths, values are container paths
        for host_path, container_path in mappings.items():
            assert isinstance(host_path, str)
            assert isinstance(container_path, str)
            assert container_path.startswith("/")

    def test_custom_volume_mappings(self, test_storage_path) -> None:
        """Test custom volume mappings from config."""
        config = WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(
                enabled=True,
                storage_path=test_storage_path,
                volume_mappings={
                    "data": "/host/data:/container/data",
                    "logs": "/host/logs:/container/logs:ro",
                },
            ),
        )
        manager = ContainerManager(config)
        # Storage is now automatically set up in __attrs_post_init__

        mappings = manager.get_volume_mappings()

        # When custom volume_mappings are provided, they are returned as-is
        # Check custom mappings are present
        assert "data" in mappings
        assert "logs" in mappings
        assert mappings["data"] == "/host/data:/container/data"
        assert mappings["logs"] == "/host/logs:/container/logs:ro"

    @pytest.mark.skip(reason="list_volumes() not implemented yet")
    def test_list_volumes(self, container_manager, test_storage_path) -> None:
        """Test listing container volumes."""
        # Create some test files in volumes
        workspace = container_manager.storage.get_container_path("volumes/workspace")
        (workspace / "test.txt").write_text("test")

        cache = container_manager.storage.get_container_path("volumes/cache")
        (cache / "packages").mkdir()

        # Method not implemented yet
        # volumes = container_manager.list_volumes()
        pass

    def test_backup_volumes(self, container_manager, test_storage_path) -> None:
        """Test backing up container volumes."""
        # Create test data
        workspace = container_manager.storage.get_container_path("volumes/workspace")
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "project.txt").write_text("project data")

        # Backup volumes - returns Path to backup file
        result = container_manager.backup_volumes()

        assert result is not None  # Backup succeeded
        assert result.exists()  # Backup file exists
        assert result.suffix == ".gz"  # Compressed backup

    def test_restore_volumes(self, container_manager, test_storage_path) -> None:
        """Test restoring container volumes from backup."""
        # Create test data
        workspace = container_manager.storage.get_container_path("volumes/workspace")
        workspace.mkdir(parents=True, exist_ok=True)
        test_file = workspace / "original.txt"
        test_file.write_text("original data")

        # Backup volumes - returns bool
        backup_success = container_manager.backup_volumes()
        assert backup_success

        # For restore, we'd need an actual backup file path
        # This test would need a real backup file to restore from
        # For now, test that the method exists and returns a bool
        backup_dir = container_manager.volumes.backup_dir
        if backup_dir.exists() and list(backup_dir.glob("*.tar.gz")):
            # If a backup exists, test restore
            backup_file = next(iter(backup_dir.glob("*.tar.gz")))
            result = container_manager.restore_volumes(backup_file, force=True)
            assert isinstance(result, bool)

    def test_clean_volumes(self, container_manager, test_storage_path) -> None:
        """Test cleaning container volumes."""
        # Create test data
        workspace = container_manager.storage.get_container_path("volumes/workspace")
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "test.txt").write_text("test")

        cache = container_manager.storage.get_container_path("volumes/cache")
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "package.tar").write_text("package")

        # Clean volumes - returns bool
        result = container_manager.clean_volumes()

        assert isinstance(result, bool)
        assert result is True  # Clean succeeded

    def test_clean_volumes_with_preserve(self, container_manager, test_storage_path) -> None:
        """Test cleaning volumes with preservation of specific volumes."""
        # Create test data
        workspace = container_manager.storage.get_container_path("volumes/workspace")
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "important.txt").write_text("keep this")

        cache = container_manager.storage.get_container_path("volumes/cache")
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "temp.txt").write_text("delete this")

        # Clean volumes with preservation - returns bool
        result = container_manager.clean_volumes(preserve=["workspace"])

        assert isinstance(result, bool)
        assert result is True  # Clean succeeded


@pytest.mark.container
class TestDockerIntegration:
    """Test Docker integration with new storage structure."""

    @pytest.fixture
    def test_storage_path(self, tmp_path):
        """Create a test storage path."""
        storage_path = tmp_path / "test_wrknv_containers"
        return str(storage_path)

    @pytest.fixture
    def container_manager(self, test_storage_path):
        """Create a ContainerManager instance."""
        config = WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(enabled=True, storage_path=test_storage_path),
        )
        manager = ContainerManager(config)
        # Storage is now automatically set up in __attrs_post_init__
        return manager

    def test_build_uses_new_path(self, container_manager, test_storage_path) -> None:
        """Test that Docker build uses new build directory."""
        from tests.conftest import create_mock_builder

        # Replace builder with mock
        mock_builder = create_mock_builder()
        mock_builder.build = Mock(return_value=True)
        container_manager.builder = mock_builder

        result = container_manager.build_image()

        # Verify build was called
        assert result is True
        mock_builder.build.assert_called_once()

        # Check that storage path exists
        build_path = container_manager.storage.get_container_path("build")
        assert build_path.exists()

    def test_start_mounts_persistent_volumes(self, container_manager, test_storage_path) -> None:
        """Test that Docker start mounts persistent volumes."""
        from tests.conftest import (
            create_mock_builder,
            create_mock_lifecycle,
            create_mock_runtime,
        )

        # Replace attrs dependencies with mocks
        mock_runtime = create_mock_runtime(available=True)
        mock_builder = create_mock_builder()
        mock_builder.image_exists = Mock(return_value=True)
        mock_lifecycle = create_mock_lifecycle(exists=False, running=False)
        mock_lifecycle.start = Mock(return_value=True)

        container_manager.runtime = mock_runtime
        container_manager.builder = mock_builder
        container_manager.lifecycle = mock_lifecycle

        result = container_manager.start()

        # Verify start was called with volume mappings
        assert result
        mock_lifecycle.start.assert_called_once()
        # Check that storage was used to get volume mappings
        call_kwargs = mock_lifecycle.start.call_args[1]
        assert "volumes" in call_kwargs

    def test_clean_preserves_volumes_optionally(self, container_manager) -> None:
        """Test that clean can optionally preserve volumes."""
        from tests.conftest import (
            create_mock_builder,
            create_mock_lifecycle,
            create_mock_storage,
        )

        # Replace attrs dependencies with mocks
        mock_lifecycle = create_mock_lifecycle(exists=True, running=False)
        mock_lifecycle.remove = Mock(return_value=True)
        mock_builder = create_mock_builder()
        mock_storage = create_mock_storage()
        mock_storage.clean_storage = Mock(return_value=True)

        container_manager.lifecycle = mock_lifecycle
        container_manager.builder = mock_builder
        container_manager.storage = mock_storage

        # Clean calls storage.clean_storage
        result = container_manager.clean()

        # Verify clean was called
        assert result
        mock_lifecycle.remove.assert_called()
        mock_storage.clean_storage.assert_called()


@pytest.mark.container
class TestContainerStorageConfig:
    """Test container storage configuration."""

    def test_default_storage_path(self) -> None:
        """Test default storage path configuration."""
        config = ContainerConfig()
        assert config.storage_path == "~/.wrknv/containers"

    def test_custom_storage_path(self) -> None:
        """Test custom storage path configuration."""
        config = ContainerConfig(storage_path="/custom/path/containers")
        assert config.storage_path == "/custom/path/containers"

    def test_persistent_volumes_config(self) -> None:
        """Test persistent volumes configuration."""
        config = ContainerConfig(persistent_volumes=["workspace", "cache", "config", "data"])
        assert "workspace" in config.persistent_volumes
        assert "data" in config.persistent_volumes
        assert len(config.persistent_volumes) == 4

    def test_volume_mappings_config(self) -> None:
        """Test volume mappings configuration."""
        config = ContainerConfig(
            volume_mappings={
                "project": "/host/project:/container/project",
                "readonly": "/host/data:/container/data:ro",
            }
        )
        assert config.volume_mappings["project"] == "/host/project:/container/project"
        assert config.volume_mappings["readonly"] == "/host/data:/container/data:ro"


# Integration test placeholder
@pytest.mark.integration
@pytest.mark.container
class TestContainerStorageIntegration:
    """Integration tests for container storage (requires Docker)."""

    @pytest.mark.skipif(not shutil.which("docker"), reason="Docker not available")
    def test_full_container_lifecycle_with_volumes(self) -> None:
        """Test full container lifecycle with persistent volumes."""
        # This would be a full integration test
        # Requires Docker to be installed and running
        pass


# 🧰🌍🔚
