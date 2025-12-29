#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for wrknv.container.errors
=================================
Comprehensive tests for all container error classes."""

from __future__ import annotations

import pytest

from wrknv.container.errors import (
    ContainerAlreadyExistsError,
    ContainerBuildError,
    ContainerNotFoundError,
    ContainerNotRunningError,
    ContainerRuntimeError,
    ImageNotFoundError,
    VolumeNotFoundError,
)


class TestContainerNotFoundError:
    """Tests for ContainerNotFoundError exception."""

    def test_container_not_found_basic(self) -> None:
        """Test basic container not found error."""
        error = ContainerNotFoundError("my-container")
        assert "Container 'my-container' not found" in str(error)
        assert error.container_name == "my-container"
        assert error.message == "Container 'my-container' not found"

    def test_container_not_found_different_name(self) -> None:
        """Test container not found with different name."""
        error = ContainerNotFoundError("test-container")
        assert "Container 'test-container' not found" in str(error)
        assert error.container_name == "test-container"

    def test_container_not_found_error_instance(self) -> None:
        """Test that error can be instantiated and raised."""
        with pytest.raises(ContainerNotFoundError) as exc_info:
            raise ContainerNotFoundError("missing-container")
        assert exc_info.value.container_name == "missing-container"


class TestContainerNotRunningError:
    """Tests for ContainerNotRunningError exception."""

    def test_container_not_running_basic(self) -> None:
        """Test basic container not running error."""
        error = ContainerNotRunningError("stopped-container")
        assert "Container 'stopped-container' is not running" in str(error)
        assert error.container_name == "stopped-container"

    def test_container_not_running_different_name(self) -> None:
        """Test container not running with different name."""
        error = ContainerNotRunningError("idle-container")
        assert "Container 'idle-container' is not running" in str(error)
        assert error.container_name == "idle-container"

    def test_container_not_running_error_instance(self) -> None:
        """Test that error can be raised."""
        with pytest.raises(ContainerNotRunningError) as exc_info:
            raise ContainerNotRunningError("my-container")
        assert exc_info.value.container_name == "my-container"


class TestContainerAlreadyExistsError:
    """Tests for ContainerAlreadyExistsError exception."""

    def test_container_already_exists_basic(self) -> None:
        """Test basic container already exists error."""
        error = ContainerAlreadyExistsError("duplicate-container")
        assert "Container 'duplicate-container' already exists" in str(error)
        assert error.container_name == "duplicate-container"

    def test_container_already_exists_different_name(self) -> None:
        """Test container already exists with different name."""
        error = ContainerAlreadyExistsError("existing-container")
        assert "Container 'existing-container' already exists" in str(error)
        assert error.container_name == "existing-container"

    def test_container_already_exists_error_instance(self) -> None:
        """Test that error can be raised."""
        with pytest.raises(ContainerAlreadyExistsError) as exc_info:
            raise ContainerAlreadyExistsError("my-container")
        assert exc_info.value.container_name == "my-container"


class TestImageNotFoundError:
    """Tests for ImageNotFoundError exception."""

    def test_image_not_found_basic(self) -> None:
        """Test basic image not found error."""
        error = ImageNotFoundError("ubuntu:22.04")
        assert "Image 'ubuntu:22.04' not found" in str(error)
        assert error.image_name == "ubuntu:22.04"

    def test_image_not_found_different_image(self) -> None:
        """Test image not found with different image name."""
        error = ImageNotFoundError("nginx:latest")
        assert "Image 'nginx:latest' not found" in str(error)
        assert error.image_name == "nginx:latest"

    def test_image_not_found_error_instance(self) -> None:
        """Test that error can be raised."""
        with pytest.raises(ImageNotFoundError) as exc_info:
            raise ImageNotFoundError("alpine:3.18")
        assert exc_info.value.image_name == "alpine:3.18"


class TestVolumeNotFoundError:
    """Tests for VolumeNotFoundError exception."""

    def test_volume_not_found_basic(self) -> None:
        """Test basic volume not found error."""
        error = VolumeNotFoundError("my-volume")
        assert "Volume 'my-volume' not found" in str(error)
        assert error.volume_name == "my-volume"

    def test_volume_not_found_different_volume(self) -> None:
        """Test volume not found with different volume name."""
        error = VolumeNotFoundError("data-volume")
        assert "Volume 'data-volume' not found" in str(error)
        assert error.volume_name == "data-volume"

    def test_volume_not_found_error_instance(self) -> None:
        """Test that error can be raised."""
        with pytest.raises(VolumeNotFoundError) as exc_info:
            raise VolumeNotFoundError("missing-volume")
        assert exc_info.value.volume_name == "missing-volume"


class TestContainerRuntimeError:
    """Tests for ContainerRuntimeError exception."""

    def test_runtime_error_without_reason(self) -> None:
        """Test runtime error without specific reason."""
        error = ContainerRuntimeError("docker")
        assert "Container runtime 'docker' is not available" in str(error)
        assert error.runtime == "docker"
        assert error.reason is None

    def test_runtime_error_with_reason(self) -> None:
        """Test runtime error with specific reason."""
        error = ContainerRuntimeError("docker", reason="daemon not running")
        assert "Container runtime 'docker' is not available: daemon not running" in str(error)
        assert error.runtime == "docker"
        assert error.reason == "daemon not running"

    def test_runtime_error_podman(self) -> None:
        """Test runtime error with podman."""
        error = ContainerRuntimeError("podman")
        assert "Container runtime 'podman' is not available" in str(error)
        assert error.runtime == "podman"

    def test_runtime_error_instance(self) -> None:
        """Test that error can be raised."""
        with pytest.raises(ContainerRuntimeError) as exc_info:
            raise ContainerRuntimeError("docker", reason="not installed")
        assert exc_info.value.runtime == "docker"
        assert exc_info.value.reason == "not installed"


class TestContainerBuildError:
    """Tests for ContainerBuildError exception."""

    def test_build_error_without_reason(self) -> None:
        """Test build error without specific reason."""
        error = ContainerBuildError("myapp:latest")
        assert "Failed to build image 'myapp:latest'" in str(error)
        assert error.image_tag == "myapp:latest"
        assert error.reason is None

    def test_build_error_with_reason(self) -> None:
        """Test build error with specific reason."""
        error = ContainerBuildError("myapp:v1.0", reason="invalid Dockerfile syntax")
        assert "Failed to build image 'myapp:v1.0': invalid Dockerfile syntax" in str(error)
        assert error.image_tag == "myapp:v1.0"
        assert error.reason == "invalid Dockerfile syntax"

    def test_build_error_different_image(self) -> None:
        """Test build error with different image name."""
        error = ContainerBuildError("webapp:dev")
        assert "Failed to build image 'webapp:dev'" in str(error)
        assert error.image_tag == "webapp:dev"

    def test_build_error_instance(self) -> None:
        """Test that error can be raised."""
        with pytest.raises(ContainerBuildError) as exc_info:
            raise ContainerBuildError("broken:latest", reason="missing base image")
        assert exc_info.value.image_tag == "broken:latest"
        assert exc_info.value.reason == "missing base image"


class TestErrorInheritance:
    """Tests for error class inheritance and hierarchy."""

    def test_all_errors_import(self) -> None:
        """Test that all error classes can be imported."""

        # If we got here, all imports succeeded
        assert True

    def test_error_base_classes(self) -> None:
        """Test that errors inherit from correct foundation classes."""
        from provide.foundation.errors import (
            AlreadyExistsError,
            NotFoundError,
            ResourceError,
            RuntimeError,
            StateError,
        )

        # Check inheritance
        assert issubclass(ContainerNotFoundError, NotFoundError)
        assert issubclass(ContainerNotRunningError, StateError)
        assert issubclass(ContainerAlreadyExistsError, AlreadyExistsError)
        assert issubclass(ImageNotFoundError, NotFoundError)
        assert issubclass(VolumeNotFoundError, NotFoundError)
        assert issubclass(ContainerRuntimeError, RuntimeError)
        assert issubclass(ContainerBuildError, ResourceError)


# 🧰🌍🔚
