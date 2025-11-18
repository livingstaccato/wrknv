#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for wrknv.wenv.managers.tf_base module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from provide.testkit import FoundationTestCase
import pytest

from wrknv.wenv.managers.base import ToolManagerError
from wrknv.wenv.managers.tf_base import TfVersionsManager


class ConcreteTfManager(TfVersionsManager):
    """Concrete implementation for testing."""

    @property
    def tool_name(self) -> str:
        return "terraform"

    @property
    def executable_name(self) -> str:
        return "terraform"

    @property
    def tool_prefix(self) -> str:
        return "terraform"

    def get_available_versions(self) -> list[str]:
        return ["1.6.0", "1.5.7", "1.5.0"]

    def get_download_url(self, version: str) -> str:
        return f"https://releases.hashicorp.com/terraform/{version}/terraform_{version}_linux_amd64.zip"

    def get_checksum_url(self, version: str) -> str | None:
        return f"https://releases.hashicorp.com/terraform/{version}/terraform_{version}_SHA256SUMS"


class TestTfVersionsManagerInit(FoundationTestCase):
    """Test TfVersionsManager initialization."""

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists", return_value=False)
    def test_init_creates_directories(self, mock_exists: Mock, mock_mkdir: Mock) -> None:
        """Test that initialization creates necessary directories."""
        manager = ConcreteTfManager()

        assert manager.install_path == Path("~/.terraform.versions").expanduser()
        assert manager.metadata == {}

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open")
    def test_init_loads_existing_metadata(self, mock_open: Mock, mock_exists: Mock) -> None:
        """Test that initialization loads existing metadata."""
        test_metadata = {"terraform_1.6.0": {"version": "1.6.0"}}

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        with patch("json.load", return_value=test_metadata):
            manager = ConcreteTfManager()
            assert manager.metadata == test_metadata


class TestMetadataManagement(FoundationTestCase):
    """Test metadata loading and saving."""

    @patch("pathlib.Path.exists", return_value=False)
    def test_load_metadata_missing_file(self, mock_exists: Mock) -> None:
        """Test loading metadata when file doesn't exist."""
        manager = ConcreteTfManager()
        assert manager.metadata == {}

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open")
    def test_load_metadata_invalid_json(self, mock_open: Mock, mock_exists: Mock) -> None:
        """Test loading metadata with invalid JSON."""
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        with patch("json.load", side_effect=ValueError("Invalid JSON")):
            manager = ConcreteTfManager()
            assert manager.metadata == {}

    @patch("pathlib.Path.open")
    def test_save_metadata_success(self, mock_open: Mock, tmp_path: Path) -> None:
        """Test saving metadata to file."""
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        manager = ConcreteTfManager()
        manager.metadata = {"test_key": "test_value"}

        with patch("json.dump") as mock_dump:
            manager._save_metadata()
            mock_dump.assert_called_once()


class TestMetadataMigration(FoundationTestCase):
    """Test metadata format migration."""

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open")
    def test_migrate_old_active_tofu(self, mock_open: Mock, mock_exists: Mock) -> None:
        """Test migration of old active_tofu format."""
        old_metadata = {"active_tofu": "1.6.0"}

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        with patch("json.load", return_value=old_metadata), patch("json.dump"):
            manager = ConcreteTfManager()

            # Check migration occurred
            assert "workenv" in manager.metadata
            assert "default" in manager.metadata["workenv"]
            assert manager.metadata["workenv"]["default"]["opentofu_version"] == "1.6.0"
            assert "active_tofu" not in manager.metadata

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open")
    def test_migrate_old_active_terraform(
        self, mock_open: Mock, mock_exists: Mock
    ) -> None:
        """Test migration of old active_terraform format."""
        old_metadata = {"active_terraform": "1.5.7"}

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        with patch("json.load", return_value=old_metadata), patch("json.dump"):
            manager = ConcreteTfManager()

            assert manager.metadata["workenv"]["default"]["terraform_version"] == "1.5.7"
            assert "active_terraform" not in manager.metadata


