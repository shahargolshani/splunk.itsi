#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Splunk ITSI Ansible Collection Maintainers
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (
    absolute_import,
    division,
    print_function,
)

__metaclass__ = type


DOCUMENTATION = r"""
---
module: itsi_service
short_description: Manage Splunk ITSI Service objects via itoa_interface
version_added: "1.0.0"
description: |
  Create, update, or delete Splunk ITSI Service objects using the itoa_interface REST API.
  Idempotent by comparing stable fields on the service: title, enabled, description, sec_grp,
  base_service_template_id, service_tags, entity_rules, plus any keys provided in "extra".
  Uses the splunk.itsi.itsi_api_client httpapi plugin for authentication and transport.
author:
  - Ansible Ecosystem Engineering team (@ansible)
notes:
  - Requires ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client.
  - Update operations must include a valid title; this module will inject the current title if you do not supply one.
  - When creating a service with base_service_template_id, the template configuration (entity_rules, KPIs, etc.)
    takes precedence over module parameters. After creation, these fields can be updated independently.
  - The base_service_template_id is only applied during creation and is ignored on subsequent updates.
options:
  service_id:
    description: "ITSI service _key. When provided, used as the primary identifier."
    type: str
  name:
    description: "Exact service title (service.title). Required if service_id is not provided."
    type: str

  enabled:
    description: "Enable/disable the service (true/false or 1/0)."
    type: bool
  description:
    description: "Service description (free text)."
    type: str
  sec_grp:
    description: "ITSI team (security group) key to assign the service to."
    type: str

  entity_rules:
    description: >
      List of entity rule objects defining which entities belong to this service.
      Each rule has rule_condition (AND/OR) and rule_items array with field, field_type,
      rule_type (matches/is/contains), and value.
      Mutually exclusive with base_service_template_id - you cannot specify both.
      To customize entity_rules on a templated service, first create with the template,
      then update with entity_rules (without the template field).
    type: list
    elements: dict

  service_tags:
    description: >
      List of user-assigned tags for this service. Comparison is order-insensitive.
      Note: template_tags (inherited from service template) are managed by ITSI and
      cannot be set through this module.
    type: list
    elements: str

  base_service_template_id:
    description: >
      Service template identifier to base this service on.
      You can pass either the template ID (_key) or the template title. If a non-UUID value is provided,
      the module will look up an ITSI base service template (object_type=base_service_template) by exact
      title and use its _key as base_service_template_id.
      Note: For ITSI default/built-in service templates (e.g., "Cloud KPIs - AWS EBS (SAI)"), use the
      template title rather than the ID, as default template IDs are not stable across ITSI installations.
      Only applied during creation; ignored on updates (read-only after creation).
      Mutually exclusive with entity_rules - you cannot specify both. The template's configuration
      (including entity_rules, KPIs) is inherited during creation.
    type: str

  extra:
    description: >
      Additional JSON fields to include in payload (merged on top of managed fields).
      Keys present in extra will override first-class options on conflicts.
    type: dict
    default: {}

  state:
    description: Desired state.
    type: str
    choices: [present, absent]
    default: present
"""

EXAMPLES = r"""
- name: Ensure a service exists (idempotent upsert by title)
  splunk.itsi.itsi_service:
    name: api-gateway
    enabled: true
    description: Frontend + API
    sec_grp: default_itsi_security_group
    service_tags: [prod, payments]
    entity_rules: []
    state: present

- name: Create a service based on a template (pass template title or ID)
  splunk.itsi.itsi_service:
    name: api-gateway-from-template
    base_service_template_id: "My Service Template"
    state: present

- name: Remove a service by title
  splunk.itsi.itsi_service:
    name: old-dev-service
    state: absent

- name: Update specific service by key
  splunk.itsi.itsi_service:
    service_id: a2961217-9728-4e9f-b67b-15bf4a40ad7c
    enabled: false
    description: "Disabled for maintenance"
"""

