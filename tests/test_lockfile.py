#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for lockfile management."""

from __future__ import annotations

import json
from pathlib import Path

from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.config import WorkenvConfig
from wrknv.lockfile import Lockfile, LockfileManager, ResolvedTool


class TestResolvedTool(FoundationTestCase):
    """Test ResolvedTool dataclass."""

    def test_create_resolved_tool(self) -> None:
        """Test creating a resolved tool."""
        tool = ResolvedTool(
            name="uv",
            version="0.5.0",
            resolved_from="0.5.x",
            checksum="abc123",
            installed_at="2025-01-01T00:00:00",
            install_path="/path/to/uv",
        )

        assert tool.name == "uv"
        assert tool.version == "0.5.0"
        assert tool.resolved_from == "0.5.x"
        assert tool.checksum == "abc123"
        assert tool.installed_at == "2025-01-01T00:00:00"
        assert tool.install_path == "/path/to/uv"

    def test_create_resolved_tool_minimal(self) -> None:
        """Test creating a resolved tool with minimal fields."""
        tool = ResolvedTool(
            name="uv",
            version="0.5.0",
            resolved_from="0.5.x",
        )

        assert tool.name == "uv"
        assert tool.version == "0.5.0"
        assert tool.resolved_from == "0.5.x"
        assert tool.checksum is None
        assert tool.installed_at is None
        assert tool.install_path is None


class TestLockfile(FoundationTestCase):
    """Test Lockfile class."""

    def test_from_config(self) -> None:
        """Test creating lockfile from config."""
        config = WorkenvConfig()
        config.tools = {"uv": "0.5.x"}

        with patch("provide.foundation.time.provide_now") as mock_now:
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-01T00:00:00"))
            lockfile = Lockfile.from_config(config)

        assert lockfile.config_checksum
        assert len(lockfile.config_checksum) == 12
        assert lockfile.created_at == "2025-01-01T00:00:00"
        assert lockfile.wrknv_version == "0.3.0"
        assert len(lockfile.resolved_tools) == 0

    def test_add_resolved_tool(self) -> None:
        """Test adding a resolved tool to lockfile."""
        lockfile = Lockfile(config_checksum="abc123")

        with patch("provide.foundation.time.provide_now") as mock_now:
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-01T00:00:00"))
            lockfile.add_resolved_tool(
                name="uv",
                version="0.5.0",
                resolved_from="0.5.x",
                checksum="def456",
                install_path="/path/to/uv",
            )

        assert "uv" in lockfile.resolved_tools
        tool = lockfile.resolved_tools["uv"]
        assert tool.name == "uv"
        assert tool.version == "0.5.0"
        assert tool.resolved_from == "0.5.x"
        assert tool.checksum == "def456"
        assert tool.installed_at == "2025-01-01T00:00:00"
        assert tool.install_path == "/path/to/uv"

    def test_get_resolved_version(self) -> None:
        """Test getting resolved version for a tool."""
        lockfile = Lockfile(config_checksum="abc123")
        lockfile.resolved_tools["uv"] = ResolvedTool(
            name="uv",
            version="0.5.0",
            resolved_from="0.5.x",
        )

        assert lockfile.get_resolved_version("uv") == "0.5.0"
        assert lockfile.get_resolved_version("nonexistent") is None

    def test_is_tool_installed(self) -> None:
        """Test checking if tool is installed."""
        lockfile = Lockfile(config_checksum="abc123")

        # Tool with installed_at
        lockfile.resolved_tools["uv"] = ResolvedTool(
            name="uv",
            version="0.5.0",
            resolved_from="0.5.x",
            installed_at="2025-01-01T00:00:00",
        )

        # Tool without installed_at
        lockfile.resolved_tools["go"] = ResolvedTool(
            name="go",
            version="1.22.0",
            resolved_from="1.22.x",
        )

        assert lockfile.is_tool_installed("uv") is True
        assert lockfile.is_tool_installed("go") is False
        assert lockfile.is_tool_installed("nonexistent") is False

    def test_to_dict(self) -> None:
        """Test converting lockfile to dictionary."""
        lockfile = Lockfile(
            config_checksum="abc123",
            created_at="2025-01-01T00:00:00",
            wrknv_version="0.3.0",
        )
        lockfile.resolved_tools["uv"] = ResolvedTool(
            name="uv",
            version="0.5.0",
            resolved_from="0.5.x",
            checksum="def456",
            installed_at="2025-01-01T00:00:00",
            install_path="/path/to/uv",
        )

        data = lockfile.to_dict()

        assert data["config_checksum"] == "abc123"
        assert data["created_at"] == "2025-01-01T00:00:00"
        assert data["wrknv_version"] == "0.1.0"
        assert "uv" in data["resolved_tools"]
        assert data["resolved_tools"]["uv"]["version"] == "0.5.0"

    def test_from_dict(self) -> None:
        """Test creating lockfile from dictionary."""
        data = {
            "config_checksum": "abc123",
            "created_at": "2025-01-01T00:00:00",
            "wrknv_version": "0.3.0",
            "resolved_tools": {
                "uv": {
                    "name": "uv",
                    "version": "0.5.0",
                    "resolved_from": "0.5.x",
                    "checksum": "def456",
                    "installed_at": "2025-01-01T00:00:00",
                    "install_path": "/path/to/uv",
                }
            },
        }

        lockfile = Lockfile.from_dict(data)

        assert lockfile.config_checksum == "abc123"
        assert lockfile.created_at == "2025-01-01T00:00:00"
        assert lockfile.wrknv_version == "0.3.0"
        assert "uv" in lockfile.resolved_tools
        tool = lockfile.resolved_tools["uv"]
        assert tool.version == "0.5.0"

    def test_from_dict_minimal(self) -> None:
        """Test creating lockfile from minimal dictionary."""
        data = {
            "config_checksum": "abc123",
            "resolved_tools": {},
        }

        lockfile = Lockfile.from_dict(data)

        assert lockfile.config_checksum == "abc123"
        assert lockfile.created_at is None
        assert lockfile.wrknv_version == "0.3.0"
        assert len(lockfile.resolved_tools) == 0


