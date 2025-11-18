#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from provide.testkit import FoundationTestCase
import pytest

#!/usr/bin/env python3
"""Test container runtime implementations."""

from provide.foundation.process import CompletedProcess, ProcessError
from provide.testkit.mocking import patch

from wrknv.container.runtime.docker import DockerRuntime


@pytest.mark.container
class TestDockerRuntime(FoundationTestCase):
    """Test Docker runtime implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.runtime = DockerRuntime(runtime_name="docker", runtime_command="docker")

    @patch("wrknv.container.runtime.docker.run")
    def test_run_container(self, mock_run) -> None:
        """Test starting a new container."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "run"], returncode=0, stdout="abc123container", stderr=""
        )

        result = self.runtime.run_container(
            image="ubuntu:latest",
            name="test-container",
            detach=True,
            volumes=["/host:/container"],
            environment={"KEY": "value"},
            ports=["8080:80"],
            workdir="/app",
            command=["echo", "hello"],
        )

        assert result.stdout == "abc123container"
        mock_run.assert_called_once()

        # Check command construction
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "docker"
        assert cmd[1] == "run"
        assert "-d" in cmd
        assert "--name" in cmd
        assert "test-container" in cmd
        assert "-v" in cmd
        assert "/host:/container" in cmd
        assert "-e" in cmd
        assert "KEY=value" in cmd
        assert "-p" in cmd
        assert "8080:80" in cmd
        assert "--workdir" in cmd
        assert "/app" in cmd
        assert "ubuntu:latest" in cmd
        assert "echo" in cmd
        assert "hello" in cmd

    @patch("wrknv.container.runtime.docker.run")
    def test_start_container(self, mock_run) -> None:
        """Test starting an existing container."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "start"], returncode=0, stdout="test-container", stderr=""
        )

        result = self.runtime.start_container("test-container")

        assert result.stdout == "test-container"
        mock_run.assert_called_once_with(["docker", "start", "test-container"], check=True)

    @patch("wrknv.container.runtime.docker.run")
    def test_stop_container(self, mock_run) -> None:
        """Test stopping a container."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "stop"], returncode=0, stdout="test-container", stderr=""
        )

        self.runtime.stop_container("test-container", timeout=15)

        mock_run.assert_called_once_with(["docker", "stop", "-t", "15", "test-container"], check=True)

    @patch("wrknv.container.runtime.docker.run")
    def test_container_exists_true(self, mock_run) -> None:
        """Test checking if container exists - found case."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "ps"], returncode=0, stdout="container1\ntest-container\ncontainer3", stderr=""
        )

        exists = self.runtime.container_exists("test-container")

        assert exists
        mock_run.assert_called_once_with(["docker", "ps", "-a", "--format", "{{.Names}}"], check=False)

    @patch("wrknv.container.runtime.docker.run")
    def test_container_exists_false(self, mock_run) -> None:
        """Test checking if container exists - not found case."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "ps"], returncode=0, stdout="container1\ncontainer2", stderr=""
        )

        exists = self.runtime.container_exists("test-container")

        assert not exists

    @patch("wrknv.container.runtime.docker.run")
    def test_container_running(self, mock_run) -> None:
        """Test checking if container is running."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "ps"], returncode=0, stdout="test-container\nother-container", stderr=""
        )

        running = self.runtime.container_running("test-container")

        assert running
        mock_run.assert_called_once_with(["docker", "ps", "--format", "{{.Names}}"], check=False)

    @patch("wrknv.container.runtime.docker.run")
    def test_exec_in_container(self, mock_run) -> None:
        """Test executing command in container."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "exec"], returncode=0, stdout="command output", stderr=""
        )

        result = self.runtime.exec_in_container(
            name="test-container",
            command=["ls", "-la"],
            interactive=True,
            tty=True,
            user="root",
            workdir="/app",
            environment={"VAR": "value"},
        )

        assert result.stdout == "command output"

        cmd = mock_run.call_args[0][0]
        assert "-i" in cmd
        assert "-t" in cmd
        assert "-u" in cmd
        assert "root" in cmd
        assert "-w" in cmd
        assert "/app" in cmd
        assert "-e" in cmd
        assert "VAR=value" in cmd
        assert "test-container" in cmd
        assert "ls" in cmd
        assert "-la" in cmd

    @patch("wrknv.container.runtime.docker.run")
    def test_build_image(self, mock_run) -> None:
        """Test building a Docker image."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "build"], returncode=0, stdout="Successfully built abc123", stderr=""
        )

        result = self.runtime.build_image(
            dockerfile="Dockerfile",
            tag="myapp:latest",
            context=".",
            build_args={"VERSION": "1.0"},
            no_cache=True,
            platform="linux/amd64",
        )

        assert "Successfully built" in result.stdout

        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "docker"
        assert cmd[1] == "build"
        assert "-f" in cmd
        assert "Dockerfile" in cmd
        assert "-t" in cmd
        assert "myapp:latest" in cmd
        assert "--build-arg" in cmd
        assert "VERSION=1.0" in cmd
        assert "--no-cache" in cmd
        assert "--platform" in cmd
        assert "linux/amd64" in cmd
        assert "." in cmd

    @patch("wrknv.container.runtime.docker.run")
    def test_list_containers(self, mock_run) -> None:
        """Test listing containers."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "ps"],
            returncode=0,
            stdout='{"Name":"container1","Status":"running"}\n{"Name":"container2","Status":"stopped"}',
            stderr="",
        )

        containers = self.runtime.list_containers(all=True)

        assert len(containers) == 2
        assert containers[0]["Name"] == "container1"
        assert containers[1]["Name"] == "container2"

        mock_run.assert_called_once_with(["docker", "ps", "--format", "json", "-a"], check=True)

    @patch("wrknv.container.runtime.docker.run")
    def test_error_handling(self, mock_run) -> None:
        """Test error handling when command fails."""
        mock_run.side_effect = ProcessError(
            message="Error: No such container: nonexistent",
            command=["docker", "start", "nonexistent"],
            returncode=1,
            stdout="",
            stderr="Error: No such container: nonexistent",
        )

        with pytest.raises(ProcessError) as exc_info:
            self.runtime.start_container("nonexistent")

        assert "nonexistent" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# 🧰🌍🔚
