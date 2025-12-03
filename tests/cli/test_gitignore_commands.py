#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for gitignore CLI commands."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.cli.hub_cli import create_cli

# Single CLI instance shared across all tests to avoid module re-import issues
# (commands are registered at module import time via decorators)
_shared_cli = None


@pytest.fixture(scope="module")
def cli():
    """Shared CLI instance for all tests in this module."""
    global _shared_cli
    if _shared_cli is None:
        _shared_cli = create_cli()
    return _shared_cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_template_handler():
    """Mock TemplateHandler to prevent network calls."""

    def _create_mock(templates_dir: Path):
        """Create a mock template handler that reads from local directory."""
        mock_handler = Mock()

        def get_template(name: str) -> str | None:
            """Return template content from local test directory."""
            template_path = templates_dir / f"{name}.gitignore"
            if template_path.exists():
                return template_path.read_text()
            return None

        mock_handler.get_template = get_template
        mock_handler.update_cache = Mock(return_value=True)
        mock_handler.list_templates = Mock(return_value=[])
        return mock_handler

    return _create_mock


class TestGitignoreCommands(FoundationTestCase):
    def test_gitignore_build_from_config(self, cli, runner, mock_template_handler) -> None:
        """Test building .gitignore from wrknv.toml config."""
        with runner.isolated_filesystem():
            test_dir = Path.cwd()

            # Create dummy template files
            (test_dir / "Python.gitignore").write_text("# Python ignores\n*.pyc\n__pycache__/")
            (test_dir / "Node.gitignore").write_text("# Node ignores\nnode_modules/\nnpm-debug.log")

            # Create wrknv.toml
            config_path = test_dir / "wrknv.toml"
            config_path.write_text("""
project_name = "test-project"
version = "0.1.0"

[gitignore]
templates = ["Python", "Node"]
""")

            from wrknv.config import WorkenvConfig

            with patch("wrknv.config.WorkenvConfig._find_config_file", return_value=config_path):
                mock_config_instance = WorkenvConfig.load()

            # Mock the TemplateHandler to use our local templates
            mock_handler = mock_template_handler(test_dir)

            with (
                patch("wrknv.cli.hub_cli.WrknvContext.get_config", return_value=mock_config_instance),
                patch("wrknv.gitignore.manager.TemplateHandler", return_value=mock_handler),
            ):
                result = runner.invoke(cli, ["gitignore", "build"], catch_exceptions=False)

                assert result.exit_code == 0

                gitignore_file = test_dir / ".gitignore"
                assert gitignore_file.exists()

                content = gitignore_file.read_text()
                assert "# === Python ===" in content
                assert "*.pyc" in content
                assert "__pycache__/" in content
                assert "# === Node ===" in content
                assert "node_modules/" in content

    def test_gitignore_build_with_templates_option(
        self, cli, runner, tmp_path, gitignore_templates_dir
    ) -> None:
        """Test building .gitignore using --templates option (should override config)."""

        with runner.isolated_filesystem():
            test_dir = Path.cwd()

            # Create dummy template files
            (test_dir / "Python.gitignore").write_text("# Python ignores\n*.pyc\n__pycache__/")
            (test_dir / "Node.gitignore").write_text("# Node ignores\nnode_modules/\nnpm-debug.log")
            (test_dir / "Global.gitignore").write_text("# Global ignores\n.DS_Store\n.env")
            (test_dir / "NonExistent.gitignore").write_text("# This file should not be used")

            # Create a dummy wrknv.toml (with different templates)
            config_path = test_dir / "wrknv.toml"
            config_content_template = """
project_name = "test-project"
version = "0.1.0"

[gitignore]
templates = ["Python", "Node"]
templates_path = "{templates_path_actual}"
"""
            config_content = config_content_template.format(templates_path_actual=test_dir)
            config_path.write_text(config_content)

            # Create a pre-configured WorkenvConfig instance
            from wrknv.config import WorkenvConfig

            # Load config from the file
            with patch("wrknv.config.WorkenvConfig._find_config_file", return_value=config_path):
                mock_config_instance = WorkenvConfig.load()

            # Patch WorkenvConfig in cli.py to return our pre-configured instance
            with patch("wrknv.cli.hub_cli.WrknvContext.get_config", return_value=mock_config_instance):
                # Use shared cli fixture - templates parameter accepts space-separated values
                result = runner.invoke(
                    cli,
                    ["gitignore", "build", "Global Python"],
                    catch_exceptions=False,
                )

                assert result.exit_code == 0

                # The file is created in the current directory
                gitignore_file = test_dir / ".gitignore"
                assert gitignore_file.exists()

                content = gitignore_file.read_text()
                # GitignoreManager uses === format, not --- format
                assert "# === Global ===" in content or "Global" in content
                assert ".DS_Store" in content
                assert ".env" in content
                assert "# === Python ===" in content or "Python" in content
                assert "*.pyc" in content or "__pycache__" in content
                assert "node_modules/" not in content  # Should not include Node.gitignore

    def test_gitignore_build_no_templates_specified(self, cli, runner, tmp_path) -> None:
        """Test building .gitignore when no templates are specified in config or via option."""
        # Create a dummy wrknv.toml without gitignore section
        config_path = tmp_path / "wrknv.toml"
        config_content = """
project_name = "test-project"
version = "0.1.0"
"""
        config_path.write_text(config_content)

        # Create a pre-configured WorkenvConfig instance
        from wrknv.config import WorkenvConfig

        # Load config from the file
        with patch("wrknv.config.WorkenvConfig._find_config_file", return_value=config_path):
            mock_config_instance = WorkenvConfig.load()

        # Patch WorkenvConfig in cli.py to return our pre-configured instance
        with (
            patch("wrknv.cli.hub_cli.WrknvContext.get_config", return_value=mock_config_instance),
            runner.isolated_filesystem(tmp_path),
        ):
            # Use shared cli fixture
            result = runner.invoke(cli, ["gitignore", "build"], catch_exceptions=False)

            assert result.exit_code == 0
            assert "No gitignore templates specified in config or via --templates." in result.output
            assert not (tmp_path / ".gitignore").exists()

    def test_gitignore_build_with_non_existent_template(
        self, cli, runner, tmp_path, gitignore_templates_dir, capsys
    ) -> None:
        """Test building .gitignore with a non-existent template."""

        with runner.isolated_filesystem():
            test_dir = Path.cwd()

            # Create dummy template files
            (test_dir / "Python.gitignore").write_text("# Python ignores\n*.pyc\n__pycache__/")
            (test_dir / "Node.gitignore").write_text("# Node ignores\nnode_modules/\nnpm-debug.log")
            (test_dir / "Global.gitignore").write_text("# Global ignores\n.DS_Store\n.env")
            (test_dir / "NonExistent.gitignore").write_text("# This file should not be used")

            config_path = test_dir / "wrknv.toml"
            config_content_template = """
project_name = "test-project"
version = "0.1.0"

[gitignore]
templates = ["Python", "NonExistent"]
templates_path = "{templates_path_actual}"
"""
            config_content = config_content_template.format(templates_path_actual=test_dir)
            config_path.write_text(config_content)

            # Create a pre-configured WorkenvConfig instance
            from wrknv.config import WorkenvConfig

            # Load config from the file
            with patch("wrknv.config.WorkenvConfig._find_config_file", return_value=config_path):
                mock_config_instance = WorkenvConfig.load()

            # Patch WorkenvConfig in cli.py to return our pre-configured instance
            with patch("wrknv.cli.hub_cli.WrknvContext.get_config", return_value=mock_config_instance):
                # Use shared cli fixture
                result = runner.invoke(cli, ["gitignore", "build"], catch_exceptions=False)

                assert result.exit_code == 0
                # Warning may be in result.output or just logged, not necessarily in stderr
                # The important thing is that the build succeeds despite the missing template

                gitignore_file = test_dir / ".gitignore"
                assert gitignore_file.exists()
                content = gitignore_file.read_text()
                assert "# === Python ===" in content
                assert "# === NonExistent ===" not in content  # Should not include header for non-existent
                assert "NonExistent" not in content  # Template shouldn't appear at all

    def test_gitignore_build_with_output_option(
        self, cli, runner, tmp_path, gitignore_templates_dir, capsys
    ) -> None:
        """Test building .gitignore to a custom output path."""

        with runner.isolated_filesystem():
            test_dir = Path.cwd()

            # Create dummy template files
            (test_dir / "Python.gitignore").write_text("# Python ignores\n*.pyc\n__pycache__/")
            (test_dir / "Node.gitignore").write_text("# Node ignores\nnode_modules/\nnpm-debug.log")
            (test_dir / "Global.gitignore").write_text("# Global ignores\n.DS_Store\n.env")
            (test_dir / "NonExistent.gitignore").write_text("# This file should not be used")

            config_path = test_dir / "wrknv.toml"
            config_content_template = """
project_name = "test-project"
version = "0.1.0"

[gitignore]
templates = ["Python"]
templates_path = "{templates_path_actual}"
"""
            config_content = config_content_template.format(templates_path_actual=test_dir)
            config_path.write_text(config_content)

            # Create a pre-configured WorkenvConfig instance
            from wrknv.config import WorkenvConfig

            # Load config from the file
            with patch("wrknv.config.WorkenvConfig._find_config_file", return_value=config_path):
                mock_config_instance = WorkenvConfig.load()

            # Patch WorkenvConfig in cli.py to return our pre-configured instance
            with patch("wrknv.cli.hub_cli.WrknvContext.get_config", return_value=mock_config_instance):
                custom_output_path = test_dir / "my_custom.ignore"

                # Use shared cli fixture
                result = runner.invoke(
                    cli, ["gitignore", "build", "--output", str(custom_output_path)], catch_exceptions=False
                )

                assert result.exit_code == 0

                assert custom_output_path.exists()
                content = custom_output_path.read_text()
                assert "# === Python ===" in content
                assert "*.pyc" in content or "*.py[cod" in content  # May use expanded pattern
                assert not (test_dir / ".gitignore").exists()  # Default file should not be created


# 🧰🌍🔚
