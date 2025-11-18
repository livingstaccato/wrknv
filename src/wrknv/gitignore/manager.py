#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Gitignore Manager
=================
Central manager for gitignore operations."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from provide.foundation import logger

from .builder import GitignoreBuilder
from .detector import ProjectDetector
from .templates import TemplateHandler

if TYPE_CHECKING:
    from wrknv.wenv.schema import GitignoreConfig


class GitignoreManager:
    """Manages gitignore file generation and updates."""

    def __init__(
        self,
        project_dir: Path | None = None,
        output_path: Path | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        """
        Initialize the manager.

        Args:
            project_dir: Project directory to work with
            output_path: Custom output path for gitignore file
            cache_dir: Custom cache directory for templates
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.gitignore_path = output_path or self.project_dir / ".gitignore"
        self.template_handler = TemplateHandler(cache_dir=cache_dir)
        self.detector = ProjectDetector()

        logger.debug(f"GitignoreManager initialized for project: {self.project_dir}")
        logger.debug(f"Gitignore path: {self.gitignore_path}")

    def build_from_templates(
        self,
        templates: list[str],
        custom_rules: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        append: bool = False,
        project_name: str | None = None,
    ) -> bool:
        """
        Build gitignore from specified templates.

        Args:
            templates: List of template names
            custom_rules: Custom rules to add
            exclude_patterns: Patterns to exclude from templates
            append: Whether to append to existing file
            project_name: Project name for header

        Returns:
            True if successful
        """
        logger.info(f"Building gitignore from templates: {templates}")

        builder = GitignoreBuilder()

        # Add header unless appending
        if not append:
            builder.add_header(project_name=project_name)

        # Add template sections
        for template_name in templates:
            content = self.template_handler.get_template(template_name)
            if content:
                # Filter excluded patterns
                if exclude_patterns:
                    lines = content.split("\n")
                    filtered_lines = []
                    for line in lines:
                        if not any(pattern in line for pattern in exclude_patterns):
                            filtered_lines.append(line)
                    content = "\n".join(filtered_lines)

                builder.add_template_section(template_name, content)
                logger.debug(f"Added template: {template_name}")
            else:
                logger.warning(f"Template '{template_name}' not found")

        # Add wrknv section
        builder.add_wrknv_section()

        # Add provide ecosystem section
        builder.add_provide_section()

        # Add custom rules
        if custom_rules:
            builder.add_custom_rules(custom_rules)

        # Build or merge
        if append and self.gitignore_path.exists():
            # Append mode - merge with existing
            existing_content = self.gitignore_path.read_text()
            new_content = builder.build()
            final_content = existing_content + "\n\n" + new_content
        elif self.gitignore_path.exists():
            # Overwrite mode but preserve custom rules
            final_content = builder.merge_with_existing(self.gitignore_path)
        else:
            # New file
            final_content = builder.build()

        # Write the file
        self.gitignore_path.write_text(final_content)
        logger.info(f"Successfully wrote gitignore to {self.gitignore_path}")

        return True

    def build_from_detection(
        self,
        custom_rules: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        max_depth: int = 5,
    ) -> bool:
        """
        Build gitignore from auto-detection.

        Args:
            custom_rules: Custom rules to add
            exclude_patterns: Patterns to exclude
            max_depth: Maximum scan depth

        Returns:
            True if successful
        """
        logger.info("Building gitignore from auto-detection")

        # Scan project
        self.detector.reset()
        self.detector.scan_directory(self.project_dir, max_depth=max_depth)

        # Get suggested templates
        templates = self.detector.suggest_templates()

        if not templates:
            logger.warning("No templates detected")
            return False

        logger.info(f"Auto-detected templates: {templates}")

        # Build from detected templates
        return self.build_from_templates(
            templates=templates,
            custom_rules=custom_rules,
            exclude_patterns=exclude_patterns,
            project_name=self.project_dir.name,
        )

    def build_from_config(self, config: GitignoreConfig) -> bool:
        """
        Build gitignore from configuration object.

        Args:
            config: GitignoreConfig object

        Returns:
            True if successful
        """
        logger.info("Building gitignore from configuration")

        return self.build_from_templates(
            templates=config.templates,
            custom_rules=config.custom_rules if hasattr(config, "custom_rules") else None,
            exclude_patterns=config.exclude_patterns if hasattr(config, "exclude_patterns") else None,
            append=False,
        )

    def add_templates(
        self,
        templates: list[str],
        custom_rules: list[str] | None = None,
    ) -> bool:
        """
        Add templates to existing gitignore.

        Args:
            templates: Templates to add
            custom_rules: Additional custom rules

        Returns:
            True if successful
        """
        logger.info(f"Adding templates to existing gitignore: {templates}")

        return self.build_from_templates(
            templates=templates,
            custom_rules=custom_rules,
            append=True,
        )

    def list_available_templates(self, category: str | None = None) -> list[str]:
        """
        List available templates.

        Args:
            category: Optional category filter

        Returns:
            List of template names
        """
        return self.template_handler.list_templates(category=category)

    def search_templates(self, pattern: str) -> list[str]:
        """
        Search for templates.

        Args:
            pattern: Search pattern

        Returns:
            List of matching template names
        """
        return self.template_handler.search_templates(pattern)

    def update_templates(self, force: bool = False) -> bool:
        """
        Update template cache from GitHub.

        Args:
            force: Force update even if cache is valid

        Returns:
            True if updated
        """
        logger.info("Updating gitignore templates")
        return self.template_handler.update_cache(force=force)

    def preview(
        self,
        templates: list[str],
        custom_rules: list[str] | None = None,
    ) -> str:
        """
        Preview what would be generated.

        Args:
            templates: Templates to preview
            custom_rules: Custom rules to include

        Returns:
            Preview content
        """
        if not templates:
            return "No templates specified"

        builder = GitignoreBuilder()
        builder.add_header()

        for template_name in templates:
            content = self.template_handler.get_template(template_name)
            if content:
                builder.add_template_section(template_name, content)

        builder.add_wrknv_section()
        builder.add_provide_section()

        if custom_rules:
            builder.add_custom_rules(custom_rules)

        return builder.build()

    def get_detection_report(self) -> str:
        """
        Get a report of detected project characteristics.

        Returns:
            Detection report as string
        """
        self.detector.reset()
        self.detector.scan_directory(self.project_dir)

        report_lines = ["Project Detection Report", "=" * 24, ""]

        if self.detector.detected_languages:
            report_lines.append(f"Languages: {', '.join(sorted(self.detector.detected_languages))}")

        if self.detector.detected_frameworks:
            report_lines.append(f"Frameworks: {', '.join(sorted(self.detector.detected_frameworks))}")

        if self.detector.detected_tools:
            report_lines.append(f"Tools: {', '.join(sorted(self.detector.detected_tools))}")

        if self.detector.detected_os:
            report_lines.append(f"OS: {', '.join(sorted(self.detector.detected_os))}")

        if not any(
            [
                self.detector.detected_languages,
                self.detector.detected_frameworks,
                self.detector.detected_tools,
                self.detector.detected_os,
            ]
        ):
            report_lines.append("No project characteristics detected")

        return "\n".join(report_lines)


# 🧰🌍🔚