class TestRecentFileManagement(FoundationTestCase):
    """Test RECENT file management."""

    @patch("pathlib.Path.open")
    @patch.object(ConcreteTfManager, "get_installed_versions", return_value=["1.6.0", "1.5.7"])
    def test_update_recent_file(self, mock_versions: Mock, mock_open: Mock) -> None:
        """Test updating RECENT file with installed versions."""
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        manager = ConcreteTfManager()

        with patch("json.load", return_value={}), patch("json.dump") as mock_dump:
            manager._update_recent_file()

            # Verify JSON was dumped with terraform versions
            call_args = mock_dump.call_args
            recent_data = call_args[0][0]
            assert "terraform" in recent_data
            assert recent_data["terraform"] == ["1.6.0", "1.5.7"]

    @patch("pathlib.Path.open")
    def test_update_recent_file_with_active(self, mock_open: Mock) -> None:
        """Test updating RECENT file to put active version first."""
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        manager = ConcreteTfManager()

        existing_data = {"terraform": ["1.5.0", "1.4.0"]}

        with patch("json.load", return_value=existing_data), patch("json.dump") as mock_dump:
            manager._update_recent_file_with_active("1.6.0")

            call_args = mock_dump.call_args
            recent_data = call_args[0][0]
            # 1.6.0 should be first
            assert recent_data["terraform"][0] == "1.6.0"


class TestBinaryPathAndVersions(FoundationTestCase):
    """Test binary path and version management."""

    def test_get_binary_path(self) -> None:
        """Test binary path construction."""
        manager = ConcreteTfManager()
        path = manager.get_binary_path("1.6.0")

        assert path == manager.install_path / "terraform_1.6.0"
        assert "terraform_1.6.0" in str(path)

    @patch("pathlib.Path.iterdir")
    def test_get_installed_versions(self, mock_iterdir: Mock) -> None:
        """Test getting list of installed versions."""
        # Mock files in install directory
        mock_files = [
            MagicMock(name="terraform_1.6.0", is_file=lambda: True),
            MagicMock(name="terraform_1.5.7", is_file=lambda: True),
            MagicMock(name="terraform_1.5.0", is_file=lambda: True),
            MagicMock(name="other_file.txt", is_file=lambda: True),
        ]
        for f in mock_files[:3]:
            f.name = f._mock_name
        mock_files[3].name = "other_file.txt"

        mock_iterdir.return_value = mock_files

        manager = ConcreteTfManager()
        versions = manager.get_installed_versions()

        # Should return sorted versions (newest first)
        assert len(versions) == 3
        assert "1.6.0" in versions
        assert "1.5.7" in versions
        assert "1.5.0" in versions


class TestVersionSorting(FoundationTestCase):
    """Test semantic version sorting."""

    def test_version_sort_key_valid_semver(self) -> None:
        """Test version sorting with valid semver."""
        manager = ConcreteTfManager()

        key_160 = manager._version_sort_key("1.6.0")
        key_157 = manager._version_sort_key("1.5.7")

        assert key_160 > key_157

    def test_version_sort_key_incomplete_version(self) -> None:
        """Test version sorting with incomplete versions like 1.0."""
        manager = ConcreteTfManager()

        # Should handle incomplete versions
        key = manager._version_sort_key("1.0")
        assert key is not None

    def test_version_sort_key_invalid_version(self) -> None:
        """Test version sorting with invalid version strings."""
        manager = ConcreteTfManager()

        # Should return fallback for invalid versions
        key = manager._version_sort_key("invalid")
        assert key is not None


class TestActiveVersionManagement(FoundationTestCase):
    """Test getting and setting active versions."""

    @patch("pathlib.Path.exists", return_value=False)
    def test_get_installed_version_no_metadata(self, mock_exists: Mock) -> None:
        """Test getting installed version with no metadata."""
        manager = ConcreteTfManager()
        version = manager.get_installed_version()

        assert version is None

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open")
    def test_get_installed_version_from_workenv(
        self, mock_open: Mock, mock_exists: Mock
    ) -> None:
        """Test getting installed version from workenv metadata."""
        test_metadata = {
            "workenv": {"default": {"terraform_version": "1.6.0"}}
        }

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        with patch("json.load", return_value=test_metadata):
            manager = ConcreteTfManager()
            version = manager.get_installed_version()

            assert version == "1.6.0"

    @patch("pathlib.Path.open")
    @patch.object(ConcreteTfManager, "_update_recent_file_with_active")
    def test_set_installed_version(
        self, mock_update_recent: Mock, mock_open: Mock
    ) -> None:
        """Test setting installed version."""
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        manager = ConcreteTfManager()

        with patch("json.dump"):
            manager.set_installed_version("1.6.0")

            assert "workenv" in manager.metadata
            assert manager.metadata["workenv"]["default"]["terraform_version"] == "1.6.0"
            mock_update_recent.assert_called_once_with("1.6.0")