RETURN = r"""
changed:
  description: Whether any change was made.
  type: bool
  returned: always
before:
  description: Service state before the operation. Empty dict on create or when already absent.
  type: dict
  returned: always
  sample:
    title: "api-gateway"
    enabled: 1
    description: "Frontend + API"
after:
  description: Service state after the operation. Empty dict on delete.
  type: dict
  returned: always
  sample:
    title: "api-gateway"
    enabled: 0
    description: "Disabled for maintenance"
diff:
  description: Fields that differ between before and after. Empty dict when unchanged.
  type: dict
  returned: always
  sample:
    enabled: 0
    description: "Disabled for maintenance"
response:
  description: Raw HTTP API response body from the last API call.
  type: dict
  returned: always
  sample:
    _key: "a2961217-9728-4e9f-b67b-15bf4a40ad7c"
    title: "api-gateway"
"""

import json
import re
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)
from urllib.parse import quote_plus

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest
from ansible_collections.splunk.itsi.plugins.module_utils.splunk_utils import (
    build_have_conf,
    exit_with_result,
)

BASE = "servicesNS/nobody/SA-ITOA/itoa_interface/service"
TEMPLATE_BASE = "servicesNS/nobody/SA-ITOA/itoa_interface/base_service_template"
DIFF_FIELDS = (
    "title",
    "enabled",
    "description",
    "sec_grp",
    "base_service_template_id",
    "service_tags",
    "entity_rules",
)
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
)
# Fields that are either managed explicitly or are ITSI system fields
# that should not trigger change detection in extra fields comparison
MANAGED_FIELDS = {
    # Explicitly managed fields
    "title",
    "enabled",
    "description",
    "sec_grp",
    "service_tags",
    "entity_rules",
    "base_service_template_id",
    # ITSI system/internal fields (read-only or auto-managed)
    "kpis",
    "permissions",
    "object_type",
    "mod_source",
    "mod_timestamp",
    "_version",
    "identifying_name",
    "is_healthscore_calculate_by_entity_enabled",
    "serviceTemplateId",  # Internal ITSI field (different from base_service_template_id)
}


def _looks_like_uuid(value: str) -> bool:
    """Check whether a value looks like a UUID.

    Args:
        value: String value to check.

    Returns:
        True if the value matches a UUID pattern, False otherwise.
    """
    return bool(UUID_RE.match(value))


def _resolve_base_service_template_id(
    *,
    client: ItsiRequest,
    template_ref: str,
    module: AnsibleModule,
) -> str:
    """Resolve a template reference (ID or title) into a template ID.

    Args:
        client: ItsiRequest instance.
        template_ref: Template identifier provided by the user. Can be a UUID-like `_key` or a title.
        module: Ansible module (used for fail_json).

    Returns:
        The resolved template `_key`.
    """
    if _looks_like_uuid(template_ref):
        return template_ref

    api_result = client.get(TEMPLATE_BASE, params={"filter": json.dumps({"title": template_ref})})
    if api_result is None:
        module.fail_json(msg=f"Template '{template_ref}' not found.")
    _status, _headers, body = api_result

    template = None
    if isinstance(body, list):
        matches = [d for d in body if isinstance(d, dict) and d.get("title") == template_ref]
        if len(matches) > 1:
            module.fail_json(
                msg="Multiple service templates found with the same title; use the template ID (_key).",
            )
        if matches:
            template = matches[0]

    if not template or not template.get("_key"):
        module.fail_json(
            msg=f"Service template with title '{template_ref}' was not found. Use the template ID (_key).",
        )

    return str(template["_key"])


def _int_bool(v: Any) -> Any:
    """Normalize boolean values to ITSI integer format.

    Args:
        v: Value to normalize. Booleans are converted to 1/0. Integers 0/1 are
            preserved. All other values are returned unchanged.

    Returns:
        Normalized integer for boolean-like values, otherwise the original value.
    """
    if isinstance(v, bool):
        return 1 if v else 0
    if v in (0, 1):
        return int(v)
    return v


def _normalize_service_tags(val: Any) -> Any:
    """Normalize service_tags for comparison.

    Sorts the ``tags`` array for order-insensitive comparison and strips
    ``template_tags`` which are ITSI-managed and should not affect diff.

    Args:
        val: service_tags value from API or desired payload.

    Returns:
        Normalized service_tags dict, or the original value if not a dict.
    """
    if not isinstance(val, dict):
        return val
    out = {k: v for k, v in val.items() if k != "template_tags"}
    if "tags" in out and isinstance(out["tags"], list):
        out["tags"] = sorted(out["tags"])
    return out


