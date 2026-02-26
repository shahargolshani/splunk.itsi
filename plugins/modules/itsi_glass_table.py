#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers


DOCUMENTATION = r"""
---
module: itsi_glass_table
short_description: Manage Splunk ITSI Glass Table objects via itoa_interface
description:
  - Create, update, or delete Splunk ITSI Glass Table objects using the itoa_interface REST API.
  - Glass table titles are NOT unique; multiple glass tables can share the same title.
  - The glass table C(_key) is the unique identifier. Provide C(glass_table_id) to update or delete.
  - When C(glass_table_id) is omitted with C(state=present), a new glass table is always created.
  - Uses the splunk.itsi.itsi_api_client httpapi plugin for authentication and transport.
  - For more information on glass tables see
    U(https://help.splunk.com/en/splunk-it-service-intelligence/splunk-it-service-intelligence/visualize-and-assess-service-health/4.19/glass-tables/overview-of-the-glass-table-editor-in-itsi).
version_added: "1.0.0"
author:
  - Ansible Ecosystem Engineering team (@ansible)
options:
  glass_table_id:
    description:
      - The glass table C(_key) for update or delete operations.
      - Required for C(state=absent).
      - When provided with C(state=present), the module updates the existing glass table.
      - When omitted with C(state=present), a new glass table is created.
    type: str
    required: false
  title:
    description:
      - The title of the glass table.
      - Required when creating a new glass table (C(state=present) without C(glass_table_id)).
      - Glass table titles are not unique; duplicates are allowed.
    type: str
    required: false
  description:
    description:
      - Description text for the glass table.
    type: str
    required: false
  definition:
    description:
      - Raw JSON definition object for the glass table.
      - Contains the full layout, visualizations, data sources, and inputs configuration.
      - The module passes this value as-is to the API without modification.
      - The user is responsible for all fields within the definition, including
        C(definition.title) and C(definition.description) if desired.
      - Required when creating a new glass table (C(state=present) without C(glass_table_id)).
    type: dict
    required: false
  sharing:
    description:
      - Controls the sharing level of the glass table via C(acl.sharing).
      - C(user) makes the glass table private to the owner.
      - C(app) makes the glass table available at the app level.
    type: str
    choices: ['user', 'app']
    required: false
  state:
    description:
      - Desired state of the glass table.
      - C(present) ensures the glass table exists with the specified configuration.
      - C(absent) ensures the glass table is deleted.
    type: str
    choices: ['present', 'absent']
    default: present

requirements:
  - Connection configuration requires C(ansible_connection=httpapi) and
    C(ansible_network_os=splunk.itsi.itsi_api_client).
  - Authentication via Bearer token, session key, or username/password as documented
    in the httpapi plugin.
notes:
  - This module manages ITSI glass tables using the itoa_interface/glass_table endpoint.
  - Glass table titles are NOT unique. Use C(glass_table_id) to target a specific glass table
    for updates or deletion.
  - The C(definition) parameter is a raw JSON dict passed as-is to the API. The module does
    not auto-populate C(definition.title) or C(definition.description).
  - Update operations use C(is_partial_data=1) and send only the fields that changed.
  - This module is idempotent. If the desired field values already match the current state,
    no update is performed and C(changed) is returned as C(false).
  - Check mode is supported. In check mode the module reports whether changes would be made
    without actually calling the API.
  - Diff detection uses recursive comparison via C(dict_diff) from ansible.netcommon, so
    changes nested deep inside C(definition) are properly detected.
"""

