#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Ansible module for querying Splunk ITSI correlation searches."""

DOCUMENTATION = r"""
---
module: itsi_correlation_search_info
short_description: Query Splunk ITSI correlation searches
description:
  - Retrieve information about correlation searches in Splunk IT Service Intelligence (ITSI).
  - Query a specific correlation search by ID or name, or list all correlation searches.
  - This is a read-only info module that does not make any changes.
  - Uses the ITSI Event Management Interface REST API.
version_added: "1.0.0"
author:
  - Ansible Ecosystem Engineering team (@ansible)
options:
  correlation_search_id:
    description:
      - The correlation search ID for direct lookup.
      - This is the internal identifier (often the saved search name without spaces).
      - Takes precedence over name parameter.
    type: str
    required: false
  name:
    description:
      - The display name/title of the correlation search.
      - Used for lookup when correlation_search_id is not provided.
    type: str
    required: false
  fields:
    description:
      - Comma-separated list of field names to include in response.
      - Useful for retrieving only specific fields.
    type: str
    required: false
  filter_data:
    description:
      - MongoDB-style JSON filter for listing correlation searches.
      - Only applies when listing multiple items (no name or correlation_search_id specified).
    type: str
    required: false
  count:
    description:
      - Maximum number of correlation searches to return when listing.
      - Only applies when listing multiple items.
    type: int
    required: false

requirements:
  - Connection configuration requires C(ansible_connection=httpapi) and C(ansible_network_os=splunk.itsi.itsi_api_client).
  - Authentication via Bearer token, session key, or username/password as documented in the httpapi plugin.

notes:
  - This is an info module for querying ITSI correlation searches using the event_management_interface/correlation_search endpoint.
  - For creating, updating, or deleting correlation searches, use the C(itsi_correlation_search) module.
  - Specify either C(name) or C(correlation_search_id) to fetch a specific search.
  - Without specifying a search identifier, the module lists all correlation searches.
"""

EXAMPLES = r"""
# List all correlation searches
- name: Get all correlation searches
  splunk.itsi.itsi_correlation_search_info:
  register: all_searches

- name: Display correlation search count
  debug:
    msg: "Found {{ all_searches.correlation_searches | length }} correlation searches"

# Query specific correlation search by ID
- name: Get correlation search by ID
  splunk.itsi.itsi_correlation_search_info:
    correlation_search_id: "Service_Monitoring_KPI_Degraded"
  register: search_by_id

# Query correlation search by display name
- name: Get correlation search by name
  splunk.itsi.itsi_correlation_search_info:
    name: "Service Monitoring - KPI Degraded"
  register: search_by_name

# Query with specific fields only
- name: Get correlation search with specific fields
  splunk.itsi.itsi_correlation_search_info:
    correlation_search_id: "my_correlation_search"
    fields: "name,disabled,is_scheduled,cron_schedule,actions"
  register: search_details

# List correlation searches with filtering
- name: List enabled correlation searches
  splunk.itsi.itsi_correlation_search_info:
    filter_data: '{"disabled": "0"}'
    count: 10
  register: enabled_searches

# List with count limit
- name: Get first 5 correlation searches
  splunk.itsi.itsi_correlation_search_info:
    count: 5
  register: limited_searches
"""

