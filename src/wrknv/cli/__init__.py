#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv CLI Module
================
Command-line interface for wrknv tool management."""

from __future__ import annotations

from wrknv.cli.hub_cli import create_cli, main

# Compatibility aliases
entry_point = main

__all__ = ["create_cli", "entry_point", "main"]

# 🧰🌍🔚
