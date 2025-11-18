#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for wrknv.wenv.exceptions
================================
Comprehensive tests for all custom exception classes."""

from __future__ import annotations

from wrknv.wenv.exceptions import (
    CommandNotFoundError,
    ConfigurationError,
    ContainerError,
    DependencyError,
    NetworkError,
    PackageError,
    PermissionError,
    ProfileError,
    ToolNotFoundError,
    ValidationError,
    WorkenvError,
    WrkenvError,
)


class TestWrkenvError:
    """Tests for base WrkenvError exception."""

    def test_basic_error(self) -> None:
        """Test basic error without suggestion."""
        error = WrkenvError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.suggestion is None
        assert error.exit_code == 1

    def test_error_with_suggestion(self) -> None:
        """Test error with suggestion."""
        error = WrkenvError("Something went wrong", suggestion="Try this instead")
        assert "Something went wrong" in str(error)
        assert "💡 Try this instead" in str(error)
        assert error.suggestion == "Try this instead"

    def test_custom_exit_code(self) -> None:
        """Test error with custom exit code."""
        error = WrkenvError("Fatal error", exit_code=2)
        assert error.exit_code == 2


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_basic_config_error(self) -> None:
        """Test basic configuration error."""
        error = ConfigurationError("Invalid config")
        assert "Invalid config" in str(error)
        assert error.line_number is None

    def test_config_error_with_line_number(self) -> None:
        """Test configuration error with line number."""
        error = ConfigurationError("Invalid syntax", line_number=42)
        assert "Line 42: Invalid syntax" in str(error)
        assert error.line_number == 42

    def test_config_error_with_suggestion(self) -> None:
        """Test configuration error with suggestion."""
        error = ConfigurationError(
            "Missing required field",
            suggestion="Add 'name' field to config",
            line_number=10,
        )
        assert "Line 10: Missing required field" in str(error)
        assert "💡 Add 'name' field to config" in str(error)


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error(self) -> None:
        """Test validation error is a subclass of ConfigurationError."""
        error = ValidationError("Invalid value")
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, WrkenvError)
        assert "Invalid value" in str(error)


class TestProfileError:
    """Tests for ProfileError exception."""

    def test_profile_not_found_default_message(self) -> None:
        """Test profile error with default message."""
        error = ProfileError("prod")
        assert "Profile 'prod' not found" in str(error)
        assert error.profile_name == "prod"

    def test_profile_error_with_custom_message(self) -> None:
        """Test profile error with custom message."""
        error = ProfileError("prod", message="Cannot load profile 'prod'")
        assert "Cannot load profile 'prod'" in str(error)

    def test_profile_error_with_available_profiles(self) -> None:
        """Test profile error showing available profiles."""
        error = ProfileError("prod", available_profiles=["dev", "staging"])
        assert "Profile 'prod' not found" in str(error)
        assert "💡 Available profiles: dev, staging" in str(error)


class TestToolNotFoundError:
    """Tests for ToolNotFoundError exception."""

    def test_tool_not_found_without_version(self) -> None:
        """Test tool not found without version."""
        error = ToolNotFoundError("terraform")
        assert "terraform not found" in str(error)
        assert error.tool == "terraform"
        assert error.version is None

    def test_tool_not_found_with_version(self) -> None:
        """Test tool not found with specific version."""
        error = ToolNotFoundError("terraform", version="1.5.0")
        assert "terraform version 1.5.0 not found" in str(error)
        assert error.tool == "terraform"
        assert error.version == "1.5.0"

    def test_tool_not_found_with_few_available_versions(self) -> None:
        """Test tool not found with available versions (less than 5)."""
        error = ToolNotFoundError(
            "terraform",
            version="1.5.0",
            available_versions=["1.6.0", "1.7.0"],
        )
        assert "terraform version 1.5.0 not found" in str(error)
        assert "💡 Available versions: 1.6.0, 1.7.0" in str(error)
        assert "..." not in str(error)

    def test_tool_not_found_with_many_available_versions(self) -> None:
        """Test tool not found with many available versions (more than 5)."""
        versions = ["1.6.0", "1.7.0", "1.8.0", "1.9.0", "2.0.0", "2.1.0", "2.2.0"]
        error = ToolNotFoundError(
            "terraform",
            version="1.5.0",
            available_versions=versions,
        )
        assert "terraform version 1.5.0 not found" in str(error)
        assert "💡 Available versions: 1.6.0, 1.7.0, 1.8.0, 1.9.0, 2.0.0..." in str(error)
        assert "wrknv terraform --list" in str(error)


class TestNetworkError:
    """Tests for NetworkError exception."""

    def test_network_error_without_url(self) -> None:
        """Test network error without URL."""
        error = NetworkError("Connection timeout")
        assert "Connection timeout" in str(error)
        assert "Check your internet connection" in str(error)
        assert error.url is None

    def test_network_error_with_url(self) -> None:
        """Test network error with URL."""
        url = "https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip"
        error = NetworkError("404 Not Found", url=url)
        assert f"Failed to download from {url}" in str(error)
        assert "404 Not Found" in str(error)
        assert f"curl -LO {url}" in str(error)


class TestPermissionError:
    """Tests for PermissionError exception."""

    def test_permission_error_default_operation(self) -> None:
        """Test permission error with default operation."""
        error = PermissionError("/usr/local/bin/terraform")
        assert "Permission denied: Cannot access /usr/local/bin/terraform" in str(error)
        assert "ls -la /usr/local/bin/terraform" in str(error)
        assert error.path == "/usr/local/bin/terraform"

    def test_permission_error_custom_operation(self) -> None:
        """Test permission error with custom operation."""
        error = PermissionError("/var/log/wrknv.log", operation="write to")
        assert "Permission denied: Cannot write to /var/log/wrknv.log" in str(error)
        assert "ls -la /var/log/wrknv.log" in str(error)


class TestDependencyError:
    """Tests for DependencyError exception."""

    def test_single_dependency_missing(self) -> None:
        """Test error with single missing dependency."""
        error = DependencyError(["git"])
        assert "Missing required dependencies: git" in str(error)
        assert "git: https://git-scm.com/downloads" in str(error)
        assert error.missing_deps == ["git"]

    def test_multiple_dependencies_missing(self) -> None:
        """Test error with multiple missing dependencies."""
        error = DependencyError(["git", "curl", "docker"])
        assert "Missing required dependencies: git, curl, docker" in str(error)
        assert "git: https://git-scm.com/downloads" in str(error)
        assert "curl: Install via package manager" in str(error)
        assert "docker: https://docs.docker.com/get-docker/" in str(error)

    def test_dependency_error_with_required_for(self) -> None:
        """Test dependency error with 'required for' context."""
        error = DependencyError(["docker"], required_for="container operations")
        assert "Missing required dependencies: docker" in str(error)
        assert "(required for container operations)" in str(error)

    def test_unknown_dependency(self) -> None:
        """Test error with unknown dependency shows generic message."""
        error = DependencyError(["unknown-tool"])
        assert "Missing required dependencies: unknown-tool" in str(error)
        assert "unknown-tool: Install via package manager" in str(error)

    def test_python3_dependency(self) -> None:
        """Test error with python3 dependency."""
        error = DependencyError(["python3"])
        assert "python3: https://www.python.org/downloads/" in str(error)


class TestCommandNotFoundError:
    """Tests for CommandNotFoundError exception."""

    def test_command_not_found_without_suggestions(self) -> None:
        """Test command not found without similar commands."""
        error = CommandNotFoundError("unknowncommand")
        assert "Command 'unknowncommand' not found" in str(error)
        assert error.command == "unknowncommand"
        assert "Did you mean" not in str(error)

    def test_command_not_found_with_suggestions(self) -> None:
        """Test command not found with similar commands."""
        error = CommandNotFoundError("sttaus", similar_commands=["status", "state"])
        assert "Command 'sttaus' not found" in str(error)
        assert "💡 Did you mean: status, state?" in str(error)


class TestWorkenvError:
    """Tests for WorkenvError exception."""

    def test_workenv_error_without_path(self) -> None:
        """Test workenv error without path."""
        error = WorkenvError("Workenv is corrupted")
        assert "Workenv is corrupted" in str(error)
        assert error.workenv_path is None

    def test_workenv_error_with_path(self) -> None:
        """Test workenv error with workenv path."""
        path = "./workenv/wrknv_darwin_arm64"
        error = WorkenvError("Workenv is corrupted", workenv_path=path)
        assert "Workenv is corrupted" in str(error)
        assert f"rm -rf {path}" in str(error)
        assert "wrknv setup --init" in str(error)
        assert error.workenv_path == path


class TestContainerError:
    """Tests for ContainerError exception."""

    def test_container_error_without_name(self) -> None:
        """Test container error without container name."""
        error = ContainerError("Docker daemon not running")
        assert "Docker daemon not running" in str(error)
        assert "Make sure Docker is installed and running" in str(error)
        assert error.container_name is None

    def test_container_error_with_name(self) -> None:
        """Test container error with container name."""
        error = ContainerError("Container failed to start", container_name="wrknv-dev")
        assert "Container failed to start" in str(error)
        assert "Make sure Docker is installed and running" in str(error)
        assert "docker ps -a | grep wrknv-dev" in str(error)
        assert error.container_name == "wrknv-dev"


class TestPackageError:
    """Tests for PackageError exception."""

    def test_package_error(self) -> None:
        """Test basic package error."""
        error = PackageError("Failed to build package")
        assert isinstance(error, WrkenvError)
        assert "Failed to build package" in str(error)


# 🧰🌍🔚
