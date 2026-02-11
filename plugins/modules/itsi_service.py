#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Splunk ITSI Ansible Collection Maintainers
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


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
service:
  description: Service document after the operation when available.
  type: dict
  returned: when not bulk
changed_fields:
  description: Keys that changed during update.
  type: list
  elements: str
  returned: when state=present and an update occurred
diff:
  description: Structured before/after for managed fields.
  type: dict
  returned: when check_mode is true or an update/delete occurs
raw:
  description: Raw JSON from Splunk for the last call.
  type: raw
  returned: always
changed:
  description: Whether any change was made.
  type: bool
  returned: always
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import quote_plus

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

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
    result: Dict[str, Any],
) -> str:
    """Resolve a template reference (ID or title) into a template ID.

    Args:
        client: ItsiRequest instance.
        template_ref: Template identifier provided by the user. Can be a UUID-like `_key` or a title.
        module: Ansible module (used for fail_json).
        result: Result dict (passed to fail_json for context).

    Returns:
        The resolved template `_key`.
    """
    if _looks_like_uuid(template_ref):
        return template_ref

    api_result = client.get(TEMPLATE_BASE, params={"filter": json.dumps({"title": template_ref})})
    if api_result is None:
        module.fail_json(msg=f"Template '{template_ref}' not found.", **result)
    _status, _headers, body = api_result

    # ITSI itoa_interface API returns a list directly
    template = None
    if isinstance(body, list):
        matches = [d for d in body if isinstance(d, dict) and d.get("title") == template_ref]
        if len(matches) > 1:
            module.fail_json(
                msg="Multiple service templates found with the same title; use the template ID (_key).",
                **result,
            )
        if matches:
            template = matches[0]

    if not template or not template.get("_key"):
        module.fail_json(
            msg=f"Service template with title '{template_ref}' was not found. Use the template ID (_key).",
            **result,
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


def _equal_service_tags(desired: dict, current: dict) -> bool:
    """Order-insensitive service_tags comparison.

    Only compares the 'tags' array (user-assigned). The 'template_tags' array is
    inherited from the service template and managed by ITSI, so we don't compare it
    to avoid false positives due to ITSI's async processing of template inheritance.

    Args:
        desired: Desired service_tags from module parameters.
        current: Current service_tags from API response.

    Returns:
        True if service_tags are equivalent (no update needed), False otherwise.
    """
    # Normalize None/empty to empty dict for comparison
    desired = desired or {}
    current = current or {}

    # If both are empty/None, they're equal
    if not desired and not current:
        return True

    # Compare only 'tags' (user-assigned) - order insensitive
    # 'template_tags' are inherited from template and managed by ITSI
    desired_tags = set(desired.get("tags") or [])
    current_tags = set(current.get("tags") or [])

    if desired_tags != current_tags:
        return False

    # Compare any other keys in service_tags (excluding template_tags)
    other_keys = (set(desired.keys()) | set(current.keys())) - {"tags", "template_tags"}
    for key in other_keys:
        if desired.get(key) != current.get(key):
            return False

    return True


def _compare_scalar_fields(
    current_doc: dict,
    desired_doc: dict,
) -> Tuple[Dict[str, Any], List[str]]:
    """Compare scalar fields (title, description, sec_grp).

    Args:
        current_doc: Current document from API.
        desired_doc: Desired document from module params.

    Returns:
        Tuple of (patch dict, list of changed field names).
    """
    patch: Dict[str, Any] = {}
    changed: List[str] = []
    for field in ("title", "description", "sec_grp"):
        if field in desired_doc and desired_doc.get(field) != current_doc.get(field):
            patch[field] = desired_doc[field]
            changed.append(field)
    return patch, changed


def _compare_enabled(
    current_doc: dict,
    desired_doc: dict,
) -> Tuple[Dict[str, Any], List[str]]:
    """Compare enabled field with 0/1 integer semantics.

    Args:
        current_doc: Current document from API.
        desired_doc: Desired document from module params.

    Returns:
        Tuple of (patch dict, list of changed field names).
    """
    patch: Dict[str, Any] = {}
    changed: List[str] = []
    if "enabled" in desired_doc:
        want = _int_bool(desired_doc.get("enabled"))
        have = _int_bool(current_doc.get("enabled"))
        if want != have:
            patch["enabled"] = want
            changed.append("enabled")
    return patch, changed


def _compare_service_tags_field(
    current_doc: dict,
    desired_doc: dict,
) -> Tuple[Dict[str, Any], List[str]]:
    """Compare service_tags field with order-insensitive comparison.

    Args:
        current_doc: Current document from API.
        desired_doc: Desired document from module params.

    Returns:
        Tuple of (patch dict, list of changed field names).
    """
    patch: Dict[str, Any] = {}
    changed: List[str] = []
    if "service_tags" in desired_doc and not _equal_service_tags(
        desired_doc.get("service_tags"),
        current_doc.get("service_tags"),
    ):
        patch["service_tags"] = desired_doc["service_tags"]
        changed.append("service_tags")
    return patch, changed


def _compare_entity_rules(
    current_doc: dict,
    desired_doc: dict,
) -> Tuple[Dict[str, Any], List[str]]:
    """Compare entity_rules field with raw comparison.

    Args:
        current_doc: Current document from API.
        desired_doc: Desired document from module params.

    Returns:
        Tuple of (patch dict, list of changed field names).
    """
    patch: Dict[str, Any] = {}
    changed: List[str] = []
    if "entity_rules" in desired_doc and desired_doc.get("entity_rules") != current_doc.get("entity_rules"):
        patch["entity_rules"] = desired_doc["entity_rules"]
        changed.append("entity_rules")
    return patch, changed


def _compare_extra_fields(
    current_doc: dict,
    desired_doc: dict,
) -> Tuple[Dict[str, Any], List[str]]:
    """Compare extra (unmanaged) fields in desired and detect removed fields.

    Args:
        current_doc: Current document from API.
        desired_doc: Desired document from module params.

    Returns:
        Tuple of (patch dict, list of changed field names).
    """
    patch: Dict[str, Any] = {}
    changed: List[str] = []

    # Check for new or modified extra fields
    for field, value in desired_doc.items():
        if field in MANAGED_FIELDS:
            continue
        if current_doc.get(field) != value:
            patch[field] = value
            changed.append(field)

    # Check for removed extra fields (present in current but not in desired)
    for field in current_doc.keys():
        if field in MANAGED_FIELDS:
            continue
        # Skip internal fields that start with underscore
        if field.startswith("_"):
            continue
        if field not in desired_doc and current_doc.get(field) is not None:
            patch[field] = None
            changed.append(field)

    return patch, changed


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
    # Wrap service_tags list into API format {"tags": [...]}
    if params.get("service_tags") is not None:
        out["service_tags"] = {"tags": params["service_tags"]}
    # ITSI API requires enabled as integer (0/1), not boolean
    if params.get("enabled") is not None:
        out["enabled"] = _int_bool(params["enabled"])
    extra = params.get("extra") or {}
    out.update(extra)
    return out


def _compute_patch(current_doc: dict, desired_doc: dict) -> Tuple[dict, list]:
    """Compare selected fields and build minimal patch.

    Args:
        current_doc: Current document from API.
        desired_doc: Desired document from module params.

    Returns:
        Tuple of (patch dict, list of changed field names).

    Notes:
        - enabled compared as 0/1 (ITSI requires integer)
        - service_tags: only 'tags' array is compared (template_tags are ITSI-managed)
        - entity_rules compared raw
        - base_service_template_id is NOT included (only used during creation)
    """
    patch: Dict[str, Any] = {}
    changed: List[str] = []

    # Compare scalar fields (title, description, sec_grp)
    scalar_patch, scalar_changed = _compare_scalar_fields(current_doc, desired_doc)
    patch.update(scalar_patch)
    changed.extend(scalar_changed)

    # Compare enabled field with integer semantics
    enabled_patch, enabled_changed = _compare_enabled(current_doc, desired_doc)
    patch.update(enabled_patch)
    changed.extend(enabled_changed)

    # Compare service_tags with order-insensitive comparison
    tags_patch, tags_changed = _compare_service_tags_field(current_doc, desired_doc)
    patch.update(tags_patch)
    changed.extend(tags_changed)

    # Compare entity_rules with raw comparison
    rules_patch, rules_changed = _compare_entity_rules(current_doc, desired_doc)
    patch.update(rules_patch)
    changed.extend(rules_changed)

    # Compare extra (unmanaged) fields
    extra_patch, extra_changed = _compare_extra_fields(current_doc, desired_doc)
    patch.update(extra_patch)
    changed.extend(extra_changed)

    return patch, changed


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
    current_doc: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Update a service by key.

    Args:
        client: ItsiRequest instance.
        key: Service _key.
        patch: Dict of fields to update.
        current_doc: Optional current document to merge patch into for full update.

    Returns:
        Response body dict, or None if not found.
    """
    if current_doc:
        # Full object update: merge patch into current doc
        # This is more reliable for ITSI as partial updates don't always persist
        payload = {**current_doc, **patch, "_key": key}
        # Remove system/internal fields that shouldn't be sent in updates
        for skip_field in (
            "_user",
            "_version",
            "mod_source",
            "mod_timestamp",
            "object_type",
            "permissions",
            "kpis",
            "identifying_name",
            "is_healthscore_calculate_by_entity_enabled",
        ):
            payload.pop(skip_field, None)
    else:
        # Partial update fallback
        payload = {"_key": key, **patch}
    api_result = client.post(f"{BASE}/{quote_plus(key)}", payload=payload)
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
    result: Dict[str, Any],
) -> None:
    """Handle state=absent: delete the service if it exists.

    Args:
        module: Ansible module instance.
        client: ItsiRequest instance.
        current: Current service document, or None if not found.
        key: Service _key if provided.
        result: Result dict to update.
    """
    if not current:
        module.exit_json(**result)

    before_diff = {k: current.get(k) for k in DIFF_FIELDS}

    if module.check_mode:
        result["changed"] = True
        result["diff"]["before"] = before_diff
        result["diff"]["after"] = {}
        module.exit_json(**result)

    body = _delete(client, current.get("_key", key))
    result["raw"] = body
    result["changed"] = True
    result["service"] = None
    result["changed_fields"] = ["_deleted"]
    result["diff"]["before"] = before_diff
    result["diff"]["after"] = {}
    module.exit_json(**result)


def _handle_create(
    module: AnsibleModule,
    client: ItsiRequest,
    desired: Dict[str, Any],
    name: Optional[str],
    result: Dict[str, Any],
) -> None:
    """Handle service creation when no current service exists.

    Args:
        module: Ansible module instance.
        client: ItsiRequest instance.
        desired: Desired service payload.
        name: Service name/title if provided.
        result: Result dict to update.
    """
    if "title" not in desired:
        if name:
            desired["title"] = name
        else:
            module.fail_json(msg="Creating a service requires 'name' (title).", **result)

    template_ref = desired.get("base_service_template_id")
    if template_ref not in (None, ""):
        desired["base_service_template_id"] = _resolve_base_service_template_id(
            client=client,
            template_ref=str(template_ref),
            module=module,
            result=result,
        )

    if module.check_mode:
        result["changed"] = True
        result["diff"]["before"] = {}
        result["diff"]["after"] = {k: desired.get(k) for k in DIFF_FIELDS}
        module.exit_json(**result)

    body = _create(client, desired)
    result["raw"] = body

    created = body if isinstance(body, dict) else {}
    result["service"] = {"_key": created.get("_key"), **desired} if created.get("_key") else desired
    result["changed"] = True
    result["changed_fields"] = list(desired.keys())
    result["diff"]["before"] = {}
    result["diff"]["after"] = {k: desired.get(k) for k in DIFF_FIELDS}
    module.exit_json(**result)


def _handle_update(
    module: AnsibleModule,
    client: ItsiRequest,
    current: Dict[str, Any],
    key: Optional[str],
    desired: Dict[str, Any],
    result: Dict[str, Any],
) -> None:
    """Handle service update when a current service exists.

    Args:
        module: Ansible module instance.
        client: ItsiRequest instance.
        current: Current service document.
        key: Service _key if provided.
        desired: Desired service payload.
        result: Result dict to update.
    """
    # Ensure title present in payload for Splunk validation
    if "title" not in desired and current.get("title"):
        desired["title"] = current["title"]

    patch, changed_fields = _compute_patch(current, desired)

    if not patch:
        result["service"] = current
        module.exit_json(**result)

    # ITSI requires title in UPDATE requests even if unchanged
    if "title" not in patch and current.get("title"):
        patch["title"] = current["title"]

    before_diff = {k: current.get(k) for k in DIFF_FIELDS}

    if module.check_mode:
        after = dict(current)
        after.update(patch)
        result["changed"] = True
        result["changed_fields"] = changed_fields
        result["diff"]["before"] = before_diff
        result["diff"]["after"] = {k: after.get(k) for k in DIFF_FIELDS}
        module.exit_json(**result)

    body = _update(client, current.get("_key", key), patch, current_doc=current)
    result["raw"] = body

    result["changed"] = True
    result["changed_fields"] = changed_fields
    after = dict(current)
    after.update(patch)
    result["service"] = after
    result["diff"]["before"] = before_diff
    result["diff"]["after"] = {k: after.get(k) for k in DIFF_FIELDS}
    module.exit_json(**result)


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
    client = ItsiRequest(Connection(module._socket_path), module)

    result: Dict[str, Any] = {
        "changed": False,
        "service": None,
        "raw": {},
        "changed_fields": [],
        "diff": {"before": {}, "after": {}},
    }

    state = params["state"]
    key = params.get("service_id")
    name = params.get("name")

    # Discover current service state
    current = _discover_current(client=client, key=key, name=name)

    # Absent
    if state == "absent":
        _handle_absent(module, client, current, key, result)

    # Handle state=present
    desired = _desired_payload(params)

    if not current:
        _handle_create(module, client, desired, name, result)

    _handle_update(module, client, current, key, desired, result)


if __name__ == "__main__":
    main()
