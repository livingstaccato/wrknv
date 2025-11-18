#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""GitHub API Types
================
Type definitions for GitHub API responses."""

from __future__ import annotations

from attrs import define, field


@define
class Asset:
    """GitHub release asset."""

    name: str
    browser_download_url: str
    size: int
    content_type: str
    id: int = 0
    state: str = "uploaded"
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_api(cls, data: dict) -> Asset:
        """Create Asset from GitHub API response."""
        return cls(
            name=data["name"],
            browser_download_url=data["browser_download_url"],
            size=data["size"],
            content_type=data["content_type"],
            id=data.get("id", 0),
            state=data.get("state", "uploaded"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@define
class Release:
    """GitHub release."""

    tag_name: str
    name: str
    prerelease: bool
    draft: bool
    assets: list[Asset] = field(factory=list)
    body: str = ""
    published_at: str = ""
    created_at: str = ""
    id: int = 0
    html_url: str = ""

    @classmethod
    def from_api(cls, data: dict) -> Release:
        """Create Release from GitHub API response."""
        assets = [Asset.from_api(asset) for asset in data.get("assets", [])]

        return cls(
            tag_name=data["tag_name"],
            name=data.get("name", ""),
            prerelease=data.get("prerelease", False),
            draft=data.get("draft", False),
            assets=assets,
            body=data.get("body", ""),
            published_at=data.get("published_at", ""),
            created_at=data.get("created_at", ""),
            id=data.get("id", 0),
            html_url=data.get("html_url", ""),
        )


@define
class Tag:
    """GitHub tag."""

    name: str
    commit_sha: str
    zipball_url: str = ""
    tarball_url: str = ""

    @classmethod
    def from_api(cls, data: dict) -> Tag:
        """Create Tag from GitHub API response."""
        return cls(
            name=data["name"],
            commit_sha=data["commit"]["sha"],
            zipball_url=data.get("zipball_url", ""),
            tarball_url=data.get("tarball_url", ""),
        )


__all__ = [
    "Asset",
    "Release",
    "Tag",
]

# 🧰🌍🔚
