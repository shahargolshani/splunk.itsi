# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026, Splunk ITSI Ansible Collection maintainers
"""Utility functions for Splunk ITSI Ansible modules."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote_plus, urlencode

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


def parse_response_body(body_text: str) -> dict[str, Any]:
    """
    Parse response body from Splunk API.

    Args:
        body_text: Raw response body text

    Returns:
        dict: Parsed response data, always as a dictionary
    """
    if not body_text:
        return {}

    try:
        parsed_data = json.loads(body_text)
        # Ensure we always return a dict, even if API returns a list
        if isinstance(parsed_data, list):
            return {"results": parsed_data}
        elif isinstance(parsed_data, dict):
            return parsed_data
        else:
            return {"raw_response": parsed_data}
    except ValueError:
        return {"raw_response": body_text}


def validate_api_response(result: Any) -> tuple[bool, str]:
    """
    Validate that an API response has the expected format.

    Args:
        result: Response from send_request

    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(result, dict):
        return False, f"Expected dict, got: {type(result)}"
    if "status" not in result:
        return False, "Missing 'status' in response"
    if "body" not in result:
        return False, "Missing 'body' in response"
    return True, ""


def handle_request_exception(exc: Exception) -> tuple[int, dict[str, str]]:
    """
    Handle common exceptions from API requests.

    Args:
        exc: The exception that was raised

    Returns:
        tuple: (status_code, error_dict)
    """
    error_text = str(exc)

    # Handle common error patterns
    if "401" in error_text or "Unauthorized" in error_text:
        return 401, {"error": "Authentication failed"}
    elif "404" in error_text or "Not Found" in error_text:
        return 404, {"error": "Resource not found"}
    else:
        return 500, {"error": error_text}


def process_api_response(result: Any) -> tuple[int, dict[str, Any]]:
    """
    Process and normalize an API response from send_request.

    Args:
        result: Raw response from connection.send_request

    Returns:
        tuple: (status_code, response_dict with parsed body and headers)
    """
    # Validate response format
    is_valid, error_msg = validate_api_response(result)
    if not is_valid:
        return 500, {"error": f"Invalid response format from send_request. {error_msg}"}

    status = result["status"]
    headers = result.get("headers", {})
    body_text = result["body"]

    # Parse response body
    data = parse_response_body(body_text)

    # Include headers in response for debugging (ensure data is dict)
    if isinstance(data, dict):
        data["_response_headers"] = headers
    else:
        data = {"results": data, "_response_headers": headers}

    return status, data


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


def _build_request_path(path: str, params: dict[str, Any] | None) -> str:
    """Build request path with query parameters."""
    if not params:
        return path

    query_params = {k: v for k, v in params.items() if v is not None and v != ""}
    if not query_params:
        return path

    sep = "&" if "?" in path else "?"
    return f"{path}{sep}{urlencode(query_params, doseq=True)}"


def _prepare_request_body(payload: dict | list | str | None) -> str:
    """Prepare request body from payload."""
    if isinstance(payload, (dict, list)):
        return json.dumps(payload)
    if payload is None:
        return ""
    return str(payload)


def _parse_response(result: dict) -> tuple[int, dict[str, Any]]:
    """Parse response from send_request."""
    status = result["status"]
    body_text = result["body"]
    headers = result.get("headers", {})

    if not body_text:
        return status, {"_response_headers": headers}

    try:
        parsed_data = json.loads(body_text)
        if isinstance(parsed_data, dict):
            parsed_data["_response_headers"] = headers
        return status, parsed_data
    except json.JSONDecodeError:
        return status, {"raw_response": body_text, "_response_headers": headers}


def send_itsi_request(
    conn: Any,
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    payload: dict | list | str | None = None,
) -> tuple[int, dict[str, Any]]:
    """
    Send request via itsi_api_client.

    Args:
        conn: Connection object
        method: HTTP method (GET, POST, DELETE)
        path: API path
        params: Query parameters dict
        payload: Request body data (dict, list, or string)

    Returns:
        tuple: (status_code, response_dict)
    """
    try:
        request_path = _build_request_path(path, params)
        body = _prepare_request_body(payload)
        result = conn.send_request(request_path, method=method.upper(), body=body)

        # Validate response format
        if not isinstance(result, dict) or "status" not in result or "body" not in result:
            return 500, {
                "error": f"Invalid response format from send_request. Expected dict with 'status' and 'body', got: {type(result)}",
            }

        return _parse_response(result)

    except Exception as e:
        return 500, {"error": f"Request failed: {str(e)}"}


def get_aggregation_policy_by_id(
    conn: Any,
    policy_id: str,
    fields: str | None = None,
) -> tuple[int, dict[str, Any]]:
    """
    Get a specific aggregation policy by ID (_key) via EMI.

    Args:
        conn: Connection object
        policy_id: Policy ID (_key)
        fields: Comma-separated list of fields to retrieve

    Returns:
        tuple: (status_code, policy_data)
    """
    path = f"{BASE_AGGREGATION_POLICY_ENDPOINT}/{quote_plus(policy_id)}"
    params = {"output_mode": "json"}

    if fields:
        params["fields"] = fields

    status, data = send_itsi_request(conn, "GET", path, params=params)

    if status == 200:
        # Flatten the policy object for consistent access
        policy_data = flatten_policy_object(data)
        return status, policy_data

    return status, data


def list_aggregation_policies(
    conn: Any,
    fields: str | None = None,
    filter_data: str | None = None,
    limit: int | None = None,
) -> tuple[int, dict[str, Any]]:
    """
    List aggregation policies via EMI.

    Args:
        conn: Connection object
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

    status, data = send_itsi_request(conn, "GET", BASE_AGGREGATION_POLICY_ENDPOINT, params=params)

    if status == 200:
        entries = normalize_policy_list(data)
        results = [flatten_policy_object(e) for e in entries]
        result_data = {
            "aggregation_policies": results,
            "_response_headers": data.get("_response_headers", {}) if isinstance(data, dict) else {},
        }
        return status, result_data
    else:
        return status, data


def get_aggregation_policies_by_title(
    conn: Any,
    title: str,
    fields: str | None = None,
) -> tuple[int, dict[str, Any]]:
    """
    Get aggregation policies by title via EMI.

    Since multiple policies can have the same title, this returns a list
    of all matching policies. Uses client-side filtering for reliability
    across different ITSI versions.

    Args:
        conn: Connection object
        title: Policy title to search for
        fields: Comma-separated list of fields to retrieve

    Returns:
        tuple: (status_code, policies_data_dict)
            policies_data_dict contains 'aggregation_policies' list and '_response_headers'
    """
    # Fetch all policies and filter client-side for reliability
    # (EMI API doesn't reliably support server-side title filtering)
    status, data = list_aggregation_policies(conn, fields=fields)

    if status != 200:
        return status, data

    # Filter by exact title match client-side
    all_policies = data.get("aggregation_policies", [])
    matching_policies = [p for p in all_policies if isinstance(p, dict) and p.get("title") == title]

    return status, {
        "aggregation_policies": matching_policies,
        "_response_headers": data.get("_response_headers", {}),
    }