EXAMPLES = r"""
# Create a glass table with a full definition
- name: Create glass table with definition
  splunk.itsi.itsi_glass_table:
    title: "Detailed Glass Table"
    description: "Glass table with custom layout"
    definition:
      title: "Detailed Glass Table"
      description: "Glass table with custom layout"
      defaults:
        dataSources:
          global:
            options:
              queryParameters:
                earliest: "$global_time.earliest$"
                latest: "$global_time.latest$"
              refreshType: delay
              refresh: "$global_refresh_rate$"
      layout:
        options:
          showTitleAndDescription: true
        globalInputs:
          - input_global_trp
          - input_global_refresh_rate
        tabs:
          items:
            - layoutId: layout_1
              label: "Layout 1"
        layoutDefinitions:
          layout_1:
            type: absolute
            options:
              width: 1920
              height: 1080
              backgroundColor: "#FFFFFF"
            structure: []
      dataSources: {}
      visualizations: {}
      inputs:
        input_global_trp:
          options:
            defaultValue: "-60m@m, now"
            token: global_time
          type: input.timerange
          title: Global Time Range
        input_global_refresh_rate:
          options:
            items:
              - value: "60s"
                label: "1 Minute"
              - value: "300s"
                label: "5 Minutes"
            defaultValue: "60s"
            token: global_refresh_rate
          type: input.dropdown
          title: Global Refresh Rate
    state: present
  register: result

# Update an existing glass table by ID
- name: Update glass table description
  splunk.itsi.itsi_glass_table:
    glass_table_id: "{{ glass_table_id }}"
    description: "Updated description"
    state: present

# Delete a glass table
- name: Remove glass table
  splunk.itsi.itsi_glass_table:
    glass_table_id: "6992e850280636204503b3f6"
    state: absent

# Check mode -- preview changes without applying them
- name: Preview glass table update (check mode)
  splunk.itsi.itsi_glass_table:
    glass_table_id: "{{ glass_table_id }}"
    title: "Renamed Glass Table"
  check_mode: true
  register: preview

- name: Show what would change
  ansible.builtin.debug:
    msg: "Before: {{ preview.before }} / After: {{ preview.after }} / Diff: {{ preview.diff }}"
"""

RETURN = r"""
changed:
  description: Whether the glass table was actually modified.
  returned: always
  type: bool
  sample: true
before:
  description:
    - The current values of the targeted fields before the operation.
    - Only contains the fields that were requested for update.
  returned: always
  type: dict
  sample:
    title: "Old Title"
    description: "Old description"
    sharing: "user"
after:
  description:
    - The desired values of the targeted fields after the operation.
    - When changed is false, before and after are identical.
  returned: always
  type: dict
  sample:
    title: "New Title"
    description: "New description"
    sharing: "app"
diff:
  description:
    - Dictionary of fields that differ between current and desired state.
    - For nested dicts like definition, shows only the changed nested keys (recursive).
    - Empty when no changes are needed.
  returned: always
  type: dict
  sample:
    title: "New Title"
response:
  description:
    - Raw JSON response returned by the Splunk ITSI API.
    - Empty dict when no API call was made (no changes needed or check mode).
  returned: always
  type: dict
"""

