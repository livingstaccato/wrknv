#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#


from __future__ import annotations

from provide.testkit import FoundationTestCase
import pytest

#!/usr/bin/env python3
"""Test container operations modules."""

from pathlib import Path
from unittest.mock import MagicMock

from provide.foundation.process import CompletedProcess, ProcessError
from provide.testkit.mocking import patch
from rich.console import Console

from wrknv.container.operations.build import ContainerBuilder
from wrknv.container.operations.exec import ContainerExec
from wrknv.container.operations.lifecycle import ContainerLifecycle
from wrknv.container.operations.logs import ContainerLogs
from wrknv.container.operations.volumes import VolumeManager
from wrknv.container.runtime.docker import DockerRuntime


@pytest.mark.container
class TestContainerLifecycle(FoundationTestCase):
    """Test container lifecycle operations."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.runtime = DockerRuntime(runtime_name="docker", runtime_command="docker")
        self.lifecycle = ContainerLifecycle(
            runtime=self.runtime,
            container_name="test-container",
            console=Console(),
            start_emoji="🚀",
            stop_emoji="⏹️",
            restart_emoji="🔄",
            status_emoji="📊",
        )

    @patch("wrknv.container.runtime.docker.run")
    def test_start_existing_container(self, mock_run) -> None:
        """Test starting an existing container."""
        # Container exists
        mock_run.side_effect = [
            CompletedProcess(args=["docker", "ps"], returncode=0, stdout="test-container", stderr=""),
            # Container not running
            CompletedProcess(args=["docker", "ps"], returncode=0, stdout="", stderr=""),
            # Start container
            CompletedProcess(args=["docker", "start"], returncode=0, stdout="test-container", stderr=""),
        ]

        result = self.lifecycle.start(create_if_missing=False)

        assert result
        assert mock_run.call_count == 3

    @patch("wrknv.container.runtime.docker.run")
    def test_start_create_new_container(self, mock_run) -> None:
        """Test creating and starting a new container."""
        # Container doesn't exist
        mock_run.side_effect = [
            CompletedProcess(args=["docker", "ps"], returncode=0, stdout="", stderr=""),
            # Create container
            CompletedProcess(args=["docker", "run"], returncode=0, stdout="abc123", stderr=""),
        ]

        result = self.lifecycle.start(
            create_if_missing=True,
            image="ubuntu:latest",
            volumes=["/host:/container"],
            environment={"KEY": "value"},
        )

        assert result
        assert mock_run.call_count == 2

    @patch("wrknv.container.runtime.docker.run")
    def test_stop_container(self, mock_run) -> None:
        """Test stopping a container."""
        # Container is running
        mock_run.side_effect = [
            CompletedProcess(args=["docker", "ps"], returncode=0, stdout="test-container", stderr=""),
            # Stop container
            CompletedProcess(args=["docker", "stop"], returncode=0, stdout="test-container", stderr=""),
        ]

        result = self.lifecycle.stop(timeout=10)

        assert result
        assert mock_run.call_count == 2

    @patch("wrknv.container.runtime.docker.run")
    def test_restart_container(self, mock_run) -> None:
        """Test restarting a container."""
        # Container is running (for stop check)
        mock_run.side_effect = [
            # Check if running (for restart)
            CompletedProcess(args=["docker", "ps"], returncode=0, stdout="test-container", stderr=""),
            # Check if running again (for stop)
            CompletedProcess(args=["docker", "ps"], returncode=0, stdout="test-container", stderr=""),
            # Stop container
            CompletedProcess(args=["docker", "stop"], returncode=0, stdout="test-container", stderr=""),
            # Check if container exists (for start)
            CompletedProcess(args=["docker", "ps", "-a"], returncode=0, stdout="test-container", stderr=""),
            # Check if running (should be stopped)
            CompletedProcess(args=["docker", "ps"], returncode=0, stdout="", stderr=""),
            # Start container
            CompletedProcess(args=["docker", "start"], returncode=0, stdout="test-container", stderr=""),
        ]

        result = self.lifecycle.restart(timeout=10)

        assert result
        assert mock_run.call_count == 6

    @patch("wrknv.container.runtime.docker.run")
    def test_status(self, mock_run) -> None:
        """Test getting container status."""
        mock_run.side_effect = [
            # Container exists
            CompletedProcess(args=["docker", "ps"], returncode=0, stdout="test-container", stderr=""),
            # Container is running
            CompletedProcess(args=["docker", "ps"], returncode=0, stdout="test-container", stderr=""),
            # Container inspect
            CompletedProcess(
                args=["docker", "inspect"],
                returncode=0,
                stdout='[{"Id": "abc123", "State": {"Running": true}}]',
                stderr="",
            ),
        ]

        status = self.lifecycle.status()

        assert status["exists"]
        assert status["running"]
        assert "id" in status
        assert mock_run.call_count == 3


@pytest.mark.container
class TestContainerExec(FoundationTestCase):
    """Test container exec operations."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.runtime = DockerRuntime(runtime_name="docker", runtime_command="docker")
        self.exec = ContainerExec(
            runtime=self.runtime,
            container_name="test-container",
            console=Console(),
            available_shells=["/bin/bash", "/bin/sh"],
            default_shell="/bin/sh",
        )

    @patch("wrknv.container.runtime.docker.run")
    def test_run_command(self, mock_run) -> None:
        """Test running a command in container."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "exec"], returncode=0, stdout="command output", stderr=""
        )

        result = self.exec.run_command(command=["echo", "hello"], capture_output=True)

        assert result == "command output"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "exec" in cmd
        assert "test-container" in cmd
        assert "echo" in cmd
        assert "hello" in cmd

    @patch("wrknv.container.runtime.docker.run")
    def test_find_shell(self, mock_run) -> None:
        """Test finding available shell."""
        # First shell fails, second succeeds
        mock_run.side_effect = [
            ProcessError(message="bash not found", command=["docker", "exec"], returncode=127),
            CompletedProcess(args=["docker", "exec"], returncode=0, stdout="/bin/sh", stderr=""),
        ]

        shell = self.exec._detect_shell()

        assert shell == "/bin/sh"
        assert mock_run.call_count == 2

    @patch("wrknv.container.runtime.docker.run")
    @patch("subprocess.run")
    def test_enter_container(self, mock_subprocess_run, mock_run) -> None:
        """Test entering container interactively."""
        # Mock container running and shell detection
        mock_run.side_effect = [
            # Container is running check
            CompletedProcess(args=["docker", "ps"], returncode=0, stdout="test-container", stderr=""),
            # Shell detection (test -f /bin/bash)
            CompletedProcess(args=["docker", "exec"], returncode=0, stdout="", stderr=""),
        ]
        # Mock subprocess.run for the interactive exec (returns a mock result with returncode=0)
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        result = self.exec.enter(shell=None)

        assert result
        assert mock_run.call_count == 2  # Container running + shell detection
        mock_subprocess_run.assert_called_once()
        # Check that subprocess.run was called with a list of args (not a shell string)
        call_args = mock_subprocess_run.call_args
        cmd_list = call_args[0][0]  # First positional arg is the command list
        assert isinstance(cmd_list, list)
        assert "docker" in cmd_list
        assert "exec" in cmd_list
        assert "-i" in cmd_list
        assert "-t" in cmd_list
        assert "test-container" in cmd_list
        assert "/bin/bash" in cmd_list


@pytest.mark.container
class TestContainerBuilder(FoundationTestCase):
    """Test container build operations."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.runtime = DockerRuntime(runtime_name="docker", runtime_command="docker")
        self.builder = ContainerBuilder(runtime=self.runtime, console=Console())

    @patch("wrknv.container.runtime.docker.run")
    def test_build_simple(self, mock_run) -> None:
        """Test simple build."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "build"], returncode=0, stdout="Successfully built abc123", stderr=""
        )

        result = self.builder.build(
            dockerfile="Dockerfile", tag="myapp:latest", context=".", build_args=None, stream_output=False
        )

        assert result
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "build" in cmd
        assert "-f" in cmd
        assert "Dockerfile" in cmd
        assert "-t" in cmd
        assert "myapp:latest" in cmd
        assert "." in cmd

    @patch("wrknv.container.runtime.docker.run")
    def test_build_with_args(self, mock_run) -> None:
        """Test build with build args."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "build"], returncode=0, stdout="Successfully built abc123", stderr=""
        )

        result = self.builder.build(
            dockerfile="Dockerfile",
            tag="myapp:latest",
            context=".",
            build_args={"VERSION": "1.0", "ENV": "production"},
            stream_output=False,
            no_cache=True,
            platform="linux/amd64",
        )

        assert result
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "--build-arg" in cmd
        assert "VERSION=1.0" in cmd
        assert "ENV=production" in cmd
        assert "--no-cache" in cmd
        assert "--platform" in cmd
        assert "linux/amd64" in cmd

    @patch("wrknv.container.operations.build.stream")
    def test_build_with_stream(self, mock_stream) -> None:
        """Test build with streaming output."""
        mock_stream.return_value = iter(
            ["Step 1/5 : FROM ubuntu:latest", "Step 2/5 : RUN apt-get update", "Successfully built abc123"]
        )

        result = self.builder.build(
            dockerfile="Dockerfile", tag="myapp:latest", context=".", build_args=None, stream_output=True
        )

        assert result
        mock_stream.assert_called_once()


