#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers

DOCUMENTATION = r"""
---
module: itsi_correlation_search
short_description: Manage Splunk ITSI correlation searches
description:
  - Create, update, and delete correlation searches in Splunk IT Service Intelligence (ITSI).
  - A correlation search is a recurring search that generates a notable event when search results meet specific conditions.
  - Multi-KPI alerts are a type of correlation search.
  - Uses the ITSI Event Management Interface REST API for full CRUD operations.
  - For querying correlation searches, use the C(itsi_correlation_search_info) module.
version_added: "1.0.0"
author:
  - Ansible Ecosystem Engineering team (@ansible)
options:
  name:
    description:
      - The name/title of the correlation search.
      - Required for create operations.
      - Used for lookup when correlation_search_id is not provided.
    type: str
    required: false
  correlation_search_id:
    description:
      - The correlation search ID for direct lookup.
      - This is the internal identifier (often the saved search name).
      - Takes precedence over name parameter for update/delete operations.
      - For new correlation searches, this becomes the search name.
    type: str
    required: false
  state:
    description:
      - Desired state of the correlation search.
      - C(present) ensures the correlation search exists with specified configuration.
      - C(absent) ensures the correlation search is deleted.
    type: str
    choices: ['present', 'absent']
    default: 'present'
  search:
    description:
      - The SPL search query for the correlation search.
      - Required when creating new correlation searches.
    type: str
    required: false
  disabled:
    description:
      - Whether the correlation search is disabled.
      - Use C(false) to enable, C(true) to disable.
    type: bool
    required: false
  cron_schedule:
    description:
      - Cron schedule for the correlation search execution.
      - Standard cron format (e.g., "*/5 * * * *" for every 5 minutes).
    type: str
    required: false
  earliest_time:
    description:
      - Earliest time for the search window (e.g., "-15m", "-1h").
    type: str
    required: false
  latest_time:
    description:
      - Latest time for the search window (e.g., "now", "-5m").
    type: str
    required: false
  description:
    description:
      - Description of the correlation search purpose and functionality.
    type: str
    required: false
  actions:
    description:
      - Comma-separated list of actions to trigger.
      - Required for correlation searches to appear in the ITSI GUI.
    type: str
    required: false
    default: "itsi_event_generator"
  additional_fields:
    description:
      - Dictionary of additional fields to set on the correlation search.
      - Allows setting any valid correlation search field not covered by specific parameters.
    type: dict
    required: false

requirements:
  - Connection configuration requires C(ansible_connection=httpapi) and C(ansible_network_os=splunk.itsi.itsi_api_client).
  - Authentication via Bearer token, session key, or username/password as documented in the httpapi plugin.

notes:
  - This module manages ITSI correlation searches using the event_management_interface/correlation_search endpoint.
  - When creating correlation searches, the C(name) or C(correlation_search_id) and C(search) parameters are required.
  - Update operations modify only the specified fields, leaving other configuration unchanged.
  - The correlation search must exist before updating or deleting it.
  - For querying correlation searches, use the C(itsi_correlation_search_info) module.
"""

