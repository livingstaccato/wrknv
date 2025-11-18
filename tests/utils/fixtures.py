#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test Fixtures and Mock Factories
=================================
Utilities for creating properly mocked attrs-based objects for testing.

The attrs library makes classes immutable by default, which prevents
mocking individual methods. These factories create mock objects that
work with the attrs architecture.

Note: Imports are done lazily inside functions to avoid circular import
issues when this module is loaded by conftest.py."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from provide.testkit.mocking import Mock

# Use TYPE_CHECKING to avoid runtime imports
if TYPE_CHECKING:
    from wrknv.config import WorkenvConfig
    from wrknv.container.manager import ContainerManager


def create_test_config(
    project_name: str = "test-project",
    container_enabled: bool = True,
    **kwargs: Any,
) -> WorkenvConfig:
    """Create a test WorkenvConfig with sensible defaults.

    Args:
        project_name: Project name
        container_enabled: Whether container support is enabled
        **kwargs: Additional config parameters

    Returns:
        WorkenvConfig instance
    """
    # Lazy import to avoid circular dependency
    from wrknv.config import WorkenvConfig
    from wrknv.wenv.schema import ContainerConfig

    container = ContainerConfig(enabled=container_enabled) if container_enabled else None

    return WorkenvConfig(
        project_name=project_name,
        container=container,
        **kwargs,
    )


def create_mock_runtime(
    name: str = "docker",
    available: bool = True,
    **kwargs: Any,
) -> Mock:
    """Create a mock DockerRuntime for testing.

    This creates a Mock with the spec of DockerRuntime but allows
    mocking individual methods since it's not a real attrs instance.

    Args:
        name: Runtime name
        available: Whether runtime is available
        **kwargs: Additional runtime attributes

    Returns:
        Mock configured as DockerRuntime
    """
    # Lazy import to avoid circular dependency
    from wrknv.container.runtime.docker import DockerRuntime

    runtime = Mock(spec=DockerRuntime)
    runtime.runtime_name = name
    runtime.runtime_command = name
    runtime.is_available = Mock(return_value=available)
    runtime.run_container = Mock(return_value=Mock(returncode=0, stdout="", stderr=""))
    runtime.start_container = Mock(return_value=Mock(returncode=0))
    runtime.stop_container = Mock(return_value=Mock(returncode=0))
    runtime.remove_container = Mock(return_value=Mock(returncode=0))
    runtime.exec_in_container = Mock(return_value=Mock(returncode=0, stdout="", stderr=""))
    runtime.container_exists = Mock(return_value=True)
    runtime.container_running = Mock(return_value=True)
    runtime.build_image = Mock(return_value=Mock(returncode=0))

    # Apply any additional attributes
    for key, value in kwargs.items():
        setattr(runtime, key, value)

    return runtime


def create_mock_lifecycle(
    container_name: str = "test-project-dev",
    exists: bool = True,
    running: bool = True,
    **kwargs: Any,
) -> Mock:
    """Create a mock ContainerLifecycle for testing.

    Args:
        container_name: Container name
        exists: Whether container exists
        running: Whether container is running
        **kwargs: Additional lifecycle attributes

    Returns:
        Mock configured as ContainerLifecycle
    """
    # Lazy import to avoid circular dependency
    from wrknv.container.operations.lifecycle import ContainerLifecycle

    lifecycle = Mock(spec=ContainerLifecycle)
    lifecycle.container_name = container_name
    lifecycle.exists = Mock(return_value=exists)
    lifecycle.is_running = Mock(return_value=running)
    lifecycle.start = Mock(return_value=True)
    lifecycle.stop = Mock(return_value=True)
    lifecycle.restart = Mock(return_value=True)
    lifecycle.remove = Mock(return_value=True)
    lifecycle.status = Mock(
        return_value={
            "exists": exists,
            "running": running,
            "name": container_name,
            "status": "running" if running else "stopped",
            "id": "abc123",
            "image": "test-image:latest",
        }
    )

    for key, value in kwargs.items():
        setattr(lifecycle, key, value)

    return lifecycle


def create_mock_exec(
    container_name: str = "test-project-dev",
    **kwargs: Any,
) -> Mock:
    """Create a mock ContainerExec for testing.

    Args:
        container_name: Container name
        **kwargs: Additional exec attributes

    Returns:
        Mock configured as ContainerExec
    """
    # Lazy import to avoid circular dependency
    from wrknv.container.operations.exec import ContainerExec

    exec_mock = Mock(spec=ContainerExec)
    exec_mock.container_name = container_name
    exec_mock.enter = Mock(return_value=True)
    exec_mock.run = Mock(return_value=Mock(returncode=0, stdout="", stderr=""))

    for key, value in kwargs.items():
        setattr(exec_mock, key, value)

    return exec_mock


def create_mock_logs(
    container_name: str = "test-project-dev",
    **kwargs: Any,
) -> Mock:
    """Create a mock ContainerLogs for testing.

    Args:
        container_name: Container name
        **kwargs: Additional logs attributes

    Returns:
        Mock configured as ContainerLogs
    """
    # Lazy import to avoid circular dependency
    from wrknv.container.operations.logs import ContainerLogs

    logs_mock = Mock(spec=ContainerLogs)
    logs_mock.container_name = container_name
    logs_mock.get_logs = Mock(return_value="test logs")
    logs_mock.stream_logs = Mock(return_value=True)

    for key, value in kwargs.items():
        setattr(logs_mock, key, value)

    return logs_mock


