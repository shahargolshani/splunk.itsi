#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#


DOCUMENTATION = r"""
---
module: itsi_add_episode_comments
short_description: Add comments to Splunk ITSI episodes
description:
  - Add comments to existing episodes in Splunk IT Service Intelligence (ITSI).
  - Comments are associated with a specific episode and can provide context or status updates.
  - Every invocation creates a new comment; comments cannot be updated or deleted via the API.
version_added: "1.0.0"
author:
  - Ansible Ecosystem Engineering team (@ansible)
options:
  episode_key:
    description:
      - The episode _key to add a comment to.
      - This is the C(_key) field from an episode, as returned by
        M(splunk.itsi.itsi_episode_details_info).
    type: str
    required: true
  comment:
    description:
      - The text content of the comment to add to the episode.
      - Can contain any text describing actions taken, status updates,
        or other relevant information.
    type: str
    required: true
  is_group:
    description:
      - Whether this comment is for an episode group.
      - Should be set to C(true) for ITSI episodes (notable event groups).
    type: bool
    default: true

requirements:
  - Connection configuration requires C(ansible_connection=httpapi) and
    C(ansible_network_os=splunk.itsi.itsi_api_client).
  - Authentication via Bearer token, session key, or username/password
    as documented in the httpapi plugin.
notes:
  - This module adds comments to existing ITSI episodes using the
    notable_event_comment endpoint.
  - The episode must exist before adding comments to it.
  - Comments are permanently associated with the episode and cannot be
    deleted via the API.
  - Use M(splunk.itsi.itsi_episode_details_info) to retrieve episode
    C(_key) values for commenting.
  - This module always returns C(changed=true) because every run creates
    a new comment. Idempotency does not apply.
  - Check mode is supported. In check mode the module reports
    C(changed=true) without actually calling the API.
"""

EXAMPLES = r"""
# Add a simple comment to an episode
- name: Add comment to episode
  splunk.itsi.itsi_add_episode_comments:
    episode_key: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
    comment: "Investigating root cause - checking application logs"

# Add a comment with variable content
- name: Add dynamic comment to episode
  splunk.itsi.itsi_add_episode_comments:
    episode_key: "{{ episode_key }}"
    comment: "{{ comment_text }}"
    is_group: true

# Add comment using episode data from a previous task
- name: Get episodes and add comment to first one
  block:
    - name: Get episode list
      splunk.itsi.itsi_episode_details_info:
        limit: 1
      register: episodes_result

    - name: Add comment to first episode
      splunk.itsi.itsi_add_episode_comments:
        episode_key: "{{ episodes_result.episodes[0]._key }}"
        comment: "Automated comment from Ansible playbook"
      when: episodes_result.episodes | length > 0

# Check mode -- preview without posting a comment
- name: Preview comment (check mode)
  splunk.itsi.itsi_add_episode_comments:
    episode_key: "{{ episode_key }}"
    comment: "Dry-run comment"
  check_mode: true
  register: preview

- name: Show preview result
  ansible.builtin.debug:
    msg: "Before: {{ preview.before }} / After: {{ preview.after }}"
"""

RETURN = r"""
changed:
  description: Always true (every run creates a new comment).
  returned: always
  type: bool
  sample: true
episode_key:
  description: The episode _key that was targeted.
  returned: always
  type: str
  sample: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
before:
  description:
    - The state before the operation.
    - Always an empty dict because comments are newly created.
  returned: always
  type: dict
  sample: {}
after:
  description:
    - The comment payload that was (or would be) sent to the API.
  returned: always
  type: dict
  sample:
    comment: "Investigating root cause"
    event_id: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
    is_group: true
diff:
  description:
    - Dictionary of fields that differ between before and after.
    - Always equal to after because comments are newly created.
  returned: always
  type: dict
  sample:
    comment: "Investigating root cause"
    event_id: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
    is_group: true
response:
  description:
    - Raw JSON response returned by the Splunk ITSI comment API.
    - Empty dict when no API call was made (check mode).
  returned: always
  type: dict
  sample:
    success: true
"""

from typing import Any

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

# API endpoint for ITSI notable event comments
BASE_COMMENT_ENDPOINT = "servicesNS/nobody/SA-ITOA/event_management_interface/notable_event_comment"


def _build_comment_data(
    episode_key: str,
    comment: str,
    is_group: bool,
) -> dict[str, Any]:
    """Build the comment payload for the ITSI API.

    Maps the user-facing ``episode_key`` parameter to the ``event_id``
    field that the ITSI notable_event_comment endpoint expects.

    Args:
        episode_key: The episode _key to comment on.
        comment: Comment text to add.
        is_group: Whether this is a group comment.

    Returns:
        Dictionary payload ready for the API POST request.
    """
    return {
        "comment": comment,
        "event_id": episode_key,
        "is_group": is_group,
    }


def _add_comment(
    client: ItsiRequest,
    comment_data: dict[str, Any],
) -> dict[str, Any]:
    """Post a comment to an ITSI episode.

    Args:
        client: ItsiRequest instance for API requests.
        comment_data: The comment payload to send.

    Returns:
        Response dictionary from the API.
    """
    result = client.post(BASE_COMMENT_ENDPOINT, payload=comment_data)
    if result is None:
        raise ValueError("Failed to add comment (no response from API)")
    _status, _headers, body = result
    return body


def main() -> None:
    """Main module execution."""
    module_args = dict(
        episode_key=dict(type="str", required=True, no_log=False),
        comment=dict(type="str", required=True),
        is_group=dict(type="bool", default=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    episode_key: str = module.params["episode_key"]
    comment: str = module.params["comment"]
    is_group: bool = module.params["is_group"]

    comment_data = _build_comment_data(episode_key, comment, is_group)

    # Build result dict with common keys
    # before is always empty because comments are newly created
    result: dict[str, Any] = {
        "episode_key": episode_key,
        "before": {},
        "after": comment_data,
        "diff": comment_data,
        "response": {},
    }

    # Check mode -- report what would be posted without calling the API
    if module.check_mode:
        result["changed"] = True
        module.exit_json(**result)

    try:
        client = ItsiRequest(Connection(module._socket_path), module)
        response = _add_comment(client, comment_data)

        result.update(changed=True, response=response)
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(
            msg=f"Error adding episode comment: {str(e)}",
            episode_key=episode_key,
        )


if __name__ == "__main__":
    main()
