#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers


DOCUMENTATION = r"""
---
module: itsi_update_episode_details
short_description: Update specific fields of Splunk ITSI episodes
description:
  - Update specific fields of existing episodes in Splunk IT Service Intelligence (ITSI).
  - Uses partial data updates to modify only the specified fields without affecting other episode data.
  - Supports common episode fields like severity, status, owner, and instruction.
version_added: "1.0.0"
author:
  - Ansible Ecosystem Engineering team (@ansible)
options:
  episode_id:
    description:
      - The episode ID (_key field) to update.
      - This should be the _key field from an episode, such as returned by notable_event_group_info.
    type: str
    required: true
  severity:
    description:
      - Update the severity level of the episode.
      - Common values are 1 (Info), 2 (Normal), 3 (Low), 4 (Medium), 5 (High), 6 (Critical).
    type: str
    required: false
  status:
    description:
      - Update the status of the episode.
      - Common values are 1 (New), 2 (In Progress), 3 (Pending), 4 (Resolved), 5 (Closed).
    type: str
    required: false
  owner:
    description:
      - Update the owner/assignee of the episode.
      - Can be a username or 'unassigned' to clear assignment.
    type: str
    required: false
  instruction:
    description:
      - Update the instruction field of the episode.
      - Contains guidance or notes about how to handle the episode.
      - Set to C(all_instruction) to reset the instruction in the ITSI UI,
        effectively clearing it so the episode shows no instruction provided.
    type: str
    required: false
  fields:
    description:
      - Dictionary of additional fields to update.
      - Allows updating any valid episode field not covered by specific parameters.
      - Field names should match ITSI episode schema.
    type: dict
    required: false

requirements:
  - Connection configuration requires C(ansible_connection=httpapi) and C(ansible_network_os=splunk.itsi.itsi_api_client).
  - Authentication via Bearer token, session key, or username/password as documented in the httpapi plugin.
notes:
  - This module updates existing ITSI episodes using the event_management_interface/notable_event_group endpoint.
  - Uses partial data updates (is_partial_data=1) to modify only specified fields.
  - The episode must exist before updating it.
  - Use notable_event_group_info module to retrieve episode IDs and current field values.
  - At least one field parameter (severity, status, owner, instruction, or fields) must
    be provided.
  - This module is idempotent. If the desired field values already match the current episode
    state, no update is performed and C(changed) is returned as C(false).
  - Check mode is supported. In check mode the module reports whether changes would be made
    without actually calling the update API.
"""

EXAMPLES = r"""
# Update episode severity
- name: Set episode to critical severity
  splunk.itsi.itsi_update_episode_details:
    episode_id: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
    severity: "6"

# Update episode status and owner
- name: Assign episode and mark in progress
  splunk.itsi.itsi_update_episode_details:
    episode_id: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
    status: "2"
    owner: "admin"

# Update multiple fields at once
- name: Update episode with multiple fields
  splunk.itsi.itsi_update_episode_details:
    episode_id: "{{ episode_id }}"
    severity: "4"
    status: "2"
    owner: "incident_team"
    instruction: "Check database performance and disk space"

# Update using fields dictionary for custom fields
- name: Update custom episode fields
  splunk.itsi.itsi_update_episode_details:
    episode_id: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
    fields:
      custom_field: "custom_value"
      priority: "high"

# Close an episode (status 5 = Closed)
- name: Close resolved episode
  splunk.itsi.itsi_update_episode_details:
    episode_id: "{{ target_episode_id }}"
    status: "5"
    instruction: "Issue resolved - monitoring system restored"

# Idempotent update -- running this twice results in changed=false the second time
- name: Ensure episode severity is set to 4
  splunk.itsi.itsi_update_episode_details:
    episode_id: "{{ episode_id }}"
    severity: "4"
  register: result

- name: Show whether anything changed
  ansible.builtin.debug:
    msg: "Changed: {{ result.changed }}"

# Check mode -- preview changes without applying them
- name: Preview episode update (check mode)
  splunk.itsi.itsi_update_episode_details:
    episode_id: "{{ episode_id }}"
    status: "2"
    owner: "analyst"
  check_mode: true
  register: preview

- name: Show what would change
  ansible.builtin.debug:
    msg: "Before: {{ preview.before }} / After: {{ preview.after }}"
"""

