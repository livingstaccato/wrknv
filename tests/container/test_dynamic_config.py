#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from provide.testkit import FoundationTestCase
import pytest

#!/usr/bin/env python3

"""
Test suite for dynamic container configuration.
"""

from provide.testkit.mocking import MagicMock, patch

from wrknv.config import WorkenvConfig
from wrknv.container.manager import ContainerManager
from wrknv.wenv.schema import ContainerConfig


@pytest.mark.container
class TestDynamicContainerConfiguration(FoundationTestCase):
    """Test that container manager uses dynamic configuration from wrknv.toml."""

    def test_default_container_config(self) -> None:
        """Test container manager with default configuration."""
        from wrknv.container.manager import create_container_manager

        manager = create_container_manager()

        assert manager.container_name == "wrknv-dev"
        assert manager.image_name == "wrknv-dev"
        assert manager.container_config is not None
        assert not manager.container_config.enabled

    def test_custom_project_name(self) -> None:
        """Test container manager with custom project name."""
        config = WorkenvConfig(project_name="my-awesome-project", container=ContainerConfig(enabled=True))

        manager = ContainerManager(config)

        assert manager.container_name == "my-awesome-project-dev"
        assert manager.image_name == "my-awesome-project-dev"

    def test_dockerfile_with_default_config(self) -> None:
        """Test Dockerfile generation with default configuration."""
        from wrknv.container.manager import create_container_manager

        manager = create_container_manager()
        dockerfile = manager._generate_dockerfile()

        assert "FROM ubuntu:22.04" in dockerfile
        assert "python3.11" in dockerfile
        assert "curl" in dockerfile
        assert "git" in dockerfile

    def test_dockerfile_with_custom_config(self) -> None:
        """Test Dockerfile generation with custom configuration."""
        config = WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(
                enabled=True,
                base_image="python:3.12-slim",
                python_version="3.12",
                additional_packages=["nodejs", "npm", "postgresql-client"],
                environment={"NODE_ENV": "development", "DEBUG": "true"},
            ),
        )

        manager = ContainerManager(config)
        dockerfile = manager._generate_dockerfile()

        # Check base image
        assert "FROM python:3.12-slim" in dockerfile

        # Python packages are not installed when using Python base image

        # Check additional packages
        assert "nodejs" in dockerfile
        assert "npm" in dockerfile
        assert "postgresql-client" in dockerfile

        # Check environment variables
        assert "ENV NODE_ENV=development" in dockerfile
        assert "ENV DEBUG=true" in dockerfile

    @pytest.mark.skip(reason="Needs refactoring to use attrs mock factory pattern")
    @patch("provide.foundation.process.run")
    @patch("wrknv.container.manager.ContainerManager.container_running")
    @patch("wrknv.container.manager.ContainerManager.container_exists")
    @patch("wrknv.container.manager.ContainerManager.image_exists")
    def test_start_with_custom_volumes_and_ports(
        self, mock_image_exists, mock_container_exists, mock_container_running, mock_run
    ) -> None:
        """Test container start with custom volumes and ports."""
        mock_image_exists.return_value = True
        mock_container_exists.return_value = False
        mock_container_running.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        config = WorkenvConfig(
            project_name="test-project",
            container=ContainerConfig(
                enabled=True,
                volumes=["/data:/data", "/logs:/logs"],
                ports=["8080:80", "5432:5432"],
                environment={"API_KEY": "secret123"},
            ),
        )

        manager = ContainerManager(config)
        manager.start()

        # Check that docker run was called
        assert mock_run.called

        # Get the command that was executed
        cmd = mock_run.call_args[0][0]

        # Check container name
        assert "test-project-dev" in cmd

        # Check custom volumes
        assert "/data:/data" in cmd
        assert "/logs:/logs" in cmd

        # Check custom ports
        assert "8080:80" in cmd
        assert "5432:5432" in cmd

        # Check custom environment variable
        assert "API_KEY=secret123" in cmd

        # Check default volumes are still included
        assert "/host-home" in " ".join(cmd)
        assert "/var/run/docker.sock:/var/run/docker.sock" in " ".join(cmd)

    def test_container_config_from_toml(self) -> None:
        """Test loading container configuration from TOML-like structure."""
        config_dict = {
            "project_name": "web-app",
            "container": {
                "enabled": True,
                "base_image": "node:18-alpine",
                "python_version": "3.11",
                "additional_packages": ["redis-tools", "mysql-client"],
                "environment": {
                    "DATABASE_URL": "postgresql://localhost/mydb",
                    "REDIS_URL": "redis://localhost:6379",
                },
                "volumes": ["/app/data:/data"],
                "ports": ["3000:3000", "5000:5000"],
            },
        }

        # This would normally come from loading a TOML file
        import cattrs

        converter = cattrs.Converter()
        config = converter.structure(config_dict, WorkenvConfig)

        manager = ContainerManager(config)

        assert manager.container_name == "web-app-dev"
        assert manager.container_config.enabled
        assert manager.container_config.base_image == "node:18-alpine"
        assert len(manager.container_config.additional_packages) == 2
        assert len(manager.container_config.environment) == 2
        assert len(manager.container_config.volumes) == 1
        assert len(manager.container_config.ports) == 2

    def test_dockerfile_python_version_formatting(self) -> None:
        """Test that Python version is correctly formatted in Dockerfile."""
        test_cases = [
            ("3.11", "python3.11"),
            ("3.12", "python3.12"),
            ("3.10", "python3.10"),
        ]

        for py_version, expected_package in test_cases:
            config = WorkenvConfig(project_name="test", container=ContainerConfig(python_version=py_version))

            manager = ContainerManager(config)
            dockerfile = manager._generate_dockerfile()

            # Check that Python version is installed (without -pip, just -venv)
            assert expected_package in dockerfile
            assert f"{expected_package}-venv" in dockerfile


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# 🧰🌍🔚
