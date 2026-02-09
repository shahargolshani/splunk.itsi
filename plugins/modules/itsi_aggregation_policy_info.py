#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Ansible module for querying Splunk ITSI aggregation policies."""


DOCUMENTATION = r"""
---
module: itsi_aggregation_policy_info
short_description: Get information about Splunk ITSI aggregation policies
description:
  - Retrieve information about aggregation policies in Splunk IT Service Intelligence (ITSI).
  - Query by policy_id for a specific policy, by title for all matching policies, or list all policies.
  - This is a read-only module that does not modify any policies.
  - Uses the ITSI Event Management Interface REST API.
version_added: "1.0.0"
author:
  - Ansible Ecosystem Engineering team (@ansible)
options:
  policy_id:
    description:
      - The aggregation policy ID/key (unique identifier).
      - Provides direct lookup by unique ID.
      - Returns a single policy in C(aggregation_policy).
    type: str
    required: false
  title:
    description:
      - The title/name of the aggregation policy to search for.
      - Note that multiple policies can have the same title.
      - Returns all matching policies in C(aggregation_policies) list.
      - If exactly one match, C(aggregation_policy) is also set for convenience.
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
      - MongoDB-style JSON filter for listing aggregation policies.
      - Only applies when listing multiple items (no title or policy_id specified).
    type: str
    required: false
  limit:
    description:
      - Maximum number of aggregation policies to return when listing.
      - Only applies when listing multiple items.
    type: int
    required: false

requirements:
  - Connection configuration requires C(ansible_connection=httpapi) and C(ansible_network_os=splunk.itsi.itsi_api_client).
  - Authentication via Bearer token, session key, or username/password as documented in the httpapi plugin.

notes:
  - This module retrieves ITSI aggregation policies using the event_management_interface/notable_event_aggregation_policy endpoint.
  - When querying by C(policy_id), returns a single policy in C(aggregation_policy).
  - When querying by C(title), returns all matching policies in C(aggregation_policies) list since titles are not unique.
  - Without any identifier, lists all aggregation policies.
  - This is a read-only module and will never modify policies.
"""

EXAMPLES = r"""
# List all aggregation policies
- name: Get all aggregation policies
  splunk.itsi.itsi_aggregation_policy_info:
  register: all_policies
# Access: all_policies.aggregation_policies

# Get aggregation policy by ID (returns single policy)
- name: Get aggregation policy by ID
  splunk.itsi.itsi_aggregation_policy_info:
    policy_id: "itsi_default_policy"
  register: policy_by_id
# Access: policy_by_id.aggregation_policy

# Get aggregation policies by title (may return multiple)
- name: Get all aggregation policies with a specific title
  splunk.itsi.itsi_aggregation_policy_info:
    title: "Default Policy"
  register: policies_by_title
# Access: policies_by_title.aggregation_policies (list of all matching)
# If exactly one match: policies_by_title.aggregation_policy also available

# Get aggregation policy with specific fields only
- name: Get aggregation policy with field projection
  splunk.itsi.itsi_aggregation_policy_info:
    policy_id: "itsi_default_policy"
    fields: "title,disabled,priority,group_severity"
  register: policy_details

# List aggregation policies with filtering
- name: List enabled aggregation policies
  splunk.itsi.itsi_aggregation_policy_info:
    filter_data: '{"disabled": 0}'
    limit: 10
  register: enabled_policies

# List policies with specific fields
- name: List all policies with minimal fields
  splunk.itsi.itsi_aggregation_policy_info:
    fields: "_key,title,disabled"
  register: policy_list
"""

RETURN = r"""
aggregation_policy:
  description: The aggregation policy data (single policy query by ID, or single match by title)
  type: dict
  returned: when querying by policy_id, or when exactly one policy matches the title
  sample:
    title: "Default Policy"
    description: "Default aggregation policy"
    disabled: 0
    _key: "itsi_default_policy"
aggregation_policies:
  description: List of aggregation policies
  type: list
  returned: when listing policies or querying by title
  sample:
    - title: "Policy 1"
      _key: "policy1"
    - title: "Policy 2"
      _key: "policy2"
status:
  description: HTTP status code from the API response
  type: int
  returned: always
  sample: 200
headers:
  description: HTTP response headers from the API
  type: dict
  returned: always
  sample: {"content-type": "application/json"}
"""

# Ansible imports
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection

# Import shared utilities
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_utils import (
    get_aggregation_policies_by_title,
    get_aggregation_policy_by_id,
    list_aggregation_policies,
)


def _normalize_response_data(data):
    """Ensure data is a dict with expected keys for safe access."""
    if isinstance(data, dict):
        return data
    return {"aggregation_policies": [], "_response_headers": {}}


def _query_by_policy_id(client, policy_id, fields):
    """Query a specific aggregation policy by ID."""
    status, data = get_aggregation_policy_by_id(client, policy_id, fields)
    headers = data.get("_response_headers", {}) if isinstance(data, dict) else {}

    result = {"status": status, "headers": headers}
    result["aggregation_policy"] = data if status == 200 else None
    return result


def _query_by_title(client, title, fields):
    """Query aggregation policies by title (may return multiple)."""
    status, data = get_aggregation_policies_by_title(client, title, fields)
    data = _normalize_response_data(data)
    policies = data.get("aggregation_policies", [])

    result = {
        "status": status,
        "headers": data.get("_response_headers", {}),
        "aggregation_policies": policies,
    }

    # For convenience, also set aggregation_policy if exactly one or zero results
    result["aggregation_policy"] = policies[0] if len(policies) == 1 else None
    return result


def _list_all_policies(client, fields, filter_data, limit):
    """List all aggregation policies."""
    status, data = list_aggregation_policies(client, fields, filter_data, limit)
    data = _normalize_response_data(data)

    return {
        "status": status,
        "headers": data.get("_response_headers", {}),
        "aggregation_policies": data.get("aggregation_policies", []),
    }


def main():
    """Main module function."""

    # Define module arguments
    module_args = dict(
        policy_id=dict(type="str", required=False),
        title=dict(type="str", required=False),
        fields=dict(type="str", required=False),
        filter_data=dict(type="str", required=False),
        limit=dict(type="int", required=False),
    )

    # Initialize module
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    try:
        client = ItsiRequest(Connection(module._socket_path))
        policy_id = module.params.get("policy_id")
        title = module.params.get("title")
        fields = module.params.get("fields")

        # Route to appropriate query function
        if policy_id:
            result = _query_by_policy_id(client, policy_id, fields)
        elif title:
            result = _query_by_title(client, title, fields)
        else:
            filter_data = module.params.get("filter_data")
            limit = module.params.get("limit")
            result = _list_all_policies(client, fields, filter_data, limit)

        result["changed"] = False
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(
            msg=f"Exception occurred: {str(e)}",
            policy_id=module.params.get("policy_id"),
            title=module.params.get("title"),
        )


if __name__ == "__main__":
    main()
