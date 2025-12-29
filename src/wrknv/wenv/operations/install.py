#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv Installation Operations
========================================
Functions for extracting archives and making files executable."""

from __future__ import annotations

import pathlib
import stat

from provide.foundation import logger
from provide.foundation.archive.operations import ArchiveOperations
from provide.foundation.archive.tar import TarArchive
from provide.foundation.archive.zip import ZipArchive
from provide.foundation.errors import ResourceError, ValidationError, resilient
from provide.foundation.file import (
    ensure_dir,
    get_size,
    safe_copy,
    safe_delete,
    safe_rmtree,
)


@resilient
def extract_archive(archive_path: pathlib.Path, extract_dir: pathlib.Path) -> None:
    """Extract archive to specified directory."""

    if not archive_path.exists():
        raise ResourceError(f"Archive not found: {archive_path}")

    # Create extraction directory
    extract_dir.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Extracting {archive_path} to {extract_dir}")

    archive_name = archive_path.name.lower()

    try:
        if archive_name.endswith((".tar.gz", ".tgz")):
            # Use foundation's extract_tar_gz with built-in path traversal protection
            ArchiveOperations.extract_tar_gz(archive_path, extract_dir)
        elif archive_name.endswith(".tar"):
            # Use foundation's TarArchive with built-in path traversal protection
            TarArchive().extract(archive_path, extract_dir)
        elif archive_name.endswith(".zip"):
            # Use foundation's ZipArchive with built-in path traversal protection
            ZipArchive().extract(archive_path, extract_dir)
        else:
            raise ValidationError(f"Unsupported archive format: {archive_path}")

        logger.debug(f"Successfully extracted {archive_path}")

    except Exception as e:
        raise ResourceError(f"Failed to extract {archive_path}: {e}") from e


@resilient
def make_executable(file_path: pathlib.Path) -> None:
    """Make file executable on Unix-like systems."""

    if not file_path.exists():
        raise ResourceError(f"File not found: {file_path}")

    # Only needed on Unix-like systems
    import platform

    if platform.system().lower() == "windows":
        logger.debug(f"Skipping chmod on Windows for {file_path}")
        return

    try:
        # Get current permissions
        current_mode = file_path.stat().st_mode

        # Add execute permissions for owner, group, and others
        new_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

        # Set new permissions
        file_path.chmod(new_mode)

        logger.debug(f"Made {file_path} executable (mode: {oct(new_mode)})")

    except Exception as e:
        logger.warning(f"Failed to make {file_path} executable: {e}")


@resilient
def create_symlink(target: pathlib.Path, link_path: pathlib.Path) -> None:
    """Create symbolic link, handling platform differences."""

    if not target.exists():
        raise ResourceError(f"Target does not exist: {target}")

    # Remove existing link if it exists
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()

    # Create parent directories
    link_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        link_path.symlink_to(target)
        logger.debug(f"Created symlink: {link_path} -> {target}")

    except OSError as e:
        # Fall back to copying on Windows if symlink fails
        import platform

        if platform.system().lower() == "windows":
            logger.warning(f"Symlink failed on Windows, copying instead: {e}")
            import shutil

            shutil.copy2(target, link_path)
        else:
            raise


def copy_file(source: pathlib.Path, destination: pathlib.Path, preserve_permissions: bool = True) -> None:
    """Copy file with optional permission preservation."""
    # Use foundation's safe_copy which handles all edge cases
    safe_copy(source, destination, overwrite=True, preserve_mode=preserve_permissions)
    logger.debug(f"Copied {source} to {destination}")


def ensure_directory(dir_path: pathlib.Path, mode: int = 0o755) -> None:
    """Ensure directory exists with specified permissions."""
    # Use foundation's ensure_dir which handles all edge cases
    ensure_dir(dir_path, mode=mode)
    logger.debug(f"Created/verified directory: {dir_path}")


def clean_directory(dir_path: pathlib.Path, keep_hidden: bool = True) -> None:
    """Clean all files from directory, optionally keeping hidden files."""

    if not dir_path.exists():
        return

    if not dir_path.is_dir():
        raise Exception(f"Path is not a directory: {dir_path}")

    for item in dir_path.iterdir():
        if keep_hidden and item.name.startswith("."):
            continue

        try:
            if item.is_dir():
                safe_rmtree(item, missing_ok=True)
            else:
                safe_delete(item, missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to remove {item}: {e}")

    logger.debug(f"Cleaned directory: {dir_path}")


@resilient
def get_file_size(file_path: pathlib.Path) -> int:
    """Get file size in bytes."""
    # Use foundation's get_size which returns 0 for missing files
    size = get_size(file_path)
    if size == 0 and not file_path.exists():
        raise ResourceError(f"File not found: {file_path}")
    return size


def is_executable(file_path: pathlib.Path) -> bool:
    """Check if file is executable."""

    if not file_path.exists():
        return False

    import platform

    if platform.system().lower() == "windows":
        # On Windows, check file extension
        return file_path.suffix.lower() in [".exe", ".bat", ".cmd"]
    else:
        # On Unix-like systems, check execute permission
        return bool(file_path.stat().st_mode & stat.S_IXUSR)


# 🧰🌍🔚