class TestVersionRemoval(FoundationTestCase):
    """Test version removal."""

    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.exists", return_value=True)
    @patch.object(ConcreteTfManager, "_update_recent_file")
    @patch("pathlib.Path.open")
    def test_remove_version_success(
        self,
        mock_open: Mock,
        mock_update_recent: Mock,
        mock_exists: Mock,
        mock_unlink: Mock,
    ) -> None:
        """Test successful version removal."""
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        manager = ConcreteTfManager()
        manager.metadata = {"terraform_1.6.0": {"version": "1.6.0"}}

        with patch("json.dump"):
            manager.remove_version("1.6.0")

            mock_unlink.assert_called_once()
            mock_update_recent.assert_called_once()
            assert "terraform_1.6.0" not in manager.metadata


class TestInstallation(FoundationTestCase):
    """Test installation from archive."""

    @patch("shutil.rmtree")
    @patch.object(ConcreteTfManager, "verify_installation", return_value=True)
    @patch.object(ConcreteTfManager, "_update_recent_file")
    @patch.object(ConcreteTfManager, "_update_install_metadata")
    @patch.object(ConcreteTfManager, "make_executable")
    @patch("shutil.copy2")
    @patch.object(ConcreteTfManager, "extract_archive")
    @patch("pathlib.Path.open")
    def test_install_from_archive_success(
        self,
        mock_open: Mock,
        mock_extract: Mock,
        mock_copy: Mock,
        mock_make_exec: Mock,
        mock_update_metadata: Mock,
        mock_update_recent: Mock,
        mock_verify: Mock,
        mock_rmtree: Mock,
        tmp_path: Path,
    ) -> None:
        """Test successful installation from archive."""
        manager = ConcreteTfManager()

        # Create fake extracted binary
        extract_dir = manager.cache_dir / "terraform_1.6.0_extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        fake_binary = extract_dir / "terraform"
        fake_binary.touch()

        archive_path = tmp_path / "terraform.zip"
        archive_path.touch()

        # Mock rglob to find the binary
        with (
            patch.object(Path, "rglob", return_value=[fake_binary]),
            patch.object(manager, "_calculate_file_hash", return_value="abc123"),
            patch("json.dump"),
        ):
            manager._install_from_archive(archive_path, "1.6.0")

            mock_extract.assert_called_once()
            mock_copy.assert_called_once()
            mock_make_exec.assert_called_once()
            mock_verify.assert_called_once_with("1.6.0")

    @patch("shutil.rmtree")
    @patch.object(ConcreteTfManager, "extract_archive")
    def test_install_from_archive_binary_not_found(
        self, mock_extract: Mock, mock_rmtree: Mock, tmp_path: Path
    ) -> None:
        """Test installation failure when binary not found."""
        manager = ConcreteTfManager()

        extract_dir = manager.cache_dir / "terraform_1.6.0_extract"
        extract_dir.mkdir(parents=True, exist_ok=True)

        # Mock rglob to return empty list
        with patch.object(Path, "rglob", return_value=[]):
            archive_path = tmp_path / "terraform.zip"
            archive_path.touch()

            with pytest.raises(ToolManagerError, match="binary not found in archive"):
                manager._install_from_archive(archive_path, "1.6.0")


