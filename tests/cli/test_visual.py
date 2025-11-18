#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for CLI visual utilities."""

from __future__ import annotations

from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch
import pytest
from rich.console import Console

from wrknv.cli.visual import (
    Emoji,
    get_console,
    get_tool_emoji,
    print_dim,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)


class TestEmoji(FoundationTestCase):
    """Test Emoji constants."""

    def test_tool_emojis(self) -> None:
        """Test tool emoji constants exist."""
        assert Emoji.TERRAFORM
        assert Emoji.OPENTOFU
        assert Emoji.GO

    def test_action_emojis(self) -> None:
        """Test action emoji constants exist."""
        assert Emoji.BUILD
        assert Emoji.START
        assert Emoji.STOP
        assert Emoji.CLEAN
        assert Emoji.STATUS
        assert Emoji.SYNC
        assert Emoji.DOWNLOAD
        assert Emoji.INSTALL

    def test_status_emojis(self) -> None:
        """Test status emoji constants exist."""
        assert Emoji.ERROR
        assert Emoji.WARNING
        assert Emoji.INFO
        assert Emoji.SUCCESS
        assert Emoji.RUNNING
        assert Emoji.STOPPED

    def test_environment_emojis(self) -> None:
        """Test environment emoji constants exist."""
        assert Emoji.PROFILE
        assert Emoji.WORKBENCH
        assert Emoji.CONFIG

    def test_language_emojis(self) -> None:
        """Test language emoji constants exist."""
        assert Emoji.PYTHON
        assert Emoji.UV
        assert Emoji.PACKAGE


class TestVisualFunctions(FoundationTestCase):
    """Test visual print functions."""

    def test_get_console(self) -> None:
        """Test getting configured console."""
        console = get_console()
        assert isinstance(console, Console)
        # Console has theme configured (no direct accessor)

    def test_print_header_with_emoji(self) -> None:
        """Test printing header with emoji."""
        with patch("wrknv.cli.visual.Console") as mock_console_cls:
            mock_console = Mock()
            mock_console_cls.return_value = mock_console

            print_header("Test Header", emoji="🎉")

            assert mock_console.print.call_count == 2
            calls = mock_console.print.call_args_list
            assert "🎉 Test Header" in str(calls[0])
            assert "=" in str(calls[1])

    def test_print_header_without_emoji(self) -> None:
        """Test printing header without emoji."""
        with patch("wrknv.cli.visual.Console") as mock_console_cls:
            mock_console = Mock()
            mock_console_cls.return_value = mock_console

            print_header("Test Header")

            assert mock_console.print.call_count == 2
            calls = mock_console.print.call_args_list
            assert "Test Header" in str(calls[0])

    def test_print_info(self) -> None:
        """Test printing info message."""
        with patch("wrknv.cli.visual.Console") as mock_console_cls:
            mock_console = Mock()
            mock_console_cls.return_value = mock_console

            print_info("Info message")

            mock_console.print.assert_called_once()
            call_args = str(mock_console.print.call_args)
            assert "Info message" in call_args
            assert "[info]" in call_args

    def test_print_success(self) -> None:
        """Test printing success message."""
        with patch("wrknv.cli.visual.Console") as mock_console_cls:
            mock_console = Mock()
            mock_console_cls.return_value = mock_console

            print_success("Success message")

            mock_console.print.assert_called_once()
            call_args = str(mock_console.print.call_args)
            assert "Success message" in call_args
            assert "[success]" in call_args

    def test_print_warning(self) -> None:
        """Test printing warning message."""
        with patch("wrknv.cli.visual.Console") as mock_console_cls:
            mock_console = Mock()
            mock_console_cls.return_value = mock_console

            print_warning("Warning message")

            mock_console.print.assert_called_once()
            call_args = str(mock_console.print.call_args)
            assert "Warning message" in call_args
            assert "[warning]" in call_args

    def test_print_error(self) -> None:
        """Test printing error message."""
        with patch("wrknv.cli.visual.Console") as mock_console_cls:
            mock_console = Mock()
            mock_console_cls.return_value = mock_console

            print_error("Error message")

            mock_console.print.assert_called_once()
            call_args = str(mock_console.print.call_args)
            assert "Error message" in call_args
            assert "[error]" in call_args

    def test_print_dim(self) -> None:
        """Test printing dimmed text."""
        with patch("wrknv.cli.visual.Console") as mock_console_cls:
            mock_console = Mock()
            mock_console_cls.return_value = mock_console

            print_dim("Dim text")

            mock_console.print.assert_called_once()
            call_args = str(mock_console.print.call_args)
            assert "Dim text" in call_args
            assert "[dim]" in call_args

    def test_get_tool_emoji_known_tools(self) -> None:
        """Test getting emoji for known tools."""
        assert get_tool_emoji("terraform") == Emoji.TERRAFORM
        assert get_tool_emoji("tofu") == Emoji.OPENTOFU
        assert get_tool_emoji("opentofu") == Emoji.OPENTOFU
        assert get_tool_emoji("go") == Emoji.GO
        assert get_tool_emoji("python") == Emoji.PYTHON
        assert get_tool_emoji("uv") == Emoji.UV

    def test_get_tool_emoji_case_insensitive(self) -> None:
        """Test tool emoji lookup is case insensitive."""
        assert get_tool_emoji("TERRAFORM") == Emoji.TERRAFORM
        assert get_tool_emoji("Tofu") == Emoji.OPENTOFU
        assert get_tool_emoji("GO") == Emoji.GO

    def test_get_tool_emoji_unknown_tool(self) -> None:
        """Test getting emoji for unknown tool returns default."""
        assert get_tool_emoji("unknown") == Emoji.WORKBENCH
        assert get_tool_emoji("random-tool") == Emoji.WORKBENCH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