EXAMPLES = r"""
# Create new correlation search
- name: Create new correlation search
  splunk.itsi.itsi_correlation_search:
    name: "test-corrsearch-ansible"
    search: "index=itsi | head 1"
    description: "Test correlation search created by Ansible"
    disabled: false
    cron_schedule: "*/10 * * * *"
    earliest_time: "-15m"
    latest_time: "now"
    actions: "itsi_event_generator"
    state: present
  register: create_result

# Update existing correlation search
- name: Update correlation search schedule
  splunk.itsi.itsi_correlation_search:
    correlation_search_id: "test-corrsearch-ansible"
    cron_schedule: "*/5 * * * *"
    disabled: false
    state: present
  register: update_result

# Update using additional fields
- name: Update correlation search with custom fields
  splunk.itsi.itsi_correlation_search:
    correlation_search_id: "test-corrsearch-ansible"
    additional_fields:
      priority: "high"
      custom_field: "custom_value"
    state: present

# Delete correlation search by ID
- name: Remove correlation search
  splunk.itsi.itsi_correlation_search:
    correlation_search_id: "test-corrsearch-ansible"
    state: absent
  register: delete_result

# Delete correlation search by name
- name: Remove correlation search by name
  splunk.itsi.itsi_correlation_search:
    name: "test-corrsearch-ansible"
    state: absent

# Error handling example
- name: Create correlation search with error handling
  splunk.itsi.itsi_correlation_search:
    name: "monitoring-alert"
    search: "index=main error | stats count"
    state: present
  register: result
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
changed:
  description: Whether the correlation search was modified
  returned: always
  type: bool
  sample: true
operation:
  description: The operation that was performed (create, update, delete, no_change)
  returned: always
  type: str
  sample: "create"
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.parse import quote, quote_plus
from ansible_collections.splunk.itsi.plugins.module_utils.correlation_search_utils import (
    BASE_EVENT_MGMT,
    flatten_search_object,
    get_correlation_search,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

# Field name constants for dispatch time settings
DISPATCH_EARLIEST_TIME = "dispatch.earliest_time"
DISPATCH_LATEST_TIME = "dispatch.latest_time"

# ---- Tiny idempotency & shape-refactor helpers ---------------------------------
COMPARE_FIELDS = [
    "search",
    "disabled",
    "cron_schedule",
    "earliest_time",
    "latest_time",
    "description",
    "actions",
    DISPATCH_EARLIEST_TIME,
    DISPATCH_LATEST_TIME,
]


def _normalize_disabled(value) -> str:
    """Normalize disabled field to string '0' or '1'."""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def _canonicalize(payload):
    """
    Reduce an object to just the fields we compare/update. Handles both
    desired (module args) and current (Splunk GET) shapes.
    """
    if not isinstance(payload, dict):
        return {}
    # Unwrap to content if needed
    if "entry" in payload or "content" in payload:
        payload = flatten_search_object(payload)

    out = {}
    # Map time fields (dispatch.* or short form)
    time_field_map = [
        (DISPATCH_EARLIEST_TIME, "earliest_time"),
        (DISPATCH_LATEST_TIME, "latest_time"),
    ]
    for dispatch_key, short_key in time_field_map:
        if dispatch_key in payload or short_key in payload:
            out[dispatch_key] = payload.get(dispatch_key, payload.get(short_key))

    # Copy passthrough fields
    for k in ("search", "description", "cron_schedule", "actions"):
        if k in payload:
            out[k] = payload[k]

    # Normalize boolean-like disabled field
    if "disabled" in payload:
        out["disabled"] = _normalize_disabled(payload["disabled"])

    return out


def _diff_canonical(desired_canon, current_canon):
    """Return a shallow diff: {field: (current, desired)} where values differ."""
    diffs = {}
    # Only compare fields that are explicitly provided by the user
    for k in desired_canon.keys():
        dv = desired_canon.get(k)
        cv = current_canon.get(k)
        # treat None and "" as equal for time fields
        if k.startswith("dispatch.") and (dv in (None, "") and cv in (None, "")):
            continue
        if str(dv) != str(cv):
            diffs[k] = (cv, dv)
    return diffs


def create_correlation_search(client, search_data):
    """Create a new correlation search via EMI."""
    payload = dict(search_data)
    if DISPATCH_EARLIEST_TIME in payload:
        payload["earliest_time"] = payload.pop(DISPATCH_EARLIEST_TIME)
    if DISPATCH_LATEST_TIME in payload:
        payload["latest_time"] = payload.pop(DISPATCH_LATEST_TIME)
    if "earliest_time" in payload:
        payload[DISPATCH_EARLIEST_TIME] = payload["earliest_time"]
    if "latest_time" in payload:
        payload[DISPATCH_LATEST_TIME] = payload["latest_time"]
    params = {"output_mode": "json"}
    return client.post(BASE_EVENT_MGMT, params=params, payload=payload)


def update_correlation_search(client, search_identifier, update_data):
    """Update correlation search via EMI with is_partial_data=1."""
    path = f"{BASE_EVENT_MGMT}/{quote_plus(search_identifier)}"
    params = {"output_mode": "json", "is_partial_data": "1"}
    payload = {"name": search_identifier}
    if update_data:
        u = dict(update_data)
        if DISPATCH_EARLIEST_TIME in u:
            u["earliest_time"] = u[DISPATCH_EARLIEST_TIME]
        if DISPATCH_LATEST_TIME in u:
            u["latest_time"] = u[DISPATCH_LATEST_TIME]
        payload.update(u)
    return client.post(path, params=params, payload=payload)


def delete_correlation_search(client, search_identifier, use_name_encoding=False):
    """Delete a correlation search."""
    if use_name_encoding:
        path = f"{BASE_EVENT_MGMT}/{quote(search_identifier, safe='')}"
    else:
        path = f"{BASE_EVENT_MGMT}/{quote_plus(search_identifier)}"
    params = {"output_mode": "json"}
    return client.delete(path, params=params)


def _should_set_is_scheduled(existing_flat: dict, diff: dict) -> bool:
    """Check if is_scheduled should be set to '1' during update."""
    if "cron_schedule" not in diff:
        return False
    current_is_scheduled = str(existing_flat.get("is_scheduled", "0")).lower() in ("1", "true")
    return not current_is_scheduled


# ------------------------------------------------------------------
# Result helper
# ------------------------------------------------------------------


def _result(changed, status, headers, body, **extra):
    """Build a unified result dict."""
    r = {"changed": changed, "status": status, "headers": headers, "body": body}
    r.update(extra)
    return r


# ------------------------------------------------------------------
# Business logic
# ------------------------------------------------------------------


def _build_desired_data(params: dict, search_identifier: str) -> dict:
    """Build desired data dictionary from module parameters."""
    desired_data = {"name": search_identifier}
    if params.get("search"):
        desired_data["search"] = params["search"]
    if params.get("disabled") is not None:
        desired_data["disabled"] = params["disabled"]
    for field in ("cron_schedule", "earliest_time", "latest_time", "description", "actions"):
        if params.get(field):
            desired_data[field] = params[field]
    if params.get("additional_fields"):
        desired_data.update(params["additional_fields"])
    return desired_data


def _handle_state_present(module, client, params: dict, result: dict):
    """Handle state=present logic."""
    name = params.get("name")
    correlation_search_id = params.get("correlation_search_id")
    search_identifier = correlation_search_id or name

    if not search_identifier:
        module.fail_json(msg="Either 'name' or 'correlation_search_id' is required for present state")

    use_name_encoding = correlation_search_id is None and name is not None
    current = get_correlation_search(client, search_identifier, use_name_encoding=use_name_encoding)
    exists = current is not None

    if not exists and not params.get("search"):
        module.fail_json(msg="'search' parameter is required when creating new correlation search")

    desired_data = _build_desired_data(params, search_identifier)

    if module.check_mode:
        result.update(
            _result(
                True,
                0,
                {},
                desired_data,
                check_mode=True,
                operation="update" if exists else "create",
            ),
        )
        return

    # Create
    if not exists:
        _status, _hdr, _body = create_correlation_search(client, desired_data)
        # Re-fetch to get the uniform flattened shape
        after = get_correlation_search(client, search_identifier, use_name_encoding=use_name_encoding)
        body = after[2] if after is not None else {}
        result.update(_result(True, _status, _hdr, body))
        return

    # Update path – idempotency check
    _cur_status, cur_hdr, cur_obj = current
    existing_flat = flatten_search_object(cur_obj) if isinstance(cur_obj, dict) else {}
    current_c = _canonicalize(existing_flat)
    desired_c = _canonicalize(desired_data)

    complete_desired = dict(current_c)
    complete_desired.update(desired_c)
    diff = _diff_canonical(complete_desired, current_c)

    if not diff:
        result.update(_result(False, _cur_status, cur_hdr, cur_obj))
        return

    update_payload = dict(desired_c)
    if _should_set_is_scheduled(existing_flat, diff):
        update_payload["is_scheduled"] = "1"

    _status, _hdr, _body = update_correlation_search(client, search_identifier, update_payload)
    result.update(_result(True, _status, _hdr, _body, diff=diff))


def _handle_absent_state(module, client, params: dict, result: dict):
    """Handle state=absent logic."""
    name = params.get("name")
    correlation_search_id = params.get("correlation_search_id")
    search_identifier = correlation_search_id or name

    if not search_identifier:
        module.fail_json(msg="Either 'name' or 'correlation_search_id' is required for absent state")

    use_name_encoding = correlation_search_id is None and name is not None
    exists = get_correlation_search(client, search_identifier, use_name_encoding=use_name_encoding) is not None

    if not exists:
        result.update(_result(False, 0, {}, {}, msg="Correlation search already absent"))
        return

    if module.check_mode:
        result.update(_result(True, 0, {}, {}, check_mode=True))
        return

    del_result = delete_correlation_search(client, search_identifier, use_name_encoding=use_name_encoding)
    if del_result is None:
        result.update(_result(True, 0, {}, {}))
    else:
        _status, _hdr, body = del_result
        result.update(_result(True, _status, _hdr, body))


def main():
    """Main module execution."""
    module_args = dict(
        name=dict(type="str", required=False),
        correlation_search_id=dict(type="str", required=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        search=dict(type="str", required=False),
        disabled=dict(type="bool", required=False),
        cron_schedule=dict(type="str", required=False),
        earliest_time=dict(type="str", required=False),
        latest_time=dict(type="str", required=False),
        description=dict(type="str", required=False),
        actions=dict(type="str", required=False, default="itsi_event_generator"),
        additional_fields=dict(type="dict", required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if not getattr(module, "_socket_path", None):
        module.fail_json(msg="Use ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client")

    client = ItsiRequest(Connection(module._socket_path), module)
    result = {"changed": False, "status": 0, "headers": {}, "body": {}}

    state = module.params["state"]
    if state == "present":
        _handle_state_present(module, client, module.params, result)
    elif state == "absent":
        _handle_absent_state(module, client, module.params, result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
