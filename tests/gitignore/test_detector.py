#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for Project Detector
==========================="""

from __future__ import annotations

import pytest

from wrknv.gitignore.detector import ProjectDetector


class TestProjectDetector:
    """Test suite for ProjectDetector."""

    @pytest.fixture
    def detector(self):
        """Create a ProjectDetector instance."""
        return ProjectDetector()

    @pytest.fixture
    def project_dir(self, tmp_path):
        """Create a temporary project directory."""
        return tmp_path / "project"

    def test_init(self, detector) -> None:
        """Test detector initialization."""
        assert detector.detected_languages == set()
        assert detector.detected_frameworks == set()
        assert detector.detected_tools == set()
        assert detector.detected_os == set()

    def test_detect_python_files(self, detector, project_dir) -> None:
        """Test detection of Python project."""
        project_dir.mkdir()
        (project_dir / "main.py").touch()
        (project_dir / "test_main.py").touch()
        (project_dir / "src").mkdir()
        (project_dir / "src" / "module.py").touch()

        detector.scan_directory(project_dir)

        assert "Python" in detector.detected_languages

    def test_detect_python_requirements(self, detector, project_dir) -> None:
        """Test detection of Python requirements files."""
        project_dir.mkdir()
        (project_dir / "requirements.txt").touch()

        detector.scan_directory(project_dir)

        assert "Python" in detector.detected_languages

    def test_detect_python_tools(self, detector, project_dir) -> None:
        """Test detection of Python tools."""
        project_dir.mkdir()

        # Poetry
        (project_dir / "poetry.lock").touch()
        detector.scan_directory(project_dir)
        assert "Poetry" in detector.detected_tools

        # PDM
        detector.reset()
        (project_dir / "pdm.lock").touch()
        detector.scan_directory(project_dir)
        assert "PDM" in detector.detected_tools

        # Pipenv
        detector.reset()
        (project_dir / "Pipfile.lock").touch()
        detector.scan_directory(project_dir)
        assert "Pipenv" in detector.detected_tools

        # Ruff
        detector.reset()
        (project_dir / ".ruff_cache").mkdir()
        detector.scan_directory(project_dir)
        assert "Ruff" in detector.detected_tools

    def test_detect_javascript_files(self, detector, project_dir) -> None:
        """Test detection of JavaScript project."""
        project_dir.mkdir()
        (project_dir / "index.js").touch()
        (project_dir / "app.mjs").touch()

        detector.scan_directory(project_dir)

        assert "Node" in detector.detected_languages

    def test_detect_node_package_json(self, detector, project_dir) -> None:
        """Test detection of Node.js via package.json."""
        project_dir.mkdir()
        (project_dir / "package.json").touch()

        detector.scan_directory(project_dir)

        assert "Node" in detector.detected_languages

    def test_detect_typescript(self, detector, project_dir) -> None:
        """Test detection of TypeScript."""
        project_dir.mkdir()
        (project_dir / "index.ts").touch()
        (project_dir / "tsconfig.json").touch()

        detector.scan_directory(project_dir)

        assert "TypeScript" in detector.detected_languages
        assert "Node" in detector.detected_languages  # TypeScript implies Node

    def test_detect_go_files(self, detector, project_dir) -> None:
        """Test detection of Go project."""
        project_dir.mkdir()
        (project_dir / "main.go").touch()
        (project_dir / "go.mod").touch()

        detector.scan_directory(project_dir)

        assert "Go" in detector.detected_languages

    def test_detect_rust_files(self, detector, project_dir) -> None:
        """Test detection of Rust project."""
        project_dir.mkdir()
        (project_dir / "main.rs").touch()
        (project_dir / "Cargo.toml").touch()

        detector.scan_directory(project_dir)

        assert "Rust" in detector.detected_languages

    def test_detect_java_files(self, detector, project_dir) -> None:
        """Test detection of Java project."""
        project_dir.mkdir()
        (project_dir / "Main.java").touch()
        (project_dir / "pom.xml").touch()

        detector.scan_directory(project_dir)

        assert "Java" in detector.detected_languages
        assert "Maven" in detector.detected_tools

    def test_detect_gradle(self, detector, project_dir) -> None:
        """Test detection of Gradle."""
        project_dir.mkdir()
        (project_dir / "build.gradle").touch()

        detector.scan_directory(project_dir)

        assert "Gradle" in detector.detected_tools

    def test_detect_docker(self, detector, project_dir) -> None:
        """Test detection of Docker."""
        project_dir.mkdir()
        (project_dir / "Dockerfile").touch()
        (project_dir / "docker-compose.yml").touch()

        detector.scan_directory(project_dir)

        assert "Docker" in detector.detected_tools

    def test_detect_terraform(self, detector, project_dir) -> None:
        """Test detection of Terraform."""
        project_dir.mkdir()
        (project_dir / "main.tf").touch()
        (project_dir / "variables.tf").touch()

        detector.scan_directory(project_dir)

        assert "Terraform" in detector.detected_tools

    def test_detect_os_files(self, detector, project_dir) -> None:
        """Test detection of OS-specific files."""
        project_dir.mkdir()

        # macOS
        (project_dir / ".DS_Store").touch()
        detector.scan_directory(project_dir)
        assert "macOS" in detector.detected_os

        # Windows
        detector.reset()
        (project_dir / "Thumbs.db").touch()
        detector.scan_directory(project_dir)
        assert "Windows" in detector.detected_os

    def test_detect_ide_files(self, detector, project_dir) -> None:
        """Test detection of IDE files."""
        project_dir.mkdir()

        # VS Code
        (project_dir / ".vscode").mkdir()
        detector.scan_directory(project_dir)
        assert "VisualStudioCode" in detector.detected_tools

        # JetBrains
        detector.reset()
        (project_dir / ".idea").mkdir()
        detector.scan_directory(project_dir)
        assert "JetBrains" in detector.detected_tools

    def test_detect_react(self, detector, project_dir) -> None:
        """Test detection of React framework."""
        project_dir.mkdir()
        package_json = project_dir / "package.json"
        package_json.write_text('{"dependencies": {"react": "^18.0.0"}}')

        detector.scan_directory(project_dir)

        assert "React" in detector.detected_frameworks

    def test_detect_vue(self, detector, project_dir) -> None:
        """Test detection of Vue framework."""
        project_dir.mkdir()
        package_json = project_dir / "package.json"
        package_json.write_text('{"dependencies": {"vue": "^3.0.0"}}')

        detector.scan_directory(project_dir)

        assert "Vue" in detector.detected_frameworks

    def test_detect_django(self, detector, project_dir) -> None:
        """Test detection of Django framework."""
        project_dir.mkdir()
        (project_dir / "manage.py").touch()
        (project_dir / "settings.py").touch()

        detector.scan_directory(project_dir)

        assert "Django" in detector.detected_frameworks

    def test_detect_flask(self, detector, project_dir) -> None:
        """Test detection of Flask framework."""
        project_dir.mkdir()
        requirements = project_dir / "requirements.txt"
        requirements.write_text("flask>=2.0.0\nflask-cors")

        detector.scan_directory(project_dir)

        assert "Flask" in detector.detected_frameworks

    def test_suggest_templates(self, detector, project_dir) -> None:
        """Test template suggestions based on detection."""
        project_dir.mkdir()
        (project_dir / "main.py").touch()
        (project_dir / "requirements.txt").touch()
        (project_dir / ".DS_Store").touch()
        (project_dir / ".vscode").mkdir()

        detector.scan_directory(project_dir)
        suggestions = detector.suggest_templates()

        assert "Python" in suggestions
        assert "macOS" in suggestions
        assert "VisualStudioCode" in suggestions

    def test_suggest_templates_with_priority(self, detector, project_dir) -> None:
        """Test that suggestions are prioritized correctly."""
        project_dir.mkdir()
        (project_dir / "main.py").touch()
        (project_dir / "poetry.lock").touch()
        (project_dir / "manage.py").touch()  # Django

        detector.scan_directory(project_dir)
        suggestions = detector.suggest_templates()

        # Languages should come first
        assert suggestions[0] == "Python"
        # Frameworks should come before tools
        assert suggestions.index("Django") < suggestions.index("Poetry")

    def test_reset(self, detector, project_dir) -> None:
        """Test resetting detector state."""
        project_dir.mkdir()
        (project_dir / "main.py").touch()

        detector.scan_directory(project_dir)
        assert "Python" in detector.detected_languages

        detector.reset()
        assert detector.detected_languages == set()
        assert detector.detected_frameworks == set()
        assert detector.detected_tools == set()
        assert detector.detected_os == set()

    def test_scan_ignores_hidden_directories(self, detector, project_dir) -> None:
        """Test that hidden directories are ignored by default."""
        project_dir.mkdir()
        git_dir = project_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").touch()

        # Should not detect Git internals
        detector.scan_directory(project_dir)
        assert "Git" not in detector.detected_tools

    def test_scan_respects_max_depth(self, detector, project_dir) -> None:
        """Test that scan respects maximum depth."""
        project_dir.mkdir()
        deep_dir = project_dir / "a" / "b" / "c" / "d" / "e"
        deep_dir.mkdir(parents=True)
        (deep_dir / "main.py").touch()

        # With default max depth (e.g., 5), should still find it
        detector.scan_directory(project_dir, max_depth=5)
        assert "Python" in detector.detected_languages

        # With shallow depth, should not find it
        detector.reset()
        detector.scan_directory(project_dir, max_depth=2)
        assert "Python" not in detector.detected_languages

    def test_detect_multiple_languages(self, detector, project_dir) -> None:
        """Test detection of multiple languages in one project."""
        project_dir.mkdir()
        (project_dir / "main.py").touch()
        (project_dir / "index.js").touch()
        (project_dir / "main.go").touch()

        detector.scan_directory(project_dir)

        assert "Python" in detector.detected_languages
        assert "Node" in detector.detected_languages
        assert "Go" in detector.detected_languages

    def test_comprehensive_project(self, detector, project_dir) -> None:
        """Test detection in a comprehensive project."""
        project_dir.mkdir()

        # Python backend
        backend = project_dir / "backend"
        backend.mkdir()
        (backend / "main.py").touch()
        (backend / "requirements.txt").touch()
        (backend / "Dockerfile").touch()

        # React frontend
        frontend = project_dir / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}')
        (frontend / "tsconfig.json").touch()

        # Infrastructure
        (project_dir / "docker-compose.yml").touch()
        (project_dir / ".github").mkdir()

        # IDE
        (project_dir / ".vscode").mkdir()

        detector.scan_directory(project_dir)

        assert "Python" in detector.detected_languages
        assert "TypeScript" in detector.detected_languages
        assert "Node" in detector.detected_languages
        assert "React" in detector.detected_frameworks
        assert "Docker" in detector.detected_tools
        assert "VisualStudioCode" in detector.detected_tools


# 🧰🌍🔚
