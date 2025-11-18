#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Doctor command for diagnosing wrknv environment issues.

This module provides diagnostic tools to help users identify and fix
common problems with their wrknv setup."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import shutil
import sys

from provide.foundation.process import run
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class WrknvDoctor:
    """Diagnose and report on wrknv environment health."""

    def __init__(self) -> None:
        self.console = Console()
        self.checks_passed = []
        self.checks_failed = []
        self.checks_warning = []

    def run(self, verbose: bool = False) -> int:
        """
        Run all diagnostic checks.

        Args:
            verbose: If True, show detailed output.

        Returns:
            Exit code (0 if all checks pass, 1 otherwise).
        """
        self.console.print("\n[bold cyan]🩺 Running wrknv doctor...[/bold cyan]\n")

        # Run all checks
        self._check_system_info()
        self._check_wrknv_installation()
        self._check_dependencies()
        self._check_workenv_structure()
        self._check_env_script()
        self._check_config_files()
        self._check_sibling_packages()
        self._check_common_issues()

        # Print summary
        self._print_summary(verbose)

        # Return appropriate exit code
        if self.checks_failed:
            return 1
        return 0

    def _check_system_info(self) -> None:
        """Check and display system information."""
        try:
            info = {
                "Platform": platform.platform(),
                "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "Architecture": platform.machine(),
                "Working Directory": str(Path.cwd()),
            }

            self.console.print("[bold]System Information:[/bold]")
            for key, value in info.items():
                self.console.print(f"  {key}: {value}")
            self.console.print()

            self.checks_passed.append(("System Info", "Collected successfully"))
        except Exception as e:
            self.checks_failed.append(("System Info", str(e)))

    def _check_wrknv_installation(self) -> None:
        """Check if wrknv is properly installed."""
        try:
            # Check if wrknv module is importable
            import wrknv

            version = getattr(wrknv, "__version__", "unknown")
            self.checks_passed.append(("wrknv Installation", f"Version {version}"))

            # Check if wrknv CLI is available
            result = run(["wrknv", "--version"], timeout=5)
            if result.returncode == 0:
                self.checks_passed.append(("wrknv CLI", "Available"))
            else:
                self.checks_warning.append(("wrknv CLI", "Not in PATH"))
        except ImportError:
            self.checks_failed.append(("wrknv Installation", "Module not found"))
        except FileNotFoundError:
            self.checks_warning.append(("wrknv CLI", "Not found in PATH"))
        except Exception as e:
            self.checks_failed.append(("wrknv Installation", str(e)))

    def _check_dependencies(self) -> None:
        """Check for required dependencies."""
        dependencies = {
            "uv": "Package manager",
            "git": "Version control",
            "python3": "Python interpreter",
            "bash": "Shell for env.sh",
        }

        for cmd, description in dependencies.items():
            if shutil.which(cmd):
                self.checks_passed.append((f"{cmd}", f"{description} - Found"))
            else:
                if cmd in ["uv"]:
                    self.checks_failed.append((f"{cmd}", f"{description} - Required but not found"))
                else:
                    self.checks_warning.append((f"{cmd}", f"{description} - Optional but recommended"))

    def _check_workenv_structure(self) -> None:
        """Check if workenv directory exists and has correct structure."""
        workenv_dir = Path.cwd() / "workenv"

        if not workenv_dir.exists():
            self.checks_warning.append(("workenv Directory", "Not found - run 'source env.sh' to create"))
            return

        # Check for platform-specific subdirectories
        subdirs = list(workenv_dir.iterdir())
        if not subdirs:
            self.checks_warning.append(("workenv Structure", "Empty - no environments created"))
            return

        # Check structure of first workenv
        for subdir in subdirs:
            if subdir.is_dir():
                expected_dirs = ["bin", "lib", "include"]
                missing = []
                for expected in expected_dirs:
                    if not (subdir / expected).exists():
                        missing.append(expected)

                if missing:
                    self.checks_warning.append(
                        (f"workenv/{subdir.name}", f"Missing directories: {', '.join(missing)}")
                    )
                else:
                    self.checks_passed.append((f"workenv/{subdir.name}", "Structure OK"))
                break

    def _check_env_script(self) -> None:
        """Check if env.sh exists and is valid."""
        env_script = Path.cwd() / "env.sh"

        if not env_script.exists():
            self.checks_failed.append(("env.sh", "Not found - run 'wrknv generate'"))
            return

        # Check if env.sh was generated by wrknv
        content = env_script.read_text()
        is_wrknv_generated = "Generated by wrknv" in content or "WORKENV_DIR=" in content

        if not is_wrknv_generated:
            self.checks_failed.append(
                ("env.sh", "Not generated by wrknv - run 'wrknv generate' to regenerate")
            )
            return

        # Check if it's executable
        if not os.access(env_script, os.X_OK):
            self.checks_warning.append(("env.sh", "Not executable - run 'chmod +x env.sh'"))

        # Check for correct workenv pattern
        system = platform.system().lower()
        machine = platform.machine().lower()
        if machine in ["x86_64", "amd64"]:
            arch = "amd64"
        elif machine in ["arm64", "aarch64"]:
            arch = "arm64"
        else:
            arch = machine

        package_name = Path.cwd().name
        expected_workenv = f"workenv/{package_name}_{system}_{arch}"

        if expected_workenv not in content:
            self.checks_failed.append(
                (
                    "env.sh Workenv Path",
                    f"Incorrect pattern - expected '{expected_workenv}'. Regenerate with 'wrknv generate'",
                )
            )
            return

        # Check required patterns for proper functioning
        required_patterns = [
            "WORKENV_DIR=",
            "UV_INSTALLER_URL=",
            "uv venv",
            "uv pip",
        ]

        missing = []
        for pattern in required_patterns:
            if pattern not in content:
                missing.append(pattern)

        if missing:
            self.checks_failed.append(
                (
                    "env.sh Content",
                    f"Missing required patterns: {', '.join(missing)}. Regenerate with 'wrknv generate'",
                )
            )
        else:
            # Test if env.sh actually works
            self._test_env_script_execution(env_script)

    def _test_env_script_execution(self, env_script: Path) -> None:
        """Test if env.sh can be executed successfully."""
        try:
            # Try to source env.sh and check if VIRTUAL_ENV is set
            result = run(["bash", "-c", f"source {env_script} && echo $VIRTUAL_ENV"], timeout=10)

            if result.returncode != 0:
                self.checks_failed.append(
                    (
                        "env.sh Execution",
                        f"Failed to execute: {result.stderr.strip()}. Regenerate with 'wrknv generate'",
                    )
                )
            elif not result.stdout.strip():
                self.checks_failed.append(
                    ("env.sh Execution", "VIRTUAL_ENV not set. Regenerate with 'wrknv generate'")
                )
            else:
                workenv_path = result.stdout.strip()
                if Path(workenv_path).exists():
                    self.checks_passed.append(("env.sh", f"Valid and working → {workenv_path}"))
                else:
                    self.checks_warning.append(
                        ("env.sh Execution", f"Points to non-existent workenv: {workenv_path}")
                    )
        except TimeoutError:
            self.checks_failed.append(
                ("env.sh Execution", "Timed out - possible infinite loop. Regenerate with 'wrknv generate'")
            )
        except Exception as e:
            self.checks_failed.append(
                ("env.sh Execution", f"Unexpected error: {e}. This may be a bug in wrknv")
            )

    def _check_config_files(self) -> None:
        """Check for wrknv.toml configuration."""
        config_file = Path.cwd() / "wrknv.toml"

        if not config_file.exists():
            self.checks_warning.append(("wrknv.toml", "Not found - using defaults"))
            return

        try:
            import tomli

            with config_file.open("rb") as f:
                config = tomli.load(f)

            # Check for required sections
            if "project" in config:
                self.checks_passed.append(("wrknv.toml", "Valid project configuration"))
            else:
                self.checks_warning.append(("wrknv.toml", "Missing [project] section"))

            # Check for tools configuration
            if "tools" in config:
                tool_count = len(config["tools"])
                self.checks_passed.append(("Tools Configuration", f"{tool_count} tools configured"))

            # Check for siblings configuration
            if "siblings" in config:
                patterns = config["siblings"].get("patterns", [])
                if patterns:
                    self.checks_passed.append(("Sibling Packages", f"{len(patterns)} patterns configured"))

        except Exception as e:
            self.checks_failed.append(("wrknv.toml", f"Parse error: {e}"))

    def _check_sibling_packages(self) -> None:
        """Check if configured sibling packages are accessible."""
        config_file = Path.cwd() / "wrknv.toml"
        if not config_file.exists():
            return

        try:
            import tomli

            with config_file.open("rb") as f:
                config = tomli.load(f)

            siblings = config.get("siblings", {}).get("patterns", [])
            for sibling in siblings:
                # Check in parent directory
                sibling_path = Path.cwd().parent / sibling
                if sibling_path.exists():
                    self.checks_passed.append((f"Sibling: {sibling}", "Found"))
                else:
                    self.checks_warning.append((f"Sibling: {sibling}", "Not found in parent directory"))

        except Exception:
            pass  # Already reported in config check

    def _check_common_issues(self) -> None:
        """Check for common issues that users encounter."""
        # Check if .venv exists (shouldn't use this with wrknv)
        if (Path.cwd() / ".venv").exists():
            self.checks_warning.append((".venv Directory", "Found - should use workenv/ instead with wrknv"))

        # Check for conflicting environment variables
        problematic_vars = ["VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME"]
        active_vars = []
        for var in problematic_vars:
            if os.environ.get(var):
                active_vars.append(var)

        if active_vars:
            self.checks_warning.append(
                ("Environment Variables", f"Potentially conflicting: {', '.join(active_vars)}")
            )

        # Check if we're inside another virtual environment
        if sys.prefix != sys.base_prefix:
            self.checks_warning.append(("Virtual Environment", "Already activated - may conflict with wrknv"))

    def _print_summary(self, verbose: bool) -> None:
        """Print summary of all checks."""
        # Create summary table
        table = Table(title="Diagnostic Results", box=box.ROUNDED)
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details")

        # Add passed checks
        for check, details in self.checks_passed:
            table.add_row(check, "[green]✅ PASS[/green]", details)

        # Add warnings
        for check, details in self.checks_warning:
            table.add_row(check, "[yellow]⚠️  WARN[/yellow]", details)

        # Add failed checks
        for check, details in self.checks_failed:
            table.add_row(check, "[red]❌ FAIL[/red]", details)

        self.console.print(table)

        # Print summary statistics
        total = len(self.checks_passed) + len(self.checks_warning) + len(self.checks_failed)

        summary = Panel(
            f"[green]Passed: {len(self.checks_passed)}[/green] | "
            f"[yellow]Warnings: {len(self.checks_warning)}[/yellow] | "
            f"[red]Failed: {len(self.checks_failed)}[/red] | "
            f"Total: {total}",
            title="Summary",
            box=box.DOUBLE,
        )
        self.console.print(summary)

        # Print recommendations if there are issues
        if self.checks_failed or self.checks_warning:
            self._print_recommendations()

    def _print_recommendations(self) -> None:
        """Print recommendations based on failed checks."""
        self.console.print("\n[bold]Recommendations:[/bold]")

        recommendations = []

        # Priority 1: Fix critical failures
        has_env_issues = False
        for check, _details in self.checks_failed:
            if "env.sh" in check or "Workenv Path" in check:
                has_env_issues = True
            elif "uv" in check:
                recommendations.append(("🔧 Install uv", "curl -LsSf https://astral.sh/uv/install.sh | sh"))
            elif "wrknv Installation" in check:
                recommendations.append(("🔧 Reinstall wrknv", "See installation docs"))

        # If there are any env.sh issues, recommend regeneration
        if has_env_issues:
            recommendations.insert(0, ("🔄 Regenerate env.sh", "wrknv generate --force"))
            recommendations.append(("📝 After regenerating", "source env.sh"))

        # Priority 2: Address warnings
        for check, _details in self.checks_warning:
            if ".venv Directory" in check:
                recommendations.append(("🗑️  Remove .venv", "rm -rf .venv && source env.sh"))
            elif "workenv Directory" in check and not has_env_issues:
                recommendations.append(("🔧 Check workenv", "wrknv doctor"))
            elif "Virtual Environment" in check:
                recommendations.append(("🚪 Exit current venv", "deactivate && source env.sh"))

        # Remove duplicates and print
        seen = set()
        for title, command in recommendations:
            key = command
            if key not in seen:
                self.console.print(f"\n  {title}")
                self.console.print(f"  [dim]$ {command}[/dim]")
                seen.add(key)

        # If multiple env.sh failures, suggest bug report
        env_failure_count = sum(1 for check, _ in self.checks_failed if "env.sh" in check)
        if env_failure_count >= 3:
            self.console.print(
                "\n[yellow]⚠️  Multiple env.sh issues detected. "
                "If regenerating doesn't help, this may be a bug in wrknv.[/yellow]"
            )
            self.console.print("  [dim]Please report at: https://github.com/provide-io/wrknv/issues[/dim]")


def run_doctor(verbose: bool = False) -> int:
    """
    Run the doctor diagnostic tool.

    Args:
        verbose: If True, show detailed output.

    Returns:
        Exit code.
    """
    doctor = WrknvDoctor()
    return doctor.run(verbose)


# 🧰🌍🔚
