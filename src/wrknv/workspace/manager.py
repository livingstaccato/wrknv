#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Workspace Manager
================
Manage multi-repo workspaces with configuration synchronization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from provide.foundation import logger
from provide.foundation.file import read_toml, write_toml

from .discovery import WorkspaceDiscovery
from .schema import RepoConfig, TemplateSource, WorkspaceConfig
from .sync import WorkspaceSync


class WorkspaceManager:
    """Manage multi-repo workspaces."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()
        self.config_dir = self.root / ".wrknv"
        self.config_path = self.config_dir / "workspace.toml"
        self.discovery = WorkspaceDiscovery(self.root)

    def init_workspace(
        self, template_source: str | None = None, auto_discover: bool = True
    ) -> WorkspaceConfig:
        """Initialize workspace in current directory."""
        logger.info("🚀 Initializing workspace", root=str(self.root))

        # Create .wrknv directory
        self.config_dir.mkdir(exist_ok=True)

        # Auto-discover repositories if requested
        repos = []
        if auto_discover:
            discovered = self.discovery.discover_repos()
            repos = [
                RepoConfig(
                    path=repo.path,
                    name=repo.name or repo.path.name,
                    type=repo.detected_type or "unknown",
                    template_profile=self._get_default_profile(repo.detected_type),
                    features=self._get_default_features(repo.detected_type),
                )
                for repo in discovered
            ]
            logger.info("📋 Auto-discovered repositories", count=len(repos))

        # Set up template source
        source = None
        if template_source:
            source = TemplateSource(
                type="local" if Path(template_source).exists() else "git",
                location=template_source,
            )

        # Create workspace config
        config = WorkspaceConfig(
            root=self.root,
            repos=repos,
            template_source=source,
            global_standards=self._get_default_standards(),
        )

        # Save configuration
        self.save_config(config)

        return config

    def load_config(self) -> WorkspaceConfig | None:
        """Load workspace configuration."""
        if not self.config_path.exists():
            return None

        try:
            data = read_toml(self.config_path, default={})
            if not data:
                return None
            return WorkspaceConfig.from_dict(data)

        except Exception as e:
            logger.error("❌ Failed to load workspace config", error=str(e))
            return None

    def save_config(self, config: WorkspaceConfig) -> None:
        """Save workspace configuration."""
        try:
            # Convert to dictionary and write with foundation's atomic TOML writer
            write_toml(self.config_path, config.to_dict(), atomic=True)
            logger.debug("💾 Workspace config saved", path=str(self.config_path))

        except Exception as e:
            logger.error("❌ Failed to save workspace config", error=str(e))
            raise

    def add_repo(
        self,
        repo_path: Path | str,
        name: str | None = None,
        repo_type: str | None = None,
        template_profile: str | None = None,
    ) -> WorkspaceConfig:
        """Add repository to workspace."""
        repo_path = Path(repo_path)
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

        # Analyze repository
        repo_info = self.discovery.analyze_repo(repo_path)

        # Create repo config
        repo_config = RepoConfig(
            path=repo_path,
            name=name or repo_info.name or repo_path.name,
            type=repo_type or repo_info.detected_type or "unknown",
            template_profile=template_profile or self._get_default_profile(repo_info.detected_type),
            features=self._get_default_features(repo_info.detected_type),
        )

        # Load current config and add repo
        config = self.load_config()
        if config is None:
            config = self.init_workspace(auto_discover=False)

        updated_config = config.add_repo(repo_config)
        self.save_config(updated_config)

        return updated_config

    def remove_repo(self, name: str) -> WorkspaceConfig:
        """Remove repository from workspace."""
        config = self.load_config()
        if config is None:
            raise RuntimeError("No workspace configuration found")

        updated_config = config.remove_repo(name)
        self.save_config(updated_config)

        return updated_config

    async def sync_all(self, dry_run: bool = False) -> dict[str, Any]:
        """Sync configurations across all repos."""
        config = self.load_config()
        if config is None:
            raise RuntimeError("No workspace configuration found")

        sync = WorkspaceSync(config)
        return await sync.sync_all(dry_run=dry_run)

    async def sync_repo(self, name: str, dry_run: bool = False) -> dict[str, Any]:
        """Sync configuration for specific repository."""
        config = self.load_config()
        if config is None:
            raise RuntimeError("No workspace configuration found")

        repo = config.find_repo(name)
        if repo is None:
            raise ValueError(f"Repository not found in workspace: {name}")

        sync = WorkspaceSync(config)
        return await sync.sync_repo(repo, dry_run=dry_run)

    def check_drift(self) -> dict[str, Any]:
        """Check for configuration drift."""
        config = self.load_config()
        if config is None:
            raise RuntimeError("No workspace configuration found")

        sync = WorkspaceSync(config)
        return sync.check_drift()

    def get_workspace_status(self) -> dict[str, Any]:
        """Get comprehensive workspace status."""
        config = self.load_config()
        if config is None:
            return {"error": "No workspace configuration found"}

        summary = self.discovery.get_workspace_summary()
        issues = self.discovery.validate_workspace_structure(self.root)

        return {
            "root": str(self.root),
            "config_path": str(self.config_path),
            "repos_configured": len(config.repos),
            "repos_discovered": summary["total_repos"],
            "type_distribution": summary["type_distribution"],
            "issues": issues,
            "sync_strategy": config.sync_strategy,
            "template_source": config.template_source.to_dict() if config.template_source else None,
        }

    def _get_default_profile(self, repo_type: str | None) -> str:
        """Get default template profile for repository type."""
        profiles = {
            "foundation": "foundation-based",
            "foundation-based": "foundation-based",
            "provider": "pyvider-plugin",
            "pyvider-plugin": "pyvider-plugin",
            "testkit": "testkit-extension",
            "packaging": "standalone",
        }
        return profiles.get(repo_type or "unknown", "standalone")

    def _get_default_features(self, repo_type: str | None) -> list[str]:
        """Get default features for repository type."""
        base_features = ["pyproject", "claude", "gitignore"]

        type_features = {
            "foundation-based": [*base_features, "coverage"],
            "pyvider-plugin": [*base_features, "coverage"],
            "testkit": [*base_features, "coverage"],
        }

        return type_features.get(repo_type or "unknown", base_features)

    def _get_default_standards(self) -> dict[str, Any]:
        """Get default global standards."""
        return {
            "python_version": "3.11",
            "ruff_line_length": 111,
            "authors": [{"name": "Tim Perkins", "email": "code@tim.life"}],
            "maintainers": [{"name": "provide.io", "email": "code@provide.io"}],
            "license": "Apache-2.0",
            "development_status": "3 - Alpha",
        }

    def setup_workspace(self, generate_only: bool = False) -> dict[str, Any]:
        """Setup all repositories in workspace.

        Args:
            generate_only: If True, only generate env scripts without running them

        Returns:
            Dictionary with setup results
        """
        from wrknv.wenv.env_generator import create_project_env_scripts

        config = self.load_config()
        if config is None:
            raise RuntimeError("No workspace configuration found. Run 'wrknv workspace init' first.")

        results: dict[str, Any] = {
            "success_count": 0,
            "total_count": len(config.repos),
            "failures": {},
            "generated": [],
        }

        for repo in config.repos:
            repo_path = repo.path if repo.path.is_absolute() else self.root / repo.path

            if not repo_path.exists():
                results["failures"][repo.name] = f"Repository path does not exist: {repo_path}"
                continue

            if not (repo_path / "pyproject.toml").exists():
                results["failures"][repo.name] = "No pyproject.toml found"
                continue

            try:
                # Generate env scripts
                logger.info(f"📝 Generating env scripts for {repo.name}")
                sh_path, ps1_path = create_project_env_scripts(repo_path)

                results["generated"].append(
                    {"repo": repo.name, "sh_path": str(sh_path), "ps1_path": str(ps1_path)}
                )

                results["success_count"] += 1

            except Exception as e:
                logger.error(f"❌ Failed to setup {repo.name}", error=str(e))
                results["failures"][repo.name] = str(e)

        return results


# 🧰🌍🔚
