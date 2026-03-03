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
changed:
  description: Whether the correlation search was modified.
  type: bool
  returned: always
  sample: true
before:
  description: Search state before the operation. Empty dict on create or when already absent.
  type: dict
  returned: always
  sample:
    search: "index=itsi | head 1"
    disabled: "0"
after:
  description: Search state after the operation. Empty dict on delete.
  type: dict
  returned: always
  sample:
    search: "index=itsi | head 1"
    disabled: "0"
diff:
  description: Fields that differ between before and after. Empty dict when unchanged.
  type: dict
  returned: always
  sample:
    cron_schedule: "*/5 * * * *"
response:
  description: Raw HTTP API response body from the last API call.
  type: dict
  returned: always
  sample:
    name: "test-search"
    disabled: "0"
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.parse import quote, quote_plus
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.splunk.itsi.plugins.module_utils.correlation_search_utils import (
    BASE_EVENT_MGMT,
    get_correlation_search,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest
from ansible_collections.splunk.itsi.plugins.module_utils.splunk_utils import (
    build_have_conf,
    exit_with_result,
)

# Field name constants for dispatch time settings
DISPATCH_EARLIEST_TIME = "dispatch.earliest_time"
DISPATCH_LATEST_TIME = "dispatch.latest_time"


def _normalize_disabled(value) -> str:
    """Normalize disabled field to string '0' or '1'."""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


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
# Business logic
# ------------------------------------------------------------------


def _build_desired_data(params: dict, search_identifier: str) -> dict:
    """Build desired data dictionary from module parameters.

    Normalizes types to match the API response format so ``dict_diff``
    does not see phantom changes:
    - ``disabled``: bool -> string ``"0"``/``"1"``
    - ``earliest_time`` -> ``dispatch.earliest_time``
    - ``latest_time`` -> ``dispatch.latest_time``
    """
    desired_data = {"name": search_identifier}
    if params.get("search"):
        desired_data["search"] = params["search"]
    if params.get("disabled") is not None:
        desired_data["disabled"] = _normalize_disabled(params["disabled"])
    for field in ("cron_schedule", "description", "actions"):
        if params.get(field):
            desired_data[field] = params[field]
    if params.get("earliest_time"):
        desired_data[DISPATCH_EARLIEST_TIME] = params["earliest_time"]
    if params.get("latest_time"):
        desired_data[DISPATCH_LATEST_TIME] = params["latest_time"]
    if params.get("additional_fields"):
        desired_data.update(params["additional_fields"])
    return desired_data


def _handle_state_present(module, client, params: dict):
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

    # --- Create ---
    if not exists:
        if module.check_mode:
            exit_with_result(module, changed=True, after=desired_data, diff=desired_data)

        _status, _hdr, body = create_correlation_search(client, desired_data)
        after = desired_data
        refetched = get_correlation_search(client, search_identifier, use_name_encoding=use_name_encoding)
        if refetched is not None:
            after = refetched[2]
        exit_with_result(module, changed=True, after=after, diff=desired_data, response=body)

    # --- Update ---
    _cur_status, _cur_hdr, cur_obj = current

    have_conf = build_have_conf(
        desired_data,
        cur_obj,
        normalizers={"disabled": _normalize_disabled},
        exclude_keys={"name"},
    )
    want_conf: dict = {k: v for k, v in utils.remove_empties(desired_data).items() if k != "name"}
    diff: dict = utils.dict_diff(have_conf, want_conf)

    after: dict = dict(cur_obj)
    after.update(want_conf)

    if not diff:
        exit_with_result(module, before=cur_obj, after=cur_obj)

    if module.check_mode:
        exit_with_result(module, changed=True, before=cur_obj, after=after, diff=diff)

    update_payload = dict(want_conf)
    if _should_set_is_scheduled(cur_obj, diff):
        update_payload["is_scheduled"] = "1"
    _status, _hdr, body = update_correlation_search(client, search_identifier, update_payload)
    exit_with_result(
        module,
        changed=True,
        before=cur_obj,
        after=after,
        diff=diff,
        response=body,
    )


def _handle_absent_state(module, client, params: dict):
    """Handle state=absent logic."""
    name = params.get("name")
    correlation_search_id = params.get("correlation_search_id")
    search_identifier = correlation_search_id or name

    if not search_identifier:
        module.fail_json(msg="Either 'name' or 'correlation_search_id' is required for absent state")

    use_name_encoding = correlation_search_id is None and name is not None
    current = get_correlation_search(client, search_identifier, use_name_encoding=use_name_encoding)

    if current is None:
        exit_with_result(module)

    _cur_status, _cur_hdr, cur_obj = current

    if module.check_mode:
        exit_with_result(module, changed=True, before=cur_obj, diff=cur_obj)

    response: dict = {}
    del_result = delete_correlation_search(client, search_identifier, use_name_encoding=use_name_encoding)
    if del_result is not None:
        _status, _hdr, body = del_result
        response = body
    exit_with_result(
        module,
        changed=True,
        before=cur_obj,
        diff=cur_obj,
        response=response,
    )


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

    try:
        client = ItsiRequest(Connection(module._socket_path), module)
    except Exception as e:
        module.fail_json(msg=f"Failed to establish connection: {e}")

    try:
        state = module.params["state"]
        if state == "present":
            _handle_state_present(module, client, module.params)
        else:
            _handle_absent_state(module, client, module.params)

    except Exception as e:
        module.fail_json(msg=f"Exception occurred: {str(e)}")


if __name__ == "__main__":
    main()
