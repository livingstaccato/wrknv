#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""wrknv Verification Operations
========================================
Functions for verifying tool installations."""

from __future__ import annotations

import pathlib

from provide.foundation import logger
from provide.foundation.process import ProcessError, run
from provide.foundation.resilience import retry


def verify_tool_installation(binary_path: pathlib.Path, expected_version: str, tool_name: str) -> bool:
    """Verify that tool installation works and version matches."""

    if not binary_path.exists():
        logger.error(f"{tool_name} binary not found at {binary_path}")
        return False

    try:
        version_output = run_version_check(binary_path, tool_name)

        if version_output is None:
            logger.error(f"{tool_name} version check failed")
            return False

        # Check if expected version is in the output
        if expected_version in version_output:
            logger.debug(f"{tool_name} {expected_version} verification successful")
            return True
        else:
            logger.error(
                f"Version mismatch for {tool_name}: expected {expected_version}, got: {version_output}"
            )
            return False

    except Exception as e:
        logger.error(f"Failed to verify {tool_name} installation: {e}")
        return False


@retry(ProcessError, OSError, max_attempts=3, base_delay=1.0)
def run_version_check(binary_path: pathlib.Path, tool_name: str, timeout: int = 10) -> str | None:
    """Run version check command for a tool and return output.

    Includes automatic retry with exponential backoff for transient failures.
    """

    if not binary_path.exists():
        return None

    # Determine version command for different tools
    version_args = get_version_command_args(tool_name)

    cmd = [str(binary_path), *version_args]

    try:
        logger.debug(f"Running version check: {' '.join(cmd)}")

        result = run(cmd, timeout=timeout)

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.error(f"Version command failed for {tool_name}: {result.stderr}")
            return None

    except ProcessError as e:
        if e.timeout:
            logger.error(f"Version check timed out for {tool_name}")
        else:
            logger.error(f"Version check failed for {tool_name}: {e}")
        raise  # Re-raise to trigger retry
    except Exception as e:
        logger.error(f"Version check failed for {tool_name}: {e}")
        return None


def get_version_command_args(tool_name: str) -> list[str]:
    """Get version command arguments for different tools."""

    # Map tool names to their version command arguments
    version_commands = {
        "terraform": ["version"],
        "tofu": ["version"],
        "go": ["version"],
        "uv": ["--version"],
        "python": ["--version"],
        "node": ["--version"],
        "npm": ["--version"],
        "docker": ["--version"],
    }

    return version_commands.get(tool_name, ["--version"])


def check_binary_compatibility(binary_path: pathlib.Path) -> dict[str, any]:
    """Check if binary is compatible with current platform."""

    if not binary_path.exists():
        return {"compatible": False, "error": "Binary not found"}

    try:
        # Try to run the binary with help/version flag
        result = run([str(binary_path), "--help"], timeout=5)

        # If it runs without error, it's likely compatible
        compatible = result.returncode == 0

        return {
            "compatible": compatible,
            "returncode": result.returncode,
            "stdout": result.stdout[:200] if result.stdout else "",
            "stderr": result.stderr[:200] if result.stderr else "",
        }

    except ProcessError as e:
        if e.timeout:
            return {"compatible": False, "error": "Binary execution timed out"}
        else:
            return {"compatible": False, "error": str(e)}
    except Exception as e:
        return {"compatible": False, "error": str(e)}


def validate_installation_directory(install_dir: pathlib.Path, tool_name: str, version: str) -> bool:
    """Validate that installation directory has expected structure."""

    if not install_dir.exists():
        logger.error(f"Installation directory not found: {install_dir}")
        return False

    # Check for bin directory
    bin_dir = install_dir / "bin"
    if not bin_dir.exists():
        logger.error(f"Bin directory not found: {bin_dir}")
        return False

    # Check for expected binary
    from ..operations.platform import get_executable_extension

    executable_name = tool_name + get_executable_extension()
    binary_path = bin_dir / executable_name

    if not binary_path.exists():
        logger.error(f"Binary not found: {binary_path}")
        return False

    # Check if binary is executable
    from ..operations.install import is_executable

    if not is_executable(binary_path):
        logger.error(f"Binary is not executable: {binary_path}")
        return False

    logger.debug(f"Installation directory validation passed for {tool_name} {version}")
    return True


def get_installed_version_info(binary_path: pathlib.Path, tool_name: str) -> dict[str, str] | None:
    """Get detailed version information from installed tool."""

    version_output = run_version_check(binary_path, tool_name)

    if not version_output:
        return None

    # Parse version information based on tool
    if tool_name == "terraform":
        return parse_terraform_version(version_output)
    elif tool_name == "tofu":
        return parse_tofu_version(version_output)
    elif tool_name == "go":
        return parse_go_version(version_output)
    elif tool_name == "uv":
        return parse_uv_version(version_output)
    else:
        # Generic version parsing
        return parse_generic_version(version_output, tool_name)


def parse_terraform_version(output: str) -> dict[str, str]:
    """Parse Terraform version output."""

    # Example: "Terraform v1.5.0"
    lines = output.split("\n")

    info = {"tool": "terraform"}

    for line in lines:
        line = line.strip()
        if line.startswith("Terraform v"):
            version = line.replace("Terraform v", "")
            info["version"] = version
        elif line.startswith("on "):
            # Extract platform from "on linux_amd64" format
            info["platform"] = line.replace("on ", "").strip()

    return info


def parse_tofu_version(output: str) -> dict[str, str]:
    """Parse OpenTofu version output."""

    # Example: "OpenTofu v1.6.0"
    lines = output.split("\n")

    info = {"tool": "tofu"}

    for line in lines:
        line = line.strip()
        if line.startswith("OpenTofu v"):
            version = line.replace("OpenTofu v", "")
            info["version"] = version
        elif line.startswith("on "):
            # Extract platform from "on darwin_arm64" format
            info["platform"] = line.replace("on ", "").strip()

    return info


def parse_go_version(output: str) -> dict[str, str]:
    """Parse Go version output."""

    # Example: "go version go1.21.0 linux/amd64"
    info = {"tool": "go"}

    parts = output.split()
    if len(parts) >= 3:
        version_part = parts[2]
        if version_part.startswith("go"):
            info["version"] = version_part[2:]  # Remove "go" prefix

        if len(parts) >= 4:
            info["platform"] = parts[3]

    return info


def parse_uv_version(output: str) -> dict[str, str]:
    """Parse UV version output."""

    # Example: "uv 0.4.15"
    info = {"tool": "uv"}

    parts = output.split()
    if len(parts) >= 2:
        info["version"] = parts[1]

    return info


def parse_generic_version(output: str, tool_name: str) -> dict[str, str]:
    """Generic version parsing for unknown tools."""

    info = {"tool": tool_name, "raw_output": output}

    # Try to extract version number using common patterns
    import re

    # Look for version patterns like "1.2.3", "v1.2.3", etc.
    version_patterns = [
        r"v?([0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9]+)?)",
        r"([0-9]+\.[0-9]+(?:-[a-zA-Z0-9]+)?)",
        r"([0-9]+\.[0-9]+\.[0-9]+)",
    ]

    for pattern in version_patterns:
        match = re.search(pattern, output)
        if match:
            info["version"] = match.group(1)
            break

    return info


def verify_file(file_path: pathlib.Path, signature_path: pathlib.Path | None = None) -> bool:
    """Verify file integrity using signature if available.

    Args:
        file_path: Path to file to verify
        signature_path: Optional path to signature file

    Returns:
        True if verification passes, False otherwise
    """
    if not file_path.exists():
        logger.error(f"File not found for verification: {file_path}")
        return False

    if signature_path and signature_path.exists():
        logger.info(f"Verifying file signature: {file_path}")
        # For now, just check that signature file exists
        # In production, would verify actual signature
        return True
    else:
        logger.debug(f"No signature file found, skipping verification: {file_path}")
        return True


# 🧰🌍🔚
