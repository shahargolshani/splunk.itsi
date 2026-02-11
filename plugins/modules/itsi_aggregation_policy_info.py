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
      - Returns a single-element list in C(aggregation_policies).
    type: str
    required: false
  title:
    description:
      - The title/name of the aggregation policy to search for.
      - Note that multiple policies can have the same title.
      - Returns all matching policies in C(aggregation_policies) list.
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
  - When querying by C(policy_id), returns a single-element list in C(aggregation_policies).
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

# Get aggregation policy by ID (returns single-element list)
- name: Get aggregation policy by ID
  splunk.itsi.itsi_aggregation_policy_info:
    policy_id: "itsi_default_policy"
  register: policy_by_id
# Access: policy_by_id.aggregation_policies[0]

# Get aggregation policies by title (may return multiple)
- name: Get all aggregation policies with a specific title
  splunk.itsi.itsi_aggregation_policy_info:
    title: "Default Policy"
  register: policies_by_title
# Access: policies_by_title.aggregation_policies (list of all matching)

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
aggregation_policies:
  description: List of aggregation policies matching the query
  type: list
  elements: dict
  returned: always
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
from typing import Any, Optional, Tuple

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.splunk.itsi.plugins.module_utils.aggregation_policy_utils import (
    get_aggregation_policy_by_id,
    list_aggregation_policies,
)

# Import shared utilities
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest


def get_aggregation_policies_by_title(
    client: Any,
    title: str,
    fields: Optional[str] = None,
) -> Optional[Tuple[int, dict, Any]]:
    """Get aggregation policies by title (client-side filtering).

    Returns:
        ``(status, headers, {"aggregation_policies": [...]})`` or ``None``.
    """
    result = list_aggregation_policies(client, fields=fields)
    if result is None:
        return None
    status, headers, body = result
    all_policies = body.get("aggregation_policies", [])
    matching = [p for p in all_policies if isinstance(p, dict) and p.get("title") == title]
    return status, headers, {"aggregation_policies": matching}


def _query_by_policy_id(client, policy_id, fields):
    """Query a specific aggregation policy by ID."""
    api_result = get_aggregation_policy_by_id(client, policy_id, fields)
    if api_result is None:
        return {"status": 0, "headers": {}, "body": {}, "aggregation_policies": []}
    status, headers, body = api_result
    return {"status": status, "headers": headers, "body": body, "aggregation_policies": [body]}


def _query_by_title(client, title, fields):
    """Query aggregation policies by title (may return multiple)."""
    api_result = get_aggregation_policies_by_title(client, title, fields)
    if api_result is None:
        return {"status": 0, "headers": {}, "body": {}, "aggregation_policies": []}
    status, headers, body = api_result
    policies = body.get("aggregation_policies", []) if isinstance(body, dict) else []
    return {"status": status, "headers": headers, "body": body, "aggregation_policies": policies}


def _list_all_policies(client, fields, filter_data, limit):
    """List all aggregation policies."""
    api_result = list_aggregation_policies(client, fields, filter_data, limit)
    if api_result is None:
        return {"status": 0, "headers": {}, "body": {}, "aggregation_policies": []}
    status, headers, body = api_result
    policies = body.get("aggregation_policies", []) if isinstance(body, dict) else []
    return {"status": status, "headers": headers, "body": body, "aggregation_policies": policies}


def main():
    """Main module function."""
    module_args = dict(
        policy_id=dict(type="str", required=False),
        title=dict(type="str", required=False),
        fields=dict(type="str", required=False),
        filter_data=dict(type="str", required=False),
        limit=dict(type="int", required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not getattr(module, "_socket_path", None):
        module.fail_json(msg="Use ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client")

    client = ItsiRequest(Connection(module._socket_path), module)
    policy_id = module.params.get("policy_id")
    title = module.params.get("title")
    fields = module.params.get("fields")

    if policy_id:
        result = _query_by_policy_id(client, policy_id, fields)
    elif title:
        result = _query_by_title(client, title, fields)
    else:
        result = _list_all_policies(client, fields, module.params.get("filter_data"), module.params.get("limit"))

    result["changed"] = False
    module.exit_json(**result)


if __name__ == "__main__":
    main()