RETURN = r"""
status:
  description: HTTP status code from the ITSI API response
  returned: always
  type: int
  sample: 200
headers:
  description: HTTP response headers from the ITSI API
  returned: always
  type: dict
  sample:
    Content-Type: application/json
    Server: Splunkd
body:
  description: Response body from the ITSI API
  returned: always
  type: str
  sample: '{"name": "test-search", "disabled": "0"}'
correlation_searches:
  description: List of correlation searches (when listing multiple)
  returned: when no specific search is requested
  type: list
  elements: dict
  sample: [{"name": "Search 1", "disabled": "0"}, {"name": "Search 2", "disabled": "1"}]
correlation_search:
  description: Single correlation search details
  returned: when specific search is requested
  type: dict
  sample: {"name": "test-search", "disabled": "0", "search": "index=main | head 1"}
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.parse import quote, quote_plus
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_utils import (
    flatten_search_object,
    normalize_to_list,
)

# EMI endpoint for all correlation search operations
BASE_EVENT_MGMT = "servicesNS/nobody/SA-ITOA/event_management_interface/correlation_search"


def get_correlation_search(client, search_identifier, fields=None):
    """Get correlation search by ID using direct path lookup."""
    path = f"{BASE_EVENT_MGMT}/{quote_plus(search_identifier)}"
    params = {"output_mode": "json"}
    if fields:
        params["fields"] = ",".join(fields) if isinstance(fields, (list, tuple)) else fields
    status, data = client.get(path, params=params)
    if status == 200 and isinstance(data, dict):
        flat = flatten_search_object(data)
        if isinstance(data, dict) and "_response_headers" in data:
            flat["_response_headers"] = data.get("_response_headers", {})
        return 200, flat
    return status, data


def get_correlation_search_by_name(client, name, fields=None):
    """
    Query correlation search by name using direct path lookup.

    Uses quote to properly encode spaces as %20 in the URL path.

    Args:
        client: ItsiRequest instance
        name: The correlation search name (can contain spaces)
        fields: Optional comma-separated field list

    Returns:
        tuple: (status_code, correlation_search_dict or error)
    """
    # Use quote with safe='' to encode spaces as '%20' in the URL path
    path = f"{BASE_EVENT_MGMT}/{quote(name, safe='')}"
    params = {"output_mode": "json"}

    if fields:
        params["fields"] = ",".join(fields) if isinstance(fields, (list, tuple)) else fields

    status, data = client.get(path, params=params)

    if status == 200 and isinstance(data, dict):
        flat = flatten_search_object(data)
        if "_response_headers" in data:
            flat["_response_headers"] = data.get("_response_headers", {})
        return 200, flat

    return status, data


def list_correlation_searches(client, fields=None, filter_data=None, count=None):
    """
    List correlation searches with optional filtering.

    Args:
        client: ItsiRequest instance
        fields: Optional comma-separated field list
        filter_data: Optional MongoDB-style filter JSON string
        count: Optional count for number of results

    Returns:
        tuple: (status_code, correlation_searches_list)
    """
    params = {"output_mode": "json"}

    if fields:
        params["fields"] = ",".join(fields) if isinstance(fields, (list, tuple)) else fields
    if filter_data:
        params["filter_data"] = filter_data
    if count:
        params["count"] = count

    status, data = client.get(BASE_EVENT_MGMT, params=params)

    if status == 200:
        entries = normalize_to_list(data)
        results = [flatten_search_object(e) for e in entries]
        result_data = {
            "correlation_searches": results,
            "_response_headers": data.get("_response_headers", {}) if isinstance(data, dict) else {},
        }
        return status, result_data
    else:
        return status, data


def _get_headers(data) -> dict:
    """Extract headers from response data safely."""
    return data.get("_response_headers", {}) if isinstance(data, dict) else {}


def _to_body(data) -> str:
    """Convert data to JSON body string."""
    return json.dumps(data) if isinstance(data, (dict, list)) else str(data)


def _query_single_search(client, params: dict, result: dict):
    """Query a specific correlation search by ID or name."""
    correlation_search_id = params.get("correlation_search_id")
    name = params.get("name")
    fields = params.get("fields")

    if correlation_search_id:
        status, data = get_correlation_search(client, correlation_search_id, fields)
    else:
        status, data = get_correlation_search_by_name(client, name, fields)

    result.update({"status": status, "headers": _get_headers(data), "body": _to_body(data)})
    result["correlation_search"] = data if status == 200 else None


def _query_all_searches(client, params: dict, result: dict):
    """List all correlation searches."""
    fields = params.get("fields")
    filter_data = params.get("filter_data")
    count = params.get("count")

    status, data = list_correlation_searches(client, fields, filter_data, count)
    if not isinstance(data, dict):
        data = {"results": data, "_response_headers": {}}

    result.update(
        {
            "status": status,
            "headers": data.get("_response_headers", {}),
            "body": _to_body(data),
            "correlation_searches": data.get("correlation_searches", []),
        },
    )


def main():
    """Main module execution."""
    module_args = dict(
        correlation_search_id=dict(type="str", required=False),
        name=dict(type="str", required=False),
        fields=dict(type="str", required=False),
        filter_data=dict(type="str", required=False),
        count=dict(type="int", required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if not getattr(module, "_socket_path", None):
        module.fail_json(msg="Use ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client")

    try:
        client = ItsiRequest(Connection(module._socket_path))
        result = {"changed": False, "status": 0, "headers": {}, "body": ""}

        search_identifier = module.params.get("correlation_search_id") or module.params.get("name")
        if search_identifier:
            _query_single_search(client, module.params, result)
        else:
            _query_all_searches(client, module.params, result)

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(
            msg=f"Exception occurred: {str(e)}",
            correlation_search_id=module.params.get("correlation_search_id"),
            name=module.params.get("name"),
        )


if __name__ == "__main__":
    main()
