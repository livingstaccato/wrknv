#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""GitHub Releases API Client
===========================
Client for interacting with GitHub Releases API using provide-foundation transport."""

from __future__ import annotations

from collections.abc import Callable
import pathlib
import re
from types import TracebackType
from typing import Literal

from provide.foundation.hub import get_hub
from provide.foundation.logger import get_logger
from provide.foundation.transport import UniversalClient

from wrknv.managers.github.types import Asset, Release, Tag
from wrknv.wenv.resilience import get_circuit_breaker, get_retry_policy

logger = get_logger(__name__)


class GitHubReleasesClient:
    """GitHub Releases API client using foundation transport."""

    def __init__(self, repo: str, token: str | None = None) -> None:
        """Initialize GitHub client.

        Args:
            repo: Repository in format 'owner/name'
            token: Optional GitHub token for authentication
        """
        self.repo = repo
        self.token = token

        # Build headers
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Get hub and create client
        hub = get_hub()
        self.client = UniversalClient(hub=hub, default_headers=headers)

        # Get resilience components
        self.retry_policy = get_retry_policy("github")
        self.circuit_breaker = get_circuit_breaker("github")

    async def list_releases(self, include_prereleases: bool = False, per_page: int = 100) -> list[Release]:
        """List all releases from repository.

        Args:
            include_prereleases: Include prerelease versions
            per_page: Number of releases per page (max 100)

        Returns:
            List of Release objects
        """
        url = f"https://api.github.com/repos/{self.repo}/releases"
        params = {"per_page": min(per_page, 100)}

        logger.debug(f"Fetching releases from {self.repo}")

        response = await self.client.get(url, params=params)
        data = response.json()

        releases = [Release.from_api(r) for r in data]

        # Filter prereleases if needed
        if not include_prereleases:
            releases = [r for r in releases if not r.prerelease]

        logger.debug(f"Found {len(releases)} releases")
        return releases

    async def get_latest_release(self) -> Release:
        """Get the latest non-prerelease, non-draft release.

        Returns:
            Latest Release object
        """
        url = f"https://api.github.com/repos/{self.repo}/releases/latest"

        logger.debug(f"Fetching latest release from {self.repo}")

        response = await self.client.get(url)
        data = response.json()

        return Release.from_api(data)

    async def get_release_by_tag(self, tag: str) -> Release:
        """Get release by tag name.

        Args:
            tag: Tag name (with or without 'v' prefix)

        Returns:
            Release object
        """
        url = f"https://api.github.com/repos/{self.repo}/releases/tags/{tag}"

        logger.debug(f"Fetching release {tag} from {self.repo}")

        response = await self.client.get(url)
        data = response.json()

        return Release.from_api(data)

    async def list_tags(self, per_page: int = 100) -> list[Tag]:
        """List all tags from repository.

        Args:
            per_page: Number of tags per page (max 100)

        Returns:
            List of Tag objects
        """
        url = f"https://api.github.com/repos/{self.repo}/tags"
        params = {"per_page": min(per_page, 100)}

        logger.debug(f"Fetching tags from {self.repo}")

        response = await self.client.get(url, params=params)
        data = response.json()

        tags = [Tag.from_api(t) for t in data]

        logger.debug(f"Found {len(tags)} tags")
        return tags

    async def download_asset(
        self,
        asset: Asset,
        destination: pathlib.Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """Download release asset to destination.

        Args:
            asset: Asset to download
            destination: Where to save the file
            progress_callback: Optional callback(downloaded_bytes, total_bytes)
        """
        await self._download_file(asset.browser_download_url, destination, progress_callback)

    async def download_archive(
        self,
        ref: str,
        destination: pathlib.Path,
        format: Literal["zipball", "tarball"] = "zipball",
        ref_type: Literal["heads", "tags"] = "heads",
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """Download repository archive.

        Args:
            ref: Branch name, tag name, or commit SHA
            destination: Where to save archive
            format: Archive format - 'zipball' (.zip) or 'tarball' (.tar.gz)
            ref_type: Reference type - 'heads' (branch) or 'tags'
            progress_callback: Optional callback(downloaded_bytes, total_bytes)

        Examples:
            # Download main branch as zip
            await client.download_archive("main", "repo.zip", "zipball", "heads")

            # Download tag as tarball
            await client.download_archive("v1.0.0", "repo.tar.gz", "tarball", "tags")
        """
        ext = "zip" if format == "zipball" else "tar.gz"
        url = f"https://github.com/{self.repo}/archive/refs/{ref_type}/{ref}.{ext}"

        logger.info(f"Downloading archive from {url}")

        await self._download_file(url, destination, progress_callback)

    async def _download_file(
        self,
        url: str,
        destination: pathlib.Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """Download file using streaming.

        Args:
            url: URL to download
            destination: Where to save file
            progress_callback: Optional callback(downloaded_bytes, total_bytes)
                             total_bytes will be 0 if size is unknown
        """
        # Create parent directories
        destination.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading {url} to {destination}")

        downloaded = 0
        total_size = 0

        # First get total size from HEAD request if possible
        try:
            head_response = await self.client.head(url)
            if "content-length" in head_response.headers:
                total_size = int(head_response.headers["content-length"])
        except Exception:
            pass  # Size unknown, continue without it

        # Stream download
        async with self.client:
            with destination.open("wb") as f:
                async for chunk in self.client.stream(url):
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Call progress callback even if total size is unknown (pass 0)
                    if progress_callback:
                        progress_callback(downloaded, total_size)

        logger.info(f"Successfully downloaded {destination.name} ({downloaded} bytes)")

    async def get_versions(self, include_prereleases: bool = False) -> list[str]:
        """Get list of version strings from releases.

        Args:
            include_prereleases: Include prerelease versions

        Returns:
            List of version strings (tag names with 'v' prefix stripped)
        """
        releases = await self.list_releases(include_prereleases=include_prereleases)
        versions = []

        for release in releases:
            version = release.tag_name
            # Strip leading 'v' if present
            if version.startswith("v"):
                version = version[1:]
            versions.append(version)

        return versions

    def find_asset(self, release: Release, pattern: str) -> Asset | None:
        """Find asset in release matching pattern.

        Args:
            release: Release to search
            pattern: Regex pattern or simple glob-like pattern (*) to match

        Returns:
            First matching Asset or None
        """
        # First try exact match
        for asset in release.assets:
            if asset.name == pattern:
                logger.debug(f"Found exact matching asset: {asset.name}")
                return asset

        # Convert simple glob to regex
        regex_pattern = pattern.replace(".", r"\.").replace("*", ".*") if "*" in pattern else pattern

        # Try pattern match
        for asset in release.assets:
            if re.search(regex_pattern, asset.name):
                logger.debug(f"Found matching asset: {asset.name}")
                return asset

        logger.debug(f"No asset found matching pattern: {pattern}")
        return None

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        # UniversalClient will cleanup in __aexit__

    async def __aenter__(self) -> GitHubReleasesClient:
        """Context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        await self.close()


__all__ = [
    "GitHubReleasesClient",
]

# 🧰🌍🔚
