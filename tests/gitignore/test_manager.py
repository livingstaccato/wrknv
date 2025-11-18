#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for Gitignore Manager
============================"""

from __future__ import annotations

from pathlib import Path

from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.gitignore.manager import GitignoreManager


class TestGitignoreManager:
    """Test suite for GitignoreManager."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory."""
        test_project = tmp_path / "test_project"
        test_project.mkdir(exist_ok=True)
        return test_project

    @pytest.fixture
    def mock_template_handler(self):
        """Create a mock template handler."""
        handler = Mock()
        handler.get_template.side_effect = lambda name: {
            "Python": "*.pyc\n__pycache__/",
            "Node": "node_modules/\nnpm-debug.log",
            "macOS": ".DS_Store",
            "Docker": "*.pid\n*.log",
        }.get(name)
        handler.list_templates.return_value = ["Python", "Node", "macOS", "Docker"]
        handler.search_templates.return_value = []
        return handler

    @pytest.fixture
    def mock_detector(self):
        """Create a mock project detector."""
        detector = Mock()
        detector.detected_languages = {"Python"}
        detector.detected_frameworks = set()
        detector.detected_tools = {"Docker"}
        detector.detected_os = {"macOS"}
        detector.suggest_templates.return_value = ["Python", "Docker", "macOS"]
        return detector

    def test_init_with_project_dir(self, temp_dir) -> None:
        """Test initialization with project directory."""
        manager = GitignoreManager(project_dir=temp_dir)
        assert manager.project_dir == temp_dir
        assert manager.gitignore_path == temp_dir / ".gitignore"

    def test_init_with_custom_output(self, temp_dir) -> None:
        """Test initialization with custom output path."""
        output_path = temp_dir / "custom.gitignore"
        manager = GitignoreManager(project_dir=temp_dir, output_path=output_path)
        assert manager.gitignore_path == output_path

    def test_init_default_project_dir(self) -> None:
        """Test initialization with default project directory."""
        manager = GitignoreManager()
        assert manager.project_dir == Path.cwd()

    @patch("wrknv.gitignore.manager.TemplateHandler")
    @patch("wrknv.gitignore.manager.ProjectDetector")
    def test_build_from_templates(self, mock_detector_class, mock_handler_class, temp_dir) -> None:
        """Test building gitignore from specific templates."""
        mock_handler = Mock()
        mock_handler.get_template.side_effect = lambda name: {
            "Python": "*.pyc\n__pycache__/",
            "Node": "node_modules/",
        }.get(name)
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        manager.build_from_templates(["Python", "Node"])

        gitignore_file = temp_dir / ".gitignore"
        assert gitignore_file.exists()

        content = gitignore_file.read_text()
        assert "*.pyc" in content
        assert "__pycache__/" in content
        assert "node_modules/" in content
        assert "=== Python ===" in content
        assert "=== Node ===" in content

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_build_from_templates_with_custom_rules(self, mock_handler_class, temp_dir) -> None:
        """Test building with custom rules."""
        mock_handler = Mock()
        mock_handler.get_template.return_value = "*.pyc"
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        manager.build_from_templates(["Python"], custom_rules=["*.secret", "local.conf"])

        content = temp_dir / ".gitignore"
        content_text = content.read_text()
        assert "*.secret" in content_text
        assert "local.conf" in content_text
        assert "=== Custom Rules ===" in content_text

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_build_from_templates_missing_template(self, mock_handler_class, temp_dir) -> None:
        """Test building with missing template."""
        mock_handler = Mock()
        mock_handler.get_template.return_value = None
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        with patch("wrknv.gitignore.manager.logger") as mock_logger:
            manager.build_from_templates(["NonExistent"])
            mock_logger.warning.assert_called_with("Template 'NonExistent' not found")

    @patch("wrknv.gitignore.manager.TemplateHandler")
    @patch("wrknv.gitignore.manager.ProjectDetector")
    def test_build_from_detection(self, mock_detector_class, mock_handler_class, temp_dir) -> None:
        """Test building gitignore from auto-detection."""
        # Set up mock detector
        mock_detector = Mock()
        mock_detector.suggest_templates.return_value = ["Python", "Docker"]
        mock_detector_class.return_value = mock_detector

        # Set up mock handler
        mock_handler = Mock()
        mock_handler.get_template.side_effect = lambda name: {
            "Python": "*.pyc",
            "Docker": "*.pid",
        }.get(name)
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        manager.build_from_detection()

        mock_detector.scan_directory.assert_called_once_with(temp_dir, max_depth=5)

        content = temp_dir / ".gitignore"
        content_text = content.read_text()
        assert "*.pyc" in content_text
        assert "*.pid" in content_text

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_add_templates_to_existing(self, mock_handler_class, temp_dir) -> None:
        """Test adding templates to existing gitignore."""
        # Create existing gitignore
        existing_file = temp_dir / ".gitignore"
        existing_file.write_text("# Existing\n*.log\n\n# === Custom Rules ===\n*.secret")

        mock_handler = Mock()
        mock_handler.get_template.return_value = "*.pyc"
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        manager.add_templates(["Python"])

        content = existing_file.read_text()
        assert "*.pyc" in content
        assert "*.log" in content  # Original content preserved
        assert "*.secret" in content  # Custom rules preserved

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_list_available_templates(self, mock_handler_class, temp_dir) -> None:
        """Test listing available templates."""
        mock_handler = Mock()
        mock_handler.list_templates.return_value = ["Python", "Node", "Go"]
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        templates = manager.list_available_templates()

        assert templates == ["Python", "Node", "Go"]
        mock_handler.list_templates.assert_called_once_with(category=None)

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_list_available_templates_by_category(self, mock_handler_class, temp_dir) -> None:
        """Test listing templates by category."""
        mock_handler = Mock()
        mock_handler.list_templates.return_value = ["macOS", "Windows"]
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        templates = manager.list_available_templates(category="Global")

        assert templates == ["macOS", "Windows"]
        mock_handler.list_templates.assert_called_once_with(category="Global")

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_search_templates(self, mock_handler_class, temp_dir) -> None:
        """Test searching for templates."""
        mock_handler = Mock()
        mock_handler.search_templates.return_value = ["Python", "PureScript"]
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        results = manager.search_templates("py")

        assert results == ["Python", "PureScript"]
        mock_handler.search_templates.assert_called_once_with("py")

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_update_templates(self, mock_handler_class, temp_dir) -> None:
        """Test updating template cache."""
        mock_handler = Mock()
        mock_handler.update_cache.return_value = True
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        result = manager.update_templates(force=True)

        assert result is True
        mock_handler.update_cache.assert_called_once_with(force=True)

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_preview_no_templates(self, mock_handler_class, temp_dir) -> None:
        """Test preview with no templates."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        preview = manager.preview([])
        assert "No templates specified" in preview

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_preview_with_templates(self, mock_handler_class, temp_dir) -> None:
        """Test preview with templates."""
        mock_handler = Mock()
        mock_handler.get_template.side_effect = lambda name: {
            "Python": "*.pyc\n__pycache__/",
            "Node": "node_modules/",
        }.get(name)
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        preview = manager.preview(["Python", "Node"])

        assert "=== Python ===" in preview
        assert "*.pyc" in preview
        assert "=== Node ===" in preview
        assert "node_modules/" in preview

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_build_with_exclude_patterns(self, mock_handler_class, temp_dir) -> None:
        """Test building with exclude patterns."""
        mock_handler = Mock()
        mock_handler.get_template.return_value = "*.pyc\n*.md\n__pycache__/"
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        manager.build_from_templates(["Python"], exclude_patterns=["*.md"])

        content = temp_dir / ".gitignore"
        content_text = content.read_text()
        assert "*.pyc" in content_text
        assert "__pycache__/" in content_text
        assert "*.md" not in content_text  # Excluded pattern

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_build_with_append_mode(self, mock_handler_class, temp_dir) -> None:
        """Test building in append mode."""
        # Create existing file
        existing_file = temp_dir / ".gitignore"
        existing_file.write_text("# Original\n*.log")

        mock_handler = Mock()
        mock_handler.get_template.return_value = "*.pyc"
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        manager.build_from_templates(["Python"], append=True)

        content = existing_file.read_text()
        assert "# Original" in content
        assert "*.log" in content
        assert "*.pyc" in content

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_build_with_overwrite_mode(self, mock_handler_class, temp_dir) -> None:
        """Test building in overwrite mode."""
        # Create existing file
        existing_file = temp_dir / ".gitignore"
        existing_file.write_text("# Original\n*.obsolete\n\n# === Custom Rules ===\n*.secret")

        mock_handler = Mock()
        mock_handler.get_template.return_value = "*.pyc"
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        manager.build_from_templates(["Python"], append=False)

        content = existing_file.read_text()
        assert "# Original" not in content  # Original content gone
        assert "*.obsolete" not in content  # Original pattern removed
        assert "*.log" in content  # Provide section adds *.log
        assert "*.secret" in content  # Custom rules preserved
        assert "*.pyc" in content

    @patch("wrknv.gitignore.manager.TemplateHandler")
    @patch("wrknv.gitignore.manager.ProjectDetector")
    def test_get_detection_report(self, mock_detector_class, mock_handler_class, temp_dir) -> None:
        """Test getting detection report."""
        # Mock handler
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler

        # Mock detector
        mock_detector = Mock()
        mock_detector.detected_languages = {"Python", "JavaScript"}
        mock_detector.detected_frameworks = {"Django"}
        mock_detector.detected_tools = {"Docker", "Poetry"}
        mock_detector.detected_os = {"macOS"}
        mock_detector_class.return_value = mock_detector

        manager = GitignoreManager(project_dir=temp_dir)
        report = manager.get_detection_report()

        assert "Languages: JavaScript, Python" in report or "Languages: Python, JavaScript" in report
        assert "Frameworks: Django" in report
        assert "Tools: Docker, Poetry" in report or "Tools: Poetry, Docker" in report
        assert "OS: macOS" in report

    @patch("wrknv.gitignore.manager.TemplateHandler")
    def test_build_from_config(self, mock_handler_class, temp_dir) -> None:
        """Test building from configuration object."""
        from wrknv.wenv.schema import GitignoreConfig

        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler

        manager = GitignoreManager(project_dir=temp_dir)
        config = GitignoreConfig(
            templates=["Python", "Node"], custom_rules=["*.secret"], exclude_patterns=["*.md"]
        )

        with patch.object(manager, "build_from_templates") as mock_build:
            manager.build_from_config(config)
            mock_build.assert_called_once_with(
                templates=["Python", "Node"],
                custom_rules=["*.secret"],
                exclude_patterns=["*.md"],
                append=False,
            )


# 🧰🌍🔚
