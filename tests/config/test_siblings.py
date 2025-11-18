#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test siblings configuration handling in wrknv"""

from __future__ import annotations

from provide.testkit.mocking import patch

from wrknv.wenv.env_generator import EnvScriptGenerator, create_project_env_scripts


class TestSiblingsConfiguration:
    """Test the new unified siblings configuration."""

    def test_simple_string_siblings(self, tmp_path) -> None:
        """Test simple string patterns in siblings list."""
        # Create test pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
""")

        # Create test wrknv.toml
        wrknv_toml = tmp_path / "wrknv.toml"
        wrknv_toml.write_text("""
[workenv.env]
siblings = ["pyvider-*", "test-*"]
""")

        with patch("wrknv.config.WorkenvConfig._find_config_file") as mock_find:
            mock_find.return_value = wrknv_toml

            # Generate scripts
            sh_path, _ps1_path = create_project_env_scripts(tmp_path)

            # Check that siblings are in the generated script
            sh_content = sh_path.read_text()
            assert "pyvider-*" in sh_content
            assert "test-*" in sh_content

            # Extract just the sibling section to check
            import re

            sibling_match = re.search(r"# --- Sibling Packages ---.*?(?=# ---|$)", sh_content, re.DOTALL)
            assert sibling_match, "Sibling section not found"
            sibling_section = sibling_match.group(0)

            # In the sibling section, simple strings should install with deps
            assert "uv pip install -e" in sibling_section
            assert "--no-deps" in sibling_section  # Should have --no-deps for the fallback

    def test_siblings_with_explicit_config(self, tmp_path) -> None:
        """Test siblings with explicit configuration."""
        # Create test pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
""")

        # Create test wrknv.toml
        wrknv_toml = tmp_path / "wrknv.toml"
        wrknv_toml.write_text("""
[workenv.env]
siblings = [
    {"name" = "pyvider-cty", "with_deps" = true},
    {"name" = "pyvider-telemetry", "with_deps" = false}
]
""")

        with patch("wrknv.config.WorkenvConfig._find_config_file") as mock_find:
            mock_find.return_value = wrknv_toml

            # Generate scripts
            sh_path, _ps1_path = create_project_env_scripts(tmp_path)

            # Check that siblings are in the generated script
            sh_content = sh_path.read_text()

            # Extract sibling section
            import re

            sibling_match = re.search(r"# --- Sibling Packages ---.*?(?=# ---|$)", sh_content, re.DOTALL)
            assert sibling_match, "Sibling section not found"
            sibling_section = sibling_match.group(0)

            # Check pyvider-cty (with deps)
            assert "pyvider-cty" in sibling_section
            assert "PYVIDER_CTY_DIR" in sibling_section
            assert "Installing pyvider-cty with dependencies" in sibling_section

            # Check pyvider-telemetry (without deps)
            assert "pyvider-telemetry" in sibling_section
            assert "PYVIDER_TELEMETRY_DIR" in sibling_section
            assert "Installing pyvider-telemetry without dependencies" in sibling_section
            assert "--no-deps" in sibling_section  # Should have --no-deps for telemetry

    def test_siblings_with_pattern_config(self, tmp_path) -> None:
        """Test siblings with pattern configuration."""
        # Create test pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
""")

        # Create test wrknv.toml
        wrknv_toml = tmp_path / "wrknv.toml"
        wrknv_toml.write_text("""
[workenv.env]
siblings = [
    {"pattern" = "pyvider-*", "with_deps" = false},
    {"pattern" = "test-*", "with_deps" = true}
]
""")

        with patch("wrknv.config.WorkenvConfig._find_config_file") as mock_find:
            mock_find.return_value = wrknv_toml

            # Generate scripts
            sh_path, _ps1_path = create_project_env_scripts(tmp_path)

            # Check that patterns are in the generated script
            sh_content = sh_path.read_text()
            assert "pyvider-*" in sh_content
            assert "test-*" in sh_content
            assert "without dependencies" in sh_content
            assert "with dependencies" in sh_content

    def test_mixed_siblings_config(self, tmp_path) -> None:
        """Test mixing different sibling configurations."""
        # Create test pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
""")

        # Create test wrknv.toml
        wrknv_toml = tmp_path / "wrknv.toml"
        wrknv_toml.write_text("""
[workenv.env]
siblings = [
    "simple-pattern-*",
    {"pattern" = "configured-*", "with_deps" = false},
    {"name" = "explicit-package", "with_deps" = true, "var_name" = "explicit_pkg"}
]
""")

        with patch("wrknv.config.WorkenvConfig._find_config_file") as mock_find:
            mock_find.return_value = wrknv_toml

            # Generate scripts
            sh_path, _ps1_path = create_project_env_scripts(tmp_path)

            # Check all types are in the generated script
            sh_content = sh_path.read_text()
            assert "simple-pattern-*" in sh_content
            assert "configured-*" in sh_content
            assert "explicit-package" in sh_content
            assert "EXPLICIT_PKG_DIR" in sh_content  # Custom var name

    def test_backward_compatibility(self, tmp_path) -> None:
        """Test backward compatibility with old format."""
        # Create test pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
