#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv Custom Exceptions
========================
Centralized exception definitions with helpful error messages and suggestions.

Requires Python 3.11+ for native type hint support with pipe operators."""

from __future__ import annotations

from provide.foundation.errors import FoundationError


class WrkenvError(FoundationError):
    """Base exception for all wrknv errors."""

    def __init__(self, message: str, suggestion: str | None = None, exit_code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion
        self.exit_code = exit_code

    def __str__(self) -> str:
        if self.suggestion:
            return f"{self.message}\n💡 {self.suggestion}"
        return self.message


class ConfigurationError(WrkenvError):
    """Configuration file or settings errors."""

    def __init__(
        self,
        message: str,
        suggestion: str | None = None,
        line_number: int | None = None,
    ) -> None:
        if line_number:
            message = f"Line {line_number}: {message}"
        super().__init__(message, suggestion)
        self.line_number = line_number


class ValidationError(ConfigurationError):
    """Configuration validation errors."""


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

        suggestion = None
        if available_profiles:
            suggestion = f"Available profiles: {', '.join(available_profiles)}"

        super().__init__(message, suggestion)
        self.profile_name = profile_name


class ToolNotFoundError(WrkenvError):
    """Tool or version not found errors."""

    def __init__(
        self, tool: str, version: str | None = None, available_versions: list[str] | None = None
    ) -> None:
        message = f"{tool} version {version} not found" if version else f"{tool} not found"

        suggestion = None
        if available_versions:
            # Show up to 5 closest versions
            versions_str = ", ".join(available_versions[:5])
            if len(available_versions) > 5:
                versions_str += "..."
            suggestion = f"Available versions: {versions_str}. Use 'wrknv {tool} --list' to see all"

        super().__init__(message, suggestion)
        self.tool = tool
        self.version = version


class NetworkError(WrkenvError):
    """Network-related errors during downloads."""

    def __init__(self, message: str, url: str | None = None) -> None:
        suggestion = "Check your internet connection and proxy settings"
        if url:
            message = f"Failed to download from {url}: {message}"
            suggestion += f"\nTry downloading manually: curl -LO {url}"

        super().__init__(message, suggestion)
        self.url = url


class PermissionError(WrkenvError):
    """File or directory permission errors."""

    def __init__(self, path: str, operation: str = "access") -> None:
        message = f"Permission denied: Cannot {operation} {path}"
        suggestion = f"Try running with sudo or check file ownership: ls -la {path}"
        super().__init__(message, suggestion)
        self.path = path


class DependencyError(WrkenvError):
    """Missing system dependencies."""

    def __init__(self, missing_deps: list[str], required_for: str | None = None) -> None:
        deps_str = ", ".join(missing_deps)
        message = f"Missing required dependencies: {deps_str}"

        if required_for:
            message += f" (required for {required_for})"

        suggestion = "Install missing dependencies:\n"
        for dep in missing_deps:
            if dep == "git":
                suggestion += "  • git: https://git-scm.com/downloads\n"
            elif dep == "curl":
                suggestion += "  • curl: Install via package manager (apt/brew/yum)\n"
            elif dep == "docker":
                suggestion += "  • docker: https://docs.docker.com/get-docker/\n"
            elif dep == "python3":
                suggestion += "  • python3: https://www.python.org/downloads/\n"
            else:
                suggestion += f"  • {dep}: Install via package manager\n"

        super().__init__(message, suggestion.rstrip())
        self.missing_deps = missing_deps


class CommandNotFoundError(WrkenvError):
    """Command or subcommand not found."""

    def __init__(self, command: str, similar_commands: list[str] | None = None) -> None:
        message = f"Command '{command}' not found"

        suggestion = None
        if similar_commands:
            suggestion = f"Did you mean: {', '.join(similar_commands)}?"

        super().__init__(message, suggestion)
        self.command = command


class WorkenvError(WrkenvError):
    """Workenv environment errors."""

    def __init__(self, message: str, workenv_path: str | None = None) -> None:
        suggestion = None
        if workenv_path:
            suggestion = f"Try recreating the workenv: rm -rf {workenv_path} && wrknv setup --init"

        super().__init__(message, suggestion)
        self.workenv_path = workenv_path


class ContainerError(WrkenvError):
    """Container-related errors."""

    def __init__(self, message: str, container_name: str | None = None) -> None:
        suggestion = "Make sure Docker is installed and running"
        if container_name:
            suggestion += f"\nCheck container status: docker ps -a | grep {container_name}"

        super().__init__(message, suggestion)
        self.container_name = container_name


class PackageError(WrkenvError):
    """Package building or verification errors."""


# 🧰🌍🔚