def create_mock_builder(**kwargs: Any) -> Mock:
    """Create a mock ContainerBuilder for testing.

    Args:
        **kwargs: Additional builder attributes

    Returns:
        Mock configured as ContainerBuilder
    """
    # Lazy import to avoid circular dependency
    from wrknv.container.operations.build import ContainerBuilder

    builder = Mock(spec=ContainerBuilder)
    builder.build = Mock(return_value=True)
    builder.image_exists = Mock(return_value=True)

    # Mock generate_dockerfile to return a basic Dockerfile string
    builder.generate_dockerfile = Mock(
        return_value="""FROM ubuntu:22.04

WORKDIR /workspace

RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash user
RUN chown -R user:user /workspace
USER user

# Keep container running
CMD ["sleep", "infinity"]
"""
    )

    for key, value in kwargs.items():
        setattr(builder, key, value)

    return builder


def create_mock_volumes(backup_dir: Path | None = None, **kwargs: Any) -> Mock:
    """Create a mock VolumeManager for testing.

    Args:
        backup_dir: Backup directory path
        **kwargs: Additional volume attributes

    Returns:
        Mock configured as VolumeManager
    """
    # Lazy import to avoid circular dependency
    from wrknv.container.operations.volumes import VolumeManager

    volumes = Mock(spec=VolumeManager)
    volumes.backup_dir = backup_dir or Path("/tmp/backups")
    volumes.create_volume = Mock(return_value=True)
    volumes.remove_volume = Mock(return_value=True)
    volumes.list_volumes = Mock(return_value=[])
    volumes.backup_volume = Mock(return_value=True)
    volumes.restore_volume = Mock(return_value=True)
    volumes.backup = Mock(return_value=True)
    volumes.restore = Mock(return_value=True)
    volumes.clean = Mock(return_value=True)

    for key, value in kwargs.items():
        setattr(volumes, key, value)

    return volumes


def create_mock_storage(
    container_name: str = "test-project-dev",
    **kwargs: Any,
) -> Mock:
    """Create a mock ContainerStorage for testing.

    Args:
        container_name: Container name
        **kwargs: Additional storage attributes

    Returns:
        Mock configured as ContainerStorage
    """
    # Lazy import to avoid circular dependency
    from wrknv.container.storage import ContainerStorage

    storage = Mock(spec=ContainerStorage)
    storage.container_name = container_name
    storage.base_dir = Path(f"/tmp/wrknv/containers/{container_name}")
    storage.get_container_path = Mock(side_effect=lambda p: storage.base_dir / p if p else storage.base_dir)
    storage.get_volume_mappings = Mock(return_value={})
    storage.setup_storage = Mock(return_value=True)
    storage.clean_storage = Mock(return_value=True)
    storage.save_metadata = Mock()
    storage.load_metadata = Mock(return_value={})
    storage.update_metadata = Mock()

    for key, value in kwargs.items():
        setattr(storage, key, value)

    return storage


def create_mock_manager(
    project_name: str = "test-project",
    container_name: str = "test-project-dev",
    config: WorkenvConfig | None = None,
    **kwargs: Any,
) -> ContainerManager:
    """Create a ContainerManager with mocked dependencies.

    This creates a REAL ContainerManager instance but replaces all
    its attrs-based dependencies with mocks. This allows testing
    the manager's logic while controlling dependency behavior.

    Args:
        project_name: Project name
        container_name: Container name
        config: Optional config (will create default if None)
        **kwargs: Flags to control mock behavior (e.g., docker_available=False)

    Returns:
        ContainerManager with mocked dependencies

    Example:
        >>> manager = create_mock_manager(docker_available=False)
        >>> manager.check_docker()
        False
    """
    # Lazy import to avoid circular dependency
    from wrknv.container.manager import ContainerManager

    # Create config if not provided
    if config is None:
        config = create_test_config(project_name=project_name)

    # Create real manager
    manager = ContainerManager(config=config)

    # Replace attrs components with mocks
    docker_available = kwargs.get("docker_available", True)
    container_exists = kwargs.get("container_exists", True)
    container_running = kwargs.get("container_running", True)

    manager.runtime = create_mock_runtime(available=docker_available)
    manager.lifecycle = create_mock_lifecycle(
        container_name=container_name,
        exists=container_exists,
        running=container_running,
    )
    manager.exec = create_mock_exec(container_name=container_name)
    manager.logs = create_mock_logs(container_name=container_name)
    manager.builder = create_mock_builder()
    manager.volumes = create_mock_volumes()
    manager.storage = create_mock_storage(container_name=container_name)

    return manager


# Convenience function for pytest fixtures
def pytest_configure_fixtures(config) -> None:
    """Configure pytest with these fixtures.

    Add this to conftest.py:
        from tests.utils.fixtures import *
    """
    pass


# 🧰🌍🔚
