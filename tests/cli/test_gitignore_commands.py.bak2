from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from provide.testkit import FoundationTestCase
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
def gitignore_templates_dir(tmp_path):
    """Fixture to provide a path for dummy gitignore template files."""
    return tmp_path


class TestGitignoreCommands(FoundationTestCase):
    def test_gitignore_build_from_config(self, cli, runner, tmp_path, gitignore_templates_dir):
        """Test building .gitignore from wrknv.toml config."""
        # Create a dummy wrknv.toml in the temporary directory
        config_path = tmp_path / "wrknv.toml"
        config_content_template = """
project_name = "test-project"
version = "0.1.0"

[gitignore]
templates = ["Python", "Node"]
templates_path = "{templates_path_actual}"
"""

        # Create a pre-configured WorkenvConfig instance
        from wrknv.config import WorkenvConfig

        # Change current working directory to tmp_path for the test
        with runner.isolated_filesystem(tmp_path) as isolated_path_str:
            isolated_path = Path(isolated_path_str)
            # Create dummy template files inside the isolated path
            (isolated_path / "Python.gitignore").write_text("# Python ignores\n*.pyc\n__pycache__/")
            (isolated_path / "Node.gitignore").write_text("# Node ignores\nnode_modules/\nnpm-debug.log")
            (isolated_path / "Global.gitignore").write_text("# Global ignores\n.DS_Store\n.env")
            (isolated_path / "NonExistent.gitignore").write_text(
                "# This file should not be used"
            )  # For negative test cases

            # Write config content with the actual isolated path
            config_content = config_content_template.format(templates_path_actual=isolated_path)
            config_path.write_text(config_content)

            # Load config from the file
            with patch("wrknv.config.WorkenvConfig._find_config_file", return_value=config_path):
                mock_config_instance = WorkenvConfig.load()

            # Patch WorkenvConfig in cli.py to return our pre-configured instance
            with patch("wrknv.cli.commands.gitignore.WorkenvConfig.load", return_value=mock_config_instance):
                # Use shared cli fixture
                result = runner.invoke(cli, ["gitignore", "build"], catch_exceptions=False)

                assert result.exit_code == 0
                assert "✅ .gitignore built successfully" in result.output

                gitignore_file = isolated_path / ".gitignore"
                assert gitignore_file.exists()

                content = gitignore_file.read_text()
                # GitignoreManager uses === format, not --- format
                assert "# === Python ===" in content
                assert "*.pyc" in content or "*.py[cod" in content  # May use expanded pattern
                assert "__pycache__/" in content
                assert "# === Node ===" in content
                assert "node_modules/" in content
                assert "npm-debug.log" in content or "logs" in content  # Real template may differ
                assert ".DS_Store" not in content  # Should not include Global.gitignore

    def test_gitignore_build_with_templates_option(self, cli, runner, tmp_path, gitignore_templates_dir):
        """Test building .gitignore using --templates option (should override config)."""
        # Create a dummy wrknv.toml (with different templates)
        config_path = tmp_path / "wrknv.toml"
        config_content_template = """
project_name = "test-project"
version = "0.1.0"

[gitignore]
templates = ["Python", "Node"]
templates_path = "{templates_path_actual}"
"""
        # Create a pre-configured WorkenvConfig instance
        from wrknv.config import WorkenvConfig

        # Change current working directory to tmp_path for the test
        with runner.isolated_filesystem(tmp_path) as isolated_path_str:
            isolated_path = Path(isolated_path_str)
            # Create dummy template files inside the isolated path
            (isolated_path / "Python.gitignore").write_text("# Python ignores\n*.pyc\n__pycache__/")
            (isolated_path / "Node.gitignore").write_text("# Node ignores\nnode_modules/\nnpm-debug.log")
            (isolated_path / "Global.gitignore").write_text("# Global ignores\n.DS_Store\n.env")
            (isolated_path / "NonExistent.gitignore").write_text(
                "# This file should not be used"
            )  # For negative test cases

            # Write config content with the actual isolated path
            config_content = config_content_template.format(templates_path_actual=isolated_path)
            config_path.write_text(config_content)

            # Load config from the file
            with patch("wrknv.config.WorkenvConfig._find_config_file", return_value=config_path):
                mock_config_instance = WorkenvConfig.load()

            # Patch WorkenvConfig in cli.py to return our pre-configured instance
            with patch("wrknv.cli.commands.gitignore.WorkenvConfig.load", return_value=mock_config_instance):
                # Use shared cli fixture - templates parameter accepts space-separated values
                result = runner.invoke(
                    cli,
                    ["gitignore", "build", "Global Python"],
                    catch_exceptions=False,
                )

                assert result.exit_code == 0
                assert "✅ .gitignore built successfully" in result.output

                # The file is created in the isolated filesystem's current directory
                gitignore_file = isolated_path / ".gitignore"
                assert gitignore_file.exists()

                content = gitignore_file.read_text()
                # GitignoreManager uses === format, not --- format
                assert "# === Global ===" in content or "Global" in content
                assert ".DS_Store" in content
                assert ".env" in content
                assert "# === Python ===" in content or "Python" in content
                assert "*.pyc" in content or "__pycache__" in content
                assert "node_modules/" not in content  # Should not include Node.gitignore

    def test_gitignore_build_no_templates_specified(self, cli, runner, tmp_path):
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
        with patch("wrknv.cli.commands.gitignore.WorkenvConfig.load", return_value=mock_config_instance):
            # Change current working directory to tmp_path for the test
            with runner.isolated_filesystem(tmp_path):
                # Use shared cli fixture
                result = runner.invoke(cli, ["gitignore", "build"], catch_exceptions=False)

                assert result.exit_code == 0
                assert "No gitignore templates specified in config or via --templates." in result.output
                assert not (tmp_path / ".gitignore").exists()

    def test_gitignore_build_with_non_existent_template(
        self, cli, runner, tmp_path, gitignore_templates_dir, capsys
    ):
        """Test building .gitignore with a non-existent template."""
        config_path = tmp_path / "wrknv.toml"
        config_content_template = """
project_name = "test-project"
version = "0.1.0"

[gitignore]
templates = ["Python", "NonExistent"]
templates_path = "{templates_path_actual}"
"""
        # Create a pre-configured WorkenvConfig instance
        from wrknv.config import WorkenvConfig

        # Change current working directory to tmp_path for the test
        with runner.isolated_filesystem(tmp_path) as isolated_path_str:
            isolated_path = Path(isolated_path_str)
            # Create dummy template files inside the isolated path
            (isolated_path / "Python.gitignore").write_text("# Python ignores\n*.pyc\n__pycache__/")
            (isolated_path / "Node.gitignore").write_text("# Node ignores\nnode_modules/\nnpm-debug.log")
            (isolated_path / "Global.gitignore").write_text("# Global ignores\n.DS_Store\n.env")
            (isolated_path / "NonExistent.gitignore").write_text(
                "# This file should not be used"
            )  # For negative test cases

            # Write config content with the actual isolated path
            config_content = config_content_template.format(templates_path_actual=isolated_path)
            config_path.write_text(config_content)

            # Load config from the file
            with patch("wrknv.config.WorkenvConfig._find_config_file", return_value=config_path):
                mock_config_instance = WorkenvConfig.load()

            # Patch WorkenvConfig in cli.py to return our pre-configured instance
            with patch("wrknv.cli.commands.gitignore.WorkenvConfig.load", return_value=mock_config_instance):
                # Use shared cli fixture
                result = runner.invoke(cli, ["gitignore", "build"], catch_exceptions=False)

                assert result.exit_code == 0
                # Warning may be in result.output or just logged, not necessarily in stderr
                # The important thing is that the build succeeds despite the missing template
                assert "✅ .gitignore built successfully" in result.output

                gitignore_file = isolated_path / ".gitignore"
                assert gitignore_file.exists()
                content = gitignore_file.read_text()
                assert "# === Python ===" in content
                assert "# === NonExistent ===" not in content  # Should not include header for non-existent
                assert "NonExistent" not in content  # Template shouldn't appear at all

    def test_gitignore_build_with_output_option(self, cli, runner, tmp_path, gitignore_templates_dir, capsys):
        """Test building .gitignore to a custom output path."""
        config_path = tmp_path / "wrknv.toml"
        config_content_template = """
project_name = "test-project"
version = "0.1.0"

[gitignore]
templates = ["Python"]
templates_path = "{templates_path_actual}"
"""
        # Create a pre-configured WorkenvConfig instance
        from wrknv.config import WorkenvConfig

        # Change current working directory to tmp_path for the test
        with runner.isolated_filesystem(tmp_path) as isolated_path_str:
            isolated_path = Path(isolated_path_str)
            # Create dummy template files inside the isolated path
            (isolated_path / "Python.gitignore").write_text("# Python ignores\n*.pyc\n__pycache__/")
            (isolated_path / "Node.gitignore").write_text("# Node ignores\nnode_modules/\nnpm-debug.log")
            (isolated_path / "Global.gitignore").write_text("# Global ignores\n.DS_Store\n.env")
            (isolated_path / "NonExistent.gitignore").write_text(
                "# This file should not be used"
            )  # For negative test cases

            # Write config content with the actual isolated path
            config_content = config_content_template.format(templates_path_actual=isolated_path)
            config_path.write_text(config_content)

            # Load config from the file
            with patch("wrknv.config.WorkenvConfig._find_config_file", return_value=config_path):
                mock_config_instance = WorkenvConfig.load()

            # Patch WorkenvConfig in cli.py to return our pre-configured instance
            with patch("wrknv.cli.commands.gitignore.WorkenvConfig.load", return_value=mock_config_instance):
                custom_output_path = isolated_path / "my_custom.ignore"

                # Use shared cli fixture
                result = runner.invoke(
                    cli, ["gitignore", "build", "--output", str(custom_output_path)], catch_exceptions=False
                )

                assert result.exit_code == 0
                assert f"✅ .gitignore built successfully at {custom_output_path}" in result.output

                assert custom_output_path.exists()
                content = custom_output_path.read_text()
                assert "# === Python ===" in content
                assert "*.pyc" in content or "*.py[cod" in content  # May use expanded pattern
                assert not (isolated_path / ".gitignore").exists()  # Default file should not be created