@pytest.mark.container
class TestContainerLogs(FoundationTestCase):
    """Test container logs operations."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.runtime = DockerRuntime(runtime_name="docker", runtime_command="docker")
        self.logs = ContainerLogs(runtime=self.runtime, container_name="test-container", console=Console())

    @patch("wrknv.container.runtime.docker.run")
    def test_get_logs(self, mock_run) -> None:
        """Test getting container logs."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "logs"], returncode=0, stdout="Log line 1\nLog line 2\nLog line 3", stderr=""
        )

        result = self.logs.get_logs(follow=False, tail=10, since="5m", timestamps=True)

        assert result == "Log line 1\nLog line 2\nLog line 3"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "logs" in cmd
        assert "--tail" in cmd
        assert "10" in cmd
        assert "--since" in cmd
        assert "5m" in cmd
        # Note: timestamps is handled in stream_logs, not get_logs
        assert "test-container" in cmd

    @patch("wrknv.container.operations.logs.stream")
    def test_stream_logs(self, mock_stream) -> None:
        """Test streaming container logs."""
        mock_stream.return_value = iter(
            [
                "2024-01-01T00:00:00 Log line 1",
                "2024-01-01T00:00:01 Log line 2",
                "2024-01-01T00:00:02 Log line 3",
            ]
        )

        lines = list(self.logs.stream_logs(tail=10, since=None, timestamps=False))

        assert len(lines) == 3
        assert "Log line 1" in lines[0]
        mock_stream.assert_called_once()


