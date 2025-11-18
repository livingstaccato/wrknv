#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Workspace Repository Discovery
=============================
Discover and analyze repositories in workspace."""

from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any

from attrs import define
from provide.foundation import logger


@define
class RepoInfo:
    """Information about a discovered repository."""

    path: Path
    name: str | None
    has_git: bool
    has_pyproject: bool
    detected_type: str | None
    current_config: dict[str, Any] | None


class WorkspaceDiscovery:
    """Discovers and analyzes repositories in workspace."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()

    def discover_repos(self, patterns: list[str] | None = None) -> list[RepoInfo]:
        """Find all Git repos with pyproject.toml."""
        if patterns is None:
            patterns = ["*"]

        repos = []
        logger.info("🔍 Discovering repositories", root=str(self.root), patterns=patterns)

        for pattern in patterns:
            for path in self.root.glob(pattern):
                if path.is_dir() and path != self.root:
                    repo_info = self.analyze_repo(path)
                    if repo_info.has_git and repo_info.has_pyproject:
                        repos.append(repo_info)

        logger.info("📋 Discovered repositories", count=len(repos))
        return repos

    def analyze_repo(self, path: Path) -> RepoInfo:
        """Analyze a single repository."""
        has_git = (path / ".git").exists()
        has_pyproject = (path / "pyproject.toml").exists()

        name = None
        detected_type = None
        current_config = None

        if has_pyproject:
            try:
                with (path / "pyproject.toml").open("rb") as f:
                    pyproject = tomllib.load(f)

                current_config = pyproject
                name = pyproject.get("project", {}).get("name")
                detected_type = self.detect_repo_type(pyproject, path)

            except Exception as e:
                logger.warning("⚠️ Failed to parse pyproject.toml", path=str(path), error=str(e))

        if not name:
            name = path.name

        return RepoInfo(
            path=path,
            name=name,
            has_git=has_git,
            has_pyproject=has_pyproject,
            detected_type=detected_type,
            current_config=current_config,
        )

    def detect_repo_type(self, pyproject: dict[str, Any], path: Path) -> str | None:
        """Determine repository type from pyproject.toml and path."""
        project = pyproject.get("project", {})
        name = project.get("name", "")
        dependencies = project.get("dependencies", [])

        # Check name patterns
        if "provide-foundation" in name:
            return "foundation"
        elif "provide-testkit" in name:
            return "testkit"
        elif name.startswith("pyvider-"):
            return "pyvider-plugin"
        elif name == "pyvider":
            return "provider"
        elif "flavor" in name:
            return "packaging"

        # Check dependencies
        dep_str = " ".join(dependencies)
        if "provide-foundation" in dep_str:
            return "foundation-based"
        elif "pyvider" in dep_str:
            return "pyvider-plugin"

        # Check for specific files
        if (path / "src" / "pyvider").exists():
            return "provider"
        elif (path / "src" / "provide").exists():
            return "foundation-based"

        # Check classifiers
        classifiers = project.get("classifiers", [])
        for classifier in classifiers:
            if "Topic :: System :: Logging" in classifier:
                return "foundation-based"
            elif "Topic :: Software Development :: Build Tools" in classifier:
                return "packaging"

        logger.debug("🤷 Could not detect repo type", name=name)
        return "unknown"

    def get_repo_status(self, repo_path: Path) -> dict[str, Any]:
        """Get current status of repository."""
        status = {
            "path": str(repo_path),
            "exists": repo_path.exists(),
            "has_git": False,
            "has_pyproject": False,
            "has_workenv": False,
            "has_claude_md": False,
            "git_status": None,
        }

        if not repo_path.exists():
            return status

        status["has_git"] = (repo_path / ".git").exists()
        status["has_pyproject"] = (repo_path / "pyproject.toml").exists()
        status["has_workenv"] = (repo_path / "workenv").exists()
        status["has_claude_md"] = (repo_path / "CLAUDE.md").exists()

        # Get git status if available
        if status["has_git"]:
            status["git_status"] = self._get_git_status(repo_path)

        return status

    def _get_git_status(self, repo_path: Path) -> dict[str, Any] | None:
        """Get git status for repository."""
        try:
            from provide.foundation.process import run

            # Get current branch
            branch_result = run(
                ["git", "branch", "--show-current"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            # Get status
            status_result = run(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            return {
                "branch": branch_result.stdout.strip(),
                "dirty": bool(status_result.stdout.strip()),
                "files_changed": len(status_result.stdout.strip().splitlines()),
            }

        except Exception as e:
            logger.debug("⚠️ Failed to get git status", path=str(repo_path), error=str(e))
            return None

    def validate_workspace_structure(self, root: Path) -> list[str]:
        """Validate workspace structure and return issues."""
        issues = []

        if not root.exists():
            issues.append(f"Workspace root does not exist: {root}")
            return issues

        # Check for workspace config
        workspace_config = root / ".wrknv" / "workspace.toml"
        if not workspace_config.exists():
            issues.append("No workspace.toml found in .wrknv/")

        # Check for common problems
        repos = self.discover_repos()

        for repo in repos:
            if not repo.has_git:
                issues.append(f"Repository {repo.name} is not a git repository")

            if not repo.has_pyproject:
                issues.append(f"Repository {repo.name} has no pyproject.toml")

            if repo.detected_type == "unknown":
                issues.append(f"Could not detect type for repository {repo.name}")

        return issues

    def get_workspace_summary(self) -> dict[str, Any]:
        """Get summary of workspace state."""
        repos = self.discover_repos()

        type_counts = {}
        for repo in repos:
            repo_type = repo.detected_type or "unknown"
            type_counts[repo_type] = type_counts.get(repo_type, 0) + 1

        return {
            "root": str(self.root),
            "total_repos": len(repos),
            "type_distribution": type_counts,
            "repos": [
                {
                    "name": repo.name,
                    "type": repo.detected_type,
                    "path": str(repo.path.relative_to(self.root)),
                }
                for repo in repos
            ],
        }


# 🧰🌍🔚
