#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Ansible module for managing Splunk ITSI aggregation policies."""


DOCUMENTATION = r"""
---
module: itsi_aggregation_policy
short_description: Manage Splunk ITSI aggregation policies
description:
  - Create, update, and delete aggregation policies in Splunk IT Service Intelligence (ITSI).
  - An aggregation policy determines how notable events are grouped together into episodes.
  - Uses the ITSI Event Management Interface REST API for CRUD operations.
  - For querying/listing policies, use the C(itsi_aggregation_policy_info) module.
version_added: "1.0.0"
author:
  - Ansible Ecosystem Engineering team (@ansible)
options:
  title:
    description:
      - The title/name of the aggregation policy.
      - Required when creating a new policy (C(state=present) without C(policy_id)).
      - Optional when updating an existing policy (C(state=present) with C(policy_id)).
      - Note that multiple policies can have the same title.
    type: str
    required: false
  policy_id:
    description:
      - The aggregation policy ID/key (unique identifier).
      - For C(state=present) with C(policy_id), looks up the policy and updates only changed fields (idempotent).
      - For C(state=present) without C(policy_id), a new policy is always created (C(title) required).
      - For C(state=absent), required to identify which policy to delete.
    type: str
    required: false
  state:
    description:
      - Desired state of the aggregation policy.
      - C(present) ensures the aggregation policy exists with specified configuration.
      - C(absent) ensures the aggregation policy is deleted.
    type: str
    choices: ['present', 'absent']
    default: 'present'
  description:
    description:
      - Description of the aggregation policy purpose and functionality.
    type: str
    required: false
  disabled:
    description:
      - Whether the aggregation policy is disabled.
      - Use C(false) to enable, C(true) to disable.
    type: bool
    required: false
  filter_criteria:
    description:
      - Filter criteria that determines which notable events this policy applies to.
      - Dictionary with 'condition' (AND/OR) and 'items' array.
    type: dict
    required: false
  breaking_criteria:
    description:
      - Breaking criteria that determines when to create a new episode.
      - Dictionary with 'condition' (AND/OR) and 'items' array.
    type: dict
    required: false
  group_severity:
    description:
      - Default severity level for episodes created by this policy.
      - Common values are 'info', 'low', 'medium', 'high', 'critical'.
    type: str
    required: false
  group_status:
    description:
      - Default status for episodes created by this policy.
      - Common values are 'new', 'in_progress', 'pending', 'resolved', 'closed'.
    type: str
    required: false
  group_assignee:
    description:
      - Default assignee for episodes created by this policy.
    type: str
    required: false
  group_title:
    description:
      - Template for episode titles created by this policy.
      - Can use field substitution like '%title%', '%description%'.
    type: str
    required: false
  group_description:
    description:
      - Template for episode descriptions created by this policy.
      - Can use field substitution like '%title%', '%description%'.
    type: str
    required: false
  split_by_field:
    description:
      - Field to split episodes by (creates separate episodes per unique value).
    type: str
    required: false
  priority:
    description:
      - Priority level of the aggregation policy (1-10).
    type: int
    required: false
  rules:
    description:
      - List of action rules to execute when episodes are created.
      - Each rule is a dictionary with activation criteria and actions.
    type: list
    elements: dict
    required: false
  additional_fields:
    description:
      - Dictionary of additional fields to set on the aggregation policy.
      - Allows setting any valid policy field not covered by specific parameters.
    type: dict
    required: false
    default: {}

requirements:
  - Connection configuration requires C(ansible_connection=httpapi) and C(ansible_network_os=splunk.itsi.itsi_api_client).
  - Authentication via Bearer token, session key, or username/password as documented in the httpapi plugin.

notes:
  - This module manages ITSI aggregation policies using the event_management_interface/notable_event_aggregation_policy endpoint.
  - For C(state=present) with C(policy_id), the module performs idempotent updates - only changes fields that differ. Title is optional.
  - For C(state=present) without C(policy_id), a new policy is always created. Title is required.
  - For C(state=absent), C(policy_id) is required to identify which policy to delete.
  - Update operations modify only the specified fields, leaving other configuration unchanged.
  - To query or list policies, use the C(itsi_aggregation_policy_info) module.

seealso:
  - module: splunk.itsi.itsi_aggregation_policy_info
    description: Use this module to query and list aggregation policies.
"""

