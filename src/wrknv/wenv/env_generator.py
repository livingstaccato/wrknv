#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Environment Script Generator
============================
Generate env.sh and env.ps1 scripts from templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from provide.foundation import logger

from wrknv.cli.visual import Emoji, print_success


class EnvScriptGenerator:
    """Generate environment setup scripts for both bash and PowerShell."""

    def __init__(self, template_base_dir: Path | None = None) -> None:
        """Initialize the generator with template directory."""
        if template_base_dir is None:
            template_base_dir = Path(__file__).parent.parent / "templates" / "env"

        self.template_base_dir = template_base_dir

        # Create separate environments for sh and pwsh templates
        self.sh_env = Environment(
            loader=FileSystemLoader(template_base_dir / "sh"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.ps1_env = Environment(
            loader=FileSystemLoader(template_base_dir / "pwsh"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_env_script(
        self,
        project_name: str,
        output_path: Path,
        script_type: str = "sh",
        **kwargs: Any,
    ) -> None:
        """Generate an environment setup script.

        Args:
            project_name: Name of the project
            output_path: Path to write the script
            script_type: Either "sh" for bash or "ps1" for PowerShell
            **kwargs: Additional template variables
        """
        # Default configuration
        config = {
            "project_name": project_name,
            "env_profile_var": f"{project_name.upper().replace('-', '_')}_PROFILE",
            "venv_prefix": project_name.lower(),
            "use_spinner": script_type == "sh",  # PowerShell doesn't need spinner
            "strict_project_check": False,
            "install_siblings": True,
            "sibling_patterns": [],  # No default peers - specified in config
            "special_siblings": [],  # No default peers - specified in config
            "create_log_dir": True,
            "deduplicate_path": True,
            "include_tool_verification": True,  # Enable for wrknv
            "cleanup_logs": True,
            "tools_to_verify": [
                {
                    "name": "Python",
                    "command": "python",
                    "check_type": "command",
                    "var_name": "PYTHON",
                    "version_cmd": "python --version 2>&1",
                },
                {
                    "name": "UV",
                    "command": "uv",
                    "check_type": "command",
                    "var_name": "UV",
                    "version_cmd": "uv --version 2>&1",
                },
                {
                    "name": "wrknv",
                    "command": "wrknv",
                    "check_type": "command",
                    "var_name": "WRKENV",
                    "version_cmd": "wrknv --version 2>&1 || echo 'No version info'",
                },
                {
                    "name": "ibmtf",
                    "command": "ibmtf",
                    "check_type": "command",
                    "var_name": "IBMTF",
                    "version_cmd": "ibmtf version 2>&1 | head -1 || echo 'Not installed'",
                },
                {
                    "name": "tofu",
                    "command": "tofu",
                    "check_type": "command",
                    "var_name": "TOFU",
                    "version_cmd": "tofu version 2>&1 | head -1 || echo 'Not installed'",
                },
            ],
            "useful_commands": [
                {
                    "command": f"{project_name.lower()} --help",
                    "description": f"{project_name} CLI",
                },
                {"command": "wrknv status", "description": "Check tool versions"},
                {
                    "command": "wrknv container status",
                    "description": "Container status",
                },
                {"command": "pytest", "description": "Run tests"},
                {"command": "deactivate", "description": "Exit environment"},
            ],
        }

        # Update with user-provided kwargs
        config.update(kwargs)

        # Select appropriate template and environment
        if script_type == "sh":
            template = self.sh_env.get_template("base.sh.j2")
        elif script_type == "ps1":
            template = self.ps1_env.get_template("base.ps1.j2")
        else:
            raise ValueError(f"Unknown script type: {script_type}")

        # Render and write
        content = template.render(**config)
        output_path.write_text(content)

        # Make executable if it's a shell script
        if script_type == "sh":
            output_path.chmod(output_path.stat().st_mode | 0o111)

    def generate_both_scripts(
        self,
        project_name: str,
        project_dir: Path,
        **kwargs: Any,
    ) -> tuple[Path, Path]:
        """Generate both env.sh and env.ps1 scripts.

        Returns:
            Tuple of (env.sh path, env.ps1 path)
        """
        sh_path = project_dir / "env.sh"
        ps1_path = project_dir / "env.ps1"

        self.generate_env_script(project_name, sh_path, "sh", **kwargs)
        self.generate_env_script(project_name, ps1_path, "ps1", **kwargs)

        return sh_path, ps1_path


def create_project_env_scripts(project_dir: Path, workenv_name: str | None = None) -> tuple[Path, Path]:
    """Create environment scripts for a project based on its pyproject.toml.

    Args:
        project_dir: The project directory
        workenv_name: Optional workenv name override

    Returns:
        Tuple of (env.sh path, env.ps1 path)
    """
    pyproject_path = project_dir / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"No pyproject.toml found in {project_dir}")

    # Parse project name from pyproject.toml
    from provide.foundation.file.formats import read_toml

    pyproject = read_toml(pyproject_path)

    project_name = pyproject.get("project", {}).get("name", project_dir.name)
    python_requirement = pyproject.get("project", {}).get("requires-python")

    # Additional config for wrknv projects
    extra_config = {}
    if workenv_name:
        extra_config["workenv_name"] = workenv_name
        extra_config["venv_prefix"] = workenv_name

    # Add Python requirement if present
    if python_requirement:
        extra_config["python_requirement"] = python_requirement

    # Get wrknv configuration
    from wrknv.config import WorkenvConfig

    config = WorkenvConfig.load()
    env_config = config.get_env_config()

    # Use configuration from wrknv.toml if available
    if env_config:
        logger.info("Using env configuration from wrknv.toml", env_config=env_config)
        extra_config["include_tool_verification"] = env_config.get("include_tool_verification", True)

        # Handle new unified siblings format
        siblings_config = env_config.get("siblings", [])
        if siblings_config:
            extra_config["siblings"] = siblings_config
            # Keep backward compatibility
            extra_config["sibling_patterns"] = []
            extra_config["special_siblings"] = []
        else:
            # Backward compatibility with old format
            extra_config["sibling_patterns"] = env_config.get("sibling_patterns", [])
            extra_config["special_siblings"] = env_config.get("special_siblings", [])
            extra_config["siblings"] = []
    else:
        # Default configuration - empty by default
        logger.info("No env configuration found in wrknv.toml, using defaults")
        extra_config["include_tool_verification"] = True
        extra_config["sibling_patterns"] = []
        extra_config["special_siblings"] = []
        extra_config["siblings"] = []

    # Generate scripts
    generator = EnvScriptGenerator()
    sh_path, ps1_path = generator.generate_both_scripts(project_name, project_dir, **extra_config)

    print_success(f"Generated {sh_path}", Emoji.SUCCESS)
    print_success(f"Generated {ps1_path}", Emoji.SUCCESS)

    return sh_path, ps1_path


# 🧰🌍🔚
