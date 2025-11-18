#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for managers factory."""

from __future__ import annotations

from provide.testkit import FoundationTestCase
from provide.testkit.mocking import patch
import pytest

from wrknv.config import WorkenvConfig
from wrknv.managers.factory import (
    get_major_tools,
    get_secondary_tools,
    get_supported_tools,
    get_tool_manager,
)


class TestGetToolManager(FoundationTestCase):
    """Test get_tool_manager factory function."""

    def test_get_ibmtf_manager(self) -> None:
        """Test creating IbmTf manager."""
        config = WorkenvConfig()
        manager = get_tool_manager("ibmtf", config)

        assert manager is not None
        assert manager.config == config

    def test_get_tofu_manager(self) -> None:
        """Test creating Tofu manager."""
        config = WorkenvConfig()
        manager = get_tool_manager("tofu", config)

        assert manager is not None
        assert manager.config == config

    def test_get_bao_manager(self) -> None:
        """Test creating Bao manager."""
        config = WorkenvConfig()
        manager = get_tool_manager("bao", config)

        assert manager is not None
        assert manager.config == config

    def test_get_vault_manager(self) -> None:
        """Test creating Vault manager."""
        config = WorkenvConfig()
        manager = get_tool_manager("vault", config)

        assert manager is not None
        assert manager.config == config

    def test_get_uv_manager(self) -> None:
        """Test creating UV manager."""
        config = WorkenvConfig()
        manager = get_tool_manager("uv", config)

        assert manager is not None
        assert manager.config == config

    def test_get_go_manager(self) -> None:
        """Test creating Go manager."""
        config = WorkenvConfig()
        manager = get_tool_manager("go", config)

        assert manager is not None
        assert manager.config == config

    def test_get_unknown_manager_returns_none(self) -> None:
        """Test that unknown tool returns None."""
        manager = get_tool_manager("unknown-tool")
        assert manager is None

    def test_get_manager_with_default_config(self) -> None:
        """Test creating manager without providing config."""
        with patch("wrknv.managers.factory.WorkenvConfig.load") as mock_load:
            # Use real config instead of mock to avoid path issues
            real_config = WorkenvConfig()
            mock_load.return_value = real_config

            manager = get_tool_manager("uv")

            assert manager is not None
            assert manager.config == real_config
            mock_load.assert_called_once()


class TestGetSupportedTools(FoundationTestCase):
    """Test get_supported_tools function."""

    def test_returns_list_of_tools(self) -> None:
        """Test that function returns a list."""
        tools = get_supported_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_contains_expected_tools(self) -> None:
        """Test that list contains expected tools."""
        tools = get_supported_tools()
        assert "ibmtf" in tools
        assert "tofu" in tools
        assert "bao" in tools
        assert "vault" in tools
        assert "uv" in tools
        assert "go" in tools


class TestGetMajorTools(FoundationTestCase):
    """Test get_major_tools function."""

    def test_returns_list_of_major_tools(self) -> None:
        """Test that function returns a list."""
        tools = get_major_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_major_tools_are_supported(self) -> None:
        """Test that all major tools are in supported tools."""
        major = get_major_tools()
        supported = get_supported_tools()
        for tool in major:
            assert tool in supported


class TestGetSecondaryTools(FoundationTestCase):
    """Test get_secondary_tools function."""

    def test_returns_list(self) -> None:
        """Test that function returns a list."""
        tools = get_secondary_tools()
        assert isinstance(tools, list)

    def test_currently_empty(self) -> None:
        """Test that secondary tools is currently empty."""
        tools = get_secondary_tools()
        assert len(tools) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
