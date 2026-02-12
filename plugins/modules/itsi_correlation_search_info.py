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
# Access: all_searches.response.correlation_searches

- name: Display correlation search count
  debug:
    msg: "Found {{ all_searches.response.correlation_searches | length }} correlation searches"

# Query specific correlation search by ID
- name: Get correlation search by ID
  splunk.itsi.itsi_correlation_search_info:
    correlation_search_id: "Service_Monitoring_KPI_Degraded"
  register: search_by_id
# Access: search_by_id.response (single search dict)

# Query correlation search by display name
- name: Get correlation search by name
  splunk.itsi.itsi_correlation_search_info:
    name: "Service Monitoring - KPI Degraded"
  register: search_by_name
# Access: search_by_name.response (single search dict)

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
changed:
  description: Always false. This is an information module.
  type: bool
  returned: always
response:
  description: The API response body. For single-search queries (by ID or name)
    this is the flattened search dict, or empty dict when not found. For list
    queries this is a dict with a C(correlation_searches) key.
  type: raw
  returned: always
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.splunk.itsi.plugins.module_utils.correlation_search_utils import (
    get_correlation_search,
    list_correlation_searches,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest


def _query_single_search(client, params: dict):
    """Query a specific correlation search by ID or name.

    Returns:
        The flattened search dict, or ``{}`` when not found.
    """
    correlation_search_id = params.get("correlation_search_id")
    name = params.get("name")
    fields = params.get("fields")

    if correlation_search_id:
        api_result = get_correlation_search(client, correlation_search_id, fields)
    else:
        api_result = get_correlation_search(client, name, fields, use_name_encoding=True)

    if api_result is None:
        return {}

    _status, _headers, body = api_result
    return body


def _query_all_searches(client, params: dict):
    """List all correlation searches.

    Returns:
        ``{"correlation_searches": [...]}``, or ``{}`` when the API
        returns nothing.
    """
    api_result = list_correlation_searches(client, params.get("fields"), params.get("filter_data"), params.get("count"))
    if api_result is None:
        return {}

    _status, _headers, body = api_result
    return body


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

    client = ItsiRequest(Connection(module._socket_path), module)
    result: dict = {"changed": False, "response": {}}

    search_identifier = module.params.get("correlation_search_id") or module.params.get("name")
    if search_identifier:
        result["response"] = _query_single_search(client, module.params)
    else:
        result["response"] = _query_all_searches(client, module.params)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