EXAMPLES = r"""
# Create new aggregation policy (no policy_id = always creates new)
- name: Create new aggregation policy
  splunk.itsi.itsi_aggregation_policy:
    title: "Test Aggregation Policy (Ansible)"
    description: "Test policy created by Ansible"
    disabled: false
    priority: 5
    group_severity: "medium"
    group_status: "new"
    group_title: "%title%"
    group_description: "%description%"
    filter_criteria:
      condition: "AND"
      items: []
    breaking_criteria:
      condition: "AND"
      items: []
    state: present
  register: create_result
# create_result.response._key contains the generated policy_id

# Update existing aggregation policy (policy_id required, title optional)
- name: Update aggregation policy settings
  splunk.itsi.itsi_aggregation_policy:
    policy_id: "{{ create_result.response._key }}"
    group_severity: "high"
    disabled: false
    state: present
  register: update_result
# update_result.diff shows fields that changed

# Update using additional fields
- name: Update aggregation policy with custom fields
  splunk.itsi.itsi_aggregation_policy:
    policy_id: "test_policy_key"
    additional_fields:
      split_by_field: "source"
      sub_group_limit: "100"
    state: present

# Delete aggregation policy (policy_id required)
- name: Remove aggregation policy
  splunk.itsi.itsi_aggregation_policy:
    policy_id: "{{ create_result.response._key }}"
    state: absent
  register: delete_result

# Create with error handling
- name: Create aggregation policy
  splunk.itsi.itsi_aggregation_policy:
    title: "Critical Service Alert Policy"
    description: "Groups critical service alerts"
    group_severity: "critical"
    state: present
  register: result
"""

RETURN = r"""
changed:
  description: Whether the aggregation policy was modified.
  type: bool
  returned: always
  sample: true
before:
  description: Policy state before the operation. Empty dict on create or when already absent.
  type: dict
  returned: always
  sample:
    group_severity: "medium"
    disabled: 0
after:
  description: Policy state after the operation. Empty dict on delete.
  type: dict
  returned: always
  sample:
    group_severity: "high"
    disabled: 0
diff:
  description: Fields that differ between before and after. Empty dict when unchanged.
  type: dict
  returned: always
  sample:
    group_severity: "high"
response:
  description: Raw HTTP API response body from the last API call.
  type: dict
  returned: always
  sample:
    _key: "policy123"
    title: "Default Policy"
"""

# Standard library imports
import json
from urllib.parse import quote_plus

# Ansible imports
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.splunk.itsi.plugins.module_utils.aggregation_policy_utils import (
    BASE_AGGREGATION_POLICY_ENDPOINT,
    flatten_policy_object,
    get_aggregation_policy_by_id,
)

# Import shared utilities
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest


def _normalize_disabled_value(value):
    """Normalize boolean-like disabled field to integer (0 or 1)."""
    if isinstance(value, bool):
        return 1 if value else 0
    if str(value).isdigit():
        return int(value)
    if str(value).lower() in ("true", "1", "yes"):
        return 1
    return 0


# Fields to copy directly during canonicalization
_CANONICAL_FIELDS = (
    "title",
    "description",
    "priority",
    "split_by_field",
    "group_severity",
    "group_status",
    "group_assignee",
    "group_title",
    "group_description",
    "filter_criteria",
    "breaking_criteria",
    "rules",
)


