#
# wrknv/workenv/managers/tf_base.py
#
"""
Tf Manager Base
===============
Base class for Tf (IBM Terraform/OpenTofu) managers that use ~/.terraform.versions
directory structure. This implementation is compatible with tfswitch and
designed for managing Tf tool versions.
"""

from abc import abstractmethod
from datetime import datetime
import hashlib
import json
import os
import pathlib
import shutil
import sys

from provide.foundation import logger
import semver

from .base import BaseToolManager, ToolManagerError


class TfVersionsManager(BaseToolManager):
    """
    Base class for managers using ~/.terraform.versions directory.

    This directory structure is compatible with tfswitch, allowing users to
    use either tool interchangeably while providing enhanced metadata tracking
    for advanced features. Supports both IBM Terraform (formerly HashiCorp) and OpenTofu.
    """

    def __init__(self, config=None) -> None:  # noqa: ANN001
        super().__init__(config)
        # Override install path to use tf versions directory
        self.install_path = pathlib.Path("~/.terraform.versions").expanduser()
        self.install_path.mkdir(parents=True, exist_ok=True)

        # Get venv bin directory for copying active binaries
        self.venv_bin_dir = self._get_venv_bin_dir()

        # Metadata file for enriched information
        self.metadata_file = self.install_path / "metadata.json"
        self._load_metadata()

    @property
    @abstractmethod
    def tool_prefix(self) -> str:
        """Prefix for version files (e.g., 'terraform' or 'opentofu')."""
        pass

    def _load_metadata(self) -> None:
        """Load metadata from JSON file."""
        if self.metadata_file.exists():
            try:
                with self.metadata_file.open() as f:
                    self.metadata = json.load(f)

                # Migrate old format if needed
                self._migrate_metadata_format()
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _migrate_metadata_format(self) -> None:
        """Migrate old metadata format to new workenv structure."""
        needs_save = False

        # Migrate old active_* keys to workenv structure
        for old_key in ["active_tofu", "active_terraform"]:
            if old_key in self.metadata:
                tool = old_key.replace("active_", "")
                version = self.metadata.pop(old_key)

                # Ensure workenv structure exists
                if "workenv" not in self.metadata:
                    self.metadata["workenv"] = {}
                if "default" not in self.metadata["workenv"]:
                    self.metadata["workenv"]["default"] = {}

                # Set version in new structure
                # Use 'opentofu_version' for tofu
                version_key = "opentofu_version" if tool == "tofu" else f"{tool}_version"

                self.metadata["workenv"]["default"][version_key] = version
                needs_save = True

        if needs_save:
            self._save_metadata()

    def _save_metadata(self) -> None:
        """Save metadata to JSON file."""
        try:
            with self.metadata_file.open("w") as f:
                json.dump(self.metadata, f, indent=2, sort_keys=True, default=str)
        except Exception as e:
            logger.warning(f"Failed to save metadata: {e}")

    def _update_recent_file(self) -> None:
        """Update the RECENT file with current installed versions."""
        recent_file = self.install_path / "RECENT"
        recent_data = {}

        # Read existing RECENT file if it exists
        if recent_file.exists():
            try:
                with recent_file.open() as f:
                    recent_data = json.load(f)
            except Exception:
                recent_data = {}

        # Get all installed versions for this tool
        tool_key = self.tool_name if self.tool_name != "tofu" else "opentofu"
        installed_versions = self.get_installed_versions()

        if installed_versions:
            # Keep only the 5 most recent versions
            recent_data[tool_key] = installed_versions[:5]
        elif tool_key in recent_data:
            # Remove tool if no versions installed
            del recent_data[tool_key]

        # Write updated RECENT file
        try:
            with recent_file.open("w") as f:
                json.dump(recent_data, f)
        except Exception as e:
            logger.warning(f"Failed to update RECENT file: {e}")

    def _update_recent_file_with_active(self, version: str) -> None:
        """Update RECENT file to put active version first."""
        recent_file = self.install_path / "RECENT"
        recent_data = {}

        # Read existing RECENT file if it exists
        if recent_file.exists():
            try:
                with recent_file.open() as f:
                    recent_data = json.load(f)
            except Exception:
                recent_data = {}

        # Get tool key
        tool_key = self.tool_name if self.tool_name != "tofu" else "opentofu"

        # Get current list of versions
        current_versions = recent_data.get(tool_key, [])

        # Remove version if it exists
        if version in current_versions:
            current_versions.remove(version)

        # Add version at the beginning
        current_versions.insert(0, version)

        # Keep only the 5 most recent
        recent_data[tool_key] = current_versions[:5]

        # Write updated RECENT file
        try:
            with recent_file.open("w") as f:
                json.dump(recent_data, f)
        except Exception as e:
            logger.warning(f"Failed to update RECENT file with active version: {e}")

    def get_binary_path(self, version: str) -> pathlib.Path:
        """Get path to the installed binary for a version."""
        # In tf versions format, binaries are stored as prefix_version
        binary_name = f"{self.tool_prefix}_{version}"
        return self.install_path / binary_name

    def get_installed_versions(self) -> list[str]:
        """Get all installed versions of this tool."""
        versions = []

        prefix = f"{self.tool_prefix}_"
        for item in self.install_path.iterdir():
            if item.is_file() and item.name.startswith(prefix):
                # Extract version from filename
                version = item.name[len(prefix) :]
                if self._is_version_dir(version):
                    versions.append(version)

        return sorted(versions, key=self._version_sort_key, reverse=True)

    def _version_sort_key(self, version: str) -> tuple[int, ...]:
        """Generate sort key for semantic versioning using semver module."""
        try:
            # Try to parse as a semantic version
            return semver.VersionInfo.parse(version)
        except ValueError:
            # If it fails, try to make it semver-compliant
            # Handle versions like "1.0" by adding ".0"
            parts = version.split(".")
            while len(parts) < 3:
                parts.append("0")
            try:
                normalized = ".".join(parts[:3])
                return semver.VersionInfo.parse(normalized)
            except ValueError:
                # Last resort: return a very old version
                return semver.VersionInfo.parse("0.0.0")

    def get_installed_version(self) -> str | None:
        """Get currently active version from metadata only (no system fallbacks)."""
        # Get current profile (default to 'default')
        profile = self._get_current_profile()

        # Check metadata for active version in workenv
        if "workenv" in self.metadata:
            profile_data = self.metadata["workenv"].get(profile, {})
            # Use 'opentofu_version' for tofu tool
            tool_key = "opentofu_version" if self.tool_name == "tofu" else f"{self.tool_name}_version"

            if tool_key in profile_data:
                return profile_data[tool_key]

        # No fallbacks - workenv is completely self-contained
        return None

    def set_installed_version(self, version: str) -> None:
        """Set the active version in metadata."""
        # Get current profile
        profile = self._get_current_profile()

        # Ensure workenv structure exists
        if "workenv" not in self.metadata:
            self.metadata["workenv"] = {}
        if profile not in self.metadata["workenv"]:
            self.metadata["workenv"][profile] = {}

        # Store active version in metadata under workenv profile
        # Use 'opentofu_version' for tofu tool
        tool_key = "opentofu_version" if self.tool_name == "tofu" else f"{self.tool_name}_version"

        self.metadata["workenv"][profile][tool_key] = version
        self._save_metadata()

        # Also ensure it's at the front of RECENT
        self._update_recent_file_with_active(version)

        # Note: actual venv copying happens in create_symlink()

        logger.info(f"Set {self.tool_name} active version to {version} in profile '{profile}'")

    def remove_version(self, version: str) -> None:
        """Remove a specific version of the tool."""
        binary_path = self.get_binary_path(version)

        if binary_path.exists():
            binary_path.unlink()
            logger.info(f"Removed {self.tool_name} {version}")

            # Update metadata
            version_key = f"{self.tool_prefix}_{version}"
            if version_key in self.metadata:
                del self.metadata[version_key]
                self._save_metadata()

            # Update RECENT file
            self._update_recent_file()

        # Update config if this was the current version
        if self.get_installed_version() == version:
            try:
                self.config.set_tool_version(self.tool_name, "")
            except Exception:
                logger.debug(f"Could not clear {self.tool_name} version in config")

    def _calculate_file_hash(self, file_path: pathlib.Path, algorithm: str = "sha256") -> str:
        """Calculate hash of a file."""
        hash_func = hashlib.new(algorithm)
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def _install_from_archive(self, archive_path: pathlib.Path, version: str) -> None:
        """Install tool from downloaded archive in tf versions format."""
        # Extract to temporary directory
        extract_dir = self.cache_dir / f"{self.tool_prefix}_{version}_extract"
        extract_dir.mkdir(exist_ok=True)

        try:
            self.extract_archive(archive_path, extract_dir)

            # Find the binary in extracted files
            binary_name = self.executable_name
            if self.tool_name == "tofu":
                binary_name = "tofu"

            binary_path = None
            for file_path in extract_dir.rglob(f"{binary_name}*"):
                if file_path.is_file() and file_path.name in [
                    binary_name,
                    f"{binary_name}.exe",
                ]:
                    binary_path = file_path
                    break

            if not binary_path:
                raise ToolManagerError(f"{self.tool_name} binary not found in archive")

            # Copy to tf versions location
            target_path = self.get_binary_path(version)
            shutil.copy2(binary_path, target_path)

            # Make executable (Unix systems)
            self.make_executable(target_path)

            logger.info(f"Installed {self.tool_name} binary to: {target_path}")

            # Calculate installed binary hash
            binary_hash = self._calculate_file_hash(target_path)

            # Update metadata with comprehensive information
            self._update_install_metadata(version, archive_path, binary_hash)

            # Update RECENT file
            self._update_recent_file()

            # Verify installation
            if not self.verify_installation(version):
                raise ToolManagerError(f"{self.tool_name} {version} installation verification failed")

        finally:
            # Clean up extraction directory
            shutil.rmtree(extract_dir, ignore_errors=True)

    def _update_install_metadata(self, version: str, archive_path: pathlib.Path, binary_hash: str) -> None:
        """Update metadata for installed version with comprehensive information."""
        version_key = f"{self.tool_prefix}_{version}"

        # Get download URL for source tracking
        download_url = self.get_download_url(version)
        checksum_url = self.get_checksum_url(version)

        # Get file size
        binary_path = self.get_binary_path(version)
        file_size = binary_path.stat().st_size if binary_path.exists() else 0

        # Look for signature files
        sig_patterns = [
            f"{self.tool_prefix}_*.asc",
            f"{self.tool_prefix}_*SHA256SUMS.sig",
            f"{self.tool_name}_*.asc",
        ]
        signature_files = []
        for pattern in sig_patterns:
            signature_files.extend(self.install_path.glob(pattern))

        self.metadata[version_key] = {
            "tool": self.tool_name,
            "version": version,
            "installed_at": datetime.now().isoformat(),
            "download_url": download_url,
            "checksum_url": checksum_url if checksum_url else None,
            "archive_path": str(archive_path),
            "archive_size": archive_path.stat().st_size if archive_path.exists() else 0,
            "binary_path": str(binary_path),
            "binary_size": file_size,
            "binary_sha256": binary_hash,
            "signature_files": [str(f) for f in signature_files],
            "platform": self.get_platform_info(),
            "wrknv_version": "0.1.0",  # Track which version of wrknv installed this
        }

        self._save_metadata()

    def create_symlink(self, version: str) -> None:
        """Copy active tf binaries to venv bin directory for direct access.

        This replaces symlinks with a copy strategy that works on all platforms
        including Windows. The active binaries are copied to the venv's bin
        directory where they can be executed directly.
        """
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.warning(f"Binary not found at {binary_path}, skipping activation")
            return

        # Track the active version in metadata first
        self.set_installed_version(version)

        # Copy all active tf binaries to venv bin directory
        self._copy_active_binaries_to_venv()

        logger.info(f"Copied {self.tool_name} {version} to venv bin directory")

    def set_global_version(self, version: str) -> None:
        """Set a version as the global system version by copying to ~/.local/bin/."""
        binary_path = self.get_binary_path(version)
        if not binary_path.exists():
            logger.warning(f"Binary not found at {binary_path}, cannot set global version")
            return

        # Ensure ~/.local/bin directory exists
        local_bin_dir = pathlib.Path.home() / ".local" / "bin"
        local_bin_dir.mkdir(parents=True, exist_ok=True)

        # Determine target executable name
        target_name = "tofu" if self.tool_name == "tofu" else "terraform"

        if os.name == "nt":  # Windows
            target_name += ".exe"

        target_path = local_bin_dir / target_name

        # Copy the binary to ~/.local/bin
        shutil.copy2(binary_path, target_path)

        # Make executable on Unix systems
        if os.name != "nt":
            target_path.chmod(0o755)

        # Update metadata to track global version
        if "global" not in self.metadata:
            self.metadata["global"] = {}

        tool_key = "opentofu_version" if self.tool_name == "tofu" else f"{self.tool_name}_version"

        self.metadata["global"][tool_key] = version
        self._save_metadata()

        logger.info(f"Set {self.tool_name} {version} as global system version at {target_path}")

    def get_global_version(self) -> str | None:
        """Get the currently set global version."""
        if "global" not in self.metadata:
            return None

        tool_key = "opentofu_version" if self.tool_name == "tofu" else f"{self.tool_name}_version"

        return self.metadata["global"].get(tool_key)

    def get_metadata_for_version(self, version: str) -> dict | None:
        """Get metadata for a specific version."""
        version_key = f"{self.tool_prefix}_{version}"
        return self.metadata.get(version_key)

    def get_active_version_info(self) -> dict | None:
        """Get detailed information about the currently active version."""
        version = self.get_installed_version()
        if version:
            info = self.get_metadata_for_version(version)
            if info:
                # Add current status
                binary_path = self.get_binary_path(version)
                info["is_active"] = True
                info["binary_exists"] = binary_path.exists()
                return info
        return None

    def _get_current_profile(self) -> str:
        """Get the current workenv profile name."""
        # Check environment variable first
        profile = os.environ.get("WRKENV_PROFILE")
        if profile:
            return profile

        # Check metadata for current profile setting
        if "workenv" in self.metadata and "_current_profile" in self.metadata["workenv"]:
            return self.metadata["workenv"]["_current_profile"]

        # Default to 'default' profile
        return "default"

    def _get_venv_bin_dir(self) -> pathlib.Path:
        """Get the current virtual environment's bin directory."""
        # First check if we're in a virtual environment
        if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
            # We're in a virtual environment
            venv_path = pathlib.Path(sys.prefix)

            # Check if this is a wrknv (has 'workenv' in the path)
            if "workenv" in str(venv_path):
                # Use the workenv structure
                bin_dir = venv_path / "Scripts" if os.name == "nt" else venv_path / "bin"
            else:
                # Regular venv
                bin_dir = venv_path / "Scripts" if os.name == "nt" else venv_path / "bin"
        else:
            # Not in a venv, check for workenv directory relative to project root
            project_root = self._find_project_root()
            if project_root:
                workenv_dir_name = self.config.get_workenv_dir_name()
                bin_dir = project_root / workenv_dir_name / "bin"
                if bin_dir.exists():
                    return bin_dir

            # Fallback to .local/bin
            bin_dir = pathlib.Path.home() / ".local" / "bin"

        # Ensure directory exists
        bin_dir.mkdir(parents=True, exist_ok=True)
        return bin_dir

    def _find_project_root(self) -> pathlib.Path | None:
        """Find the project root by looking for pyproject.toml."""
        current = pathlib.Path.cwd()

        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent

        return None

    def _copy_active_binaries_to_venv(self) -> None:
        """Copy all active tf binaries to venv bin directory."""
        if not self.venv_bin_dir:
            logger.warning("No venv bin directory available for tf binary copying")
            return

        # Get active versions for both tools
        for tool_name in ["tofu", "terraform"]:
            try:
                # Create a temporary manager instance to get active version
                if tool_name == "tofu":
                    from .tofu import TofuManager

                    temp_manager = TofuManager(self.config)
                else:
                    from .terraform import TerraformManager

                    temp_manager = TerraformManager(self.config)

                active_version = temp_manager.get_installed_version()
                if active_version:
                    source_path = temp_manager.get_binary_path(active_version)
                    if source_path.exists():
                        # Terraform is copied as 'hctf', OpenTofu stays as 'tofu'
                        target_name = "hctf" if tool_name == "terraform" else "tofu"

                        if os.name == "nt":  # Windows
                            target_name += ".exe"

                        target_path = self.venv_bin_dir / target_name

                        # Copy the binary
                        shutil.copy2(source_path, target_path)

                        # Make executable on Unix systems
                        if os.name != "nt":
                            target_path.chmod(0o755)

                        logger.debug(f"Copied {tool_name} {active_version} to {target_path}")

            except Exception as e:
                logger.warning(f"Failed to copy {tool_name} binary: {e}")


# 🍲🥄📄🪄