@pytest.mark.container
class TestVolumeManager(FoundationTestCase):
    """Test volume management operations."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.runtime = DockerRuntime(runtime_name="docker", runtime_command="docker")
        self.volumes = VolumeManager(runtime=self.runtime, console=Console(), backup_dir=Path("/tmp/backups"))

    @patch("wrknv.container.operations.volumes.run")
    def test_create_volume(self, mock_run) -> None:
        """Test creating a volume."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "volume", "create"], returncode=0, stdout="test-volume", stderr=""
        )

        result = self.volumes.create_volume(
            name="test-volume", driver="local", options={"type": "tmpfs", "device": "tmpfs"}
        )

        assert result
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "volume" in cmd
        assert "create" in cmd
        assert "--driver" in cmd
        assert "local" in cmd
        assert "--opt" in cmd
        assert "type=tmpfs" in cmd
        assert "test-volume" in cmd

    @patch("wrknv.container.operations.volumes.run")
    def test_list_volumes(self, mock_run) -> None:
        """Test listing volumes."""
        mock_run.return_value = CompletedProcess(
            args=["docker", "volume", "ls"],
            returncode=0,
            stdout='{"Name":"vol1","Driver":"local"}\n{"Name":"vol2","Driver":"local"}',
            stderr="",
        )

        volumes = self.volumes.list_volumes(filter_label=None)

        assert len(volumes) == 2
        assert volumes[0]["Name"] == "vol1"
        assert volumes[1]["Name"] == "vol2"
        mock_run.assert_called_once()

    @patch("wrknv.container.operations.volumes.run")
    def test_backup_volume(self, mock_run) -> None:
        """Test backing up a volume."""
        mock_run.return_value = CompletedProcess(args=["docker", "run"], returncode=0, stdout="", stderr="")

        backup_file = self.volumes.backup_volume(
            volume_name="test-volume", container_name="test-container", mount_path="/data"
        )

        assert backup_file is not None
        assert str(backup_file).startswith("/tmp/backups")
        assert "test-volume" in str(backup_file)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "run" in cmd
        assert "--rm" in cmd
        assert "-v" in cmd
        assert "test-volume:/data" in cmd
        assert "alpine" in cmd
        assert "tar" in cmd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# 🧰🌍🔚
