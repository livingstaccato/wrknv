#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Display convenience helpers for `WorkenvConfig`."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wrknv.config.core import WorkenvConfig


class WorkenvConfigDisplay:
    """Handles displaying configuration information."""

    def __init__(self, config: WorkenvConfig) -> None:
        """Initialize display handler with config instance."""
        self.config = config

    def show_config(self) -> None:
        """Display configuration in a readable format."""
        from provide.foundation.cli import echo_info, echo_success

        echo_success(f"Configuration: {self.config.config_path}")

        # Project metadata
        project_name = self.config.project_name or "(not set)"
        version = self.config.version or "(not set)"
        echo_info(f"  Project: {project_name} v{version}")

        if self.config.description:
            echo_info(f"  Description: {self.config.description}")

        if self.config.tools:
            echo_info("\n  Tools:")
            for tool, config in self.config.tools.items():
                version = config.get("version", "latest") if isinstance(config, dict) else config
                echo_info(f"    {tool}: {version}")

        if self.config.profiles:
            echo_info("\n  Profiles:")
            for profile in self.config.profiles:
                echo_info(f"    - {profile}")

        echo_info("\n  Settings:")
        echo_info(f"    auto_install: {self.config.workenv.auto_install}")
        echo_info(f"    use_cache: {self.config.workenv.use_cache}")
        echo_info(f"    cache_ttl: {self.config.workenv.cache_ttl}")
        echo_info(f"    log_level: {self.config.workenv.log_level}")
        echo_info(f"    container_runtime: {self.config.workenv.container_runtime}")
        echo_info(f"    container_registry: {self.config.workenv.container_registry}")

        if self.config.container:
            echo_info("\n  Container:")
            echo_info(f"    enabled: {self.config.container.enabled}")
            echo_info(f"    base_image: {self.config.container.base_image}")
            echo_info(f"    python_version: {self.config.container.python_version}")
            if self.config.container.volumes:
                echo_info(f"    volumes: {len(self.config.container.volumes)} configured")
            if self.config.container.environment:
                echo_info(f"    environment: {len(self.config.container.environment)} variables")

        if self.config.env:
            echo_info("\n  Environment:")
            for key, value in self.config.env.items():
                if isinstance(value, dict):
                    echo_info(f"    {key}: {len(value)} items")
                else:
                    echo_info(f"    {key}: {value}")

        if self.config.gitignore:
            echo_info("\n  Gitignore:")
            for key, value in self.config.gitignore.items():
                if isinstance(value, list):
                    echo_info(f"    {key}: {len(value)} patterns")
                else:
                    echo_info(f"    {key}: {value}")


# 🧰🌍🔚
