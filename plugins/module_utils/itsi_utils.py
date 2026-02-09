# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026, Splunk ITSI Ansible Collection maintainers
"""Utility functions for Splunk ITSI Ansible modules."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

# API endpoint constants
BASE_AGGREGATION_POLICY_ENDPOINT = "servicesNS/nobody/SA-ITOA/event_management_interface/notable_event_aggregation_policy"


def _flatten_search_entry(entry):
    """Return Splunk saved-search `content` as a flat dict + minimal metadata."""
    content = dict(entry.get("content", {}))
    content["_meta"] = {
        "name": entry.get("name"),
        "id": entry.get("id"),
        "links": entry.get("links", {}),
        "acl": entry.get("acl", {}),
    }
    return content


def flatten_search_object(obj):
    """
    Accept any of the known REST shapes (EAI entry envelope, already-flat dict)
    and return a flat dict of fields with `_meta`.
    """
    if isinstance(obj, dict):
        if "entry" in obj and isinstance(obj["entry"], list) and obj["entry"]:
            return _flatten_search_entry(obj["entry"][0])
        if "content" in obj and isinstance(obj["content"], dict):
            return _flatten_search_entry(
                {
                    "content": obj["content"],
                    "name": obj.get("name"),
                    "id": obj.get("id"),
                    "links": obj.get("links", {}),
                    "acl": obj.get("acl", {}),
                },
            )
        flat = dict(obj)
        flat.setdefault("_meta", {})
        return flat
    return {"_meta": {}, "raw": obj}


def normalize_to_list(data: Any) -> list:
    """
    Normalize Splunk API responses to a list of objects.

    Args:
        data: Response data from Splunk API

    Returns:
        list: List of objects from the response
    """
    if isinstance(data, dict):
        # Handle Splunk REST API entry format
        if "entry" in data and isinstance(data["entry"], list):
            return data["entry"]
        if "results" in data and isinstance(data["results"], list):
            return data["results"]
        # Single object response
        return [data]
    elif isinstance(data, list):
        return data
    return []


# =============================================================================
# Aggregation Policy Utilities
# =============================================================================


def normalize_policy_list(data: Any) -> list:
    """
    Normalize various API response formats to a list for aggregation policies.

    Args:
        data: Response data from Splunk API

    Returns:
        list: List of policy objects from the response
    """
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if "entry" in data:
            entries = data["entry"]
            return entries if isinstance(entries, list) else [entries]
        else:
            return [data]
    else:
        return []


def flatten_policy_object(policy_obj: Any) -> Any:
    """
    Flatten aggregation policy object from Splunk API response.
    Handles nested entry/content structures.

    Args:
        policy_obj: Policy object from API response

    Returns:
        Flattened policy dict or original value if not a dict
    """
    if not isinstance(policy_obj, dict):
        return policy_obj

    # If this is an entry object with content, extract the content
    if "entry" in policy_obj and len(policy_obj) == 1:
        return flatten_policy_object(policy_obj["entry"])
    elif "content" in policy_obj:
        content = policy_obj["content"]
        # Merge entry-level fields with content
        result = dict(content)
        for k, v in policy_obj.items():
            if k != "content":
                result[k] = v
        return result
    else:
        return policy_obj


# =============================================================================
# Aggregation Policy API Functions
# =============================================================================


def get_aggregation_policy_by_id(
    client: Any,
    policy_id: str,
    fields: str | None = None,
) -> tuple[int, dict[str, Any]]:
    """
    Get a specific aggregation policy by ID (_key) via EMI.

    Args:
        client: ItsiRequest instance
        policy_id: Policy ID (_key)
        fields: Comma-separated list of fields to retrieve

    Returns:
        tuple: (status_code, policy_data)
    """
    path = f"{BASE_AGGREGATION_POLICY_ENDPOINT}/{quote_plus(policy_id)}"
    params: dict[str, Any] = {"output_mode": "json"}

    if fields:
        params["fields"] = fields

    status, data = client.get(path, params=params)

    if status == 200:
        # Flatten the policy object for consistent access
        policy_data = flatten_policy_object(data)
        return status, policy_data

    return status, data


def list_aggregation_policies(
    client: Any,
    fields: str | None = None,
    filter_data: str | None = None,
    limit: int | None = None,
) -> tuple[int, dict[str, Any]]:
    """
    List aggregation policies via EMI.

    Args:
        client: ItsiRequest instance
        fields: Comma-separated list of fields to retrieve
        filter_data: MongoDB-style JSON filter string
        limit: Maximum number of results

    Returns:
        tuple: (status_code, policies_data)
    """
    params: dict[str, Any] = {"output_mode": "json"}

    if fields:
        params["fields"] = fields
    if filter_data:
        params["filter_data"] = filter_data
    if limit:
        params["limit"] = limit

    status, data = client.get(BASE_AGGREGATION_POLICY_ENDPOINT, params=params)

    if status == 200:
        entries = normalize_policy_list(data)
        results = [flatten_policy_object(e) for e in entries]
        result_data = {
            "aggregation_policies": results,
            "_response_headers": data.get("_response_headers", {}) if isinstance(data, dict) else {},
        }
        return status, result_data

    return status, data


def get_aggregation_policies_by_title(
    client: Any,
    title: str,
    fields: str | None = None,
) -> tuple[int, dict[str, Any]]:
    """
    Get aggregation policies by title via EMI.

    Since multiple policies can have the same title, this returns a list
    of all matching policies. Uses client-side filtering for reliability
    across different ITSI versions.

    Args:
        client: ItsiRequest instance
        title: Policy title to search for
        fields: Comma-separated list of fields to retrieve

    Returns:
        tuple: (status_code, policies_data_dict)
            policies_data_dict contains 'aggregation_policies' list and '_response_headers'
    """
    # Fetch all policies and filter client-side for reliability
    # (EMI API doesn't reliably support server-side title filtering)
    status, data = list_aggregation_policies(client, fields=fields)

    if status != 200:
        return status, data

    # Filter by exact title match client-side
    all_policies = data.get("aggregation_policies", [])
    matching_policies = [p for p in all_policies if isinstance(p, dict) and p.get("title") == title]

    return status, {
        "aggregation_policies": matching_policies,
        "_response_headers": data.get("_response_headers", {}),
    }
