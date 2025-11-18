#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for workspace manager functionality."""

from __future__ import annotations

from pathlib import Path

from provide.foundation.file.temp import temp_dir
from provide.testkit.mocking import AsyncMock, Mock, patch
import pytest

from wrknv.workspace.discovery import RepoInfo
from wrknv.workspace.manager import WorkspaceManager
from wrknv.workspace.schema import RepoConfig, TemplateSource, WorkspaceConfig


@pytest.fixture
def workspace_root():
    """Create temporary workspace root."""
    with temp_dir() as temp_path:
        yield temp_path


@pytest.fixture
def manager(workspace_root):
    """WorkspaceManager instance for testing."""
    return WorkspaceManager(workspace_root)


@pytest.fixture
def sample_repo_config():
    """Sample RepoConfig for testing."""
    return RepoConfig(
        path=Path("/test/repo"),
        name="test-repo",
        type="foundation-based",
        template_profile="foundation-based",
        features=["pyproject", "claude"],
    )


@pytest.fixture
def sample_workspace_config(workspace_root, sample_repo_config):
    """Sample WorkspaceConfig for testing."""
    return WorkspaceConfig(
        root=workspace_root,
        repos=[sample_repo_config],
        template_source=TemplateSource(type="local", location="/test/templates"),
        global_standards={"python_version": "3.11"},
    )


class TestWorkspaceManager:
    """Test WorkspaceManager functionality."""

    def test_manager_initialization(self, workspace_root) -> None:
        """Test manager initialization."""
        manager = WorkspaceManager(workspace_root)

        assert manager.root == workspace_root
        assert manager.config_dir == workspace_root / ".wrknv"
        assert manager.config_path == workspace_root / ".wrknv" / "workspace.toml"
        assert manager.discovery is not None

    def test_init_workspace_basic(self, manager) -> None:
        """Test basic workspace initialization."""
        with patch.object(manager.discovery, "discover_repos", return_value=[]):
            config = manager.init_workspace(auto_discover=False)

            assert config.root == manager.root
            assert len(config.repos) == 0
            assert config.sync_strategy == "manual"
            assert manager.config_dir.exists()

    def test_init_workspace_with_discovery(self, manager) -> None:
        """Test workspace initialization with auto-discovery."""
        mock_repo = RepoInfo(
            path=Path("/test/repo"),
            name="test-repo",
            has_git=True,
            has_pyproject=True,
            detected_type="foundation-based",
            current_config={"project": {"name": "test-repo"}},
        )

        with patch.object(manager.discovery, "discover_repos", return_value=[mock_repo]):
            config = manager.init_workspace(auto_discover=True)

            assert len(config.repos) == 1
            assert config.repos[0].name == "test-repo"
            assert config.repos[0].type == "foundation-based"

    def test_init_workspace_with_template_source(self, manager) -> None:
        """Test workspace initialization with template source."""
        template_path = "/test/templates"

        with patch.object(manager.discovery, "discover_repos", return_value=[]):
            config = manager.init_workspace(template_source=template_path, auto_discover=False)

            assert config.template_source is not None
            assert config.template_source.location == template_path
            assert config.template_source.type == "git"  # Since path doesn't exist

    def test_save_and_load_config(self, manager, sample_workspace_config) -> None:
        """Test saving and loading workspace configuration."""
        # Save config
        manager.save_config(sample_workspace_config)
        assert manager.config_path.exists()

        # Load config
        loaded_config = manager.load_config()
        assert loaded_config is not None
        assert loaded_config.root == sample_workspace_config.root
        assert len(loaded_config.repos) == len(sample_workspace_config.repos)

    def test_load_config_not_found(self, manager) -> None:
        """Test loading config when file doesn't exist."""
        config = manager.load_config()
        assert config is None

    def test_add_repo(self, manager) -> None:
        """Test adding repository to workspace."""
        repo_path = manager.root / "test-repo"
        repo_path.mkdir()

        # Create pyproject.toml
        pyproject_path = repo_path / "pyproject.toml"
        pyproject_path.write_text("""
[project]
name = "test-repo"
version = "1.0.0"
""")

        # Create .git directory
        (repo_path / ".git").mkdir()

        # Initialize workspace first
        with patch.object(manager.discovery, "discover_repos", return_value=[]):
            manager.init_workspace(auto_discover=False)

        # Add repo
        config = manager.add_repo(repo_path, name="test-repo", repo_type="foundation-based")

        assert len(config.repos) == 1
        assert config.repos[0].name == "test-repo"
        assert config.repos[0].type == "foundation-based"

    def test_add_repo_nonexistent_path(self, manager) -> None:
        """Test adding repository with non-existent path."""
        nonexistent_path = Path("/nonexistent/repo")

        with pytest.raises(FileNotFoundError):
            manager.add_repo(nonexistent_path)

    def test_remove_repo(self, manager, sample_workspace_config) -> None:
        """Test removing repository from workspace."""
        # Save initial config
        manager.save_config(sample_workspace_config)

        # Remove repo
        config = manager.remove_repo("test-repo")

        assert len(config.repos) == 0

    def test_remove_repo_no_config(self, manager) -> None:
        """Test removing repo when no workspace config exists."""
        with pytest.raises(RuntimeError, match="No workspace configuration found"):
            manager.remove_repo("test-repo")

    @pytest.mark.asyncio
    async def test_sync_all(self, manager, sample_workspace_config) -> None:
        """Test syncing all repositories."""
        manager.save_config(sample_workspace_config)

        with patch("wrknv.workspace.manager.WorkspaceSync") as mock_sync_class:
            mock_sync = Mock()
            mock_sync.sync_all = AsyncMock(return_value={"test-repo": {"success": True}})
            mock_sync_class.return_value = mock_sync

            result = await manager.sync_all(dry_run=True)

            mock_sync.sync_all.assert_called_once_with(dry_run=True)
            assert "test-repo" in result

    @pytest.mark.asyncio
    async def test_sync_repo(self, manager, sample_workspace_config) -> None:
        """Test syncing specific repository."""
        manager.save_config(sample_workspace_config)

        with patch("wrknv.workspace.manager.WorkspaceSync") as mock_sync_class:
            mock_sync = Mock()
            mock_sync.sync_repo = AsyncMock(return_value={"test-repo": {"success": True}})
            mock_sync_class.return_value = mock_sync

            result = await manager.sync_repo("test-repo", dry_run=False)

            mock_sync.sync_repo.assert_called_once()
            assert "test-repo" in result

    @pytest.mark.asyncio
    async def test_sync_repo_not_found(self, manager, sample_workspace_config) -> None:
        """Test syncing non-existent repository."""
        manager.save_config(sample_workspace_config)

        with pytest.raises(ValueError, match="Repository not found"):
            await manager.sync_repo("nonexistent-repo")

    def test_check_drift(self, manager, sample_workspace_config) -> None:
        """Test checking configuration drift."""
        manager.save_config(sample_workspace_config)

        with patch("wrknv.workspace.manager.WorkspaceSync") as mock_sync_class:
            mock_sync = Mock()
            mock_sync.check_drift.return_value = {"drift_detected": False}
            mock_sync_class.return_value = mock_sync

            result = manager.check_drift()

            mock_sync.check_drift.assert_called_once()
            assert "drift_detected" in result

    def test_get_workspace_status(self, manager, sample_workspace_config) -> None:
        """Test getting workspace status."""
        manager.save_config(sample_workspace_config)

        with (
            patch.object(manager.discovery, "get_workspace_summary") as mock_summary,
            patch.object(manager.discovery, "validate_workspace_structure") as mock_validate,
        ):
            mock_summary.return_value = {
                "total_repos": 1,
                "type_distribution": {"foundation-based": 1},
            }
            mock_validate.return_value = []

            status = manager.get_workspace_status()

            assert status["repos_configured"] == 1
            assert status["repos_discovered"] == 1
            assert "type_distribution" in status
            assert "issues" in status

    def test_get_workspace_status_no_config(self, manager) -> None:
        """Test getting status when no config exists."""
        status = manager.get_workspace_status()
        assert "error" in status

    def test_get_default_profile(self, manager) -> None:
        """Test getting default profile for repo types."""
        assert manager._get_default_profile("foundation") == "foundation-based"
        assert manager._get_default_profile("pyvider-plugin") == "pyvider-plugin"
        assert manager._get_default_profile("unknown") == "standalone"

    def test_get_default_features(self, manager) -> None:
        """Test getting default features for repo types."""
        features = manager._get_default_features("foundation-based")
        assert "pyproject" in features
        assert "claude" in features
        assert "coverage" in features

        features = manager._get_default_features("unknown")
        assert "pyproject" in features
        assert "claude" in features
        assert "coverage" not in features

    def test_get_default_standards(self, manager) -> None:
        """Test getting default global standards."""
        standards = manager._get_default_standards()

        assert standards["python_version"] == "3.11"
        assert standards["ruff_line_length"] == 111
        assert "authors" in standards
        assert "license" in standards