class TestLockfileManager(FoundationTestCase):
    """Test LockfileManager class."""

    def test_init(self, tmp_path: Path) -> None:
        """Test initializing lockfile manager."""
        manager = LockfileManager(tmp_path)

        assert manager.project_dir == tmp_path
        assert manager.lockfile_path == tmp_path / "wrknv.lock"

    def test_init_default_path(self) -> None:
        """Test initializing with default path."""
        manager = LockfileManager()

        assert manager.project_dir == Path.cwd()
        assert manager.lockfile_path == Path.cwd() / "wrknv.lock"

    def test_load_lockfile_not_exists(self, tmp_path: Path) -> None:
        """Test loading lockfile when it doesn't exist."""
        manager = LockfileManager(tmp_path)

        lockfile = manager.load_lockfile()
        assert lockfile is None

    def test_load_lockfile_exists(self, tmp_path: Path) -> None:
        """Test loading existing lockfile."""
        lockfile_path = tmp_path / "wrknv.lock"
        data = {
            "config_checksum": "abc123",
            "created_at": "2025-01-01T00:00:00",
            "wrknv_version": "0.3.0",
            "resolved_tools": {},
        }
        lockfile_path.write_text(json.dumps(data))

        manager = LockfileManager(tmp_path)
        lockfile = manager.load_lockfile()

        assert lockfile is not None
        assert lockfile.config_checksum == "abc123"

    def test_load_lockfile_corrupted(self, tmp_path: Path) -> None:
        """Test loading corrupted lockfile returns None."""
        lockfile_path = tmp_path / "wrknv.lock"
        lockfile_path.write_text("invalid json")

        manager = LockfileManager(tmp_path)
        lockfile = manager.load_lockfile()

        assert lockfile is None

    def test_save_lockfile(self, tmp_path: Path) -> None:
        """Test saving lockfile to disk."""
        manager = LockfileManager(tmp_path)
        lockfile = Lockfile(config_checksum="abc123")

        manager.save_lockfile(lockfile)

        assert manager.lockfile_path.exists()
        data = json.loads(manager.lockfile_path.read_text())
        assert data["config_checksum"] == "abc123"

    def test_create_lockfile(self, tmp_path: Path) -> None:
        """Test creating lockfile from config."""
        manager = LockfileManager(tmp_path)
        config = WorkenvConfig()

        with patch("provide.foundation.time.provide_now") as mock_now:
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-01T00:00:00"))
            lockfile = manager.create_lockfile(config)

        assert lockfile.config_checksum
        assert lockfile.created_at == "2025-01-01T00:00:00"

    def test_is_lockfile_valid_no_lockfile(self, tmp_path: Path) -> None:
        """Test checking validity when no lockfile exists."""
        manager = LockfileManager(tmp_path)
        config = WorkenvConfig()

        assert manager.is_lockfile_valid(config) is False

    def test_is_lockfile_valid_matching_checksum(self, tmp_path: Path) -> None:
        """Test checking validity with matching checksum."""
        config = WorkenvConfig()
        manager = LockfileManager(tmp_path)

        # Create and save lockfile
        with patch("provide.foundation.time.provide_now") as mock_now:
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-01T00:00:00"))
            lockfile = Lockfile.from_config(config)
            manager.save_lockfile(lockfile)

        # Check validity
        assert manager.is_lockfile_valid(config) is True

    def test_is_lockfile_valid_different_checksum(self, tmp_path: Path) -> None:
        """Test checking validity with different checksum."""
        config1 = WorkenvConfig()
        config1.tools = {"uv": "0.5.x"}
        config2 = WorkenvConfig()
        config2.tools = {"uv": "0.6.x"}

        manager = LockfileManager(tmp_path)

        # Create lockfile with config1
        with patch("provide.foundation.time.provide_now") as mock_now:
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-01T00:00:00"))
            lockfile = Lockfile.from_config(config1)
            manager.save_lockfile(lockfile)

        # Check validity with config2
        assert manager.is_lockfile_valid(config2) is False

    def test_get_locked_versions_no_lockfile(self, tmp_path: Path) -> None:
        """Test getting locked versions when no lockfile exists."""
        manager = LockfileManager(tmp_path)

        versions = manager.get_locked_versions()
        assert versions == {}

    def test_get_locked_versions(self, tmp_path: Path) -> None:
        """Test getting locked versions from lockfile."""
        lockfile_path = tmp_path / "wrknv.lock"
        data = {
            "config_checksum": "abc123",
            "resolved_tools": {
                "uv": {
                    "name": "uv",
                    "version": "0.5.0",
                    "resolved_from": "0.5.x",
                },
                "go": {
                    "name": "go",
                    "version": "1.22.0",
                    "resolved_from": "1.22.x",
                },
            },
        }
        lockfile_path.write_text(json.dumps(data))

        manager = LockfileManager(tmp_path)
        versions = manager.get_locked_versions()

        assert versions == {"uv": "0.5.0", "go": "1.22.0"}

    def test_resolve_and_lock_new_lockfile(self, tmp_path: Path) -> None:
        """Test resolve and lock with no existing lockfile."""
        config = WorkenvConfig()
        config.tools = {"uv": "0.5.x"}

        manager = LockfileManager(tmp_path)

        with (
            patch("provide.foundation.time.provide_now") as mock_now,
            patch("wrknv.managers.factory.get_tool_manager") as mock_get_manager,
            patch("wrknv.utils.version_resolver.resolve_tool_versions") as mock_resolve,
        ):
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-01T00:00:00"))
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            mock_resolve.return_value = ["0.5.0"]

            lockfile = manager.resolve_and_lock(config)

        assert manager.lockfile_path.exists()
        assert "uv" in lockfile.resolved_tools
        assert lockfile.resolved_tools["uv"].version == "0.5.0"

    def test_resolve_and_lock_updates_existing(self, tmp_path: Path) -> None:
        """Test resolve and lock updates existing invalid lockfile."""
        config = WorkenvConfig()
        config.tools = {"uv": "0.6.x"}

        manager = LockfileManager(tmp_path)

        # Create old lockfile with different config
        old_config = WorkenvConfig()
        old_config.tools = {"uv": "0.5.x"}
        with patch("provide.foundation.time.provide_now") as mock_now:
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-01T00:00:00"))
            old_lockfile = Lockfile.from_config(old_config)
            manager.save_lockfile(old_lockfile)

        # Resolve with new config
        with (
            patch("provide.foundation.time.provide_now") as mock_now,
            patch("wrknv.managers.factory.get_tool_manager") as mock_get_manager,
            patch("wrknv.utils.version_resolver.resolve_tool_versions") as mock_resolve,
        ):
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-02T00:00:00"))
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            mock_resolve.return_value = ["0.6.0"]

            lockfile = manager.resolve_and_lock(config)

        assert "uv" in lockfile.resolved_tools
        assert lockfile.resolved_tools["uv"].version == "0.6.0"

    def test_resolve_and_lock_matrix_versions(self, tmp_path: Path) -> None:
        """Test resolve and lock with matrix version pattern."""
        config = WorkenvConfig()
        config.tools = {"uv": ["0.5.x", "0.6.x"]}

        manager = LockfileManager(tmp_path)

        with (
            patch("provide.foundation.time.provide_now") as mock_now,
            patch("wrknv.managers.factory.get_tool_manager") as mock_get_manager,
            patch("wrknv.utils.version_resolver.resolve_tool_versions") as mock_resolve,
        ):
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-01T00:00:00"))
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            mock_resolve.return_value = ["0.5.0", "0.6.0"]

            lockfile = manager.resolve_and_lock(config)

        assert "uv@0.5.0" in lockfile.resolved_tools
        assert "uv@0.6.0" in lockfile.resolved_tools

    def test_resolve_and_lock_handles_errors(self, tmp_path: Path) -> None:
        """Test resolve and lock continues on errors."""
        config = WorkenvConfig()
        config.tools = {"uv": "0.5.x", "go": "1.22.x"}

        manager = LockfileManager(tmp_path)

        with (
            patch("provide.foundation.time.provide_now") as mock_now,
            patch("wrknv.managers.factory.get_tool_manager") as mock_get_manager,
            patch("wrknv.utils.version_resolver.resolve_tool_versions") as mock_resolve,
        ):
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-01T00:00:00"))

            # First tool succeeds
            mock_manager_uv = Mock()
            # Second tool fails
            mock_manager_go = Mock()

            def get_manager_side_effect(tool_name, config):
                if tool_name == "uv":
                    return mock_manager_uv
                elif tool_name == "go":
                    return mock_manager_go
                return None

            mock_get_manager.side_effect = get_manager_side_effect

            def resolve_side_effect(manager, pattern):
                if manager == mock_manager_uv:
                    return ["0.5.0"]
                raise Exception("Resolution failed")

            mock_resolve.side_effect = resolve_side_effect

            lockfile = manager.resolve_and_lock(config)

        # Should have uv but not go
        assert "uv" in lockfile.resolved_tools
        assert "go" not in lockfile.resolved_tools


class TestLockfileIntegration(FoundationTestCase):
    """Integration tests for lockfile functionality."""

    def test_full_lockfile_workflow(self, tmp_path: Path) -> None:
        """Test complete workflow of creating, saving, and loading lockfile."""
        config = WorkenvConfig()
        config.tools = {"uv": "0.5.x"}

        manager = LockfileManager(tmp_path)

        # Create lockfile
        with patch("provide.foundation.time.provide_now") as mock_now:
            mock_now.return_value = Mock(isoformat=Mock(return_value="2025-01-01T00:00:00"))
            lockfile = Lockfile.from_config(config)
            lockfile.add_resolved_tool(
                name="uv",
                version="0.5.0",
                resolved_from="0.5.x",
            )

        # Save lockfile
        manager.save_lockfile(lockfile)

        # Load lockfile
        loaded = manager.load_lockfile()
        assert loaded is not None
        assert loaded.config_checksum == lockfile.config_checksum
        assert "uv" in loaded.resolved_tools
        assert loaded.resolved_tools["uv"].version == "0.5.0"

        # Check validity
        assert manager.is_lockfile_valid(config) is True

        # Get locked versions
        versions = manager.get_locked_versions()
        assert versions["uv"] == "0.5.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
