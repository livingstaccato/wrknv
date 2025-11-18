#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Comprehensive tests for the operations/verify module."""

from __future__ import annotations

import subprocess

from provide.testkit import FoundationTestCase
from provide.testkit.mocking import Mock, patch
import pytest

from wrknv.wenv.operations.verify import (
    check_binary_compatibility,
    get_installed_version_info,
    get_version_command_args,
    parse_generic_version,
    parse_go_version,
    parse_terraform_version,
    parse_tofu_version,
    parse_uv_version,
    run_version_check,
    validate_installation_directory,
    verify_tool_installation,
)


class TestVerifyOperations(FoundationTestCase):
    """Test suite for verification operations."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        super().setup_method()
        self.temp_dir = self.create_temp_dir()
        self.temp_path = self.temp_dir

    # Test verify_tool_installation
    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_verify_tool_installation_success(self, mock_run_check) -> None:
        """Test successful tool installation verification."""
        binary_path = self.temp_path / "bin" / "terraform"
        binary_path.parent.mkdir(parents=True)
        binary_path.touch()

        mock_run_check.return_value = "Terraform v1.5.0"

        result = verify_tool_installation(binary_path, "1.5.0", "terraform")

        assert result
        mock_run_check.assert_called_once_with(binary_path, "terraform")

    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_verify_tool_installation_binary_not_found(self, mock_run_check) -> None:
        """Test verification when binary doesn't exist."""
        binary_path = self.temp_path / "bin" / "terraform"

        result = verify_tool_installation(binary_path, "1.5.0", "terraform")

        assert not result
        mock_run_check.assert_not_called()

    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_verify_tool_installation_version_mismatch(self, mock_run_check) -> None:
        """Test verification with version mismatch."""
        binary_path = self.temp_path / "bin" / "terraform"
        binary_path.parent.mkdir(parents=True)
        binary_path.touch()

        mock_run_check.return_value = "Terraform v1.4.0"

        result = verify_tool_installation(binary_path, "1.5.0", "terraform")

        assert not result

    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_verify_tool_installation_check_fails(self, mock_run_check) -> None:
        """Test verification when version check fails."""
        binary_path = self.temp_path / "bin" / "terraform"
        binary_path.parent.mkdir(parents=True)
        binary_path.touch()

        mock_run_check.return_value = None

        result = verify_tool_installation(binary_path, "1.5.0", "terraform")

        assert not result

    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_verify_tool_installation_exception(self, mock_run_check) -> None:
        """Test verification with exception."""
        binary_path = self.temp_path / "bin" / "terraform"
        binary_path.parent.mkdir(parents=True)
        binary_path.touch()

        mock_run_check.side_effect = Exception("Test error")

        result = verify_tool_installation(binary_path, "1.5.0", "terraform")

        assert not result

    # Test run_version_check
    @patch("wrknv.wenv.operations.verify.run")
    def test_run_version_check_success(self, mock_run) -> None:
        """Test successful version check."""
        binary_path = self.temp_path / "terraform"
        binary_path.touch()

        mock_run.return_value = Mock(returncode=0, stdout="Terraform v1.5.0\n", stderr="")

        result = run_version_check(binary_path, "terraform", timeout=10)

        assert result == "Terraform v1.5.0"
        mock_run.assert_called_once()

    def test_run_version_check_binary_not_exists(self) -> None:
        """Test version check when binary doesn't exist."""
        binary_path = self.temp_path / "terraform"

        result = run_version_check(binary_path, "terraform")

        assert result is None

    @patch("wrknv.wenv.operations.verify.run")
    def test_run_version_check_failure(self, mock_run) -> None:
        """Test version check with non-zero return code."""
        binary_path = self.temp_path / "terraform"
        binary_path.touch()

        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error running command")

        result = run_version_check(binary_path, "terraform")

        assert result is None

    @patch("wrknv.wenv.operations.verify.run")
    def test_run_version_check_timeout(self, mock_run) -> None:
        """Test version check with timeout."""
        binary_path = self.temp_path / "terraform"
        binary_path.touch()

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)

        result = run_version_check(binary_path, "terraform")

        assert result is None

    @patch("wrknv.wenv.operations.verify.run")
    def test_run_version_check_exception(self, mock_run) -> None:
        """Test version check with general exception."""
        binary_path = self.temp_path / "terraform"
        binary_path.touch()

        mock_run.side_effect = Exception("Test error")

        result = run_version_check(binary_path, "terraform")

        assert result is None

    # Test get_version_command_args
    def test_get_version_command_args_terraform(self) -> None:
        """Test getting version args for terraform."""
        args = get_version_command_args("terraform")
        assert args == ["version"]

    def test_get_version_command_args_tofu(self) -> None:
        """Test getting version args for tofu."""
        args = get_version_command_args("tofu")
        assert args == ["version"]

    def test_get_version_command_args_go(self) -> None:
        """Test getting version args for go."""
        args = get_version_command_args("go")
        assert args == ["version"]

    def test_get_version_command_args_uv(self) -> None:
        """Test getting version args for uv."""
        args = get_version_command_args("uv")
        assert args == ["--version"]

    def test_get_version_command_args_unknown(self) -> None:
        """Test getting version args for unknown tool."""
        args = get_version_command_args("unknown")
        assert args == ["--version"]

    # Test check_binary_compatibility
    @patch("wrknv.wenv.operations.verify.run")
    def test_check_binary_compatibility_success(self, mock_run) -> None:
        """Test successful binary compatibility check."""
        binary_path = self.temp_path / "terraform"
        binary_path.touch()

        mock_run.return_value = Mock(returncode=0, stdout="Usage: terraform ...", stderr="")

        result = check_binary_compatibility(binary_path)

        assert result["compatible"]
        assert result["returncode"] == 0
        assert "Usage" in result["stdout"]

    def test_check_binary_compatibility_not_found(self) -> None:
        """Test compatibility check when binary not found."""
        binary_path = self.temp_path / "terraform"

        result = check_binary_compatibility(binary_path)

        assert not result["compatible"]
        assert result["error"] == "Binary not found"

    @patch("wrknv.wenv.operations.verify.run")
    def test_check_binary_compatibility_incompatible(self, mock_run) -> None:
        """Test incompatible binary."""
        binary_path = self.temp_path / "terraform"
        binary_path.touch()

        mock_run.return_value = Mock(returncode=127, stdout="", stderr="cannot execute binary file")

        result = check_binary_compatibility(binary_path)

        assert not result["compatible"]
        assert result["returncode"] == 127

    @patch("wrknv.wenv.operations.verify.run")
    def test_check_binary_compatibility_timeout(self, mock_run) -> None:
        """Test compatibility check with timeout."""
        binary_path = self.temp_path / "terraform"
        binary_path.touch()

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)

        result = check_binary_compatibility(binary_path)

        assert not result["compatible"]
        assert "timed out" in result["error"]

    @patch("wrknv.wenv.operations.verify.run")
    def test_check_binary_compatibility_exception(self, mock_run) -> None:
        """Test compatibility check with exception."""
        binary_path = self.temp_path / "terraform"
        binary_path.touch()

        mock_run.side_effect = Exception("Test error")

        result = check_binary_compatibility(binary_path)

        assert not result["compatible"]
        assert result["error"] == "Test error"

    # Test validate_installation_directory
    @patch("wrknv.wenv.operations.install.is_executable")
    @patch("wrknv.wenv.operations.platform.get_executable_extension")
    def test_validate_installation_directory_success(self, mock_get_ext, mock_is_exec) -> None:
        """Test successful installation directory validation."""
        install_dir = self.temp_path / "terraform" / "1.5.0"
        bin_dir = install_dir / "bin"
        bin_dir.mkdir(parents=True)

        mock_get_ext.return_value = ""
        binary_path = bin_dir / "terraform"
        binary_path.touch()
        mock_is_exec.return_value = True

        result = validate_installation_directory(install_dir, "terraform", "1.5.0")

        assert result
        mock_is_exec.assert_called_once_with(binary_path)

    def test_validate_installation_directory_not_exists(self) -> None:
        """Test validation when directory doesn't exist."""
        install_dir = self.temp_path / "terraform" / "1.5.0"

        result = validate_installation_directory(install_dir, "terraform", "1.5.0")

        assert not result

    @patch("wrknv.wenv.operations.platform.get_executable_extension")
    def test_validate_installation_directory_no_bin(self, mock_get_ext) -> None:
        """Test validation when bin directory doesn't exist."""
        install_dir = self.temp_path / "terraform" / "1.5.0"
        install_dir.mkdir(parents=True)
        mock_get_ext.return_value = ""

        result = validate_installation_directory(install_dir, "terraform", "1.5.0")

        assert not result

    @patch("wrknv.wenv.operations.platform.get_executable_extension")
    def test_validate_installation_directory_no_binary(self, mock_get_ext) -> None:
        """Test validation when binary doesn't exist."""
        install_dir = self.temp_path / "terraform" / "1.5.0"
        bin_dir = install_dir / "bin"
        bin_dir.mkdir(parents=True)
        mock_get_ext.return_value = ""

        result = validate_installation_directory(install_dir, "terraform", "1.5.0")

        assert not result

    @patch("wrknv.wenv.operations.install.is_executable")
    @patch("wrknv.wenv.operations.platform.get_executable_extension")
    def test_validate_installation_directory_not_executable(self, mock_get_ext, mock_is_exec) -> None:
        """Test validation when binary is not executable."""
        install_dir = self.temp_path / "terraform" / "1.5.0"
        bin_dir = install_dir / "bin"
        bin_dir.mkdir(parents=True)

        mock_get_ext.return_value = ""
        binary_path = bin_dir / "terraform"
        binary_path.touch()
        mock_is_exec.return_value = False

        result = validate_installation_directory(install_dir, "terraform", "1.5.0")

        assert not result

    # Test get_installed_version_info
    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_get_installed_version_info_terraform(self, mock_run_check) -> None:
        """Test getting terraform version info."""
        binary_path = self.temp_path / "terraform"
        mock_run_check.return_value = "Terraform v1.5.0\non linux_amd64"

        result = get_installed_version_info(binary_path, "terraform")

        assert result is not None
        assert result["tool"] == "terraform"
        assert result["version"] == "1.5.0"
        assert result["platform"] == "linux_amd64"

    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_get_installed_version_info_tofu(self, mock_run_check) -> None:
        """Test getting tofu version info."""
        binary_path = self.temp_path / "tofu"
        mock_run_check.return_value = "OpenTofu v1.6.0\non darwin_arm64"

        result = get_installed_version_info(binary_path, "tofu")

        assert result is not None
        assert result["tool"] == "tofu"
        assert result["version"] == "1.6.0"

    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_get_installed_version_info_go(self, mock_run_check) -> None:
        """Test getting go version info."""
        binary_path = self.temp_path / "go"
        mock_run_check.return_value = "go version go1.21.0 linux/amd64"

        result = get_installed_version_info(binary_path, "go")

        assert result is not None
        assert result["tool"] == "go"
        assert result["version"] == "1.21.0"
        assert result["platform"] == "linux/amd64"

    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_get_installed_version_info_uv(self, mock_run_check) -> None:
        """Test getting uv version info."""
        binary_path = self.temp_path / "uv"
        mock_run_check.return_value = "uv 0.1.0"

        result = get_installed_version_info(binary_path, "uv")

        assert result is not None
        assert result["tool"] == "uv"
        assert result["version"] == "0.1.0"

    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_get_installed_version_info_generic(self, mock_run_check) -> None:
        """Test getting generic tool version info."""
        binary_path = self.temp_path / "tool"
        mock_run_check.return_value = "tool version 2.3.4"

        result = get_installed_version_info(binary_path, "tool")

        assert result is not None
        assert result["tool"] == "tool"
        assert "2.3.4" in result["raw_output"]

    @patch("wrknv.wenv.operations.verify.run_version_check")
    def test_get_installed_version_info_no_output(self, mock_run_check) -> None:
        """Test getting version info with no output."""
        binary_path = self.temp_path / "tool"
        mock_run_check.return_value = None

        result = get_installed_version_info(binary_path, "tool")

        assert result is None

    # Test parse functions
    def test_parse_terraform_version(self) -> None:
        """Test parsing terraform version output."""
        output = "Terraform v1.5.0\non linux_amd64"
        result = parse_terraform_version(output)

        assert result["tool"] == "terraform"
        assert result["version"] == "1.5.0"
        assert result["platform"] == "linux_amd64"

    def test_parse_tofu_version(self) -> None:
        """Test parsing tofu version output."""
        output = "OpenTofu v1.6.0\non darwin_arm64"
        result = parse_tofu_version(output)

        assert result["tool"] == "tofu"
        assert result["version"] == "1.6.0"

    def test_parse_go_version(self) -> None:
        """Test parsing go version output."""
        output = "go version go1.21.0 linux/amd64"
        result = parse_go_version(output)

        assert result["tool"] == "go"
        assert result["version"] == "1.21.0"
        assert result["platform"] == "linux/amd64"

    def test_parse_uv_version(self) -> None:
        """Test parsing uv version output."""
        output = "uv 0.1.0"
        result = parse_uv_version(output)

        assert result["tool"] == "uv"
        assert result["version"] == "0.1.0"

    def test_parse_generic_version(self) -> None:
        """Test parsing generic version output."""
        output = "some-tool version 1.2.3\nother info"
        result = parse_generic_version(output, "some-tool")

        assert result["tool"] == "some-tool"
        assert result["raw_output"] == output
        # Should attempt to extract version
        assert "version" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# 🧰🌍🔚