RETURN = r"""
changed:
  description: Whether the episode was actually modified.
  returned: always
  type: bool
  sample: true
episode_id:
  description: The episode ID that was targeted.
  returned: always
  type: str
  sample: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
before:
  description:
    - The current values of the targeted fields before the update.
    - Only contains the fields that were requested for update.
  returned: always
  type: dict
  sample:
    severity: "4"
    status: "1"
after:
  description:
    - The desired values of the targeted fields after the update.
    - When changed is false, before and after are identical.
  returned: always
  type: dict
  sample:
    severity: "6"
    status: "2"
diff:
  description:
    - Dictionary of fields that differ between current and desired state.
    - Empty when no changes are needed.
  returned: always
  type: dict
  sample:
    severity: "6"
    status: "2"
response:
  description:
    - Raw JSON response returned by the Splunk ITSI update API.
    - Empty dict when no API call was made (no changes needed or check mode).
  returned: always
  type: dict
  sample:
    success: true
"""

from typing import Any

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.splunk.itsi.plugins.module_utils.episode_details import (
    BASE_EPISODE_ENDPOINT,
    get_episode_by_id,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

# Named parameters that map directly to episode fields
NAMED_FIELD_PARAMS = ("severity", "status", "owner", "instruction")


def _update_episode(
    client: ItsiRequest,
    episode_id: str,
    update_data: dict[str, Any],
) -> dict[str, Any]:
    """Update specific fields of an ITSI episode using partial data.

    Args:
        client: ItsiRequest instance for API requests.
        episode_id: The episode _key to update.
        update_data: Dictionary of fields to update.

    Returns:
        Response dictionary from the API.
    """
    path = f"{BASE_EPISODE_ENDPOINT}/{episode_id}"
    params = {"is_partial_data": "1"}
    result = client.post(path, params=params, payload=update_data)
    if result is None:
        raise ValueError(f"Episode '{episode_id}' not found (404)")
    _status, _headers, body = result
    return body


def _build_update_data(module: AnsibleModule) -> dict:
    """Build the desired update payload from module parameters.

    Collects values from the named field parameters (severity, status, owner,
    instruction) and merges in any additional keys from the ``fields`` dict.

    Args:
        module: The AnsibleModule instance.

    Returns:
        Dictionary of field-name to desired-value for all user-provided fields.
    """
    update_data: dict = {}

    for param in NAMED_FIELD_PARAMS:
        value = module.params.get(param)
        if value is not None:
            update_data[param] = value

    additional_fields = module.params.get("fields") or {}
    if additional_fields:
        update_data.update(additional_fields)

    return update_data


def main() -> None:
    """Main module execution."""
    module_args = dict(
        episode_id=dict(type="str", required=True),
        severity=dict(type="str", required=False),
        status=dict(type="str", required=False),
        owner=dict(type="str", required=False),
        instruction=dict(type="str", required=False),
        fields=dict(type="dict", required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    episode_id: str = module.params["episode_id"]

    # Build desired state from user parameters
    update_data = _build_update_data(module)

    if not update_data:
        module.fail_json(
            msg="At least one field must be provided for update (severity, status, owner, instruction, or fields)",
        )

    try:
        client = ItsiRequest(Connection(module._socket_path), module)

        # Fetch current episode state
        current_episode = get_episode_by_id(client, episode_id)
        if current_episode is None:
            module.fail_json(
                msg=f"Episode '{episode_id}' not found",
                episode_id=episode_id,
            )

        # Compare current state with desired state
        # Extract only the fields we intend to update from the current episode
        have_conf: dict = {k: current_episode.get(k) for k in update_data}

        # Remove None values from desired state so we only compare real values
        want_conf: dict = utils.remove_empties(update_data)

        # Compute the diff -- keys in want_conf whose values differ from have_conf
        diff: dict = utils.dict_diff(have_conf, want_conf)

        # Build the "after" snapshot (current state merged with desired changes)
        after_conf: dict = dict(have_conf)
        after_conf.update(want_conf)

        # Build result dict with common keys
        result: dict[str, Any] = {
            "episode_id": episode_id,
            "before": have_conf,
            "after": after_conf,
            "diff": diff,
            "response": {},
        }

        # No changes needed
        if not diff:
            result.update(changed=False, after=have_conf, diff={})
            module.exit_json(**result)

        # Check mode -- report what would change without calling the API
        if module.check_mode:
            result["changed"] = True
            module.exit_json(**result)

        # Apply the update
        response = _update_episode(client, episode_id, update_data)
        result.update(changed=True, response=response)
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(
            msg=f"Exception occurred: {str(e)}",
            episode_id=episode_id,
        )


if __name__ == "__main__":
    main()
