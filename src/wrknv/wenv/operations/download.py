#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv Download Operations
====================================
Functions for downloading and verifying tool archives using Foundation's ToolDownloader."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import pathlib
from urllib.parse import urlparse

from provide.foundation import logger
from provide.foundation.crypto import verify_file
from provide.foundation.hub import get_hub
from provide.foundation.resilience import circuit_breaker
from provide.foundation.tools.downloader import ToolDownloader
from provide.foundation.transport import UniversalClient


@circuit_breaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=Exception,
)
async def download_file_async(
    url: str,
    output_path: pathlib.Path,
    show_progress: bool = True,
    headers: dict[str, str] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    checksum: str | None = None,
) -> None:
    """Download a file using Foundation's ToolDownloader with streaming.

    Uses circuit breaker to prevent repeated attempts when downloads are failing.
    After 5 failures, will fast-fail for 60 seconds before retrying.

    Args:
        url: URL to download from
        output_path: Where to save the file
        show_progress: Whether to log progress
        headers: Optional custom headers
        progress_callback: Optional callback(downloaded_bytes, total_bytes)
        checksum: Optional checksum for verification

    Raises:
        RuntimeError: If circuit breaker is open (too many recent failures)
        Exception: On download failure
    """
    logger.info(f"Downloading {url} to {output_path}")

    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        hub = get_hub()
        async with UniversalClient(hub=hub, default_headers=headers or {}) as client:
            # Create ToolDownloader instance
            downloader = ToolDownloader(client)

            # Add progress callback if provided
            if progress_callback:
                downloader.add_progress_callback(progress_callback)

            # Add logging progress callback if enabled
            if show_progress:

                def log_progress(downloaded: int, total: int) -> None:
                    if total > 0:
                        percent = min(100, (downloaded * 100) // total)
                        if downloaded % (1024 * 1024) < 1024:  # Log every ~1MB
                            logger.debug(f"Download progress: {percent}% ({downloaded}/{total} bytes)")

                downloader.add_progress_callback(log_progress)

            # Download with progress and optional checksum verification
            await downloader.download_with_progress(url, output_path, checksum)

        logger.info(f"Successfully downloaded {output_path.name}")

    except Exception as e:
        # ToolDownloader already cleans up partial downloads on failure
        raise Exception(f"Failed to download {url}: {e}") from e


def download_file(
    url: str,
    output_path: pathlib.Path,
    show_progress: bool = True,
    headers: dict[str, str] | None = None,
    checksum: str | None = None,
) -> None:
    """Synchronous wrapper for download_file_async.

    Args:
        url: URL to download from
        output_path: Where to save the file
        show_progress: Whether to log progress
        headers: Optional custom headers
        checksum: Optional checksum for verification
    """
    asyncio.run(download_file_async(url, output_path, show_progress, headers, checksum=checksum))


async def download_with_mirrors_async(
    mirrors: list[str],
    output_path: pathlib.Path,
    show_progress: bool = True,
    headers: dict[str, str] | None = None,
    checksum: str | None = None,
) -> None:
    """Download a file trying multiple mirror URLs until one succeeds.

    Args:
        mirrors: List of mirror URLs to try in order
        output_path: Where to save the file
        show_progress: Whether to log progress
        headers: Optional custom headers
        checksum: Optional checksum for verification

    Raises:
        Exception: If all mirrors fail
    """
    logger.info(f"Downloading from mirrors to {output_path}")

    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        hub = get_hub()
        async with UniversalClient(hub=hub, default_headers=headers or {}) as client:
            downloader = ToolDownloader(client)

            # Add logging progress callback if enabled
            if show_progress:

                def log_progress(downloaded: int, total: int) -> None:
                    if total > 0:
                        percent = min(100, (downloaded * 100) // total)
                        if downloaded % (1024 * 1024) < 1024:  # Log every ~1MB
                            logger.debug(f"Download progress: {percent}% ({downloaded}/{total} bytes)")

                downloader.add_progress_callback(log_progress)

            # Download with mirror fallback
            await downloader.download_with_mirrors(mirrors, output_path)

            # Verify checksum if provided (mirror method doesn't support checksum param)
            if checksum and not verify_checksum(output_path, checksum):
                output_path.unlink()
                raise Exception(f"Checksum verification failed for {output_path.name}")

        logger.info(f"Successfully downloaded {output_path.name}")

    except Exception as e:
        raise Exception(f"Failed to download from all mirrors: {e}") from e


def download_with_mirrors(
    mirrors: list[str],
    output_path: pathlib.Path,
    show_progress: bool = True,
    headers: dict[str, str] | None = None,
    checksum: str | None = None,
) -> None:
    """Synchronous wrapper for download_with_mirrors_async.

    Args:
        mirrors: List of mirror URLs to try in order
        output_path: Where to save the file
        show_progress: Whether to log progress
        headers: Optional custom headers
        checksum: Optional checksum for verification
    """
    asyncio.run(download_with_mirrors_async(mirrors, output_path, show_progress, headers, checksum))


def verify_checksum(file_path: pathlib.Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """Verify file checksum using specified algorithm."""

    # Use foundation's verify_file which handles all the details
    return verify_file(file_path, expected_checksum, algorithm)


def download_checksum_file(checksum_url: str, output_dir: pathlib.Path) -> pathlib.Path | None:
    """Download checksum file and return path."""

    if not checksum_url:
        return None

    # Parse filename from URL
    parsed_url = urlparse(checksum_url)
    filename = pathlib.Path(parsed_url.path).name
    if not filename:
        filename = "checksums.txt"

    checksum_path = output_dir / filename

    try:
        download_file(checksum_url, checksum_path, show_progress=False)
        return checksum_path

    except Exception as e:
        logger.warning(f"Failed to download checksum file {checksum_url}: {e}")
        return None


def parse_checksum_file(checksum_path: pathlib.Path, target_filename: str) -> str | None:
    """Parse checksum file to find checksum for target filename."""

    if not checksum_path.exists():
        return None

    try:
        with checksum_path.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Handle different checksum file formats
                parts = line.split()
                if len(parts) >= 2:
                    checksum = parts[0]
                    filename = parts[1]

                    # Remove leading '*' or other markers
                    filename = filename.lstrip("*")

                    # Match target filename
                    if filename == target_filename or filename.endswith(target_filename):
                        logger.debug(f"Found checksum for {target_filename}: {checksum}")
                        return checksum

        logger.warning(f"Checksum not found for {target_filename} in {checksum_path}")
        return None

    except Exception as e:
        logger.error(f"Failed to parse checksum file {checksum_path}: {e}")
        return None


def get_filename_from_url(url: str) -> str:
    """Extract filename from download URL."""
    parsed_url = urlparse(url)
    filename = pathlib.Path(parsed_url.path).name

    if not filename:
        # Fallback to generating filename from URL
        filename = f"download_{hash(url) & 0x7FFFFFFF}"

    return filename


def validate_download_url(url: str) -> bool:
    """Validate that download URL is properly formatted."""

    try:
        parsed = urlparse(url)

        # Must have valid scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False

        # Must be HTTP or HTTPS
        return parsed.scheme.lower() in ["http", "https"]

    except Exception:
        return False


# 🧰🌍🔚