class TestWorkspaceManagerIntegration:
    """Integration tests for WorkspaceManager."""

    def test_full_workspace_lifecycle(self, workspace_root) -> None:
        """Test complete workspace lifecycle."""
        manager = WorkspaceManager(workspace_root)

        # Create mock repositories
        repo1_path = workspace_root / "repo1"
        repo1_path.mkdir()
        (repo1_path / ".git").mkdir()
        (repo1_path / "pyproject.toml").write_text("""
[project]
name = "repo1"
version = "1.0.0"
""")

        repo2_path = workspace_root / "repo2"
        repo2_path.mkdir()
        (repo2_path / ".git").mkdir()
        (repo2_path / "pyproject.toml").write_text("""
[project]
name = "repo2"
version = "1.0.0"
""")

        # Initialize workspace with discovery
        config = manager.init_workspace(auto_discover=True)
        assert len(config.repos) == 2

        # Add another repo manually
        repo3_path = workspace_root / "repo3"
        repo3_path.mkdir()
        (repo3_path / ".git").mkdir()
        (repo3_path / "pyproject.toml").write_text("""
[project]
name = "repo3"
version = "1.0.0"
""")

        config = manager.add_repo(repo3_path)
        assert len(config.repos) == 3

        # Remove a repo
        config = manager.remove_repo("repo2")
        assert len(config.repos) == 2

        # Verify persistence
        loaded_config = manager.load_config()
        assert len(loaded_config.repos) == 2
        assert any(repo.name == "repo1" for repo in loaded_config.repos)
        assert any(repo.name == "repo3" for repo in loaded_config.repos)
        assert not any(repo.name == "repo2" for repo in loaded_config.repos)

    def test_workspace_with_template_source(self, workspace_root) -> None:
        """Test workspace with template source configuration."""
        manager = WorkspaceManager(workspace_root)

        # Initialize with template source
        config = manager.init_workspace(
            template_source="https://github.com/provide-io/templates.git", auto_discover=False
        )

        assert config.template_source is not None
        assert config.template_source.type == "git"
        assert "github.com" in config.template_source.location

        # Verify persistence
        loaded_config = manager.load_config()
        assert loaded_config.template_source is not None
        assert loaded_config.template_source.location == config.template_source.location


# 🧰🌍🔚
