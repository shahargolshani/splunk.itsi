#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Splunk ITSI Ansible Collection Maintainers
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: itsi_service_info
short_description: Gather facts about Splunk ITSI Service objects via itoa_interface
version_added: "1.0.0"
description:
  - Read service documents from the Splunk ITSI REST API (itoa_interface).
  - You can fetch by key, fetch by exact title, or list with server-side filters.
  - Uses the splunk.itsi.itsi_api_client httpapi plugin for transport and auth.
author:
  - Ansible Ecosystem Engineering team (@ansible)
notes:
  - Requires ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client.
  - This is a read-only module. It never changes remote state.
options:
  service_id:
    description:
      - Exact ITSI service _key to fetch.
    type: str
  title:
    description:
      - Exact service title to match. If both service_id and title are provided, service_id wins.
    type: str
  enabled:
    description:
      - Optional filter on enabled state.
    type: bool
  sec_grp:
    description:
      - Optional team (security group) filter. Exact match.
    type: str
  filter:
    description:
      - Raw server-side filter object merged with simple filters when possible.
      - Use this for advanced queries such as regex title matches.
    type: dict
  fields:
    description:
      - Projection of fields to return. List of field names.
    type: list
    elements: str
  count:
    description:
      - Page size for listings. Ignored for fetch by key or title.
    type: int
  offset:
    description:
      - Offset for listings.
    type: int
"""

EXAMPLES = r"""
- name: List all services
  splunk.itsi.itsi_service_info:
  register: out

- name: Fetch by exact title
  splunk.itsi.itsi_service_info:
    title: api-gateway
  register: svc_by_title

- name: Fetch by key with projection
  splunk.itsi.itsi_service_info:
    service_id: a2961217-9728-4e9f-b67b-15bf4a40ad7c
    fields:
      - _key
      - title
      - enabled
      - sec_grp
      - entity_rules
  register: svc_by_key

- name: Filtered list
  splunk.itsi.itsi_service_info:
    enabled: true
    sec_grp: default_itsi_security_group
  register: filtered

- name: Paginated list
  splunk.itsi.itsi_service_info:
    count: 3
    offset: 0
  register: page1
"""

RETURN = r"""
services:
  description: List of service objects returned by the ITSI API.
  type: list
  elements: dict
  returned: always
service:
  description: First item from services when a single result is expected.
  type: dict
  returned: when a single result is found
raw:
  description: Raw body parsed from the server response for the last call.
  type: raw
  returned: always
changed:
  description: Always false. This is an information module.
  type: bool
  returned: always
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

BASE = "servicesNS/nobody/SA-ITOA/itoa_interface/service"


def _build_filter(module_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build server-side filter.

    If both simple options and `filter` specify the same key, the
    filter object takes precedence.

    Args:
        module_params: Module parameters from Ansible.

    Returns:
        Filter dict or None if empty.
    """
    filter_obj = dict(module_params.get("filter") or {})
    if module_params.get("title") is not None and "title" not in filter_obj:
        filter_obj["title"] = module_params["title"]
    if module_params.get("enabled") is not None and "enabled" not in filter_obj:
        filter_obj["enabled"] = 1 if module_params["enabled"] is True else 0
    if module_params.get("sec_grp") is not None and "sec_grp" not in filter_obj:
        filter_obj["sec_grp"] = module_params["sec_grp"]
    return filter_obj or None


def _handle_get_by_id(
    client: ItsiRequest,
    service_id: str,
    result: Dict[str, Any],
) -> None:
    """Handle fetching a service by its _key.

    Args:
        client: ItsiRequest instance.
        service_id: Service _key to fetch.
        result: Result dict to update.
    """
    path = f"{BASE}/{quote_plus(service_id)}"
    api_result = client.get(path)
    if api_result is None:
        return
    _status, _headers, body = api_result
    result["raw"] = body
    if isinstance(body, dict):
        result["service"] = body


def _build_list_params(module_params: Dict[str, Any]) -> Dict[str, Any]:
    """Build query parameters for listing services.

    Args:
        module_params: Module parameters from Ansible.

    Returns:
        Dict of query parameters for the list request.
    """
    params: Dict[str, Any] = {}

    if module_params.get("fields"):
        params["fields"] = _dedupe_fields(module_params["fields"])

    filter_object = _build_filter(module_params)
    if filter_object:
        params["filter"] = json.dumps(filter_object, separators=(",", ":"))

    if module_params.get("count") is not None:
        params["count"] = module_params["count"]
    if module_params.get("offset") is not None:
        params["offset"] = module_params["offset"]

    return params


def _dedupe_fields(fields: List[Any]) -> str:
    """Deduplicate and stringify a list of field names.

    Args:
        fields: List of field names.

    Returns:
        Comma-separated string of unique field names.
    """
    seen: set[str] = set()
    field_list: List[str] = []
    for field in fields:
        field_str = str(field)
        if field_str not in seen:
            seen.add(field_str)
            field_list.append(field_str)
    return ",".join(field_list)


def _parse_list_response(
    body: Any,
    result: Dict[str, Any],
) -> None:
    """Parse a list response and update the result dict.

    Args:
        body: Response body.
        result: Result dict to update.
    """
    if isinstance(body, list):
        result["items"] = body
    elif isinstance(body, dict) and "items" in body and "size" in body:
        result["paging"] = {"size": body.get("size"), "items": body.get("items")}
        result["items"] = body.get("items", [])
    else:
        result["items"] = []


def main() -> None:
    """Entry point for the itsi_service_info module."""
    module = AnsibleModule(
        argument_spec=dict(
            service_id=dict(type="str"),
            title=dict(type="str"),
            enabled=dict(type="bool"),
            sec_grp=dict(type="str"),
            filter=dict(type="dict"),
            fields=dict(type="list", elements="str"),
            count=dict(type="int"),
            offset=dict(type="int"),
        ),
        supports_check_mode=True,
    )

    if not getattr(module, "_socket_path", None):
        module.fail_json(
            msg="Use ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client",
        )

    client = ItsiRequest(Connection(module._socket_path), module)
    module_params = module.params

    result: Dict[str, Any] = {
        "changed": False,
        "raw": {},
        "items": [],
    }

    if module_params.get("service_id"):
        _handle_get_by_id(client, module_params["service_id"], result)
        module.exit_json(**result)

    params = _build_list_params(module_params)
    api_result = client.get(BASE, params=params)
    if api_result is None:
        module.exit_json(**result)
    _status, _headers, body = api_result
    result["raw"] = body
    _parse_list_response(body, result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
