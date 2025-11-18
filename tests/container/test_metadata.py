#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for container metadata management."""

from __future__ import annotations

from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock
import pytest

from wrknv.config import WorkenvConfig
from wrknv.container.metadata import ContainerMetadata


class TestContainerMetadata(FoundationTestCase):
    """Test ContainerMetadata class."""

    def test_save_metadata(self) -> None:
        """Test saving metadata."""
        mock_storage = Mock()
        config = WorkenvConfig()
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        metadata.save()

        mock_storage.save_metadata.assert_called_once()
        saved_data = mock_storage.save_metadata.call_args[0][0]
        assert saved_data["container_name"] == "test-container"
        assert saved_data["image_name"] == "test-image"

    def test_save_metadata_with_additional_data(self) -> None:
        """Test saving metadata with additional data."""
        mock_storage = Mock()
        config = WorkenvConfig()
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        metadata.save(additional_data={"custom_key": "custom_value"})

        mock_storage.save_metadata.assert_called_once()
        saved_data = mock_storage.save_metadata.call_args[0][0]
        assert saved_data["custom_key"] == "custom_value"

    def test_load_metadata(self) -> None:
        """Test loading metadata."""
        mock_storage = Mock()
        mock_storage.load_metadata.return_value = {"container_name": "test-container"}
        config = WorkenvConfig()
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        result = metadata.load()

        assert result == {"container_name": "test-container"}
        mock_storage.load_metadata.assert_called_once()

    def test_load_metadata_none(self) -> None:
        """Test loading metadata when none exists."""
        mock_storage = Mock()
        mock_storage.load_metadata.return_value = None
        config = WorkenvConfig()
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        result = metadata.load()

        assert result is None

    def test_update_metadata(self) -> None:
        """Test updating metadata."""
        mock_storage = Mock()
        config = WorkenvConfig()
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        updates = {"status": "running"}
        metadata.update(updates)

        mock_storage.update_metadata.assert_called_once_with(updates)

    def test_create_from_config(self) -> None:
        """Test creating metadata from config."""
        mock_storage = Mock()
        config = WorkenvConfig()
        config.project_name = "test-project"
        config.version = "1.0.0"
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        result = metadata.create_from_config()

        assert result["container_name"] == "test-container"
        assert result["image_name"] == "test-image"
        assert result["project_name"] == "test-project"
        assert result["config_version"] == "1.0.0"

    def test_validate_no_metadata(self) -> None:
        """Test validate when no metadata exists."""
        mock_storage = Mock()
        mock_storage.load_metadata.return_value = None
        config = WorkenvConfig()
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        is_valid, issues = metadata.validate()

        assert is_valid is False
        assert "No metadata found" in issues

    def test_validate_matching_metadata(self) -> None:
        """Test validate with matching metadata."""
        mock_storage = Mock()
        config = WorkenvConfig()
        config.project_name = "test-project"
        mock_storage.load_metadata.return_value = {
            "project_name": "test-project",
            "container_name": "test-container",
        }
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        is_valid, issues = metadata.validate()

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_project_name_mismatch(self) -> None:
        """Test validate with project name mismatch."""
        mock_storage = Mock()
        config = WorkenvConfig()
        config.project_name = "test-project"
        mock_storage.load_metadata.return_value = {
            "project_name": "different-project",
            "container_name": "test-container",
        }
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        is_valid, issues = metadata.validate()

        assert is_valid is False
        assert len(issues) == 1
        assert "Project name mismatch" in issues[0]

    def test_validate_container_name_mismatch(self) -> None:
        """Test validate with container name mismatch."""
        mock_storage = Mock()
        config = WorkenvConfig()
        config.project_name = "test-project"
        mock_storage.load_metadata.return_value = {
            "project_name": "test-project",
            "container_name": "different-container",
        }
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        is_valid, issues = metadata.validate()

        assert is_valid is False
        assert len(issues) == 1
        assert "Container name mismatch" in issues[0]

    def test_validate_multiple_mismatches(self) -> None:
        """Test validate with multiple mismatches."""
        mock_storage = Mock()
        config = WorkenvConfig()
        config.project_name = "test-project"
        mock_storage.load_metadata.return_value = {
            "project_name": "different-project",
            "container_name": "different-container",
        }
        metadata = ContainerMetadata(
            storage=mock_storage,
            container_name="test-container",
            image_name="test-image",
            config=config,
        )

        is_valid, issues = metadata.validate()

        assert is_valid is False
        assert len(issues) == 2
        assert any("Project name mismatch" in issue for issue in issues)
        assert any("Container name mismatch" in issue for issue in issues)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
