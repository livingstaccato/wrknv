#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv.env
==========
Core environment management functionality for development tool management.

Provides:
- Cross-platform tool installation (Terraform, OpenTofu, Go, UV, etc.)
- Version management and switching
- Development environment profiles
- Flexible configuration system

This module can be used standalone or integrated with other tools."""

from __future__ import annotations

# Submodules are available but not imported to avoid circular imports
# Use explicit imports: from wrknv.wenv import config, managers, etc.

__all__ = ["config", "managers", "operations"]

# 🧰🌍🔚
