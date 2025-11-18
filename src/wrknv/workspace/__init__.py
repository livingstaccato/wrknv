#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Multi-Repo Workspace Management Package
=======================================
Manage configurations across multiple independent Git repositories."""

from __future__ import annotations

from .discovery import WorkspaceDiscovery
from .manager import WorkspaceManager
from .orchestrator import WorkspaceOrchestrator, WorkspaceTaskResult
from .schema import RepoConfig, WorkspaceConfig
from .sync import WorkspaceSync

__all__ = [
    "RepoConfig",
    "WorkspaceConfig",
    "WorkspaceDiscovery",
    "WorkspaceManager",
    "WorkspaceOrchestrator",
    "WorkspaceSync",
    "WorkspaceTaskResult",
]

# 🧰🌍🔚