def _desired_payload(params: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble the outgoing payload from module params.

    Converts enabled to integer (0/1) as required by ITSI API.
    Wraps service_tags list into API format {"tags": [...]}.

    Args:
        params: Module parameters from Ansible.

    Returns:
        Payload dictionary to send to the ITSI API.
    """
    out = {}
    if params.get("name") is not None:
        out["title"] = params["name"]
    for k in ("description", "sec_grp", "entity_rules", "base_service_template_id"):
        if params.get(k) is not None:
            out[k] = params[k]
    if params.get("service_tags") is not None:
        out["service_tags"] = {"tags": sorted(params["service_tags"])}
    # ITSI API requires enabled as integer (0/1), not boolean
    if params.get("enabled") is not None:
        out["enabled"] = _int_bool(params["enabled"])
    extra = params.get("extra") or {}
    out.update(extra)
    return out


def _get_by_key(
    client: ItsiRequest,
    key: str,
    fields: Optional[Union[str, List[str]]] = None,
) -> Optional[Dict[str, Any]]:
    """Fetch a service document by `_key`.

    Args:
        client: ItsiRequest instance.
        key: Service `_key` identifier.
        fields: Optional field name or list of field names to request.

    Returns:
        Service document dict, or None.
    """
    params = {}
    if fields:
        params["fields"] = fields if isinstance(fields, str) else ",".join(fields)
    api_result = client.get(f"{BASE}/{quote_plus(key)}", params=params)
    if api_result is None:
        return None
    _status, _headers, body = api_result
    return body if isinstance(body, dict) else None


def _find_by_title(
    client: ItsiRequest,
    title: str,
) -> Optional[Dict[str, Any]]:
    """Find a service by exact title.

    Args:
        client: ItsiRequest instance.
        title: Exact service title to match.

    Returns:
        Service document dict if found, or None.
    """
    params = {"filter": json.dumps({"title": title})}
    api_result = client.get(BASE, params=params)
    if api_result is None:
        return None
    _status, _headers, body = api_result

    if not isinstance(body, list):
        return None

    matches = [d for d in body if isinstance(d, dict) and d.get("title") == title]
    return matches[0] if matches else None


def _create(client: ItsiRequest, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a service.

    Returns:
        Response body dict, or None if not found.
    """
    api_result = client.post(BASE, payload=payload)
    if api_result is None:
        return None
    _status, _headers, body = api_result
    return body


def _update(
    client: ItsiRequest,
    key: str,
    patch: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update a service by key using partial update.

    Args:
        client: ItsiRequest instance.
        key: Service _key.
        patch: Dict of fields to update.

    Returns:
        Response body dict, or None if not found.
    """
    params = {"is_partial_data": "1"}
    payload = {"_key": key, **patch}
    api_result = client.post(f"{BASE}/{quote_plus(key)}", params=params, payload=payload)
    if api_result is None:
        return None
    _status, _headers, body = api_result
    return body


def _delete(client: ItsiRequest, key: str) -> Optional[Dict[str, Any]]:
    """Delete a service by `_key`.

    Returns:
        Response body dict, or None if not found.
    """
    api_result = client.delete(f"{BASE}/{quote_plus(key)}")
    if api_result is None:
        return None
    _status, _headers, body = api_result
    return body


def _discover_current(
    *,
    client: ItsiRequest,
    key: Optional[str],
    name: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Discover the current service document.

    This resolves the target service by `_key` when provided, otherwise by exact title.
    When a service is found by title, a follow-up GET by `_key` is attempted to retrieve
    the full document, since list/filter endpoints may return partial data.

    Args:
        client: ItsiRequest instance.
        key: Service `_key` identifier, if provided.
        name: Service title, if provided.

    Returns:
        Current service document, or None if not found.
    """
    if key:
        return _get_by_key(client, key)

    doc = _find_by_title(client, name)

    # If found by title, fetch full document by _key for complete field data.
    if doc and doc.get("_key"):
        full_doc = _get_by_key(client, doc["_key"])
        return full_doc if full_doc is not None else doc

    return doc


def _handle_absent(
    module: AnsibleModule,
    client: ItsiRequest,
    current: Optional[Dict[str, Any]],
    key: Optional[str],
) -> None:
    """Handle state=absent: delete the service if it exists.

    Args:
        module: Ansible module instance.
        client: ItsiRequest instance.
        current: Current service document, or None if not found.
        key: Service _key if provided.
    """
    if not current:
        exit_with_result(module)

    if module.check_mode:
        exit_with_result(module, changed=True, before=current, diff=current)

    body = _delete(client, current.get("_key", key))
    exit_with_result(module, changed=True, before=current, diff=current, response=body or {})


def _handle_create(
    module: AnsibleModule,
    client: ItsiRequest,
    desired: Dict[str, Any],
    name: Optional[str],
) -> None:
    """Handle service creation when no current service exists.

    Args:
        module: Ansible module instance.
        client: ItsiRequest instance.
        desired: Desired service payload.
        name: Service name/title if provided.
    """
    if "title" not in desired:
        if name:
            desired["title"] = name
        else:
            module.fail_json(msg="Creating a service requires 'name' (title).")

    template_ref = desired.get("base_service_template_id")
    if template_ref not in (None, ""):
        desired["base_service_template_id"] = _resolve_base_service_template_id(
            client=client,
            template_ref=str(template_ref),
            module=module,
        )

    if module.check_mode:
        exit_with_result(module, changed=True, after=desired, diff=desired)

    body = _create(client, desired)
    after = desired
    created = body if isinstance(body, dict) else {}
    if created.get("_key"):
        after = {"_key": created["_key"], **desired}
    exit_with_result(module, changed=True, after=after, diff=desired, response=body or {})


def _handle_update(
    module: AnsibleModule,
    client: ItsiRequest,
    current: Dict[str, Any],
    key: Optional[str],
    desired: Dict[str, Any],
) -> None:
    """Handle service update when a current service exists.

    Args:
        module: Ansible module instance.
        client: ItsiRequest instance.
        current: Current service document.
        key: Service _key if provided.
        desired: Desired service payload.
    """
    if "title" not in desired and current.get("title"):
        desired["title"] = current["title"]

    # base_service_template_id is only used during creation
    desired.pop("base_service_template_id", None)

    have_conf = build_have_conf(
        desired,
        current,
        normalizers={"enabled": _int_bool, "service_tags": _normalize_service_tags},
    )
    want_conf: dict = utils.remove_empties(desired)
    diff: dict = utils.dict_diff(have_conf, want_conf)

    after: dict = dict(current)
    after.update(want_conf)

    if not diff:
        exit_with_result(module, before=current, after=current)

    # ITSI requires title in UPDATE requests even if unchanged
    if "title" not in want_conf and current.get("title"):
        want_conf["title"] = current["title"]

    if module.check_mode:
        exit_with_result(module, changed=True, before=current, after=after, diff=diff)

    body = _update(client, current.get("_key", key), want_conf)
    exit_with_result(
        module,
        changed=True,
        before=current,
        after=after,
        diff=diff,
        response=body or {},
    )


def main() -> None:
    """Entry point for the `itsi_service` Ansible module."""
    module = AnsibleModule(
        argument_spec=dict(
            service_id=dict(type="str"),
            name=dict(type="str"),
            enabled=dict(type="bool"),
            description=dict(type="str"),
            sec_grp=dict(type="str"),
            entity_rules=dict(type="list", elements="dict"),
            service_tags=dict(type="list", elements="str"),
            base_service_template_id=dict(type="str"),
            extra=dict(type="dict", default={}),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        ),
        supports_check_mode=True,
        required_one_of=[["service_id", "name"]],
        mutually_exclusive=[["base_service_template_id", "entity_rules"]],
    )

    if not getattr(module, "_socket_path", None):
        module.fail_json(
            msg="Use ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client",
        )

    params = module.params

    try:
        client = ItsiRequest(Connection(module._socket_path), module)
    except Exception as e:
        module.fail_json(msg=f"Failed to establish connection: {e}")

    try:
        state = params["state"]
        key = params.get("service_id")
        name = params.get("name")

        current = _discover_current(client=client, key=key, name=name)

        if state == "absent":
            _handle_absent(module, client, current, key)

        desired = _desired_payload(params)

        if not current:
            _handle_create(module, client, desired, name)

        _handle_update(module, client, current, key, desired)

    except Exception as e:
        module.fail_json(msg=f"Exception occurred: {str(e)}")


if __name__ == "__main__":
    main()