from typing import Any, Optional

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.splunk.itsi.plugins.module_utils.glass_table import (
    BASE_GLASS_TABLE_ENDPOINT,
    get_glass_table_by_id,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest
from ansible_collections.splunk.itsi.plugins.module_utils.splunk_utils import exit_with_result

# Fields managed by this module for diff tracking
DIFF_FIELDS = ("title", "description", "definition", "sharing")


def _validate_params(module: AnsibleModule) -> None:
    """Validate module parameters

    Args:
        module: The AnsibleModule instance.
    """
    params = module.params
    definition = params.get("definition")

    if definition is not None and not definition:
        module.fail_json(msg="'definition' must not be empty when provided")

    if params["state"] == "present" and not params.get("glass_table_id"):
        if not params.get("title"):
            module.fail_json(msg="'title' is required when creating a new glass table")
        if definition is None:
            module.fail_json(msg="'definition' is required when creating a new glass table")


def _build_desired(params: dict[str, Any]) -> dict[str, Any]:
    """Build the desired payload from module parameters.

    Only includes fields explicitly provided by the user (non-None).

    Args:
        params: Module parameters from Ansible.

    Returns:
        Payload dictionary with user-provided fields.
    """
    desired: dict[str, Any] = {}
    for field in DIFF_FIELDS:
        value = params.get(field)
        if value is not None:
            desired[field] = value
    return desired


def _sync_title_desc_into_definition(
    data: dict[str, Any],
    base_definition: Optional[dict[str, Any]] = None,
) -> None:
    """Sync top-level title/description into definition for consistency.

    When the user provides ``title`` or ``description`` at the module level,
    those values are also written into ``definition.title`` /
    ``definition.description`` so the two levels stay in sync.

    Args:
        data: Payload dict that may contain title, description, and/or definition.
        base_definition: Existing definition from the API to use as a starting
            point when *data* does not already contain a definition key.
    """
    sync_fields = {f: data[f] for f in ("title", "description") if f in data}
    if not sync_fields:
        return

    if "definition" in data:
        definition = dict(data["definition"])
    elif base_definition:
        definition = dict(base_definition)
    else:
        return

    definition.update(sync_fields)
    data["definition"] = definition


def _build_create_payload(desired: dict[str, Any]) -> dict[str, Any]:
    """Build the API payload for creating a new glass table.

    Adds required payload fields (_owner, _user, gt_version) and syncs
    top-level title/description into definition.

    Args:
        desired: Module-level desired state (title, description, definition).

    Returns:
        API-ready creation payload.
    """
    payload: dict[str, Any] = {}
    for field in ("title", "description", "definition"):
        if field in desired:
            payload[field] = desired[field]

    payload["gt_version"] = "beta"
    payload["_owner"] = "nobody"
    payload["_user"] = "nobody"

    if "sharing" in desired:
        payload["acl"] = {"sharing": desired["sharing"]}

    _sync_title_desc_into_definition(payload)

    return payload


def _update_glass_table(
    client: ItsiRequest,
    glass_table_id: str,
    update_payload: dict[str, Any],
) -> dict[str, Any]:
    """Update a glass table using partial data.

    Args:
        client: ItsiRequest instance for API requests.
        glass_table_id: The glass table _key to update.
        update_payload: Dictionary of fields to update (full values).

    Returns:
        Response dictionary from the API.
    """
    path = f"{BASE_GLASS_TABLE_ENDPOINT}/{glass_table_id}"
    params = {"is_partial_data": "1"}
    update_payload["_owner"] = "nobody"
    update_payload["_user"] = "nobody"
    result = client.post(path, params=params, payload=update_payload)
    if result is None:
        raise ValueError(f"Glass table '{glass_table_id}' not found during update (404)")
    _status, _headers, body = result
    return body


def _create_glass_table(
    client: ItsiRequest,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Create a new glass table.

    Args:
        client: ItsiRequest instance for API requests.
        payload: Full creation payload.

    Returns:
        Response dictionary from the API.
    """
    result = client.post(BASE_GLASS_TABLE_ENDPOINT, payload=payload)
    if result is None:
        raise ValueError("Failed to create glass table (API returned 404)")
    _status, _headers, body = result
    return body


def _delete_glass_table(
    client: ItsiRequest,
    glass_table_id: str,
) -> dict[str, Any]:
    """Delete a glass table by _key.

    Args:
        client: ItsiRequest instance for API requests.
        glass_table_id: The glass table _key to delete.

    Returns:
        Response dictionary from the API.
    """
    path = f"{BASE_GLASS_TABLE_ENDPOINT}/{glass_table_id}"
    result = client.delete(path)
    if result is None:
        return {}
    _status, _headers, body = result
    return body


def _handle_absent(
    module: AnsibleModule,
    client: ItsiRequest,
    glass_table_id: str,
) -> None:
    """Handle state=absent: delete the glass table if it exists.

    Args:
        module: Ansible module instance.
        client: ItsiRequest instance.
        glass_table_id: Glass table _key to delete.
    """
    current = get_glass_table_by_id(client, glass_table_id)
    if current is None:
        exit_with_result(module)

    before: dict[str, Any] = {}
    for k in DIFF_FIELDS:
        if k == "sharing":
            before[k] = current.get("acl", {}).get("sharing")
        else:
            before[k] = current.get(k)

    if module.check_mode:
        exit_with_result(module, changed=True, before=before, diff=before)

    response = _delete_glass_table(client, glass_table_id)
    exit_with_result(module, changed=True, before=before, diff=before, response=response)


def _handle_create(
    module: AnsibleModule,
    client: ItsiRequest,
    desired: dict[str, Any],
) -> None:
    """Handle glass table creation when no glass_table_id is provided.

    Args:
        module: Ansible module instance.
        client: ItsiRequest instance.
        desired: Desired payload built from module params.
    """
    after = {k: desired.get(k) for k in DIFF_FIELDS if k in desired}

    if module.check_mode:
        exit_with_result(module, changed=True, after=after, diff=after)

    api_payload = _build_create_payload(desired)
    response = _create_glass_table(client, api_payload)
    exit_with_result(module, changed=True, after=after, diff=after, response=response)


def _handle_update(
    module: AnsibleModule,
    client: ItsiRequest,
    glass_table_id: str,
    desired: dict[str, Any],
) -> None:
    """Handle glass table update when glass_table_id is provided.

    Args:
        module: Ansible module instance.
        client: ItsiRequest instance.
        glass_table_id: Glass table _key to update.
        desired: Desired payload built from module params.
    """
    current = get_glass_table_by_id(client, glass_table_id)
    if current is None:
        module.fail_json(msg=f"Glass table '{glass_table_id}' not found")

    if not desired:
        exit_with_result(module)

    _sync_title_desc_into_definition(desired, base_definition=current.get("definition"))

    # Extract comparable fields from current state.
    # sharing lives under acl.sharing in the API, so map it to the flat key.
    have_conf: dict = {}
    for k in desired:
        if k == "sharing":
            have_conf[k] = current.get("acl", {}).get("sharing")
        else:
            have_conf[k] = current.get(k)

    # Remove None/empty values from desired state so we only compare real values
    want_conf: dict = utils.remove_empties(desired)

    # Compute recursive diff -- detects nested changes inside definition
    diff: dict = utils.dict_diff(have_conf, want_conf)

    # Build the "after" snapshot (current state merged with desired changes)
    after_conf: dict = dict(have_conf)
    after_conf.update(want_conf)

    # No changes needed
    if not diff:
        exit_with_result(module, before=have_conf, after=have_conf)

    if module.check_mode:
        exit_with_result(module, changed=True, before=have_conf, after=after_conf, diff=diff)

    # Build update payload: full values for changed top-level fields only.
    # Map sharing back to acl.sharing, merging with existing acl to avoid data loss.
    update_payload: dict[str, Any] = {}
    for k in diff:
        if k == "sharing":
            current_acl = current.get("acl", {})
            update_payload["acl"] = {**current_acl, "sharing": want_conf[k]}
        else:
            update_payload[k] = want_conf[k]

    response = _update_glass_table(client, glass_table_id, update_payload)
    exit_with_result(
        module,
        changed=True,
        before=have_conf,
        after=after_conf,
        diff=diff,
        response=response,
    )


def main() -> None:
    """Entry point for the itsi_glass_table Ansible module."""
    module = AnsibleModule(
        argument_spec=dict(
            glass_table_id=dict(type="str", required=False),
            title=dict(type="str", required=False),
            description=dict(type="str", required=False),
            definition=dict(type="dict", required=False),
            sharing=dict(type="str", choices=["user", "app"], required=False),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        ),
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ("glass_table_id",)),
        ],
    )

    if not getattr(module, "_socket_path", None):
        module.fail_json(
            msg="Use ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client",
        )

    _validate_params(module)

    params = module.params

    try:
        client = ItsiRequest(Connection(module._socket_path), module)
    except Exception as e:
        module.fail_json(msg=f"Failed to establish connection: {e}")

    state = params["state"]
    glass_table_id = params.get("glass_table_id")

    try:
        if state == "absent":
            _handle_absent(module, client, glass_table_id)

        # state == "present"
        desired = _build_desired(params)

        if glass_table_id:
            _handle_update(module, client, glass_table_id, desired)
        else:
            _handle_create(module, client, desired)

    except Exception as e:
        module.fail_json(msg=f"Exception occurred: {str(e)}")


if __name__ == "__main__":
    main()
