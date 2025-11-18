#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Build Operations
==========================
Build container images with streaming output."""

from __future__ import annotations

from typing import Any

from attrs import define
from provide.foundation import logger
from provide.foundation.process import ProcessError, stream
from rich.console import Console

from wrknv.container.runtime.base import ContainerRuntime
from wrknv.wenv.schema import ContainerConfig


@define
class ContainerBuilder:
    """Handles container build operations."""

    runtime: ContainerRuntime
    console: Console

    def build(
        self,
        dockerfile: str,
        tag: str,
        context: str,
        build_args: dict[str, str] | None,
        stream_output: bool,
        **extra_options: Any,
    ) -> bool:
        """Build a container image.

        Args:
            dockerfile: Path to Dockerfile
            tag: Image tag
            context: Build context directory
            build_args: Build arguments
            stream_output: Whether to stream build output
            **extra_options: Runtime-specific build options

        Returns:
            True if build successful
        """
        try:
            if stream_output:
                # Build command for streaming
                cmd = self._build_command(
                    dockerfile=dockerfile, tag=tag, context=context, build_args=build_args, **extra_options
                )

                self.console.print(f"[cyan]🔨 Building image {tag}...[/cyan]")

                # Stream build output
                for line in stream(cmd):
                    self.console.print(line, end="")

                logger.info("Image built successfully", tag=tag, dockerfile=dockerfile)
                return True
            else:
                # Use runtime's build method
                self.runtime.build_image(
                    dockerfile=dockerfile, tag=tag, context=context, build_args=build_args, **extra_options
                )

                return True

        except ProcessError as e:
            logger.error(
                "Build failed",
                tag=tag,
                dockerfile=dockerfile,
                error=str(e),
                stderr=e.stderr,
            )
            self.console.print(f"[red]❌ Build failed: {e}[/red]")
            if e.stderr:
                self.console.print(f"[red]{e.stderr}[/red]")
            return False

    def _build_command(
        self,
        dockerfile: str,
        tag: str,
        context: str,
        build_args: dict[str, str] | None,
        **extra_options: Any,
    ) -> list[str]:
        """Construct build command.

        Args:
            dockerfile: Path to Dockerfile
            tag: Image tag
            context: Build context directory
            build_args: Build arguments
            **extra_options: Runtime-specific options

        Returns:
            Command list
        """
        cmd = [self.runtime.runtime_command, "build", "-f", dockerfile, "-t", tag]

        for key, value in (build_args or {}).items():
            cmd.extend(["--build-arg", f"{key}={value}"])

        if extra_options.get("no_cache"):
            cmd.append("--no-cache")
        if extra_options.get("platform"):
            cmd.extend(["--platform", extra_options["platform"]])
        if extra_options.get("pull"):
            cmd.append("--pull")
        if extra_options.get("quiet"):
            cmd.append("--quiet")

        cmd.append(context)
        return cmd

    def tag_image(self, source_tag: str, target_tag: str) -> bool:
        """Tag an existing image.

        Args:
            source_tag: Source image tag
            target_tag: Target image tag

        Returns:
            True if successful
        """
        try:
            from provide.foundation.process import run

            run([self.runtime.runtime_command, "tag", source_tag, target_tag], check=True)

            logger.info("Image tagged", source=source_tag, target=target_tag)
            return True

        except ProcessError as e:
            logger.error(
                "Failed to tag image",
                source=source_tag,
                target=target_tag,
                error=str(e),
            )
            self.console.print(f"[red]❌ Failed to tag image: {e}[/red]")
            return False

    def push_image(self, tag: str) -> bool:
        """Push image to registry.

        Args:
            tag: Image tag to push

        Returns:
            True if successful
        """
        try:
            from provide.foundation.process import run

            self.console.print(f"[cyan]📤 Pushing image {tag}...[/cyan]")

            run([self.runtime.runtime_command, "push", tag], check=True)

            logger.info("Image pushed", tag=tag)
            return True

        except ProcessError as e:
            logger.error("Failed to push image", tag=tag, error=str(e))
            self.console.print(f"[red]❌ Failed to push image: {e}[/red]")
            return False

    def image_exists(self, tag: str) -> bool:
        """Check if an image exists locally.

        Args:
            tag: Image tag to check

        Returns:
            True if image exists
        """
        try:
            from provide.foundation.process import run

            result = run(
                [self.runtime.runtime_command, "images", "--format", "{{.Repository}}:{{.Tag}}"],
                check=False,
            )

            if result.stdout:
                images = result.stdout.strip().splitlines()
                return tag in images

            return False

        except ProcessError:
            return False

    def generate_dockerfile(self, container_config: ContainerConfig) -> str:
        """
        Generate Dockerfile content from configuration.

        Args:
            container_config: Container configuration

        Returns:
            Dockerfile content as string
        """
        # Use configured base image or default
        base_image = container_config.base_image or "ubuntu:22.04"

        # Start with base image
        lines = [f"FROM {base_image}", ""]

        # Set working directory
        lines.extend(["WORKDIR /workspace", ""])

        # Install system packages
        if container_config.additional_packages:
            packages = " ".join(container_config.additional_packages)
            lines.extend(
                [
                    "RUN apt-get update && apt-get install -y \\",
                    f"    {packages} \\",
                    "    && rm -rf /var/lib/apt/lists/*",
                    "",
                ]
            )
        else:
            # Install default packages
            lines.extend(
                [
                    "RUN apt-get update && apt-get install -y \\",
                    "    curl \\",
                    "    git \\",
                    "    && rm -rf /var/lib/apt/lists/*",
                    "",
                ]
            )

        # Install Python if python_version is specified and base image isn't already Python
        if container_config.python_version and not base_image.startswith("python:"):
            py_version = container_config.python_version
            lines.extend(
                [
                    f"RUN apt-get update && apt-get install -y python{py_version} python{py_version}-venv \\",
                    "    && rm -rf /var/lib/apt/lists/*",
                    "",
                ]
            )

        # Set environment variables
        if container_config.environment:
            for key, value in container_config.environment.items():
                lines.append(f"ENV {key}={value}")
            lines.append("")

        # Create user and set ownership
        lines.extend(
            [
                "RUN useradd -m -s /bin/bash user",
                "RUN chown -R user:user /workspace",
                "USER user",
                "",
            ]
        )

        # Keep container running
        lines.extend(
            [
                "# Keep container running",
                'CMD ["sleep", "infinity"]',
            ]
        )

        return "\n".join(lines)


# 🧰🌍🔚
