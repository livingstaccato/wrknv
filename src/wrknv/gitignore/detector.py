#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Project Detector for Gitignore Templates
=========================================
Auto-detects project types and suggests appropriate gitignore templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

from provide.foundation import logger


class ProjectDetector:
    """Detects project characteristics to suggest gitignore templates."""

    # File patterns for language detection
    LANGUAGE_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "Python": ["*.py", "requirements.txt", "setup.py", "pyproject.toml"],
        "Node": ["*.js", "*.mjs", "*.cjs", "package.json"],
        "TypeScript": ["*.ts", "*.tsx", "tsconfig.json"],
        "Go": ["*.go", "go.mod", "go.sum"],
        "Rust": ["*.rs", "Cargo.toml", "Cargo.lock"],
        "Java": ["*.java", "pom.xml"],
        "Ruby": ["*.rb", "Gemfile", "Gemfile.lock"],
        "PHP": ["*.php", "composer.json", "composer.lock"],
        "C": ["*.c", "*.h", "Makefile"],
        "C++": ["*.cpp", "*.hpp", "*.cc", "*.cxx", "CMakeLists.txt"],
        "Swift": ["*.swift", "Package.swift"],
        "Kotlin": ["*.kt", "*.kts"],
        "Scala": ["*.scala", "build.sbt"],
        "Elixir": ["*.ex", "*.exs", "mix.exs"],
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "Django": ["manage.py", "settings.py", "urls.py"],
        "Flask": ["app.py", "flask_app.py"],
        "React": ["react", "react-dom"],  # Check in package.json
        "Vue": ["vue"],  # Check in package.json
        "Angular": ["@angular/core"],  # Check in package.json
        "NextJS": ["next"],  # Check in package.json
        "Rails": ["Gemfile", "config.ru", "Rakefile"],
        "Laravel": ["artisan", "composer.json"],  # Check for laravel in composer
        "Spring": ["pom.xml", "build.gradle"],  # Check for spring deps
    }

    # Tool detection patterns
    TOOL_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "Poetry": ["poetry.lock", "pyproject.toml"],
        "PDM": ["pdm.lock"],
        "Pipenv": ["Pipfile", "Pipfile.lock"],
        "Ruff": [".ruff_cache"],
        "Maven": ["pom.xml"],
        "Gradle": ["build.gradle", "build.gradle.kts"],
        "Docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        "Terraform": ["*.tf", "*.tfvars"],
        "Kubernetes": ["*.yaml", "*.yml"],  # Check for k8s resources
        "VisualStudioCode": [".vscode"],
        "JetBrains": [".idea"],
        "Vim": [".vimrc", ".vim"],
        "Emacs": [".emacs", ".emacs.d"],
        "Git": [".git"],
    }

    # OS detection patterns
    OS_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "macOS": [".DS_Store", ".AppleDouble", ".LSOverride"],
        "Windows": ["Thumbs.db", "Desktop.ini", "ehthumbs.db"],
        "Linux": [".directory", ".Trash-*"],
    }

    def __init__(self) -> None:
        """Initialize the detector."""
        self.detected_languages = set()
        self.detected_frameworks = set()
        self.detected_tools = set()
        self.detected_os = set()
        logger.debug("ProjectDetector initialized")

    def reset(self) -> None:
        """Reset detection state."""
        self.detected_languages.clear()
        self.detected_frameworks.clear()
        self.detected_tools.clear()
        self.detected_os.clear()
        logger.debug("ProjectDetector reset")

    def scan_directory(self, path: Path, max_depth: int = 5) -> None:
        """
        Scan a directory to detect project characteristics.

        Args:
            path: Directory path to scan
            max_depth: Maximum depth to recurse
        """
        path = Path(path)
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            return

        logger.info(f"Scanning directory: {path}")

        # Scan for files recursively
        self._scan_recursive(path, current_depth=0, max_depth=max_depth)

        # Check for framework-specific files
        self._detect_frameworks_from_configs(path)

        # Log results
        logger.debug(f"Detected languages: {self.detected_languages}")
        logger.debug(f"Detected frameworks: {self.detected_frameworks}")
        logger.debug(f"Detected tools: {self.detected_tools}")
        logger.debug(f"Detected OS: {self.detected_os}")

    def _scan_recursive(self, path: Path, current_depth: int, max_depth: int) -> None:
        """Recursively scan directory."""
        if current_depth > max_depth:
            return

        try:
            for item in path.iterdir():
                # Skip hidden directories (except IDE/tool directories)
                if item.is_dir() and item.name.startswith("."):
                    # Check for IDE/tool directories
                    if item.name in [".vscode", ".idea", ".vim", ".emacs.d", ".ruff_cache"]:
                        self._check_pattern(item.name, is_dir=True)
                    continue

                if item.is_file():
                    self._check_pattern(item.name, is_dir=False)
                elif item.is_dir() and not item.name.startswith("."):
                    self._scan_recursive(item, current_depth + 1, max_depth)
        except PermissionError:
            logger.debug(f"Permission denied accessing: {path}")

    def _check_pattern(self, filename: str, is_dir: bool) -> None:
        """Check if a filename matches any detection patterns."""
        # Check language patterns
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if self._matches_pattern(filename, pattern, is_dir):
                    self.detected_languages.add(lang)
                    logger.trace(f"Detected language {lang} from {filename}")

        # Check tool patterns
        for tool, patterns in self.TOOL_PATTERNS.items():
            for pattern in patterns:
                if self._matches_pattern(filename, pattern, is_dir):
                    self.detected_tools.add(tool)
                    logger.trace(f"Detected tool {tool} from {filename}")

        # Check OS patterns
        for os_name, patterns in self.OS_PATTERNS.items():
            for pattern in patterns:
                if self._matches_pattern(filename, pattern, is_dir):
                    self.detected_os.add(os_name)
                    logger.trace(f"Detected OS {os_name} from {filename}")

        # Check basic framework patterns
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            if framework in ["React", "Vue", "Angular", "NextJS"]:
                continue  # These are checked in package.json
            for pattern in patterns:
                if self._matches_pattern(filename, pattern, is_dir):
                    self.detected_frameworks.add(framework)
                    logger.trace(f"Detected framework {framework} from {filename}")

    def _matches_pattern(self, filename: str, pattern: str, is_dir: bool) -> bool:
        """Check if filename matches a pattern."""
        from fnmatch import fnmatch

        # Handle directory patterns (directories starting with .)
        if pattern.startswith(".") and not pattern.startswith("*."):
            # Match exact name for both files and directories
            return filename == pattern

        # Handle wildcard file patterns
        if not is_dir:
            return fnmatch(filename, pattern) or filename == pattern

        return False

    def _detect_frameworks_from_configs(self, path: Path) -> None:
        """Detect frameworks from configuration files."""
        # Check package.json for JavaScript frameworks (root and subdirectories)
        self._check_package_json(path)

        # Also check common subdirectories (frontend, backend, client, server, etc.)
        try:
            for subdir in path.iterdir():
                if subdir.is_dir() and not subdir.name.startswith("."):
                    self._check_package_json(subdir)
        except PermissionError:
            logger.debug(f"Permission denied accessing subdirectories of: {path}")

        # Check requirements.txt for Python frameworks
        requirements_txt = path / "requirements.txt"
        if requirements_txt.exists():
            try:
                content = requirements_txt.read_text().lower()
                if "flask" in content:
                    self.detected_frameworks.add("Flask")
                    logger.trace("Detected Flask from requirements.txt")
                if "django" in content:
                    self.detected_frameworks.add("Django")
                    logger.trace("Detected Django from requirements.txt")
                if "fastapi" in content:
                    self.detected_frameworks.add("FastAPI")
                    logger.trace("Detected FastAPI from requirements.txt")
            except Exception:
                logger.debug("Could not parse requirements.txt")

        # TypeScript implies Node
        if "TypeScript" in self.detected_languages:
            self.detected_languages.add("Node")
            logger.trace("Added Node due to TypeScript detection")

    def _check_package_json(self, path: Path) -> None:
        """Check a specific directory for package.json and detect frameworks."""
        package_json = path / "package.json"
        if package_json.exists():
            try:
                content = json.loads(package_json.read_text())
                deps = {**content.get("dependencies", {}), **content.get("devDependencies", {})}

                # Check for React
                if "react" in deps:
                    self.detected_frameworks.add("React")
                    logger.trace(f"Detected React from {package_json}")

                # Check for Vue
                if "vue" in deps:
                    self.detected_frameworks.add("Vue")
                    logger.trace(f"Detected Vue from {package_json}")

                # Check for Angular
                if "@angular/core" in deps:
                    self.detected_frameworks.add("Angular")
                    logger.trace(f"Detected Angular from {package_json}")

                # Check for Next.js
                if "next" in deps:
                    self.detected_frameworks.add("NextJS")
                    logger.trace(f"Detected Next.js from {package_json}")

            except (json.JSONDecodeError, KeyError):
                logger.debug(f"Could not parse {package_json}")

    def suggest_templates(self) -> list[str]:
        """
        Suggest gitignore templates based on detection.

        Returns:
            List of suggested template names, ordered by priority
        """
        suggestions = []

        # Add languages first (highest priority)
        suggestions.extend(sorted(self.detected_languages))

        # Add frameworks
        suggestions.extend(sorted(self.detected_frameworks))

        # Add tools
        tool_priority = ["Docker", "Terraform", "Poetry", "PDM", "Pipenv"]
        priority_tools = [t for t in tool_priority if t in self.detected_tools]
        other_tools = sorted(t for t in self.detected_tools if t not in tool_priority)
        suggestions.extend(priority_tools + other_tools)

        # Add OS last
        suggestions.extend(sorted(self.detected_os))

        logger.info(f"Suggested templates: {suggestions}")
        return suggestions


# 🧰🌍🔚
