#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv Platform Detection
===================================
Platform and architecture information using provide.foundation."""

from __future__ import annotations

from provide.foundation.platform import (
    get_arch_name,
    get_os_name as foundation_get_os_name,
    get_platform_string,
    get_system_info,
)


def get_platform_info() -> dict[str, str]:
    """Get platform information for tool downloads.

    Returns:
        Dictionary with platform details for tool compatibility.
    """
    # Get comprehensive system info from foundation
    sys_info = get_system_info()

    return {
        "os": sys_info.os_name,
        "arch": sys_info.arch,
        "platform": sys_info.platform,
        "python_platform": sys_info.platform,
        "machine": sys_info.arch,
        "system": sys_info.os_name,
    }


def get_architecture() -> str:
    """Get normalized architecture name for tool downloads.

    Returns:
        Architecture string suitable for tool downloads (amd64, arm64, etc).
    """
    return get_arch_name()


def get_workenv_platform() -> str:
    """Get platform string for workenv directory naming.

    Returns:
        Platform string in format: {os}_{arch}
    """
    return get_platform_string()


def is_arm_mac() -> bool:
    """Check if running on Apple Silicon Mac.

    Returns:
        True if running on ARM-based Mac (M1/M2/M3).
    """
    from provide.foundation.platform import is_arm, is_macos

    return is_macos() and is_arm()


def is_windows() -> bool:
    """Check if running on Windows.

    Returns:
        True if running on Windows.
    """
    from provide.foundation.platform import is_windows as foundation_is_windows

    return foundation_is_windows()


# Re-export for backward compatibility (remove these later)
def get_os_name() -> str:
    """Get normalized OS name for tool downloads.

    DEPRECATED: Use provide.foundation.platform.get_os_name directly.
    """
    return foundation_get_os_name()


def format_platform_string(os_name: str, arch: str) -> str:
    """Format platform string for tool downloads.

    Args:
        os_name: Operating system name
        arch: Architecture name

    Returns:
        Formatted platform string
    """
    return f"{os_name}_{arch}"


def parse_platform_string(platform_str: str) -> tuple[str, str]:
    """Parse platform string into OS and architecture.

    Args:
        platform_str: Platform string in format os_arch

    Returns:
        Tuple of (os_name, arch)
    """
    parts = platform_str.split("_", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return platform_str, ""


def get_archive_extension() -> str:
    """Get appropriate archive extension for current platform.

    Returns:
        Archive extension (.zip for Windows, .tar.gz otherwise)
    """
    return ".zip" if is_windows() else ".tar.gz"


def get_executable_extension() -> str:
    """Get executable file extension for current platform.

    Returns:
        Executable extension (.exe for Windows, empty string otherwise)
    """
    return ".exe" if is_windows() else ""


def is_supported_platform() -> bool:
    """Check if current platform is supported.

    Returns:
        True if platform is supported
    """
    supported_os = ["darwin", "linux", "windows"]
    supported_arch = ["amd64", "arm64", "x86_64", "aarch64"]

    os_name = get_os_name()
    arch = get_architecture()

    return os_name in supported_os and arch in supported_arch


def get_platform_mapping(tool_name: str) -> dict[str, str]:
    """Get platform mapping for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Dictionary mapping standard names to tool-specific names
    """
    mappings = get_download_platform_mappings()
    return mappings.get(tool_name, {})


def get_download_platform_mappings() -> dict[str, dict[str, str]]:
    """Get platform naming mappings for various tools.

    Returns:
        Dictionary of tool-specific platform mappings
    """
    return {
        "terraform": {
            "darwin_arm64": "darwin_arm64",
            "darwin_amd64": "darwin_amd64",
            "linux_arm64": "linux_arm64",
            "linux_amd64": "linux_amd64",
            "windows_amd64": "windows_amd64",
        },
        "tofu": {
            "darwin_arm64": "darwin_arm64",
            "darwin_amd64": "darwin_amd64",
            "linux_arm64": "linux_arm64",
            "linux_amd64": "linux_amd64",
            "windows_amd64": "windows_amd64",
        },
        "go": {
            "darwin_arm64": "darwin-arm64",
            "darwin_amd64": "darwin-amd64",
            "linux_arm64": "linux-arm64",
            "linux_amd64": "linux-amd64",
            "windows_amd64": "windows-amd64",
        },
    }


# 🧰🌍🔚
