# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026, Splunk ITSI Ansible Collection maintainers
"""Utility functions for Splunk ITSI correlation search modules."""

from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote, quote_plus

BASE_EVENT_MGMT = "servicesNS/nobody/SA-ITOA/event_management_interface/correlation_search"


def normalize_to_list(data: Any) -> list:
    """Normalize Splunk API responses to a list of objects."""
    if isinstance(data, dict):
        if "entry" in data and isinstance(data["entry"], list):
            return data["entry"]
        if "results" in data and isinstance(data["results"], list):
            return data["results"]
        return [data]
    if isinstance(data, list):
        return data
    return []


def _flatten_search_entry(entry):
    """Return Splunk saved-search ``content`` as a flat dict + minimal metadata."""
    content = dict(entry.get("content", {}))
    content["_meta"] = {
        "name": entry.get("name"),
        "id": entry.get("id"),
        "links": entry.get("links", {}),
        "acl": entry.get("acl", {}),
    }
    return content


def flatten_search_object(obj):
    """Flatten any of the known REST shapes into a flat dict with ``_meta``."""
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


# =============================================================================
# Correlation Search API Functions
# =============================================================================


def get_correlation_search(
    client: Any,
    search_identifier: str,
    fields: Any = None,
    use_name_encoding: bool = False,
) -> Optional[Tuple[int, dict, Any]]:
    """Get a correlation search by ID or name.

    Returns:
        ``(status, headers, flattened_body)`` or ``None`` (not found).
    """
    if use_name_encoding:
        path = f"{BASE_EVENT_MGMT}/{quote(search_identifier, safe='')}"
    else:
        path = f"{BASE_EVENT_MGMT}/{quote_plus(search_identifier)}"

    params: Dict[str, Any] = {"output_mode": "json"}
    if fields:
        params["fields"] = ",".join(fields) if isinstance(fields, (list, tuple)) else fields

    result = client.get(path, params=params)
    if result is None:
        return None
    status, headers, body = result
    flat = flatten_search_object(body) if isinstance(body, dict) else body
    return status, headers, flat


def list_correlation_searches(
    client: Any,
    fields: Any = None,
    filter_data: Optional[str] = None,
    count: Optional[int] = None,
) -> Optional[Tuple[int, dict, Any]]:
    """List correlation searches with optional filtering.

    Returns:
        ``(status, headers, {"correlation_searches": [...]})`` or ``None``.
    """
    params: Dict[str, Any] = {"output_mode": "json"}
    if fields:
        params["fields"] = ",".join(fields) if isinstance(fields, (list, tuple)) else fields
    if filter_data:
        params["filter_data"] = filter_data
    if count:
        params["count"] = count

    result = client.get(BASE_EVENT_MGMT, params=params)
    if result is None:
        return None
    status, headers, body = result
    entries = normalize_to_list(body)
    return status, headers, {"correlation_searches": [flatten_search_object(e) for e in entries]}
