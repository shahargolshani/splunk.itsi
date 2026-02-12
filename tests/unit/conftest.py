# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Shared test helpers for splunk.itsi unit tests."""

import sys
from types import ModuleType
from typing import Optional
from unittest.mock import MagicMock

# Mock ansible.netcommon for unit tests - Important to prevent import errors when running tests (SONAR CLOUD CI)
_NETCOMMON_PREFIX = "ansible_collections.ansible.netcommon"
_NETCOMMON_MODULES = [
    _NETCOMMON_PREFIX,
    f"{_NETCOMMON_PREFIX}.plugins",
    f"{_NETCOMMON_PREFIX}.plugins.module_utils",
    f"{_NETCOMMON_PREFIX}.plugins.module_utils.network",
]


class _NetcommonUtils:
    """Minimal stand-in for ansible.netcommon network.common.utils."""

    @staticmethod
    def remove_empties(data: dict) -> dict:
        """Return a copy of *data* with None values removed."""
        return {k: v for k, v in data.items() if v is not None}

    @staticmethod
    def dict_diff(have: dict, want: dict) -> dict:
        """Return keys from *want* whose values differ from *have*."""
        return {k: v for k, v in want.items() if have.get(k) != v}


# Build the mock module tree
for _mod_path in _NETCOMMON_MODULES:
    sys.modules.setdefault(_mod_path, MagicMock())

_common_mod = ModuleType(
    f"{_NETCOMMON_PREFIX}.plugins.module_utils.network.common",
)
_common_mod.utils = _NetcommonUtils()  # type: ignore[attr-defined]
sys.modules.setdefault(
    f"{_NETCOMMON_PREFIX}.plugins.module_utils.network.common",
    _common_mod,
)


# ---------------------------------------------------------------------------
# Exception classes to simulate Ansible module exit / fail behaviour.
# Inherit from SystemExit so they are NOT caught by ``except Exception``
# blocks inside the modules under test.
# ---------------------------------------------------------------------------
class AnsibleExitJson(SystemExit):
    """Exception raised when module.exit_json() is called."""

    pass


class AnsibleFailJson(SystemExit):
    """Exception raised when module.fail_json() is called."""

    pass


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------
def make_mock_conn(
    status: int = 200,
    body: str = "{}",
    headers: Optional[dict] = None,
) -> MagicMock:
    """Create a MagicMock connection with a canned send_request response.

    Args:
        status: HTTP status code to return.
        body: Response body string (usually JSON).
        headers: Optional response headers dict.

    Returns:
        A MagicMock whose ``send_request`` returns the configured response.
    """
    conn = MagicMock()
    conn.send_request.return_value = {
        "status": status,
        "body": body,
        "headers": headers or {},
    }
    return conn
