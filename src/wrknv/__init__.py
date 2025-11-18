#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""🧰🌍 wrknv - Work Environment Tool
===================================

A flexible tool for managing development environments and tool versions.
Supports Terraform, OpenTofu, Go, UV, and more.

Can be used standalone or integrated with other tools."""

from __future__ import annotations

from provide.foundation.utils.versioning import get_version

from wrknv import errors

__version__ = get_version("wrknv", caller_file=__file__)

# Public API exports
from wrknv.config import WorkenvConfig, WorkenvConfigError
from wrknv.managers.factory import get_supported_tools, get_tool_manager

__all__ = [
    "WorkenvConfig",
    "WorkenvConfigError",
    "__version__",
    "container",
    "errors",
    "get_supported_tools",
    "get_tool_manager",
    "package",
    "wenv",
]

# 🧰🌍🔚
