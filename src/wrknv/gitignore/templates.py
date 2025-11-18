#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Template Handler for Gitignore Files
=====================================
Manages gitignore templates from GitHub's collection."""

from __future__ import annotations

from pathlib import Path
import tempfile

from provide.foundation import logger
from provide.foundation.archive.operations import ArchiveOperations
from provide.foundation.file import safe_move, safe_rmtree
from provide.foundation.resilience import retry
from provide.foundation.transport import get


class TemplateHandler:
    """Handles gitignore template operations including caching and GitHub sync."""

    GITHUB_REPO = "https://github.com/github/gitignore"
    GITHUB_ARCHIVE = "https://github.com/github/gitignore/archive/refs/heads/main.tar.gz"
    GITHUB_API = "https://api.github.com/repos/github/gitignore"

    def __init__(self, cache_dir: Path | None = None) -> None:
        """
        Initialize template handler.

        Args:
            cache_dir: Directory for caching templates (default: ~/.wrknv/gitignore-templates)
        """
        self.cache_dir = cache_dir or Path.home() / ".wrknv" / "gitignore-templates"
        self.cache_dir = self.cache_dir.expanduser()
        logger.debug(f"TemplateHandler initialized with cache_dir: {self.cache_dir}")

        # Create cache directory if it doesn't exist
        if not self.cache_dir.exists():
            logger.info(f"Creating gitignore template cache directory: {self.cache_dir}")
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def update_cache(self, force: bool = False) -> bool:
        """
        Update the template cache from GitHub.

        Args:
            force: Force update even if cache exists

        Returns:
            True if cache was updated, False otherwise
        """
        self.cache_dir / ".version"

        # Check if update is needed
        if not force and self._is_cache_valid():
            logger.debug("Template cache is valid, skipping update")
            return False

        logger.info("Updating gitignore templates from GitHub...")

        try:
            # Download archive to temp file using foundation download
            from wrknv.wenv.operations.download import download_file

            # Use NamedTemporaryFile but don't delete automatically
            with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            logger.debug(f"Downloading templates archive to {tmp_path}")
            download_file(self.GITHUB_ARCHIVE, tmp_path, show_progress=False)

            # Extract archive using foundation utilities
            logger.debug("Extracting templates archive")
            with tempfile.TemporaryDirectory() as extract_dir:
                # Extract with security validation (path traversal protection)
                ArchiveOperations.extract_tar_gz(tmp_path, Path(extract_dir))

                # Find root directory (usually gitignore-main)
                extracted_items = list(Path(extract_dir).iterdir())
                if not extracted_items:
                    raise ValueError("Archive is empty")

                source_dir = extracted_items[0] if len(extracted_items) == 1 else Path(extract_dir)

                # Clear existing cache
                if self.cache_dir.exists():
                    logger.debug("Clearing existing cache")
                    safe_rmtree(self.cache_dir)

                # Move extracted files to cache
                safe_move(source_dir, self.cache_dir)

            # Clean up temp file
            tmp_path.unlink()

            # Update version file with current commit
            self._update_version_file()

            logger.info(f"Successfully updated templates in {self.cache_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to update template cache: {e}")
            return False

    def _is_cache_valid(self) -> bool:
        """Check if the cache is valid and recent enough."""
        version_file = self.cache_dir / ".version"

        if not version_file.exists():
            logger.debug("No version file found, cache invalid")
            return False

        # Check if basic templates exist
        essential_templates = ["Python.gitignore", "Node.gitignore", "Go.gitignore"]
        for template in essential_templates:
            if not (self.cache_dir / template).exists():
                logger.debug(f"Essential template {template} missing, cache invalid")
                return False

        # Cache is considered valid if version file exists and essential templates are present
        logger.debug("Cache validation passed")
        return True

    @retry(Exception, max_attempts=3, base_delay=1.0)
    def _fetch_commit_sha(self) -> str:
        """Fetch latest commit SHA from GitHub API with retry."""
        import asyncio

        logger.debug("Fetching latest commit SHA from GitHub API")
        response = asyncio.run(get(f"{self.GITHUB_API}/commits/main"))
        data = response.json()
        return data["sha"][:8]

    def _fallback_version(self) -> str:
        """Fallback version identifier using timestamp."""
        from provide.foundation.time import provide_now

        return provide_now().isoformat()

    def _update_version_file(self) -> None:
        """Update the version file with current information.

        Uses GitHub API with retry, falls back to timestamp if unavailable.
        """
        version_file = self.cache_dir / ".version"

        try:
            commit_sha = self._fetch_commit_sha()
        except Exception as e:
            logger.warning(f"Could not fetch commit SHA after retries: {e}, using timestamp fallback")
            commit_sha = self._fallback_version()

        version_file.write_text(commit_sha)
        logger.debug(f"Updated version file with: {commit_sha}")

    def get_template(self, name: str) -> str | None:
        """
        Get the content of a gitignore template.

        Args:
            name: Template name (e.g., "Python", "Node")

        Returns:
            Template content or None if not found
        """
        # Ensure cache is populated
        if not self._is_cache_valid():
            logger.info("Cache invalid, updating templates...")
            self.update_cache()

        # Try different locations for the template
        possible_paths = [
            self.cache_dir / f"{name}.gitignore",
            self.cache_dir / "Global" / f"{name}.gitignore",
            self.cache_dir / "community" / f"{name}.gitignore",
        ]

        for path in possible_paths:
            if path.exists():
                logger.debug(f"Found template at {path}")
                return path.read_text()

        logger.warning(f"Template '{name}' not found in cache")
        return None

    def list_templates(self, category: str | None = None) -> list[str]:
        """
        List available templates.

        Args:
            category: Optional category filter (e.g., "Global", "community")

        Returns:
            List of template names
        """
        # Ensure cache is populated
        if not self._is_cache_valid():
            logger.info("Cache invalid, updating templates...")
            self.update_cache()

        templates = []

        if category:
            # List templates in specific category
            category_dir = self.cache_dir / category
            if category_dir.exists():
                logger.debug(f"Listing templates in category: {category}")
                for file in category_dir.glob("*.gitignore"):
                    templates.append(file.stem)
        else:
            # List all templates
            logger.debug("Listing all templates")

            # Root level templates
            for file in self.cache_dir.glob("*.gitignore"):
                templates.append(file.stem)

            # Global templates
            global_dir = self.cache_dir / "Global"
            if global_dir.exists():
                for file in global_dir.glob("*.gitignore"):
                    templates.append(f"Global/{file.stem}")

            # Community templates
            community_dir = self.cache_dir / "community"
            if community_dir.exists():
                for file in community_dir.rglob("*.gitignore"):
                    relative = file.relative_to(community_dir)
                    templates.append(f"community/{relative.with_suffix('').as_posix()}")

        logger.debug(f"Found {len(templates)} templates")
        return sorted(templates)

    def search_templates(self, pattern: str) -> list[str]:
        """
        Search for templates matching a pattern.

        Args:
            pattern: Search pattern (case-insensitive)

        Returns:
            List of matching template names
        """
        pattern_lower = pattern.lower()
        all_templates = self.list_templates()

        matches = [t for t in all_templates if pattern_lower in t.lower()]
        logger.debug(f"Found {len(matches)} templates matching '{pattern}'")

        return matches


# 🧰🌍🔚
