#
# wrknv/env/managers/base.py
#
"""
Base Tool Manager for wrknv
=============================
Common functionality for all tool managers.
"""

from abc import ABC, abstractmethod
import pathlib
import platform
import shutil
from urllib.parse import urlparse

from provide.foundation import logger
from provide.foundation.console.output import pout
from provide.foundation.process import run as process_run

from wrknv.config import WorkenvConfig, WorkenvConfigError


class ToolManagerError(Exception):
    """Raised when there's an error in tool management."""

    pass


class BaseToolManager(ABC):
    """Base class for all tool managers in wrknv."""

    def __init__(self, config: WorkenvConfig | None = None) -> None:
        self.config = config or WorkenvConfig()
        self.install_path = pathlib.Path(
            self.config.get_setting("install_path", "~/.wrknv/tools")
        ).expanduser()
        self.cache_dir = self.install_path.parent / "cache"

        # Ensure directories exist
        self.install_path.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Name of the tool being managed."""
        pass

    @property
    @abstractmethod
    def executable_name(self) -> str:
        """Name of the executable binary."""
        pass

    @abstractmethod
    def get_available_versions(self) -> list[str]:
        """Get list of available versions from upstream."""
        pass

    @abstractmethod
    def get_download_url(self, version: str) -> str:
        """Get download URL for a specific version."""
        pass

    @abstractmethod
    def get_checksum_url(self, version: str) -> str | None:
        """Get checksum URL for verification (if available)."""
        pass

    def get_platform_info(self) -> dict[str, str]:
        """Get current platform information."""
        from ..operations.platform import get_platform_info

        return get_platform_info()

    def get_installed_version(self) -> str | None:
        """Get currently installed version from config."""
        return self.config.get_tool_version(self.tool_name)

    def set_installed_version(self, version: str) -> None:
        """Set the installed version in config."""
        try:
            self.config.set_tool_version(self.tool_name, version)
        except WorkenvConfigError as e:
            logger.warning(f"Could not save {self.tool_name} version to config: {e}")

    def get_binary_path(self, version: str) -> pathlib.Path:
        """Get path to the installed binary for a version."""
        tool_dir = self.install_path / self.tool_name / version

        # Handle platform-specific executable names
        executable = self.executable_name
        if platform.system() == "Windows":
            executable += ".exe"

        return tool_dir / "bin" / executable

    def get_current_binary_path(self) -> pathlib.Path | None:
        """Get path to the currently active binary."""
        version = self.get_installed_version()
        if version:
            return self.get_binary_path(version)
        return None

    def create_symlink(self, version: str) -> None:
        """Create symlink to make tool available in PATH."""
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.warning(f"Binary not found at {binary_path}, skipping symlink creation")
            return

        # Create symlink in ~/.wrknv/tools/bin/
        bin_dir = self.install_path / "bin"
        bin_dir.mkdir(exist_ok=True)

        symlink_path = bin_dir / self.executable_name

        # Remove existing symlink
        if symlink_path.exists() or symlink_path.is_symlink():
            symlink_path.unlink()

        try:
            symlink_path.symlink_to(binary_path)
            logger.info(f"Created symlink: {symlink_path} -> {binary_path}")
        except OSError as e:
            logger.warning(f"Could not create symlink: {e}")

    def download_file(self, url: str, destination: pathlib.Path, show_progress: bool = True) -> None:
        """Download a file with optional progress display."""
        from ..operations.download import download_file

        download_file(url, destination, show_progress)

    def verify_checksum(
        self, file_path: pathlib.Path, expected_checksum: str, algorithm: str = "sha256"
    ) -> bool:
        """Verify file checksum."""
        if not self.config.get_setting("verify_checksums", True):
            logger.debug("Checksum verification disabled")
            return True

        from ..operations.download import verify_checksum

        return verify_checksum(file_path, expected_checksum, algorithm)

    def extract_archive(self, archive_path: pathlib.Path, extract_to: pathlib.Path) -> None:
        """Extract an archive file."""
        from ..operations.install import extract_archive

        extract_archive(archive_path, extract_to)

    def make_executable(self, file_path: pathlib.Path) -> None:
        """Make a file executable (Unix systems)."""
        from ..operations.install import make_executable

        make_executable(file_path)

    def install_version(self, version: str, dry_run: bool = False) -> None:
        """Install a specific version of the tool."""
        if dry_run:
            logger.info(f"[DRY-RUN] Would install {self.tool_name} {version}")
            return

        logger.info(f"Installing {self.tool_name} {version}")

        # Check if already installed
        binary_path = self.get_binary_path(version)
        if binary_path.exists():
            logger.info(f"{self.tool_name} {version} is already installed at {binary_path}")
            self.set_installed_version(version)

            # Create symlink if configured
            if self.config.get_command_option(f"workenv.{self.tool_name}", "create_symlinks", True):
                self.create_symlink(version)
            return

        try:
            # Download
            download_url = self.get_download_url(version)
            filename = pathlib.Path(urlparse(download_url).path).name
            download_path = self.cache_dir / filename

            if not download_path.exists() or not self.config.get_setting("cache_downloads", True):
                self.download_file(download_url, download_path)
            else:
                logger.info(f"Using cached download: {download_path}")

            # Verify checksum if available and enabled
            checksum_url = self.get_checksum_url(version)
            if checksum_url and self.config.get_setting("verify_checksums", True):
                self._verify_download_checksum(download_path, checksum_url)

            # Extract and install
            self._install_from_archive(download_path, version)

            # Update configuration
            self.set_installed_version(version)

            # Create symlink if configured
            if self.config.get_command_option(f"workenv.{self.tool_name}", "create_symlinks", True):
                self.create_symlink(version)

            logger.info(f"✅ {self.tool_name} {version} installed successfully")

        except Exception as e:
            # Clean up on failure if configured
            if self.config.get_setting("clean_on_failure", True):
                self._cleanup_failed_installation(version)

            raise ToolManagerError(f"Failed to install {self.tool_name} {version}: {e}") from e

    def _verify_download_checksum(self, download_path: pathlib.Path, checksum_url: str) -> None:
        """Download and verify checksum file."""
        checksum_filename = pathlib.Path(urlparse(checksum_url).path).name
        checksum_path = self.cache_dir / checksum_filename

        # Download checksum file
        self.download_file(checksum_url, checksum_path, show_progress=False)

        # Parse checksum file and verify
        with checksum_path.open() as f:
            checksum_content = f.read()

        # Find checksum for our file
        download_filename = download_path.name
        for line in checksum_content.split("\n"):
            if download_filename in line and line.strip():
                parts = line.strip().split()
                if len(parts) >= 2:
                    expected_checksum = parts[0]
                    if not self.verify_checksum(download_path, expected_checksum):
                        raise ToolManagerError(f"Checksum verification failed for {download_path}")
                    return

        logger.warning(f"No checksum found for {download_filename} in {checksum_path}")

    @abstractmethod
    def _install_from_archive(self, archive_path: pathlib.Path, version: str) -> None:
        """Install tool from downloaded archive. Tool-specific implementation."""
        pass

    def _cleanup_failed_installation(self, version: str) -> None:
        """Clean up failed installation."""
        tool_dir = self.install_path / self.tool_name / version
        if tool_dir.exists():
            shutil.rmtree(tool_dir)
            logger.info(f"Cleaned up failed installation: {tool_dir}")

    def install_latest(self, dry_run: bool = False) -> None:
        """Install the latest stable version."""
        versions = self.get_available_versions()
        if not versions:
            raise ToolManagerError(f"No versions available for {self.tool_name}")

        latest = versions[0]  # Assume first is latest
        logger.info(f"Latest {self.tool_name} version: {latest}")
        self.install_version(latest, dry_run=dry_run)

    def list_versions(self, limit: int = 20) -> None:
        """List available versions."""
        logger.info(f"Available {self.tool_name} versions:")

        try:
            versions = self.get_available_versions()
            current = self.get_installed_version()

            for _i, version in enumerate(versions[:limit]):
                marker = " (current)" if version == current else ""
                status = "✅" if version == current else "  "
                pout(f"{status} {version}{marker}")

            if len(versions) > limit:
                pout(f"... and {len(versions) - limit} more versions available")

        except Exception as e:
            raise ToolManagerError(f"Failed to fetch versions for {self.tool_name}: {e}") from e

    def show_current(self) -> None:
        """Show current installed version."""
        version = self.get_installed_version()
        if version:
            binary_path = self.get_current_binary_path()
            if binary_path and binary_path.exists():
                pout(f"{self.tool_name}: {version} ✅")
            else:
                pout(f"{self.tool_name}: {version} (binary missing)")
        else:
            pout(f"{self.tool_name}: not installed")

    def get_installed_versions(self) -> list[str]:
        """Get all installed versions of this tool."""
        versions = []

        # Check install directory for all versions
        tool_install_dir = self.install_path / self.tool_name
        if tool_install_dir.exists():
            for item in tool_install_dir.iterdir():
                if item.is_dir() and self._is_version_dir(item.name):
                    versions.append(item.name)

        return sorted(versions, reverse=True)

    def _is_version_dir(self, name: str) -> bool:
        """Check if a directory name looks like a version."""
        # Basic semantic version check
        import re

        return bool(re.match(r"^\d+\.\d+\.\d+", name))

    def remove_version(self, version: str) -> None:
        """Remove a specific version of the tool."""
        version_dir = self.install_path / self.tool_name / version
        binary_path = self.get_binary_path(version)

        # Remove the version directory
        if version_dir.exists():
            import shutil

            shutil.rmtree(version_dir)
            logger.info(f"Removed {self.tool_name} {version} directory")

        # Remove the binary if it exists elsewhere
        if binary_path.exists() and binary_path.parent != version_dir:
            binary_path.unlink()
            logger.info(f"Removed {self.tool_name} {version} binary")

        # Update config if this was the current version
        if self.get_installed_version() == version:
            # Clear the version in config
            try:
                self.config.set_tool_version(self.tool_name, "")
            except Exception:
                # If set_tool_version doesn't exist, just log
                logger.debug(f"Could not clear {self.tool_name} version in config")

    def verify_installation(self, version: str) -> bool:
        """Verify that installation works correctly."""
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            return False

        try:
            # Try to run the tool with version flag
            result = process_run(
                [str(binary_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10.0,
                check=False,
            )

            return result.returncode == 0

        except Exception as e:
            logger.debug(f"Verification failed for {self.tool_name} {version}: {e}")
            return False


# 🍲🥄📄🪄
