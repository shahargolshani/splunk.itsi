# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026, Splunk ITSI Ansible Collection maintainers
"""Shared pure-Python utilities for Splunk ITSI Ansible modules."""
from __future__ import annotations

from typing import Any, Callable, Optional


def build_have_conf(
    desired: dict,
    current: dict,
    normalizers: Optional[dict[str, Callable]] = None,
    exclude_keys: Optional[set[str]] = None,
) -> dict:
    """Build ``have_conf`` from current state, scoped to desired keys.

    Extracts values from *current* for each key in *desired*, applying
    per-field normalization so that ``dict_diff`` compares like-with-like.

    Args:
        desired: Desired state dict (keys define the comparison scope).
        current: Current state dict (values are extracted from here).
        normalizers: Optional ``{field: callable}`` for type alignment.
        exclude_keys: Optional set of keys to skip (e.g. identifier-only fields).

    Returns:
        Dict of ``{field: normalized_current_value}`` for each desired key.
    """
    normalizers = normalizers or {}
    exclude_keys = exclude_keys or set()
    have_conf: dict = {}
    for k in desired:
        if k in exclude_keys:
            continue
        val = current.get(k)
        if k in normalizers:
            val = normalizers[k](val)
        have_conf[k] = val
    return have_conf


def exit_with_result(
    module: Any,
    changed: bool = False,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
    diff: Optional[dict] = None,
    response: Optional[dict] = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    """Exit the module with a consistently structured result.

    Guarantees that ``before``, ``after``, ``diff``, and ``response`` are
    always present in the output, defaulting to empty dicts when not provided.

    Args:
        module: The AnsibleModule instance.
        changed: Whether the resource was modified.
        before: Current field values before the operation.
        after: Desired field values after the operation.
        diff: Fields that differ between current and desired state.
        response: Raw API response from Splunk ITSI.
        extra: Optional dict of additional key-value pairs to include
            in the result on top of the standard keys.
    """
    result: dict[str, Any] = {
        "changed": changed,
        "before": before if before is not None else {},
        "after": after if after is not None else {},
        "diff": diff if diff is not None else {},
        "response": response if response is not None else {},
    }
    if extra:
        result.update(extra)
    module.exit_json(**result)