""")

        # Create test wrknv.toml with old format
        wrknv_toml = tmp_path / "wrknv.toml"
        wrknv_toml.write_text("""
[workenv.env]
sibling_patterns = ["pyvider-*"]
special_siblings = [
    {"name" = "tofusoup", "var_name" = "tofusoup", "with_deps" = true}
]
""")

        with patch("wrknv.config.WorkenvConfig._find_config_file") as mock_find:
            mock_find.return_value = wrknv_toml

            # Generate scripts
            sh_path, _ps1_path = create_project_env_scripts(tmp_path)

            # Check that old format still works
            sh_content = sh_path.read_text()
            assert "pyvider-*" in sh_content
            assert "tofusoup" in sh_content
            assert "TOFUSOUP_DIR" in sh_content
            # Old pattern format always uses --no-deps
            assert "--no-deps" in sh_content

    def test_default_with_deps_behavior(self, tmp_path) -> None:
        """Test that with_deps defaults to true for new format."""
        generator = EnvScriptGenerator()

        context = {
            "project_name": "test",
            "siblings": [
                {"name": "package1"},  # No with_deps specified
                {"name": "package2", "with_deps": True},
                {"name": "package3", "with_deps": False},
            ],
            "use_spinner": False,
        }

        # Generate shell script
        sh_template = generator.sh_env.get_template("sibling_packages.sh.j2")
        sh_content = sh_template.render(**context)

        # package1 should default to with_deps=true
        assert "Installing package1 with dependencies" in sh_content
        # package2 explicitly with deps
        assert "Installing package2 with dependencies" in sh_content
        # package3 explicitly without deps
        assert "Installing package3 without dependencies" in sh_content
        assert "--no-deps" in sh_content  # Only for package3

    def test_powershell_siblings_generation(self, tmp_path) -> None:
        """Test PowerShell script generation with siblings."""
        # Create test pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
""")

        # Create test wrknv.toml
        wrknv_toml = tmp_path / "wrknv.toml"
        wrknv_toml.write_text("""
[workenv.env]
siblings = [
    "simple-*",
    {"name" = "explicit-pkg", "with_deps" = false}
]
""")

        with patch("wrknv.config.WorkenvConfig._find_config_file") as mock_find:
            mock_find.return_value = wrknv_toml

            # Generate scripts
            _sh_path, ps1_path = create_project_env_scripts(tmp_path)

            # Check PowerShell script
            ps1_content = ps1_path.read_text()
            assert "simple-*" in ps1_content
            assert "explicit-pkg" in ps1_content
            assert "$WithDeps = $false" in ps1_content
            assert "--no-deps" in ps1_content


class TestSiblingsConfigIntegration:
    """Integration tests for siblings configuration."""

    def test_env_generator_processes_siblings_correctly(self, tmp_path) -> None:
        """Test that env generator correctly processes siblings config."""
        # Create a more complex scenario
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "complex-project"
""")

        wrknv_toml = tmp_path / "wrknv.toml"
        wrknv_toml.write_text("""
[workenv.env]
include_tool_verification = false
siblings = [
    "auto-discovered-*",
    { pattern = "pyvider-*", with_deps = true },
    { name = "special-package", var_name = "special", with_deps = false }
]
""")

        with patch("wrknv.config.WorkenvConfig._find_config_file") as mock_find:
            mock_find.return_value = wrknv_toml

            sh_path, ps1_path = create_project_env_scripts(tmp_path)

            # Verify both scripts were created
            assert sh_path.exists()
            assert ps1_path.exists()

            # Check shell script content
            sh_content = sh_path.read_text()

            # Should have all three sibling types
            assert "auto-discovered-*" in sh_content
            assert "pyvider-*" in sh_content
            assert "special-package" in sh_content

            # Check variable name customization
            assert "SPECIAL_DIR" in sh_content

            # Check PowerShell has similar content
            ps1_content = ps1_path.read_text()
            assert "auto-discovered-*" in ps1_content
            assert "special-package" in ps1_content


# 🧰🌍🔚
