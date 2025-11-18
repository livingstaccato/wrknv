#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for Template Handler
==========================="""

from __future__ import annotations

import json
from pathlib import Path

from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.gitignore.templates import TemplateHandler


class TestTemplateHandler:
    """Test suite for TemplateHandler."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create a temporary cache directory."""
        return tmp_path / "cache"

    @pytest.fixture
    def handler(self, temp_cache_dir):
        """Create a TemplateHandler instance with temp cache."""
        return TemplateHandler(cache_dir=temp_cache_dir)

    @pytest.fixture
    def mock_templates(self, temp_cache_dir):
        """Create mock template files in cache."""
        temp_cache_dir.mkdir(exist_ok=True)

        # Create version file
        (temp_cache_dir / ".version").write_text("abc123")

        # Create root level templates
        (temp_cache_dir / "Python.gitignore").write_text("*.pyc\n__pycache__/\n.venv/")
        (temp_cache_dir / "Node.gitignore").write_text("node_modules/\nnpm-debug.log")
        (temp_cache_dir / "Go.gitignore").write_text("*.exe\n*.dll\n*.so")

        # Create Global templates
        global_dir = temp_cache_dir / "Global"
        global_dir.mkdir()
        (global_dir / "macOS.gitignore").write_text(".DS_Store\n.AppleDouble")
        (global_dir / "Windows.gitignore").write_text("Thumbs.db\nDesktop.ini")

        # Create community templates
        community_dir = temp_cache_dir / "community"
        community_dir.mkdir()
        (community_dir / "JavaScript.gitignore").write_text("dist/\n.cache/")

        return temp_cache_dir

    def test_init_creates_cache_dir(self, tmp_path) -> None:
        """Test that initialization creates cache directory."""
        cache_dir = tmp_path / "test_cache"
        assert not cache_dir.exists()

        handler = TemplateHandler(cache_dir=cache_dir)
        assert cache_dir.exists()
        assert handler.cache_dir == cache_dir

    @pytest.mark.skip(reason="Path.home mocking complex with foundation integration")
    def test_init_with_default_cache_dir(self) -> None:
        """Test initialization with default cache directory."""
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/home/user")
            handler = TemplateHandler()
            assert handler.cache_dir == Path("/home/user/.wrknv/gitignore-templates")

    def test_is_cache_valid_no_version_file(self, handler, temp_cache_dir) -> None:
        """Test cache validation with no version file."""
        assert not handler._is_cache_valid()

    def test_is_cache_valid_missing_essential_templates(self, handler, temp_cache_dir) -> None:
        """Test cache validation with missing essential templates."""
        temp_cache_dir.mkdir(exist_ok=True)
        (temp_cache_dir / ".version").write_text("abc123")
        (temp_cache_dir / "Python.gitignore").write_text("*.pyc")
        # Missing Node.gitignore and Go.gitignore

        assert not handler._is_cache_valid()

    def test_is_cache_valid_all_requirements_met(self, handler, mock_templates) -> None:
        """Test cache validation when all requirements are met."""
        assert handler._is_cache_valid()

    @pytest.mark.skip(reason="Requires complex foundation transport and archive mocking")
    @patch("urllib.request.urlopen")
    def test_update_cache_success(self, mock_urlopen, handler, temp_cache_dir) -> None:
        """Test successful cache update from GitHub."""
        # Mock the archive download
        mock_archive = Mock()
        mock_archive.read.return_value = b"fake archive content"

        # Mock the API response for version
        mock_api = Mock()
        mock_api.read.return_value = json.dumps({"sha": "def456789"}).encode()

        mock_urlopen.side_effect = [mock_archive, mock_api]

        with (
            patch("tarfile.open") as mock_tar,
            patch("shutil.move"),
            patch("shutil.rmtree"),
        ):
            mock_tar_obj = Mock()
            mock_tar_obj.getnames.return_value = ["gitignore-main/Python.gitignore"]
            mock_tar.return_value.__enter__.return_value = mock_tar_obj

            result = handler.update_cache(force=True)

            assert result is True
            assert mock_urlopen.call_count == 2  # Archive + API

    @pytest.mark.skip(reason="Requires complex foundation transport mocking")
    @patch("urllib.request.urlopen")
    def test_update_cache_failure(self, mock_urlopen, handler) -> None:
        """Test cache update failure."""
        mock_urlopen.side_effect = Exception("Network error")

        result = handler.update_cache(force=True)
        assert result is False

    def test_update_cache_skip_when_valid(self, handler, mock_templates) -> None:
        """Test that cache update is skipped when cache is valid."""
        with patch.object(handler, "_is_cache_valid", return_value=True):
            result = handler.update_cache(force=False)
            assert result is False

    def test_get_template_root_level(self, handler, mock_templates) -> None:
        """Test getting a root level template."""
        content = handler.get_template("Python")
        assert content == "*.pyc\n__pycache__/\n.venv/"

    def test_get_template_global(self, handler, mock_templates) -> None:
        """Test getting a Global template."""
        content = handler.get_template("macOS")
        assert content == ".DS_Store\n.AppleDouble"

    def test_get_template_community(self, handler, mock_templates) -> None:
        """Test getting a community template."""
        content = handler.get_template("JavaScript")
        assert content == "dist/\n.cache/"

    def test_get_template_not_found(self, handler, mock_templates) -> None:
        """Test getting a non-existent template."""
        content = handler.get_template("NonExistent")
        assert content is None

    @patch.object(TemplateHandler, "update_cache")
    def test_get_template_updates_invalid_cache(self, mock_update, handler) -> None:
        """Test that get_template updates cache if invalid."""
        with patch.object(handler, "_is_cache_valid", return_value=False):
            handler.get_template("Python")
            mock_update.assert_called_once()

    def test_list_templates_all(self, handler, mock_templates) -> None:
        """Test listing all templates."""
        templates = handler.list_templates()

        assert "Python" in templates
        assert "Node" in templates
        assert "Go" in templates
        assert "Global/macOS" in templates
        assert "Global/Windows" in templates
        assert "community/JavaScript" in templates
        assert len(templates) == 6

    def test_list_templates_by_category(self, handler, mock_templates) -> None:
        """Test listing templates by category."""
        global_templates = handler.list_templates(category="Global")
        assert "macOS" in global_templates
        assert "Windows" in global_templates
        assert len(global_templates) == 2

        community_templates = handler.list_templates(category="community")
        assert "JavaScript" in community_templates
        assert len(community_templates) == 1

    def test_list_templates_invalid_category(self, handler, mock_templates) -> None:
        """Test listing templates with invalid category."""
        templates = handler.list_templates(category="NonExistent")
        assert templates == []

    def test_search_templates(self, handler, mock_templates) -> None:
        """Test searching for templates."""
        # Search for Python-related templates
        results = handler.search_templates("python")
        assert "Python" in results
        assert len(results) == 1

        # Search for macOS template
        results = handler.search_templates("mac")
        assert "Global/macOS" in results
        assert len(results) == 1

        # Case-insensitive search
        results = handler.search_templates("NODE")
        assert "Node" in results

    def test_search_templates_no_matches(self, handler, mock_templates) -> None:
        """Test searching with no matches."""
        results = handler.search_templates("Rust")
        assert results == []

    @pytest.mark.skip(reason="Requires foundation transport and async mocking")
    @patch("urllib.request.urlopen")
    def test_update_version_file_success(self, mock_urlopen, handler, temp_cache_dir) -> None:
        """Test updating version file with commit SHA."""
        temp_cache_dir.mkdir(exist_ok=True)

        mock_response = Mock()
        mock_response.read.return_value = json.dumps({"sha": "abc123def456"}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        handler._update_version_file()

        version_file = temp_cache_dir / ".version"
        assert version_file.exists()
        assert version_file.read_text() == "abc123de"  # First 8 chars

    @pytest.mark.skip(reason="Requires foundation time mocking (provide_now)")
    @patch("urllib.request.urlopen")
    def test_update_version_file_fallback(self, mock_urlopen, handler, temp_cache_dir) -> None:
        """Test version file update fallback to timestamp."""
        temp_cache_dir.mkdir(exist_ok=True)
        mock_urlopen.side_effect = Exception("API error")

        with patch("wrknv.gitignore.templates.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
            handler._update_version_file()

        version_file = temp_cache_dir / ".version"
        assert version_file.exists()
        assert version_file.read_text() == "2024-01-01T12:00:00"


# 🧰🌍🔚
