#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tf Manager Utilities
====================
Utility functions for Terraform/OpenTofu managers."""

from __future__ import annotations

import hashlib
import pathlib

import semver


def calculate_file_hash(file_path: pathlib.Path, algorithm: str = "sha256") -> str:
    """Calculate hash of a file."""
    hash_func = hashlib.new(algorithm)
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def version_sort_key(version: str) -> semver.VersionInfo:
    """Generate sort key for semantic versioning using semver module."""
    try:
        # Try to parse as a semantic version
        return semver.VersionInfo.parse(version)
    except ValueError:
        # If it fails, try to make it semver-compliant
        # Handle versions like "1.0" by adding ".0"
        parts = version.split(".")
        while len(parts) < 3:
            parts.append("0")
        try:
            normalized = ".".join(parts[:3])
            return semver.VersionInfo.parse(normalized)
        except ValueError:
            # Last resort: return a very old version
            return semver.VersionInfo.parse("0.0.0")


def get_tool_version_key(tool_name: str) -> str:
    """Get the metadata key for storing tool version."""
    return "opentofu_version" if tool_name == "tofu" else f"{tool_name}_version"


# 🧰🌍🔚
