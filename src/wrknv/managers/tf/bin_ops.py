#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tf Bin Operations
=================
Tf-specific binary operations for workenv bin directory."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

from provide.foundation import logger

from wrknv.wenv.bin_manager import copy_tool_binary

if TYPE_CHECKING:
    from wrknv.config import WorkenvConfig


def copy_tf_binaries_to_workenv(bin_dir: pathlib.Path, config: WorkenvConfig | None) -> None:
    """Copy all active tf binaries to workenv bin directory.

    Args:
        bin_dir: Target bin directory
        config: Workenv configuration
    """
    if not bin_dir:
        logger.warning("No bin directory available for tf binary copying")
        return

    # Get active versions for both tf variants
    for tool_name in ["tofu", "ibmtf"]:
        try:
            # Create a temporary manager instance to get active version
            if tool_name == "tofu":
                from wrknv.managers.tf.tofu import TofuTfVariant

                temp_manager = TofuTfVariant(config)
            else:
                from wrknv.managers.tf.ibm import IbmTfVariant

                temp_manager = IbmTfVariant(config)

            active_version = temp_manager.get_installed_version()
            if active_version:
                source_path = temp_manager.get_binary_path(active_version)
                target_name = temp_manager.executable_name

                if copy_tool_binary(source_path, target_name, bin_dir):
                    logger.debug(f"Copied {tool_name} {active_version} to {bin_dir}")

        except Exception as e:
            logger.warning(f"Failed to copy {tool_name} binary: {e}")


# 🧰🌍🔚
