#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Workspace Configuration Schema
=============================
Configuration models for multi-repo workspace management."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from attrs import define, field
from provide.foundation.config import BaseConfig


@define(frozen=True)
class RepoConfig:
    """Configuration for a single repository in the workspace."""

    path: Path
    name: str
    type: str  # "provider", "foundation", "testkit", etc.
    template_profile: str
    features: list[str] = field(factory=list)
    custom_values: dict[str, Any] = field(factory=dict)
    last_sync: str | None = None
    template_version: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RepoConfig:
        """Create RepoConfig from dictionary."""
        return cls(
            path=Path(data["path"]),
            name=data["name"],
            type=data["type"],
            template_profile=data["template_profile"],
            features=data.get("features", []),
            custom_values=data.get("custom_values", {}),
            last_sync=data.get("last_sync"),
            template_version=data.get("template_version"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values for TOML compatibility."""
        data = {
            "path": str(self.path),
            "name": self.name,
            "type": self.type,
            "template_profile": self.template_profile,
            "features": self.features,
            "custom_values": self.custom_values,
            "last_sync": self.last_sync,
            "template_version": self.template_version,
        }
        # Filter out None values - TOML cannot serialize None
        return {k: v for k, v in data.items() if v is not None}


@define(frozen=True)
class TemplateSource:
    """Source for template bundles."""

    type: str  # "local", "github", "git", "registry"
    location: str
    version: str | None = None
    branch: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateSource:
        """Create TemplateSource from dictionary."""
        return cls(
            type=data["type"],
            location=data["location"],
            version=data.get("version"),
            branch=data.get("branch"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values for TOML compatibility."""
        data = {
            "type": self.type,
            "location": self.location,
            "version": self.version,
            "branch": self.branch,
        }
        # Filter out None values - TOML cannot serialize None
        return {k: v for k, v in data.items() if v is not None}


@define(frozen=True)
class WorkspaceConfig(BaseConfig):
    """Root workspace configuration."""

    root: Path = field(converter=Path)
    version: str = "1.0"
    repos: list[RepoConfig] = field(factory=list)
    template_source: TemplateSource | None = None
    global_standards: dict[str, Any] = field(factory=dict)
    sync_strategy: str = "manual"  # "manual", "auto", "check"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkspaceConfig:
        """Create WorkspaceConfig from dictionary."""
        repos = [RepoConfig.from_dict(repo) for repo in data.get("repos", [])]

        template_source = None
        if "template_source" in data:
            template_source = TemplateSource.from_dict(data["template_source"])

        return cls(
            version=data.get("version", "1.0"),
            root=Path(data["root"]),
            repos=repos,
            template_source=template_source,
            global_standards=data.get("global_standards", {}),
            sync_strategy=data.get("sync_strategy", "manual"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values for TOML compatibility."""
        data = {
            "version": self.version,
            "root": str(self.root),
            "repos": [repo.to_dict() for repo in self.repos],
            "template_source": self.template_source.to_dict() if self.template_source else None,
            "global_standards": self.global_standards,
            "sync_strategy": self.sync_strategy,
        }
        # Filter out None values - TOML cannot serialize None
        return {k: v for k, v in data.items() if v is not None}

    def find_repo(self, name: str) -> RepoConfig | None:
        """Find repository by name."""
        for repo in self.repos:
            if repo.name == name:
                return repo
        return None

    def add_repo(self, repo: RepoConfig) -> WorkspaceConfig:
        """Add repository to workspace."""
        # Remove existing repo with same name
        repos = [r for r in self.repos if r.name != repo.name]
        repos.append(repo)

        return self.__class__(
            version=self.version,
            root=self.root,
            repos=repos,
            template_source=self.template_source,
            global_standards=self.global_standards,
            sync_strategy=self.sync_strategy,
        )

    def remove_repo(self, name: str) -> WorkspaceConfig:
        """Remove repository from workspace."""
        repos = [r for r in self.repos if r.name != name]

        return self.__class__(
            version=self.version,
            root=self.root,
            repos=repos,
            template_source=self.template_source,
            global_standards=self.global_standards,
            sync_strategy=self.sync_strategy,
        )

    def get_repos_by_type(self, repo_type: str) -> list[RepoConfig]:
        """Get all repositories of a specific type."""
        return [repo for repo in self.repos if repo.type == repo_type]

    def get_outdated_repos(self, current_version: str) -> list[RepoConfig]:
        """Get repositories that need template updates."""
        return [repo for repo in self.repos if repo.template_version != current_version]


# 🧰🌍🔚
