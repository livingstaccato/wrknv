#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for shell completions."""

from __future__ import annotations

from provide.testkit import FoundationTestCase
import pytest

from wrknv.wenv.completions import (
    generate_bash_completions,
    generate_completions,
    generate_fish_completions,
    generate_zsh_completions,
)


class TestCompletions(FoundationTestCase):
    """Test completion generation."""

    def test_generate_bash_completions(self) -> None:
        """Test Bash completion generation."""
        result = generate_bash_completions()
        assert "# Bash completion for wrknv" in result
        assert "_wrknv_completion()" in result
        assert "complete -F _wrknv_completion wrknv" in result

    def test_generate_zsh_completions(self) -> None:
        """Test Zsh completion generation."""
        result = generate_zsh_completions()
        assert "#compdef wrknv" in result
        assert "_wrknv()" in result

    def test_generate_fish_completions(self) -> None:
        """Test Fish completion generation."""
        result = generate_fish_completions()
        assert "# Fish completion for wrknv" in result
        assert "complete -c wrknv" in result

    def test_generate_completions_bash(self) -> None:
        """Test generating completions for Bash."""
        result = generate_completions("bash")
        assert "# Bash completion for wrknv" in result

    def test_generate_completions_zsh(self) -> None:
        """Test generating completions for Zsh."""
        result = generate_completions("zsh")
        assert "#compdef wrknv" in result

    def test_generate_completions_fish(self) -> None:
        """Test generating completions for Fish."""
        result = generate_completions("fish")
        assert "# Fish completion for wrknv" in result

    def test_generate_completions_unsupported_shell(self) -> None:
        """Test error for unsupported shell."""
        with pytest.raises(ValueError, match="Unsupported shell: powershell"):
            generate_completions("powershell")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
