#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers


DOCUMENTATION = r"""
---
module: itsi_episode_details_info
short_description: Read Splunk ITSI notable_event_group (episodes)
description: >
  Reads a single episode by _key, lists episodes, or returns only a count using the ITSI Event Management Interface.
  Requires ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client.
version_added: "1.0.0"
author:
  - Ansible Ecosystem Engineering team (@ansible)
options:
  episode_id:
    description: "ITSI notable_event_group _key. When provided, fetches a single episode."
    type: str
  limit:
    description: "Max entries to return when listing (ITSI parameter 'limit'). 0 means no limit param is sent."
    type: int
    default: 0
  skip:
    description: "Number of entries to skip from the start (ITSI parameter 'skip')."
    type: int
  fields:
    description: "Comma-separated list of field names to include (ITSI parameter 'fields')."
    type: str
  filter_data:
    description: "MongoDB-style JSON string to filter results (ITSI parameter 'filter_data'). Example: '{\"status\":\"2\"}'."
    type: str
  sort_key:
    description: "Field name to sort by (ITSI parameter 'sort_key')."
    type: str
  sort_dir:
    description: "Sort direction (ITSI parameter 'sort_dir'). Use 1 for ascending, 0 for descending."
    type: int
    choices:
      - 0
      - 1
  count_only:
    description: "If true, call the '/count' endpoint and return only a numeric count."
    type: bool
    default: false
notes:
  - "Connection/auth/SSL config is provided by httpapi (inventory), not by this module."
requirements:
  - ansible.netcommon
"""

EXAMPLES = r"""
- name: List first 10 episodes
  splunk.itsi.itsi_episode_details_info:
    limit: 10
  register: out

- name: Count open episodes (status=2)
  splunk.itsi.itsi_episode_details_info:
    count_only: true
    filter_data: '{"status":"2"}'
  register: cnt

- name: Get one episode by _key
  splunk.itsi.itsi_episode_details_info:
    episode_id: 000f91af-ac7d-45e2-a498-5c4b6fe96431
  register: one

- name: Advanced filtering with pagination
  splunk.itsi.itsi_episode_details_info:
    filter_data: '{"severity": {"$in": ["1", "2", "3"]}}'
    sort_key: "mod_time"
    sort_dir: 0
    limit: 20
    skip: 0
    fields: "_key,title,severity,status,mod_time"
  register: result
"""

RETURN = r"""
episodes:
  description: "Episode list (empty when count_only=true)."
  type: list
  elements: dict
  returned: when count_only is false
count:
  description: "Count of objects matching filter (when count_only=true)."
  type: int
  returned: when count_only is true
changed:
  description: "Always false (read-only)."
  type: bool
  returned: always
"""

from typing import Any, Optional

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.splunk.itsi.plugins.module_utils.episode_details import (
    BASE_EPISODE_ENDPOINT,
    get_episode_by_id,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest


def _fetch_body(
    client: ItsiRequest,
    path: str,
    params: Optional[dict[str, Any]] = None,
) -> Optional[Any]:
    """Call client.get and return only the response body.

    Args:
        client: ItsiRequest instance for API requests.
        path: API endpoint path.
        params: Optional query parameters.

    Returns:
        Parsed response body, or None if not found (404).
    """
    result = client.get(path, params=params)
    if result is None:
        return None
    _status, _headers, body = result
    return body


def _get_episode_count(
    client: ItsiRequest,
    filter_data: Optional[str],
) -> dict[str, Any]:
    """Fetch episode count, optionally filtered.

    Args:
        client: ItsiRequest instance for API requests.
        filter_data: Optional MongoDB-style JSON filter string.

    Returns:
        Result dictionary with count.
    """
    params: dict[str, Any] = {}
    if filter_data:
        params["filter_data"] = filter_data
    body = _fetch_body(client, f"{BASE_EPISODE_ENDPOINT}/count", params=params)
    count = 0
    if isinstance(body, dict) and "count" in body:
        try:
            count = int(body["count"])
        except (TypeError, ValueError):
            count = 0
    return {"count": count}


def _list_episodes(
    client: ItsiRequest,
    params: dict[str, Any],
) -> dict[str, Any]:
    """List episodes with optional filtering and pagination.

    Args:
        client: ItsiRequest instance for API requests.
        params: Query parameters for filtering, pagination, and sorting.

    Returns:
        Result dictionary with episodes list.
    """
    # List endpoint must end with '/'
    body = _fetch_body(client, f"{BASE_EPISODE_ENDPOINT}/", params=params)
    episodes = body if isinstance(body, list) else []
    return {"episodes": episodes}


PASSTHROUGH_PARAMS = ("skip", "fields", "filter_data", "sort_key", "sort_dir")


def _build_list_params(module_params: dict[str, Any]) -> dict[str, Any]:
    """Build query parameters for the list endpoint.

    Args:
        module_params: Module parameters dictionary.

    Returns:
        Filtered query parameters dict.
    """
    params: dict[str, Any] = {}
    if module_params["limit"] and module_params["limit"] > 0:
        params["limit"] = module_params["limit"]
    for key in PASSTHROUGH_PARAMS:
        if module_params[key] is not None:
            params[key] = module_params[key]
    return params


def main() -> None:
    """Main module execution."""
    module = AnsibleModule(
        argument_spec=dict(
            episode_id=dict(type="str"),
            limit=dict(type="int", default=0),
            skip=dict(type="int"),
            fields=dict(type="str"),
            filter_data=dict(type="str"),
            sort_key=dict(type="str", no_log=False),
            sort_dir=dict(type="int", choices=[0, 1]),
            count_only=dict(type="bool", default=False),
        ),
        supports_check_mode=True,
    )

    module_params = module.params

    try:
        client = ItsiRequest(Connection(module._socket_path), module)

        # Single-object GET by _key
        if module_params["episode_id"] and not module_params["count_only"]:
            body = get_episode_by_id(client, module_params["episode_id"])
            episodes = [body] if isinstance(body, dict) else []
            result = {"episodes": episodes}
        elif module_params["count_only"]:
            # Count endpoint
            result = _get_episode_count(client, module_params["filter_data"])
        else:
            # List endpoint
            params = _build_list_params(module_params)
            result = _list_episodes(client, params)

        module.exit_json(changed=False, **result)

    except Exception as e:
        module.fail_json(msg=f"Exception occurred: {str(e)}")


if __name__ == "__main__":
    main()
