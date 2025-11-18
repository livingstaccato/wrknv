#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv Errors
============
Centralized exception definitions using provide.foundation error hierarchy.

This module consolidates all wrknv exceptions with helpful error messages,
suggestions, and proper inheritance from foundation errors."""

from __future__ import annotations
from provide.foundation.errors import (
    AlreadyExistsError,
    FoundationError,
    NotFoundError,
    ResourceError,
    RuntimeError,
    StateError,
)

# Base Errors
# ===========


class WrkenvError(FoundationError):
    """Base exception for all wrknv errors."""

    def __init__(self, message: str, hint: str | None = None, exit_code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.exit_code = exit_code

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message}\n💡 {self.hint}"
        return self.message


# Configuration Errors
# ====================


class ConfigurationError(WrkenvError):
    """Configuration file or settings errors."""

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        line_number: int | None = None,
    ) -> None:
        if line_number:
            message = f"Line {line_number}: {message}"
        super().__init__(message, hint)
        self.line_number = line_number


class ValidationError(ConfigurationError):
    """Configuration validation errors."""

    pass


# Profile Errors
# ==============


class ProfileError(WrkenvError):
    """Profile-related errors."""

    def __init__(
        self,
        profile_name: str,
        message: str | None = None,
        available_profiles: list[str] | None = None,
    ) -> None:
        if not message:
            message = f"Profile '{profile_name}' not found"

        hint = None
        if available_profiles:
            hint = f"Available profiles: {', '.join(available_profiles)}"

        super().__init__(message, hint)
        self.profile_name = profile_name


# Tool Errors
# ===========


class ToolNotFoundError(NotFoundError):
    """Tool or version not found errors."""

    def __init__(
        self, tool: str, version: str | None = None, available_versions: list[str] | None = None
    ) -> None:
        if version:
            message = f"{tool} version {version} not found"
            resource_id = f"{tool}@{version}"
        else:
            message = f"{tool} not found"
            resource_id = tool

        hint = None
        if available_versions:
            # Show up to 5 closest versions
            versions_str = ", ".join(available_versions[:5])
            if len(available_versions) > 5:
                versions_str += "..."
            hint = f"Available versions: {versions_str}. Use 'wrknv {tool} --list' to see all"

        super().__init__(
            message=message,
            resource_type="tool",
            resource_id=resource_id,
            hint=hint,
        )
        self.tool = tool
        self.version = version


# Network Errors
# ==============


class NetworkError(WrkenvError):
    """Network-related errors during downloads."""

    def __init__(self, message: str, url: str | None = None) -> None:
        hint = "Check your internet connection and proxy settings"
        if url:
            message = f"Failed to download from {url}: {message}"
            hint += f"\nTry downloading manually: curl -LO {url}"

        super().__init__(message, hint)
        self.url = url


# Permission Errors
# =================


class WrkenvPermissionError(WrkenvError):
    """File or directory permission errors."""

    def __init__(self, path: str, operation: str = "access") -> None:
        message = f"Permission denied: Cannot {operation} {path}"
        hint = f"Try running with sudo or check file ownership: ls -la {path}"
        super().__init__(message, hint)
        self.path = path


# Dependency Errors
# =================


class DependencyError(WrkenvError):
    """Missing system dependencies."""

    def __init__(self, missing_deps: list[str], required_for: str | None = None) -> None:
        deps_str = ", ".join(missing_deps)
        message = f"Missing required dependencies: {deps_str}"

        if required_for:
            message += f" (required for {required_for})"

        hint = "Install missing dependencies:\n"
        for dep in missing_deps:
            if dep == "git":
                hint += "  • git: https://git-scm.com/downloads\n"
            elif dep == "curl":
                hint += "  • curl: Install via package manager (apt/brew/yum)\n"
            elif dep == "docker":
                hint += "  • docker: https://docs.docker.com/get-docker/\n"
            elif dep == "python3":
                hint += "  • python3: https://www.python.org/downloads/\n"
            else:
                hint += f"  • {dep}: Install via package manager\n"

        super().__init__(message, hint.rstrip())
        self.missing_deps = missing_deps


# Command Errors
# ==============


class CommandNotFoundError(WrkenvError):
    """Command or subcommand not found."""

    def __init__(self, command: str, similar_commands: list[str] | None = None) -> None:
        message = f"Command '{command}' not found"

        hint = None
        if similar_commands:
            hint = f"Did you mean: {', '.join(similar_commands)}?"

        super().__init__(message, hint)
        self.command = command


# Workenv Errors
# ==============


class WorkenvError(WrkenvError):
    """Workenv environment errors."""

    def __init__(self, message: str, workenv_path: str | None = None) -> None:
        hint = None
        if workenv_path:
            hint = f"Try recreating the workenv: rm -rf {workenv_path} && wrknv setup --init"

        super().__init__(message, hint)
        self.workenv_path = workenv_path


# Package Errors
# ==============


class PackageError(ResourceError):
    """Package building or verification errors."""

    def __init__(self, message: str, package_name: str | None = None, hint: str | None = None) -> None:
        super().__init__(
            message=message,
            resource_type="package",
            resource_path=package_name,
            hint=hint,
        )
        self.package_name = package_name


# Container Errors
# ================


class ContainerError(WrkenvError):
    """Base container-related errors."""

    def __init__(self, message: str, container_name: str | None = None, hint: str | None = None) -> None:
        if not hint:
            hint = "Make sure Docker is installed and running"
            if container_name:
                hint += f"\nCheck container status: docker ps -a | grep {container_name}"

        super().__init__(message, hint)
        self.container_name = container_name


class ContainerNotFoundError(NotFoundError):
    """Raised when a container is not found."""

    def __init__(self, container_name: str) -> None:
        super().__init__(
            message=f"Container '{container_name}' not found",
            resource_type="container",
            resource_id=container_name,
            hint="Use 'docker ps -a' to list all containers",
        )
        self.container_name = container_name


class ContainerNotRunningError(StateError):
    """Raised when a container is not running but needs to be."""

    def __init__(self, container_name: str) -> None:
        super().__init__(
            message=f"Container '{container_name}' is not running",
            expected_state="running",
            current_state="stopped",
            hint=f"Start the container with 'docker start {container_name}'",
        )
        self.container_name = container_name


class ContainerAlreadyExistsError(AlreadyExistsError):
    """Raised when trying to create a container that already exists."""

    def __init__(self, container_name: str) -> None:
        super().__init__(
            message=f"Container '{container_name}' already exists",
            resource_type="container",
            resource_id=container_name,
            hint=f"Use 'docker rm {container_name}' to remove existing container",
        )
        self.container_name = container_name


class ImageNotFoundError(NotFoundError):
    """Raised when a container image is not found."""

    def __init__(self, image_name: str) -> None:
        super().__init__(
            message=f"Image '{image_name}' not found",
            resource_type="image",
            resource_id=image_name,
            hint=f"Pull the image with 'docker pull {image_name}'",
        )
        self.image_name = image_name


class VolumeNotFoundError(NotFoundError):
    """Raised when a volume is not found."""

    def __init__(self, volume_name: str) -> None:
        super().__init__(
            message=f"Volume '{volume_name}' not found",
            resource_type="volume",
            resource_id=volume_name,
            hint="Use 'docker volume ls' to list available volumes",
        )
        self.volume_name = volume_name


class ContainerRuntimeError(RuntimeError):
    """Raised when the container runtime is not available."""

    def __init__(self, runtime: str, reason: str | None = None) -> None:
        message = f"Container runtime '{runtime}' is not available"
        if reason:
            message += f": {reason}"

        super().__init__(
            message=message,
            operation="container_runtime_check",
            retry_possible=True,
            hint="Ensure Docker is installed and running",
        )
        self.runtime = runtime
        self.reason = reason


class ContainerBuildError(ResourceError):
    """Raised when container build fails."""

    def __init__(self, image_tag: str, reason: str | None = None) -> None:
        message = f"Failed to build image '{image_tag}'"
        if reason:
            message += f": {reason}"

        super().__init__(
            message=message,
            resource_type="image",
            resource_path=image_tag,
            hint="Check Dockerfile syntax and build context",
        )
        self.image_tag = image_tag
        self.reason = reason


# Task Errors
# ===========


class TaskError(WrkenvError):
    """Base exception for task-related errors."""

    def __init__(self, message: str, task_name: str | None = None, hint: str | None = None) -> None:
        super().__init__(message, hint)
        self.task_name = task_name


class TaskNotFoundError(NotFoundError):
    """Task not found in registry."""

    def __init__(self, task_name: str, available_tasks: list[str] | None = None) -> None:
        message = f"Task '{task_name}' not found"

        hint = None
        if available_tasks:
            # Show up to 5 similar tasks
            tasks_str = ", ".join(available_tasks[:5])
            if len(available_tasks) > 5:
                tasks_str += "..."
            hint = f"Available tasks: {tasks_str}. Use 'wrknv tasks' to see all"

        super().__init__(
            message=message,
            resource_type="task",
            resource_id=task_name,
            hint=hint,
        )
        self.task_name = task_name


class TaskExecutionError(RuntimeError):
    """Task execution failed."""

    def __init__(
        self,
        task_name: str,
        exit_code: int,
        stderr: str | None = None,
        retry_possible: bool = False,
    ) -> None:
        message = f"Task '{task_name}' failed with exit code {exit_code}"

        hint = None
        if stderr:
            # Show first 200 chars of stderr
            stderr_preview = stderr[:200]
            if len(stderr) > 200:
                stderr_preview += "..."
            hint = f"Error output: {stderr_preview}"

        super().__init__(
            message=message,
            operation="task_execution",
            retry_possible=retry_possible,
            hint=hint,
        )
        self.task_name = task_name
        self.exit_code = exit_code
        self.stderr = stderr


class TaskTimeoutError(RuntimeError):
    """Task execution timed out."""

    def __init__(self, task_name: str, timeout: float) -> None:
        message = f"Task '{task_name}' timed out after {timeout} seconds"
        hint = f"Increase timeout in wrknv.toml:\n[tasks.{task_name}]\ntimeout = {timeout * 2}"

        super().__init__(
            message=message,
            operation="task_execution",
            retry_possible=False,
            hint=hint,
        )
        self.task_name = task_name
        self.timeout = timeout


# 🧰🌍🔚
