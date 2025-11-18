#
# wrknv/package/manager.py
#
"""
Package Manager
===============
Manages package build environment and tools.
"""

from pathlib import Path

from wrknv.config import WorkenvConfig


class PackageManager:
    """Manages package build environment and required tools."""

    def __init__(self, config: WorkenvConfig) -> None:
        """Initialize package manager with config."""
        self.config = config

    def check_required_tools(self) -> dict[str, str | None]:
        """Check for required build tools.

        Returns:
            Dictionary mapping tool names to their paths (or None if not found).
        """
        import shutil

        tools = {
            "python": shutil.which("python"),
            "uv": shutil.which("uv"),
        }
        return tools

    def setup_build_environment(self) -> dict[str, str]:
        """Set up environment variables for build.

        Returns:
            Dictionary of environment variables.
        """
        import os

        env = os.environ.copy()
        # Add any wrknv-specific environment variables here
        return env

    def get_package_cache_dir(self) -> Path:
        """Get the package cache directory.

        Returns:
            Path to the cache directory.
        """
        cache_dir = Path.home() / ".wrknv" / "cache" / "packages"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def get_package_output_dir(self) -> Path:
        """Get the package output directory.

        Returns:
            Path to the output directory.
        """
        output_dir = Path.home() / ".wrknv" / "packages"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir


# 🧰🌍🖥️🪄
