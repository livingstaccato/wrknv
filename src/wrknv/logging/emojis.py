#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv Emoji Hierarchy Definitions
==================================
Defines the emoji hierarchy for wrknv modules."""

from __future__ import annotations

# wrknv emoji hierarchy - organized by functionality
WRKNV_EMOJI_HIERARCHY = {
    # Core wrknv
    # CLI interface
    "wrknv.cli": "⌨️",
    "wrknv.cli.commands": "🎯",
    "wrknv.cli.commands.terraform": "🟦",
    "wrknv.cli.commands.container": "🐳",
    "wrknv.cli.commands.profile": "👤",
    "wrknv.cli.commands.setup": "🌱",
    # Work environment management
    "wrknv.managers.terraform": "🟦",
    "wrknv.managers.tofu": "🌿",
    "wrknv.managers.ibm_tf": "🔵",
    "wrknv.managers.go": "🐹",
    "wrknv.managers.uv": "⚡",
    "wrknv.wenv.version_resolver": "🔍",
    "wrknv.wenv.env_generator": "📝",
    "wrknv.wenv.doctor": "🩺",
    # Configuration system
    "wrknv.config.core": "🔩",
    "wrknv.config.sources": "📋",
    # Package management
    "wrknv.package": "📤",
    # Container operations
    "wrknv.container": "🐳",
    # Gitignore management
    "wrknv.gitignore.manager": "📝",
}

# 🧰🌍🔚
