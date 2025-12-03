#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv Logging Setup
===================
Provides setup functions for wrknv logging configuration."""

from __future__ import annotations

# Note: emoji hierarchy registration disabled - module not available in Foundation
# from provide.foundation.logger.emoji.hierarchy import register_emoji_hierarchy
# from .emojis import WRKNV_EMOJI_HIERARCHY


def setup_wrknv_logging() -> None:
    """
    Set up wrknv-specific logging configuration.

    Currently a placeholder as emoji hierarchy registration is disabled.
    """
    # Note: Emoji hierarchy registration disabled - module not available
    # register_emoji_hierarchy("wrknv", WRKNV_EMOJI_HIERARCHY)


def setup_wrknv_config_logging() -> None:
    """
    Set up logging based on wrknv configuration.

    Currently a placeholder as emoji hierarchy registration is disabled.
    The actual log level configuration is handled by WorkenvConfig.
    """
    # Note: Emoji hierarchy registration disabled - module not available
    # register_emoji_hierarchy("wrknv", WRKNV_EMOJI_HIERARCHY)


# 🧰🌍🔚
