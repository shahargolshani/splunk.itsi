# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026, Splunk ITSI Ansible Collection maintainers
"""Utility functions for Splunk ITSI aggregation policy modules."""

from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote_plus

BASE_AGGREGATION_POLICY_ENDPOINT = "servicesNS/nobody/SA-ITOA/event_management_interface/notable_event_aggregation_policy"


def normalize_policy_list(data: Any) -> list:
    """Normalize various API response formats to a list of policy objects."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "entry" in data:
            entries = data["entry"]
            return entries if isinstance(entries, list) else [entries]
        return [data]
    return []


def flatten_policy_object(policy_obj: Any) -> Any:
    """Flatten aggregation policy object from Splunk API response."""
    if not isinstance(policy_obj, dict):
        return policy_obj
    if "entry" in policy_obj and len(policy_obj) == 1:
        return flatten_policy_object(policy_obj["entry"])
    if "content" in policy_obj:
        content = dict(policy_obj["content"])
        for k, v in policy_obj.items():
            if k != "content":
                content[k] = v
        return content
    return policy_obj


# =============================================================================
# Aggregation Policy API Functions
# =============================================================================


def get_aggregation_policy_by_id(
    client: Any,
    policy_id: str,
    fields: Optional[str] = None,
) -> Optional[Tuple[int, dict, Any]]:
    """Get a specific aggregation policy by ID.

    Returns:
        ``(status, headers, flattened_body)`` or ``None`` (not found).
    """
    path = f"{BASE_AGGREGATION_POLICY_ENDPOINT}/{quote_plus(policy_id)}"
    params: Dict[str, Any] = {"output_mode": "json"}
    if fields:
        params["fields"] = fields

    result = client.get(path, params=params)
    if result is None:
        return None
    status, headers, body = result
    return status, headers, flatten_policy_object(body)


def list_aggregation_policies(
    client: Any,
    fields: Optional[str] = None,
    filter_data: Optional[str] = None,
    limit: Optional[int] = None,
) -> Optional[Tuple[int, dict, Any]]:
    """List aggregation policies.

    Returns:
        ``(status, headers, {"aggregation_policies": [...]})`` or ``None``.
    """
    params: Dict[str, Any] = {"output_mode": "json"}
    if fields:
        params["fields"] = fields
    if filter_data:
        params["filter_data"] = filter_data
    if limit:
        params["limit"] = limit

    result = client.get(BASE_AGGREGATION_POLICY_ENDPOINT, params=params)
    if result is None:
        return None
    status, headers, body = result
    entries = normalize_policy_list(body)
    return status, headers, {"aggregation_policies": [flatten_policy_object(e) for e in entries]}