def _canonicalize_policy(payload):
    """
    Reduce an object to just the fields we compare/update. Handles both
    desired (module args) and current (Splunk GET) shapes.
    """
    if not isinstance(payload, dict):
        return {}

    # Unwrap to content if needed
    if "entry" in payload or "content" in payload:
        payload = flatten_policy_object(payload)

    out = {}

    # Copy all canonical fields that exist in source
    for field in _CANONICAL_FIELDS:
        if field in payload:
            out[field] = payload[field]

    # Normalize boolean-like disabled field
    if "disabled" in payload:
        out["disabled"] = _normalize_disabled_value(payload["disabled"])

    return out


def _diff_canonical(desired_canon, current_canon):
    """Return a shallow diff: {field: (current, desired)} where values differ."""
    diffs = {}
    # Only compare fields that are explicitly provided by the user
    for k in desired_canon.keys():
        dv = desired_canon.get(k)
        cv = current_canon.get(k)

        # Special handling for complex objects
        if k in ("filter_criteria", "breaking_criteria", "rules"):
            if json.dumps(dv, sort_keys=True) != json.dumps(cv, sort_keys=True):
                diffs[k] = (cv, dv)
        elif str(dv) != str(cv):
            diffs[k] = (cv, dv)

    return diffs


def create_aggregation_policy(client, policy_data):
    """Create a new aggregation policy via EMI."""
    payload = {
        "title": policy_data.get("title", "Unnamed Policy"),
        "filter_criteria": policy_data.get("filter_criteria", {"condition": "AND", "items": []}),
        "breaking_criteria": policy_data.get("breaking_criteria", {"condition": "AND", "items": []}),
        "group_severity": policy_data.get("group_severity", "normal"),
        "rules": policy_data.get("rules", []),
    }
    for key, value in policy_data.items():
        if key not in payload:
            payload[key] = value
    params = {"output_mode": "json"}
    return client.post(BASE_AGGREGATION_POLICY_ENDPOINT, params=params, payload=payload)


def update_aggregation_policy(client, policy_id, update_data, current_data):
    """Update aggregation policy via EMI with is_partial_data=1.

    Args:
        current_data: Current policy body (avoids a redundant GET).
    """
    path = f"{BASE_AGGREGATION_POLICY_ENDPOINT}/{quote_plus(policy_id)}"
    params = {"output_mode": "json", "is_partial_data": "1"}
    payload = {
        "title": update_data.get("title", current_data.get("title")),
        "filter_criteria": update_data.get("filter_criteria", current_data.get("filter_criteria", {"condition": "AND", "items": []})),
        "breaking_criteria": update_data.get("breaking_criteria", current_data.get("breaking_criteria", {"condition": "AND", "items": []})),
        "group_severity": update_data.get("group_severity", current_data.get("group_severity", "normal")),
        "rules": update_data.get("rules", current_data.get("rules", [])),
    }
    for key, value in update_data.items():
        if key not in payload:
            payload[key] = value
    return client.post(path, params=params, payload=payload)


def delete_aggregation_policy(client, policy_id):
    """Delete an aggregation policy by ID."""
    path = f"{BASE_AGGREGATION_POLICY_ENDPOINT}/{quote_plus(policy_id)}"
    params = {"output_mode": "json"}
    return client.delete(path, params=params)


# ------------------------------------------------------------------
# Business logic
# ------------------------------------------------------------------


def _build_desired_data(params):
    """Build desired data dictionary from module parameters."""
    field_names = (
        "title",
        "description",
        "disabled",
        "filter_criteria",
        "breaking_criteria",
        "group_severity",
        "group_status",
        "group_assignee",
        "group_title",
        "group_description",
        "split_by_field",
        "priority",
        "rules",
    )
    desired_data = {}
    for field_name in field_names:
        field_value = params.get(field_name)
        if field_value is not None:
            desired_data[field_name] = field_value
    additional_fields = params.get("additional_fields", {})
    if additional_fields:
        desired_data.update(additional_fields)
    return desired_data


