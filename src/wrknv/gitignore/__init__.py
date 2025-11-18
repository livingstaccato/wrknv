#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Gitignore Management Module
===========================
Comprehensive gitignore file management for wrknv projects."""

from __future__ import annotations

from .builder import GitignoreBuilder
from .detector import ProjectDetector
from .manager import GitignoreManager
from .templates import TemplateHandler

__all__ = [
    "GitignoreBuilder",
    "GitignoreManager",
    "ProjectDetector",
    "TemplateHandler",
]

# 🧰🌍🔚
