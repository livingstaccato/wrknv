#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Workspace Configuration Synchronization
=======================================
Synchronize configurations across repositories in workspace."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from provide.foundation import logger

from .schema import RepoConfig, WorkspaceConfig


class WorkspaceSync:
    """Synchronize configurations across repositories."""

    def __init__(self, workspace_config: WorkspaceConfig) -> None:
        self.config = workspace_config

    async def sync_all(self, dry_run: bool = False) -> dict[str, Any]:
        """Sync all repositories in workspace."""
        logger.info("🔄 Starting workspace sync", repos=len(self.config.repos), dry_run=dry_run)

        results = {}
        for repo in self.config.repos:
            try:
                result = await self.sync_repo(repo, dry_run)
                results[repo.name] = result
            except Exception as e:
                logger.error("❌ Failed to sync repo", repo=repo.name, error=str(e))
                results[repo.name] = {"error": str(e)}

        return results

    async def sync_repo(self, repo: RepoConfig, dry_run: bool = False) -> dict[str, Any]:
        """Sync single repository configuration."""

        # Build template context
        context = self._build_template_context(repo)

        # Generate configurations
        configs = self._generate_configs(repo, context)

        # Apply changes
        changes = {}
        for filename, new_content in configs.items():
            file_path = repo.path / filename
            change_info = await self._apply_config_change(file_path, new_content, dry_run)
            changes[filename] = change_info

        result = {
            "repo": repo.name,
            "changes": changes,
            "files_updated": sum(1 for c in changes.values() if c.get("changed", False)),
        }

        logger.debug("📋 Repo sync result", **result)
        return result

    def _build_template_context(self, repo: RepoConfig) -> dict[str, Any]:
        """Build context for template rendering."""
        # Start with global standards
        context = dict(self.config.global_standards)

        # Add repo-specific values
        context.update(
            {
                "project_name": repo.name,
                "package_type": repo.type,
                "features": repo.features,
            }
        )

        # Add custom values (highest priority)
        context.update(repo.custom_values)

        # Set sensible defaults if not provided
        context.setdefault("version", "1.0.0")
        context.setdefault("python_version", "3.11")
        context.setdefault("description", f"Description for {repo.name}")
        context.setdefault("use_mypy", True)
        context.setdefault("use_pytest", True)
        context.setdefault("use_coverage", True)

        # Configure features based on repo type
        if repo.type == "foundation-based":
            context.setdefault(
                "workspace_sources",
                {
                    "provide-foundation": {"workspace": True},
                    "provide-testkit": {"workspace": True},
                },
            )
        elif repo.type == "pyvider-plugin":
            context.setdefault(
                "workspace_sources",
                {
                    "pyvider": {"workspace": True},
                    "pyvider-cty": {"workspace": True},
                    "provide-foundation": {"workspace": True},
                    "provide-testkit": {"workspace": True},
                },
            )

        return context

    def _generate_configs(self, repo: RepoConfig, context: dict[str, Any]) -> dict[str, str]:
        """Generate configuration files for repository."""
        # Configuration generation has been removed with workenv module
        return {}

    async def _apply_config_change(self, file_path: Path, new_content: str, dry_run: bool) -> dict[str, Any]:
        """Apply configuration change to file."""
        change_info = {
            "path": str(file_path),
            "exists": file_path.exists(),
            "changed": False,
            "diff": None,
        }

        # Read current content
        current_content = ""
        if file_path.exists():
            try:
                current_content = file_path.read_text()
            except Exception as e:
                logger.warning("⚠️ Failed to read file", path=str(file_path), error=str(e))
                change_info["error"] = str(e)
                return change_info

        # Check if content changed
        if current_content.strip() == new_content.strip():
            return change_info

        # Generate diff
        diff_lines = list(
            difflib.unified_diff(
                current_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=str(file_path),
                tofile=str(file_path),
                lineterm="",
            )
        )

        change_info["changed"] = True
        change_info["diff"] = "".join(diff_lines)

        if dry_run:
            logger.info("🔍 Would update file", path=str(file_path))
        else:
            try:
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write new content
                file_path.write_text(new_content)

            except Exception as e:
                logger.error("❌ Failed to write file", path=str(file_path), error=str(e))
                change_info["error"] = str(e)

        return change_info

    def check_drift(self) -> dict[str, Any]:
        """Check for configuration drift across repositories."""
        logger.info("🔍 Checking configuration drift")

        drift_report = {
            "repos_checked": len(self.config.repos),
            "drift_detected": False,
            "repo_drifts": {},
        }

        for repo in self.config.repos:
            repo_drift = self._check_repo_drift(repo)
            if repo_drift["has_drift"]:
                drift_report["drift_detected"] = True
                drift_report["repo_drifts"][repo.name] = repo_drift

        return drift_report

    def _check_repo_drift(self, repo: RepoConfig) -> dict[str, Any]:
        """Check drift for a single repository."""
        context = self._build_template_context(repo)
        expected_configs = self._generate_configs(repo, context)

        drift_info = {
            "repo": repo.name,
            "has_drift": False,
            "file_drifts": {},
        }

        for filename, expected_content in expected_configs.items():
            file_path = repo.path / filename

            if not file_path.exists():
                drift_info["has_drift"] = True
                drift_info["file_drifts"][filename] = {
                    "status": "missing",
                    "expected": len(expected_content.splitlines()),
                }
                continue

            try:
                current_content = file_path.read_text()
                if current_content.strip() != expected_content.strip():
                    drift_info["has_drift"] = True
                    drift_info["file_drifts"][filename] = {
                        "status": "different",
                        "current_lines": len(current_content.splitlines()),
                        "expected_lines": len(expected_content.splitlines()),
                    }
            except Exception as e:
                drift_info["has_drift"] = True
                drift_info["file_drifts"][filename] = {
                    "status": "error",
                    "error": str(e),
                }

        return drift_info

    def validate_templates(self) -> bool:
        """Validate that all templates are available and functional."""

        try:
            # Test template generation with minimal context
            test_context = {
                "project_name": "test-project",
                "version": "1.0.0",
                "description": "Test project",
                "python_version": "3.11",
            }

            # Test each template
            self.template_generator.generate_pyproject(test_context)
            self.template_generator.generate_claude_md(test_context)
            self.template_generator.generate_gitignore(test_context)

            return True

        except Exception as e:
            logger.error("❌ Template validation failed", error=str(e))
            return False


# 🧰🌍🔚
