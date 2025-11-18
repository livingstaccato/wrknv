#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Sub Rosa Manager Module
=======================
Secret management tools - 'sub rosa' (under the rose) - in confidence.

Provides base class and variants for managing secret management tools:
- OpenBao (open source Vault fork)
- IBM Vault (HashiCorp Vault)"""

from __future__ import annotations

from wrknv.managers.subrosa.bao import BaoVariant
from wrknv.managers.subrosa.base import SubRosaManager
from wrknv.managers.subrosa.ibm import IbmVaultVariant

__all__ = [
    "BaoVariant",
    "IbmVaultVariant",
    "SubRosaManager",
]

# 🧰🌍🔚
