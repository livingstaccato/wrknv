#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Visual UX Enhancements
======================
Emoji and color support for enhanced CLI output."""

from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

# Custom theme with colors
WRKENV_THEME = Theme(
    {
        "info": "blue",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "dim": "dim white",
        "highlight": "cyan",
    }
)


# Emoji constants for consistent visual feedback
class Emoji:
    """Emoji constants for visual feedback."""

    # Tool emojis
    TERRAFORM = "🔷"
    OPENTOFU = "🌿"
    GO = "🐹"

    # Action emojis
    BUILD = "🔨"
    START = "🚀"
    STOP = "⏹️"
    CLEAN = "🧹"
    STATUS = "📊"
    SYNC = "🔄"
    DOWNLOAD = "⬇️"
    INSTALL = "📥"

    # Container emojis
    CONTAINER = "🐳"

    # Status emojis
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ⓘ"
    SUCCESS = "✅"
    RUNNING = "🟢"
    STOPPED = "🟡"

    # Environment emojis
    PROFILE = "👤"
    WORKBENCH = "🧰"
    CONFIG = "⚙️"

    # Language emojis
    PYTHON = "🐍"
    UV = "📦"
    PACKAGE = "📦"


def get_console() -> Console:
    """Get a configured Rich console with theme."""
    return Console(theme=WRKENV_THEME)


def print_header(text: str, emoji: str | None = None) -> None:
    """Print a styled header."""
    console = get_console()
    if emoji:
        text = f"{emoji} {text}"
    console.print(f"[highlight]{text}[/highlight]")
    console.print(f"[highlight]{'=' * len(text)}[/highlight]")


def print_info(text: str, emoji: str = Emoji.INFO) -> None:
    """Print an info message."""
    console = get_console()
    console.print(f"{emoji} [info]{text}[/info]")


def print_success(text: str, emoji: str = Emoji.SUCCESS) -> None:
    """Print a success message."""
    console = get_console()
    console.print(f"{emoji} [success]{text}[/success]")


def print_warning(text: str, emoji: str = Emoji.WARNING) -> None:
    """Print a warning message."""
    console = get_console()
    console.print(f"{emoji} [warning]{text}[/warning]")


def print_error(text: str, emoji: str = Emoji.ERROR) -> None:
    """Print an error message."""
    console = get_console()
    console.print(f"{emoji} [error]{text}[/error]", style="error")


def print_dim(text: str) -> None:
    """Print dimmed text."""
    console = get_console()
    console.print(f"[dim]{text}[/dim]")


def get_tool_emoji(tool_name: str) -> str:
    """Get emoji for a specific tool."""
    tool_emojis = {
        "terraform": Emoji.TERRAFORM,
        "tofu": Emoji.OPENTOFU,
        "opentofu": Emoji.OPENTOFU,
        "go": Emoji.GO,
        "python": Emoji.PYTHON,
        "uv": Emoji.UV,
    }
    return tool_emojis.get(tool_name.lower(), Emoji.WORKBENCH)


# 🧰🌍🔚
