#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers

from __future__ import (
    absolute_import,
    division,
    print_function,
)

__metaclass__ = type


DOCUMENTATION = r"""
---
module: itsi_glass_table_info
short_description: Read Splunk ITSI glass table objects via itoa_interface
description:
  - Reads a single glass table by C(_key) or lists glass tables with optional
    server-side filtering, pagination, and sorting.
  - Uses the splunk.itsi.itsi_api_client httpapi plugin for authentication and transport.
version_added: "1.0.0"
author:
  - Ansible Ecosystem Engineering team (@ansible)
options:
  glass_table_id:
    description:
      - The glass table C(_key).
      - When provided, fetches a single glass table and returns it as a one-element list.
    type: str
  filter:
    description:
      - MongoDB-style filter for listing glass tables.
      - Accepts a dict or a JSON string.
      - Only applies when C(glass_table_id) is not provided.
      - "Example: C({\"title\": \"My Table\"})."
    type: raw
  fields:
    description:
      - Comma-separated list of field names to include in the response.
    type: str
  count:
    description:
      - Maximum number of glass tables to return (page size).
      - Only applies when listing (no C(glass_table_id)).
    type: int
  offset:
    description:
      - Number of results to skip from the start.
      - Only applies when listing (no C(glass_table_id)).
    type: int
  sort_key:
    description:
      - Field name to sort results by.
      - Only applies when listing (no C(glass_table_id)).
    type: str
  sort_dir:
    description:
      - "Sort direction: C(asc) for ascending, C(desc) for descending."
      - Only applies when listing (no C(glass_table_id)).
    type: str
    choices:
      - asc
      - desc
notes:
  - "Connection/auth/SSL config is provided by httpapi (inventory), not by this module."
  - This is a read-only module. It never changes remote state.
requirements:
  - ansible.netcommon
"""

EXAMPLES = r"""
- name: List all glass tables
  splunk.itsi.itsi_glass_table_info:
  register: all_tables

- name: Get a single glass table by key
  splunk.itsi.itsi_glass_table_info:
    glass_table_id: 6992e850280636204503b3f6
  register: one

- name: List glass tables with pagination
  splunk.itsi.itsi_glass_table_info:
    count: 10
    offset: 0
  register: page1

- name: Filter glass tables by title
  splunk.itsi.itsi_glass_table_info:
    filter: '{"title": "My Dashboard"}'
  register: filtered

- name: List glass tables sorted by modification time
  splunk.itsi.itsi_glass_table_info:
    sort_key: mod_time
    sort_dir: desc
    count: 5
  register: recent

- name: Retrieve only specific fields
  splunk.itsi.itsi_glass_table_info:
    fields: "_key,title,description,mod_time"
  register: summary
"""

RETURN = r"""
glass_tables:
  description: "List of glass table objects matching the query."
  type: list
  elements: dict
  returned: always
changed:
  description: "Always false (read-only)."
  type: bool
  returned: always
"""

import json
from typing import (
    Any,
    Optional,
)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.splunk.itsi.plugins.module_utils.glass_table import (
    BASE_GLASS_TABLE_ENDPOINT,
    get_glass_table_by_id,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest
from ansible_collections.splunk.itsi.plugins.module_utils.splunk_utils import exit_with_result


def _fetch_body(
    client: ItsiRequest,
    path: str,
    params: Optional[dict[str, Any]] = None,
) -> Optional[Any]:
    """Call client.get and return only the response body.

    Args:
        client: ItsiRequest instance for API requests.
        path: API endpoint path.
        params: Optional query parameters.

    Returns:
        Parsed response body, or None if not found (404).
    """
    result = client.get(path, params=params)
    if result is None:
        return None
    _status, _headers, body = result
    return body


PASSTHROUGH_PARAMS = ("filter", "fields", "count", "offset", "sort_key", "sort_dir")


def _build_list_params(module_params: dict[str, Any]) -> dict[str, Any]:
    """Build query parameters for the list endpoint.

    Args:
        module_params: Module parameters dictionary.

    Returns:
        Filtered query parameters dict with non-None values only.
    """
    params: dict[str, Any] = {}
    for key in PASSTHROUGH_PARAMS:
        if module_params[key] is not None:
            value = module_params[key]
            if key == "filter" and isinstance(value, dict):
                value = json.dumps(value, separators=(",", ":"))
            params[key] = value
    return params


def _list_glass_tables(
    client: ItsiRequest,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    """List glass tables with optional filtering, pagination, and sorting.

    Args:
        client: ItsiRequest instance for API requests.
        params: Query parameters for the list request.

    Returns:
        List of glass table dicts from the API.
    """
    body = _fetch_body(client, BASE_GLASS_TABLE_ENDPOINT, params=params)
    return body if isinstance(body, list) else []


def main() -> None:
    """Main module execution."""
    module = AnsibleModule(
        argument_spec=dict(
            glass_table_id=dict(type="str"),
            filter=dict(type="raw"),
            fields=dict(type="str"),
            count=dict(type="int"),
            offset=dict(type="int"),
            sort_key=dict(type="str", no_log=False),
            sort_dir=dict(type="str", choices=["asc", "desc"]),
        ),
        supports_check_mode=True,
    )

    module_params = module.params

    try:
        client = ItsiRequest(Connection(module._socket_path), module)
    except Exception as e:
        module.fail_json(msg=f"Failed to establish connection: {e}")

    try:
        if module_params["glass_table_id"]:
            body = get_glass_table_by_id(client, module_params["glass_table_id"])
            glass_tables = [body] if isinstance(body, dict) else []
        else:
            params = _build_list_params(module_params)
            glass_tables = _list_glass_tables(client, params)

        exit_with_result(module, extra={"glass_tables": glass_tables})

    except Exception as e:
        module.fail_json(msg=f"Exception occurred: {str(e)}")


if __name__ == "__main__":
    main()
