#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import sys

import pytest

# Platform detection
IS_WINDOWS = sys.platform == "win32"
IS_UNIX = sys.platform in ("linux", "darwin")


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "unix_only: mark test to run only on Unix systems")
    config.addinivalue_line("markers", "windows_only: mark test to run only on Windows")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip tests based on platform markers."""
    skip_windows = pytest.mark.skip(reason="Test requires Unix (uses bash syntax or Unix paths)")
    skip_unix = pytest.mark.skip(reason="Test requires Windows")

    for item in items:
        if "unix_only" in item.keywords and IS_WINDOWS:
            item.add_marker(skip_windows)
        if "windows_only" in item.keywords and IS_UNIX:
            item.add_marker(skip_unix)


# Import all test utilities to make them available
from tests.utils.fixtures import (
    create_mock_builder,
    create_mock_exec,
    create_mock_lifecycle,
    create_mock_logs,
    create_mock_manager,
    create_mock_runtime,
    create_mock_storage,
    create_mock_volumes,
    create_test_config,
)


# Make fixtures available as pytest fixtures
@pytest.fixture
def test_config():
    """Create a test configuration."""
    return create_test_config()


@pytest.fixture
def mock_runtime():
    """Create a mock DockerRuntime."""
    return create_mock_runtime()


@pytest.fixture
def mock_manager():
    """Create a ContainerManager with mocked dependencies."""
    return create_mock_manager()


@pytest.fixture
def mock_lifecycle():
    """Create a mock ContainerLifecycle."""
    return create_mock_lifecycle()


@pytest.fixture
def mock_exec():
    """Create a mock ContainerExec."""
    return create_mock_exec()


@pytest.fixture
def mock_logs():
    """Create a mock ContainerLogs."""
    return create_mock_logs()


@pytest.fixture
def mock_builder():
    """Create a mock ContainerBuilder."""
    return create_mock_builder()


@pytest.fixture
def mock_volumes():
    """Create a mock VolumeManager."""
    return create_mock_volumes()


@pytest.fixture
def mock_storage():
    """Create a mock ContainerStorage."""
    return create_mock_storage()


# 🧰🌍🔚
