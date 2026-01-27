# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Utility functions for Splunk ITSI Ansible modules."""

from __future__ import absolute_import, division, print_function

import json
from typing import Any

__metaclass__ = type


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
