#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""GitHub Tests Configuration
===========================
Auto-configure GitHub token from gh CLI if available."""

from __future__ import annotations

import os
import subprocess


def pytest_configure(config) -> None:
    """Configure GitHub token from gh CLI if available and not already set."""
    # Don't override if already set
    if os.environ.get("GITHUB_TOKEN"):
        return

    # Try to get token from gh CLI
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        token = result.stdout.strip()
        if token:
            os.environ["GITHUB_TOKEN"] = token
            print("\n✓ Auto-configured GITHUB_TOKEN from gh CLI")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # gh not installed or not authenticated - tests will be skipped
        pass


# 🧰🌍🔚
