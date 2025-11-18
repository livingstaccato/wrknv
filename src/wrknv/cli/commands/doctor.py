#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Doctor Commands
===============
Commands for diagnosing and testing the wrknv system."""

from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path
import sys
from typing import Any

from provide.foundation.cli import echo_error, echo_info, echo_success, echo_warning
from provide.foundation.hub import register_command

from wrknv.cli.hub_cli import WrknvContext


# Register the selftest group first
@register_command("selftest", group=True, description="Self-test and validate wrknv system")
def selftest_group() -> None:
    """Self-test and validation commands."""
    pass


@register_command("selftest.check", description="Comprehensive health check of wrknv")
def selftest_check(verbose: bool = False, fix: bool = False) -> None:
    """Run comprehensive health check of wrknv system."""
    try:
        echo_info("🩺 Running wrknv health check...")

        checks = [
            _check_environment(),
            _check_config(),
            _check_dependencies(),
            _check_commands(),
            _check_permissions(),
        ]

        passed = 0
        failed = 0
        warnings = 0

        for check_result in checks:
            if check_result["status"] == "pass":
                passed += 1
            elif check_result["status"] == "fail":
                echo_error(f"❌ {check_result['name']}")
                echo_error(f"   {check_result['message']}")
                if fix and check_result.get("fix"):
                    echo_info(f"   💡 Attempting fix: {check_result['fix']}")
                failed += 1
            elif check_result["status"] == "warn":
                echo_warning(f"⚠️  {check_result['name']}")
                echo_warning(f"   {check_result['message']}")
                warnings += 1

            if verbose and check_result.get("details"):
                echo_info(f"   Details: {check_result['details']}")

        echo_info("\n📊 Health Check Summary:")
        if warnings > 0:
            echo_warning(f"   ⚠️  Warnings: {warnings}")
        if failed > 0:
            echo_error(f"   ❌ Failed: {failed}")

        if failed > 0:
            echo_error("\n❌ Health check failed. Please fix the issues above.")
            sys.exit(1)
        elif warnings > 0:
            echo_warning("\n⚠️  Health check completed with warnings.")
        else:
            echo_success("\n✅ All health checks passed!")

    except Exception as e:
        echo_error(f"Health check failed: {e}")
        sys.exit(1)


@register_command("selftest.env", description="Check environment setup")
def selftest_env() -> None:
    """Check environment setup."""
    try:
        result = _check_environment()
        if result["status"] == "pass":
            if result.get("details"):
                echo_info(f"   {result['details']}")
        else:
            echo_error(f"❌ {result['name']}: {result['message']}")
            sys.exit(1)

    except Exception as e:
        echo_error(f"Environment check failed: {e}")
        sys.exit(1)


@register_command("selftest.config", description="Check configuration")
def selftest_config() -> None:
    """Check configuration."""
    try:
        result = _check_config()
        if result["status"] == "pass":
            if result.get("details"):
                echo_info(f"   {result['details']}")
        else:
            echo_error(f"❌ {result['name']}: {result['message']}")
            sys.exit(1)

    except Exception as e:
        echo_error(f"Configuration check failed: {e}")
        sys.exit(1)


def _check_environment() -> dict[str, Any]:
    """Check environment setup."""
    try:
        import sys

        # Check Python version

        # Check if we're in a virtual environment
        in_venv = hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )

        # Check for workenv directory
        workenv_dir = Path.cwd() / "workenv"
        if workenv_dir.exists():
            env_detail = "workenv/ directory found"
        elif in_venv:
            env_detail = f"Virtual environment active: {sys.prefix}"
        else:
            return {
                "name": "Environment Setup",
                "status": "warn",
                "message": "No workenv/ directory or virtual environment detected",
                "details": "Consider running 'wrknv workenv create' or activating a virtual environment",
            }

        return {
            "name": "Environment Setup",
            "status": "pass",
            "message": "Environment properly configured",
            "details": env_detail,
        }

    except Exception as e:
        return {"name": "Environment Setup", "status": "fail", "message": f"Environment check failed: {e}"}


def _check_config() -> dict[str, Any]:
    """Check configuration."""
    try:
        config = WrknvContext.get_config()

        # Check if config file exists
        if not config.config_exists():
            return {
                "name": "Configuration",
                "status": "warn",
                "message": "No configuration file found",
                "fix": "Run 'wrknv config init' to create one",
            }

        # Validate configuration
        is_valid, errors = config.validate()

        if not is_valid:
            return {
                "name": "Configuration",
                "status": "fail",
                "message": f"Configuration validation failed: {'; '.join(errors[:3])}",
                "fix": "Run 'wrknv config validate --verbose' for details",
            }

        return {
            "name": "Configuration",
            "status": "pass",
            "message": "Configuration is valid",
            "details": f"Config file: {config.config_path}",
        }

    except Exception as e:
        return {"name": "Configuration", "status": "fail", "message": f"Configuration check failed: {e}"}


def _check_dependencies() -> dict[str, Any]:
    """Check required dependencies."""
    try:
        missing_deps = []
        optional_missing = []

        # Check required dependencies
        required_deps = [
            ("attrs", "attrs"),
            ("cattrs", "cattrs"),
            ("provide.foundation", "provide.foundation"),
        ]

        for dep_name, import_name in required_deps:
            try:
                __import__(import_name)
            except ImportError:
                missing_deps.append(dep_name)

        # Check for TOML support (tomllib in Python 3.11+, tomli as fallback)
        if find_spec("tomllib") is None and find_spec("tomli") is None:
            missing_deps.append("tomli (for TOML parsing)")

        # Check optional dependencies
        optional_deps = [
            ("tomli_w", "for saving TOML files"),
            ("semver", "for version parsing"),
        ]

        for dep, purpose in optional_deps:
            try:
                __import__(dep)
            except ImportError:
                optional_missing.append(f"{dep} ({purpose})")

        if missing_deps:
            return {
                "name": "Dependencies",
                "status": "fail",
                "message": f"Missing required dependencies: {', '.join(missing_deps)}",
                "fix": "Run 'uv pip install -e .[all]' to install dependencies",
            }

        if optional_missing:
            return {
                "name": "Dependencies",
                "status": "warn",
                "message": f"Missing optional dependencies: {', '.join(optional_missing)}",
                "details": "Some features may not work without these dependencies",
            }

        return {"name": "Dependencies", "status": "pass", "message": "All dependencies available"}

    except Exception as e:
        return {"name": "Dependencies", "status": "fail", "message": f"Dependency check failed: {e}"}


def _check_commands() -> dict[str, Any]:
    """Check command registration and functionality."""
    try:
        from wrknv.cli.hub_cli import create_cli

        # Create CLI instance
        cli = create_cli()

        # Check that commands are registered
        if not cli.commands:
            return {"name": "Commands", "status": "fail", "message": "No commands registered in CLI"}

        # Check for core command groups
        expected_groups = ["config", "workenv", "gitignore", "package", "selftest"]
        missing_groups = []

        for group in expected_groups:
            if group not in cli.commands:
                missing_groups.append(group)

        if missing_groups:
            return {
                "name": "Commands",
                "status": "warn",
                "message": f"Missing command groups: {', '.join(missing_groups)}",
                "details": f"Found {len(cli.commands)} commands/groups",
            }

        return {
            "name": "Commands",
            "status": "pass",
            "message": "All command groups available",
            "details": f"Found {len(cli.commands)} commands/groups",
        }

    except Exception as e:
        return {"name": "Commands", "status": "fail", "message": f"Command check failed: {e}"}


def _check_permissions() -> dict[str, Any]:
    """Check file system permissions."""
    try:
        # Check current directory permissions
        cwd = Path.cwd()
        if not cwd.exists():
            return {"name": "Permissions", "status": "fail", "message": "Current directory does not exist"}

        # Check write permissions in current directory
        test_file = cwd / ".wrknv_permission_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except (PermissionError, OSError) as e:
            return {
                "name": "Permissions",
                "status": "fail",
                "message": f"No write permission in current directory: {e}",
                "fix": "Ensure you have write permissions in the project directory",
            }

        # Check home directory for config
        home_config_dir = Path.home() / ".config" / "wrknv"
        if not home_config_dir.exists():
            try:
                home_config_dir.mkdir(parents=True)
                home_config_dir.rmdir()  # Clean up test directory
            except (PermissionError, OSError):
                return {
                    "name": "Permissions",
                    "status": "warn",
                    "message": "Cannot create config directory in home folder",
                    "details": "Global configuration may not work",
                }

        return {"name": "Permissions", "status": "pass", "message": "File system permissions OK"}

    except Exception as e:
        return {"name": "Permissions", "status": "fail", "message": f"Permission check failed: {e}"}


# 🧰🌍🔚