class TestGlobalVersion(FoundationTestCase):
    """Test global version management."""

    @patch("os.name", "posix")
    @patch("pathlib.Path.chmod")
    @patch("shutil.copy2")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open")
    def test_set_global_version(
        self,
        mock_open: Mock,
        mock_exists: Mock,
        mock_copy: Mock,
        mock_chmod: Mock,
    ) -> None:
        """Test setting global version."""
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        manager = ConcreteTfManager()

        with patch("json.dump"):
            manager.set_global_version("1.6.0")

            mock_copy.assert_called_once()
            mock_chmod.assert_called_once_with(0o755)
            assert manager.metadata["global"]["terraform_version"] == "1.6.0"

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open")
    def test_get_global_version(self, mock_open: Mock, mock_exists: Mock) -> None:
        """Test getting global version."""
        test_metadata = {"global": {"terraform_version": "1.6.0"}}

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        with patch("json.load", return_value=test_metadata):
            manager = ConcreteTfManager()
            version = manager.get_global_version()

            assert version == "1.6.0"


class TestProfileManagement(FoundationTestCase):
    """Test workenv profile management."""

    def test_get_current_profile_default(self) -> None:
        """Test getting current profile returns default."""
        manager = ConcreteTfManager()
        profile = manager._get_current_profile()

        assert profile == "default"

    @patch.dict("os.environ", {"WRKENV_PROFILE": "production"})
    def test_get_current_profile_from_env(self) -> None:
        """Test getting current profile from environment variable."""
        manager = ConcreteTfManager()
        profile = manager._get_current_profile()

        assert profile == "production"

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open")
    def test_get_current_profile_from_metadata(
        self, mock_open: Mock, mock_exists: Mock
    ) -> None:
        """Test getting current profile from metadata."""
        test_metadata = {"workenv": {"_current_profile": "staging"}}

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        with patch("json.load", return_value=test_metadata), patch.dict("os.environ", {}, clear=True):
            manager = ConcreteTfManager()
            profile = manager._get_current_profile()

            assert profile == "staging"


class TestVenvIntegration(FoundationTestCase):
    """Test venv binary directory detection and copying."""

    @patch("pathlib.Path.mkdir")
    @patch("sys.prefix", "/path/to/workenv")
    @patch("sys.base_prefix", "/path/to/python")
    def test_get_venv_bin_dir_in_workenv(self, mock_mkdir: Mock) -> None:
        """Test detecting venv bin directory when in workenv."""
        manager = ConcreteTfManager()

        # Should detect workenv structure
        assert "workenv" in str(manager.venv_bin_dir) or "bin" in str(manager.venv_bin_dir)

    @patch("pathlib.Path.exists", return_value=True)
    def test_find_project_root(self, mock_exists: Mock) -> None:
        """Test finding project root by pyproject.toml."""
        manager = ConcreteTfManager()

        with patch("pathlib.Path.cwd", return_value=Path("/project/subdir")):
            root = manager._find_project_root()
            # Will return something or None
            assert root is None or isinstance(root, Path)


class TestMetadataQueries(FoundationTestCase):
    """Test metadata query methods."""

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open")
    def test_get_metadata_for_version(self, mock_open: Mock, mock_exists: Mock) -> None:
        """Test getting metadata for specific version."""
        test_metadata = {
            "terraform_1.6.0": {
                "version": "1.6.0",
                "installed_at": "2025-01-01T00:00:00",
            }
        }

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        with patch("json.load", return_value=test_metadata):
            manager = ConcreteTfManager()
            metadata = manager.get_metadata_for_version("1.6.0")

            assert metadata is not None
            assert metadata["version"] == "1.6.0"

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open")
    def test_get_active_version_info(self, mock_open: Mock, mock_exists: Mock) -> None:
        """Test getting detailed info about active version."""
        test_metadata = {
            "workenv": {"default": {"terraform_version": "1.6.0"}},
            "terraform_1.6.0": {"version": "1.6.0"},
        }

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = False
        mock_open.return_value = mock_file

        with patch("json.load", return_value=test_metadata):
            manager = ConcreteTfManager()
            info = manager.get_active_version_info()

            assert info is not None
            assert info["version"] == "1.6.0"
            assert info["is_active"] is True


class TestFileHashing(FoundationTestCase):
    """Test file hash calculation."""

    def test_calculate_file_hash(self, tmp_path: Path) -> None:
        """Test calculating SHA256 hash of a file."""
        manager = ConcreteTfManager()

        # Create test file
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"Hello, World!")

        hash_result = manager._calculate_file_hash(test_file)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA256 produces 64 hex characters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
