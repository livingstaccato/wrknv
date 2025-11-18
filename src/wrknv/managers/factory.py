#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tool Manager Factory for wrknv
================================
Factory for creating appropriate tool managers."""

from __future__ import annotations

from wrknv.config import WorkenvConfig

from .base import BaseToolManager


def get_tool_manager(tool_name: str, config: WorkenvConfig | None = None) -> BaseToolManager | None:
    """Get appropriate tool manager for a tool."""

    if config is None:
        config = WorkenvConfig.load()

    # Terraform ecosystem
    if tool_name == "ibmtf":
        from .tf.ibm import IbmTfVariant

        return IbmTfVariant(config)

    elif tool_name == "tofu":
        from .tf.tofu import TofuTfVariant

        return TofuTfVariant(config)

    # Secret management (sub rosa)
    elif tool_name == "bao":
        from .subrosa.bao import BaoVariant

        return BaoVariant(config)

    elif tool_name == "vault":
        from .subrosa.ibm import IbmVaultVariant

        return IbmVaultVariant(config)

    # Single-variant tools
    elif tool_name == "uv":
        from .uv import UvManager

        return UvManager(config)

    elif tool_name == "go":
        from .go import GoManager

        return GoManager(config)

    # Add more tools as needed:
    # elif tool_name == "python":
    #     from .python import PythonManager
    #     return PythonManager(config)
    #
    # elif tool_name == "node":
    #     from .node import NodeManager
    #     return NodeManager(config)

    return None


def get_supported_tools() -> list[str]:
    """Get list of supported tools."""
    return ["ibmtf", "tofu", "bao", "vault", "uv", "go"]


def get_major_tools() -> list[str]:
    """Get list of major tools (those with direct CLI commands)."""
    return ["ibmtf", "tofu", "bao", "vault", "uv", "go"]


def get_secondary_tools() -> list[str]:
    """Get list of secondary tools (managed via set/get commands)."""
    # For now, all tools are major tools
    # This will be expanded later for tools like python, node, docker, etc.
    return []


# 🧰🌍🔚
