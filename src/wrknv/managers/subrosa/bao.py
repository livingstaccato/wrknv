#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""OpenBao Variant for SubRosaManager
===================================
Manages OpenBao (open source Vault fork) versions for development."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from provide.foundation import logger

from wrknv.managers.base import ToolManagerError
from wrknv.managers.github import GitHubReleasesClient
from wrknv.managers.subrosa.base import SubRosaManager

if TYPE_CHECKING:
    from wrknv.config import WorkenvConfig


class BaoVariant(SubRosaManager):
    """OpenBao variant of secret management tools."""

    def __init__(self, config: WorkenvConfig | None = None) -> None:
        super().__init__(config)
        self._github_client: GitHubReleasesClient | None = None

    @property
    def variant_name(self) -> str:
        """Variant name for this secret manager."""
        return "bao"

    @property
    def github_client(self) -> GitHubReleasesClient:
        """Get or create GitHub client for OpenBao repository."""
        if self._github_client is None:
            self._github_client = GitHubReleasesClient("openbao/openbao")
        return self._github_client

    def get_available_versions(self) -> list[str]:
        """Get available OpenBao versions from GitHub releases."""
        try:
            logger.debug("Fetching OpenBao versions from GitHub")

            include_prereleases = self.config.get_setting("include_prereleases", False)

            # Use GitHub client to fetch versions
            versions = asyncio.run(self.github_client.get_versions(include_prereleases=include_prereleases))

            # OpenBao versions have 'v' prefix in tags, already stripped by client
            logger.debug(f"Found {len(versions)} OpenBao versions")
            return versions

        except Exception as e:
            raise ToolManagerError(f"Failed to fetch OpenBao versions: {e}") from e

    def get_download_url(self, version: str) -> str:
        """Get download URL for OpenBao version."""
        platform_info = self.get_platform_info()
        os_name = platform_info["os"]
        arch = platform_info["arch"]

        # OpenBao uses capitalized OS names: Darwin, Linux, Windows
        os_capitalized = os_name.capitalize()

        # OpenBao naming: bao_2.1.0_Darwin_arm64.tar.gz
        # Note: They use tar.gz for all platforms
        return f"https://github.com/openbao/openbao/releases/download/v{version}/bao_{version}_{os_capitalized}_{arch}.tar.gz"

    def get_checksum_url(self, version: str) -> str | None:
        """Get checksum URL for OpenBao version."""
        # OpenBao provides SHA256SUMS file
        return f"https://github.com/openbao/openbao/releases/download/v{version}/bao_{version}_SHA256SUMS"


__all__ = [
    "BaoVariant",
]

# 🧰🌍🔚