def _handle_state_present(module, client, result):
    """Handle state=present logic."""
    policy_id = module.params.get("policy_id")
    title = module.params.get("title")

    if not policy_id and not title:
        module.fail_json(msg="'title' is required when creating a new policy (no policy_id provided)")

    desired_data = _build_desired_data(module.params)

    # --- Create (no policy_id) ---
    if not policy_id:
        result["before"] = {}
        result["after"] = desired_data
        result["diff"] = desired_data
        result["changed"] = True
        if not module.check_mode:
            _status, _hdr, body = create_aggregation_policy(client, desired_data)
            result["response"] = body
            # Create response may only include an identifier. Re-fetch to return
            # the full created policy object in `after`.
            created_policy_id = body.get("_key") if isinstance(body, dict) else None
            if created_policy_id:
                get_created = get_aggregation_policy_by_id(client, created_policy_id)
                if get_created is not None:
                    _c_status, _c_hdr, created_obj = get_created
                    result["after"] = created_obj
                else:
                    result["after"] = body
            else:
                result["after"] = body
        return

    # --- Update (policy_id provided) ---
    get_result = get_aggregation_policy_by_id(client, policy_id)
    if get_result is None:
        module.fail_json(msg=f"Policy with ID '{policy_id}' not found")
        return

    _cur_status, _cur_hdr, current_data = get_result
    result["before"] = current_data

    # Idempotency check
    current_canon = _canonicalize_policy(current_data)
    desired_canon = _canonicalize_policy(desired_data)
    diff_check = _diff_canonical(desired_canon, current_canon)

    if not diff_check:
        result["after"] = current_data
        return

    # Build a simple diff: {field: new_value}
    diff = {k: v[1] for k, v in diff_check.items()}
    after = dict(current_data)
    after.update(desired_canon)

    result["changed"] = True
    result["diff"] = diff
    result["after"] = after

    if not module.check_mode:
        _status, _hdr, body = update_aggregation_policy(client, policy_id, desired_canon, current_data)
        result["response"] = body


def _handle_state_absent(module, client, result):
    """Handle state=absent logic."""
    policy_id = module.params.get("policy_id")

    if not policy_id:
        module.fail_json(msg="'policy_id' is required for absent state (titles are not unique)")

    get_result = get_aggregation_policy_by_id(client, policy_id)

    if get_result is None:
        # Already absent
        return

    _cur_status, _cur_hdr, current_data = get_result
    result["changed"] = True
    result["before"] = current_data
    result["diff"] = current_data

    if not module.check_mode:
        del_result = delete_aggregation_policy(client, policy_id)
        if del_result is not None:
            _status, _hdr, body = del_result
            result["response"] = body


def main():
    """Main module function."""
    module_args = dict(
        title=dict(type="str", required=False),
        policy_id=dict(type="str", required=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        description=dict(type="str", required=False),
        disabled=dict(type="bool", required=False),
        filter_criteria=dict(type="dict", required=False),
        breaking_criteria=dict(type="dict", required=False),
        group_severity=dict(type="str", required=False),
        group_status=dict(type="str", required=False),
        group_assignee=dict(type="str", required=False),
        group_title=dict(type="str", required=False),
        group_description=dict(type="str", required=False),
        split_by_field=dict(type="str", required=False),
        priority=dict(type="int", required=False),
        rules=dict(type="list", elements="dict", required=False),
        additional_fields=dict(type="dict", required=False, default={}),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not getattr(module, "_socket_path", None):
        module.fail_json(msg="Use ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client")

    client = ItsiRequest(Connection(module._socket_path), module)
    result = {"changed": False, "before": {}, "after": {}, "diff": {}, "response": {}}

    state = module.params["state"]
    if state == "present":
        _handle_state_present(module, client, result)
    elif state == "absent":
        _handle_state_absent(module, client, result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
