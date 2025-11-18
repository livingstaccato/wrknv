#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tf Wrapper Script
=================
This script acts as a 'tf' command that delegates to the
developer's chosen Tf flavor (IBM Terraform or OpenTofu)."""

import os
import pathlib
import sys


def get_workenv_root():
    """Find the workenv root directory."""
    # Start from the script's location
    current = pathlib.Path(sys.argv[0]).resolve().parent

    # Look for workenv directory pattern
    while current != current.parent:
        if current.name.startswith("workenv") and "_" in current.name:
            return current
        if current.name == "bin" and current.parent.name.startswith("workenv"):
            return current.parent
        current = current.parent

    return None


def get_tf_flavor():
    """Get the configured Tf flavor from wrknv.toml."""
    # Check for wrknv.toml
    wrknv_toml = None
    current = pathlib.Path.cwd()
    while current != current.parent:
        candidate = current / "wrknv.toml"
        if candidate.exists():
            wrknv_toml = candidate
            break
        current = current.parent

    if wrknv_toml:
        try:
            import tomllib

            with open(wrknv_toml, "rb") as f:
                config = tomllib.load(f)

            # Check for tf_flavor setting
            if "workenv" in config and "tf_flavor" in config["workenv"]:
                return config["workenv"]["tf_flavor"]
        except:
            pass

    return "ibm"  # Default to IBM Terraform


def main() -> None:
    """Main entry point."""
    flavor = get_tf_flavor()

    # Find the actual binary
    workenv_root = get_workenv_root()
    if workenv_root:
        bin_dir = workenv_root / "bin"

        # Look for the flavor binary
        if flavor == "opentofu":
            binary_name = "tofu"
        else:
            binary_name = "ibmtf"  # IBM Terraform

        if os.name == "nt":
            binary_name += ".exe"

        binary_path = bin_dir / binary_name

        if binary_path.exists():
            # Execute the actual binary with all arguments
            os.execv(str(binary_path), [binary_name, *sys.argv[1:]])
        else:
            print(f"Error: {flavor} binary not found at {binary_path}", file=sys.stderr)
            if flavor == "opentofu":
                print(
                    "Run 'wrknv tofu <version>' to install OpenTofu",
                    file=sys.stderr,
                )
            else:
                print(
                    "Run 'wrknv ibmtf <version>' to install IBM Terraform",
                    file=sys.stderr,
                )
            sys.exit(1)
    else:
        print("Error: Could not determine workenv directory", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# 🧰🌍🔚
