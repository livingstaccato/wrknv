#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test suite for platform operations."""

from __future__ import annotations

from provide.testkit import FoundationTestCase
from provide.testkit.mocking import patch
import pytest

from wrknv.wenv.operations.platform import is_arm_mac, is_windows


class TestPlatformDetection(FoundationTestCase):
    """Test platform detection functions."""

    def test_is_arm_mac_true(self) -> None:
        """Test is_arm_mac returns True when on ARM Mac."""
        with (
            patch("provide.foundation.platform.is_macos", return_value=True),
            patch("provide.foundation.platform.is_arm", return_value=True),
        ):
            assert is_arm_mac() is True

    def test_is_arm_mac_false_not_mac(self) -> None:
        """Test is_arm_mac returns False when not on Mac."""
        with (
            patch("provide.foundation.platform.is_macos", return_value=False),
            patch("provide.foundation.platform.is_arm", return_value=True),
        ):
            assert is_arm_mac() is False

    def test_is_arm_mac_false_not_arm(self) -> None:
        """Test is_arm_mac returns False when not on ARM."""
        with (
            patch("provide.foundation.platform.is_macos", return_value=True),
            patch("provide.foundation.platform.is_arm", return_value=False),
        ):
            assert is_arm_mac() is False

    def test_is_windows_true(self) -> None:
        """Test is_windows returns True on Windows."""
        with patch("provide.foundation.platform.is_windows", return_value=True):
            assert is_windows() is True

    def test_is_windows_false(self) -> None:
        """Test is_windows returns False when not on Windows."""
        with patch("provide.foundation.platform.is_windows", return_value=False):
            assert is_windows() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
