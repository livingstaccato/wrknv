#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Task execution environment detection and management.

This module provides auto-detection of virtual environments, UV projects,
and editable installs to determine the optimal task execution strategy.

Patterns adopted from pyvider's launch-context for robust detection.
"""

from __future__ import annotations

from importlib.metadata import Distribution, PackageNotFoundError
import json
import os
from pathlib import Path
import platform
import sys
from typing import Literal

from provide.foundation import logger
from provide.foundation.file.formats import read_toml

ExecutionMode = Literal["auto", "uv_run", "direct", "system"]


class ExecutionEnvironment:
    """Manages environment detection for task execution.

    This class detects the optimal execution strategy by checking:
    1. Environment variable overrides (WRKNV_TASK_RUNNER)
    2. Whether package is editable installed
    3. Whether project uses UV
    4. Available virtual environments

    Example:
        >>> env = ExecutionEnvironment(Path("/project"), "mypackage")
        >>> command = env.prepare_command("pytest tests/")
        >>> exec_env = env.prepare_environment({"FOO": "bar"})
    """

    def __init__(
        self,
        project_dir: Path,
        package_name: str | None = None,
        mode: ExecutionMode = "auto",
    ) -> None:
        """Initialize environment detection.

        Args:
            project_dir: Project root directory
            package_name: Package name to check for editable install
            mode: Execution mode override ("auto", "uv_run", "direct", "system")
        """
        self.project_dir = project_dir
        self.package_name = package_name or project_dir.name
        self.mode = mode

        # Detection results (cached)
        self.venv_path: Path | None = None
        self.is_uv_project: bool = False
        self.package_is_editable: bool = False
        self.use_uv_run: bool = False
        self.override_from_env: str | None = None

        # Run detection
        self._detect()

    def _detect(self) -> None:
        """Run all detection checks and determine execution strategy."""
        # Priority 1: Check for environment variable override
        self.override_from_env = os.environ.get("WRKNV_TASK_RUNNER")
        if self.override_from_env:
            logger.debug(
                "Task runner override from environment",
                runner=self.override_from_env,
            )
            self.use_uv_run = self.override_from_env == "uv run"
            return

        # Priority 2: Detect environment components
        self.venv_path = self._detect_venv()
        self.is_uv_project = self._is_uv_project()
        self.package_is_editable = self._is_editable_install()

        # Priority 3: Apply mode-specific logic
        if self.mode == "uv_run":
            self.use_uv_run = True
        elif self.mode == "direct":
            self.use_uv_run = False
        elif self.mode == "system":
            self.use_uv_run = False
            self.venv_path = None  # Ignore venv
        # Auto-detection logic:
        # If editable install detected -> use direct (PATH) to preserve it
        # If UV project but not editable -> use uv run
        # Otherwise -> use direct with PATH modification
        elif self.package_is_editable:
            self.use_uv_run = False
            logger.debug(
                "Editable install detected - using direct execution",
                package=self.package_name,
            )
        elif self.is_uv_project:
            self.use_uv_run = True
            logger.debug("UV project detected - using uv run")
        else:
            self.use_uv_run = False
            logger.debug("Using direct execution with PATH modification")

        logger.debug(
            "Environment detection complete",
            venv_path=str(self.venv_path) if self.venv_path else None,
            is_uv_project=self.is_uv_project,
            package_is_editable=self.package_is_editable,
            use_uv_run=self.use_uv_run,
            mode=self.mode,
        )

    def _detect_venv(self) -> Path | None:
        """Find virtual environment using priority order.

        Priority:
        1. workenv/{package}_{os}_{arch}/ (wrknv pattern)
        2. .venv/ (standard)
        3. venv/ (fallback)
        4. Current Python's venv (if running in one)

        Returns:
            Path to venv if found, None otherwise
        """
        # Priority 1: workenv pattern
        system = platform.system().lower()
        machine = platform.machine().lower()

        # Normalize architecture
        if machine in ["x86_64", "amd64"]:
            arch = "amd64"
        elif machine in ["arm64", "aarch64"]:
            arch = "arm64"
        else:
            arch = machine

        workenv_path = self.project_dir / "workenv" / f"{self.package_name}_{system}_{arch}"
        if workenv_path.exists() and (workenv_path / "pyvenv.cfg").exists():
            logger.trace("Found workenv venv", path=str(workenv_path))
            return workenv_path

        # Priority 2: .venv
        venv_path = self.project_dir / ".venv"
        if venv_path.exists() and (venv_path / "pyvenv.cfg").exists():
            logger.trace("Found .venv", path=str(venv_path))
            return venv_path

        # Priority 3: venv
        venv_path = self.project_dir / "venv"
        if venv_path.exists() and (venv_path / "pyvenv.cfg").exists():
            logger.trace("Found venv", path=str(venv_path))
            return venv_path

        # Priority 4: Check if we're currently in a venv
        if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
            current_venv = Path(sys.prefix)
            logger.trace("Using current venv", path=str(current_venv))
            return current_venv

        logger.trace("No venv found")
        return None

    def _is_uv_project(self) -> bool:
        """Check if project uses UV package manager.

        Checks for:
        1. uv.lock file (strongest indicator)
        2. [tool.uv] section in pyproject.toml

        Returns:
            True if UV project, False otherwise
        """
        # Check for uv.lock (strongest indicator)
        if (self.project_dir / "uv.lock").exists():
            logger.trace("UV project detected via uv.lock")
            return True

        # Check for [tool.uv] in pyproject.toml
        pyproject = self.project_dir / "pyproject.toml"
        if pyproject.exists():
            try:
                data = read_toml(pyproject, default={})
                if data and "tool" in data and "uv" in data["tool"]:
                    logger.trace("UV project detected via pyproject.toml [tool.uv]")
                    return True
            except Exception:
                pass

        return False

    def _is_editable_install(self) -> bool:
        """Check if package is installed in editable mode.

        Uses two detection methods:
        1. Modern: direct_url.json with editable flag (Python 3.11+)
        2. Legacy: src/ directory structure pattern (adopted from pyvider)

        Returns:
            True if package is editable install, False otherwise
        """
        # Method 1: Modern detection via direct_url.json
        try:
            dist = Distribution.from_name(self.package_name)
            direct_url_text = dist.read_text("direct_url.json")
            if direct_url_text:
                direct_url = json.loads(direct_url_text)
                if direct_url.get("dir_info", {}).get("editable", False):
                    logger.trace(
                        "Editable install detected via direct_url.json",
                        package=self.package_name,
                    )
                    return True
        except (PackageNotFoundError, FileNotFoundError, json.JSONDecodeError):
            pass

        # Method 2: Legacy detection via src/ structure (pyvider pattern)
        # Check if package module is in src/ directory structure
        try:
            import importlib

            module = importlib.import_module(self.package_name.replace("-", "_"))
            if module.__file__ is not None:
                module_path = Path(module.__file__).parent

                # Check if module is in src/ directory structure
                if module_path.parent.name == "src":
                    logger.trace(
                        "Editable install detected via src/ structure",
                        package=self.package_name,
                        path=str(module_path),
                    )
                    return True
        except (ImportError, AttributeError, TypeError):
            pass

        return False

    def prepare_command(self, command: str, prefix_override: str | None = None) -> str:
        """Prepare command with uv run prefix if needed.

        Args:
            command: Original command string
            prefix_override: Per-task prefix override (takes precedence)

        Returns:
            Modified command (may have 'uv run' or custom prefix prepended)
        """
        # Per-task override takes precedence
        if prefix_override is not None:
            if prefix_override:  # Non-empty string
                return f"{prefix_override} {command}"
            return command  # Empty string = explicitly no prefix

        # Environment variable override
        if self.override_from_env:
            return f"{self.override_from_env} {command}"

        # Auto-detected behavior
        if self.use_uv_run:
            return f"uv run {command}"

        return command

    def prepare_environment(self, base_env: dict[str, str] | None = None) -> dict[str, str]:
        """Prepare environment dictionary with PATH modifications.

        Args:
            base_env: Base environment to extend

        Returns:
            Environment dictionary with PATH modifications if needed
        """
        env = base_env.copy() if base_env else {}

        # If using uv run, don't modify PATH (uv handles it)
        if self.use_uv_run:
            return env

        # If no venv, return as-is
        if not self.venv_path:
            return env

        # Prepend venv bin to PATH for direct execution
        bin_dir = self._get_bin_dir(self.venv_path)
        if bin_dir.exists():
            separator = ";" if platform.system() == "Windows" else ":"
            current_path = env.get("PATH", os.environ.get("PATH", ""))
            env["PATH"] = f"{bin_dir}{separator}{current_path}"
            logger.trace("Prepended venv bin to PATH", bin_dir=str(bin_dir))

        return env

    @staticmethod
    def _get_bin_dir(venv_path: Path) -> Path:
        """Get bin/Scripts directory for venv.

        Args:
            venv_path: Path to virtual environment

        Returns:
            Path to bin directory (Windows: Scripts/, Unix: bin/)
        """
        if platform.system() == "Windows":
            return venv_path / "Scripts"
        return venv_path / "bin"


# 🧰🌍🔚
