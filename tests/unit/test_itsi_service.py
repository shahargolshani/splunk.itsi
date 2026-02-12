# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_service module."""


import json
from unittest.mock import MagicMock, patch

import pytest

# Import module functions for testing
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest
from ansible_collections.splunk.itsi.plugins.modules.itsi_service import (
    _compute_patch,
    _create,
    _delete,
    _desired_payload,
    _discover_current,
    _equal_service_tags,
    _find_by_title,
    _get_by_key,
    _int_bool,
    _looks_like_uuid,
    _resolve_base_service_template_id,
    _update,
    main,
)
from conftest import AnsibleExitJson, AnsibleFailJson, make_mock_conn

# Sample test data
SAMPLE_SERVICE = {
    "_key": "a2961217-9728-4e9f-b67b-15bf4a40ad7c",
    "title": "api-gateway",
    "enabled": 1,
    "description": "API Gateway Service",
    "sec_grp": "default_itsi_security_group",
    "service_tags": {"tags": ["prod", "payments"]},
    "entity_rules": [],
}

SAMPLE_SERVICE_FULL = {
    "_key": "a2961217-9728-4e9f-b67b-15bf4a40ad7c",
    "title": "api-gateway",
    "enabled": 1,
    "description": "API Gateway Service",
    "sec_grp": "default_itsi_security_group",
    "service_tags": {"tags": ["prod", "payments"], "template_tags": ["inherited"]},
    "entity_rules": [
        {
            "rule_condition": "AND",
            "rule_items": [
                {"field": "host", "field_type": "alias", "rule_type": "matches", "value": "web-*"},
            ],
        },
    ],
    "base_service_template_id": "",
    "object_type": "service",
}

SAMPLE_TEMPLATE = {
    "_key": "12345678-1234-5678-90ab-cdef12345678",
    "title": "My Service Template",
    "object_type": "base_service_template",
}


def _mock_module():
    """Create a MagicMock AnsibleModule for ItsiRequest."""
    module = MagicMock()
    module.fail_json.side_effect = AnsibleFailJson
    return module


class TestLooksLikeUuid:
    """Tests for _looks_like_uuid helper function."""

    def test_valid_uuid_lowercase(self):
        """Test valid UUID in lowercase."""
        assert _looks_like_uuid("a2961217-9728-4e9f-b67b-15bf4a40ad7c") is True

    def test_valid_uuid_uppercase(self):
        """Test valid UUID in uppercase."""
        assert _looks_like_uuid("A2961217-9728-4E9F-B67B-15BF4A40AD7C") is True

    def test_valid_uuid_mixed_case(self):
        """Test valid UUID in mixed case."""
        assert _looks_like_uuid("a2961217-9728-4E9F-b67b-15BF4A40AD7C") is True

    def test_invalid_uuid_too_short(self):
        """Test invalid UUID that is too short."""
        assert _looks_like_uuid("a2961217-9728-4e9f-b67b") is False

    def test_invalid_uuid_no_dashes(self):
        """Test invalid UUID without dashes."""
        assert _looks_like_uuid("a29612179728e9fb67b15bf4a40ad7c") is False

    def test_invalid_uuid_wrong_format(self):
        """Test invalid UUID with wrong format."""
        assert _looks_like_uuid("not-a-uuid-at-all") is False

    def test_invalid_uuid_empty_string(self):
        """Test empty string."""
        assert _looks_like_uuid("") is False

    def test_invalid_uuid_title_string(self):
        """Test a title string that is not a UUID."""
        assert _looks_like_uuid("My Service Template") is False

    def test_invalid_uuid_with_special_chars(self):
        """Test string with special characters."""
        assert _looks_like_uuid("a2961217-9728-4e9f-b67b-15bf4a40ad7!") is False


class TestIntBool:
    """Tests for _int_bool helper function."""

    def test_bool_true(self):
        """Test True converts to 1."""
        assert _int_bool(True) == 1

    def test_bool_false(self):
        """Test False converts to 0."""
        assert _int_bool(False) == 0

    def test_int_one(self):
        """Test integer 1 stays as 1."""
        assert _int_bool(1) == 1

    def test_int_zero(self):
        """Test integer 0 stays as 0."""
        assert _int_bool(0) == 0

    def test_string_value(self):
        """Test string value passes through unchanged."""
        assert _int_bool("enabled") == "enabled"

    def test_none_value(self):
        """Test None value passes through unchanged."""
        assert _int_bool(None) is None

    def test_int_two(self):
        """Test integer 2 passes through unchanged."""
        assert _int_bool(2) == 2

    def test_negative_int(self):
        """Test negative integer passes through unchanged."""
        assert _int_bool(-1) == -1


class TestEqualServiceTags:
    """Tests for _equal_service_tags helper function."""

    def test_both_empty(self):
        """Test both None are equal."""
        assert _equal_service_tags(None, None) is True

    def test_both_empty_dict(self):
        """Test both empty dicts are equal."""
        assert _equal_service_tags({}, {}) is True

    def test_none_vs_empty_dict(self):
        """Test None equals empty dict."""
        assert _equal_service_tags(None, {}) is True
        assert _equal_service_tags({}, None) is True

    def test_equal_tags(self):
        """Test equal tags."""
        desired = {"tags": ["prod", "payments"]}
        current = {"tags": ["prod", "payments"]}
        assert _equal_service_tags(desired, current) is True

    def test_equal_tags_different_order(self):
        """Test equal tags in different order."""
        desired = {"tags": ["payments", "prod"]}
        current = {"tags": ["prod", "payments"]}
        assert _equal_service_tags(desired, current) is True

    def test_different_tags(self):
        """Test different tags."""
        desired = {"tags": ["prod"]}
        current = {"tags": ["prod", "payments"]}
        assert _equal_service_tags(desired, current) is False

    def test_template_tags_ignored(self):
        """Test template_tags are ignored in comparison."""
        desired = {"tags": ["prod"]}
        current = {"tags": ["prod"], "template_tags": ["inherited", "from-template"]}
        assert _equal_service_tags(desired, current) is True

    def test_only_template_tags_differ(self):
        """Test only template_tags differ (should be equal)."""
        desired = {"tags": ["prod"], "template_tags": []}
        current = {"tags": ["prod"], "template_tags": ["inherited"]}
        assert _equal_service_tags(desired, current) is True

    def test_desired_empty_current_has_tags(self):
        """Test desired empty but current has tags."""
        desired = {}
        current = {"tags": ["prod"]}
        assert _equal_service_tags(desired, current) is False

    def test_desired_has_tags_current_empty(self):
        """Test desired has tags but current is empty."""
        desired = {"tags": ["prod"]}
        current = {}
        assert _equal_service_tags(desired, current) is False

    def test_other_keys_equal(self):
        """Test other keys in service_tags are compared."""
        desired = {"tags": ["prod"], "custom_key": "value"}
        current = {"tags": ["prod"], "custom_key": "value"}
        assert _equal_service_tags(desired, current) is True

    def test_other_keys_differ(self):
        """Test other keys in service_tags that differ."""
        desired = {"tags": ["prod"], "custom_key": "value1"}
        current = {"tags": ["prod"], "custom_key": "value2"}
        assert _equal_service_tags(desired, current) is False


class TestDesiredPayload:
    """Tests for _desired_payload helper function."""

    def test_name_to_title(self):
        """Test name param becomes title in payload."""
        params = {"name": "my-service"}
        result = _desired_payload(params)
        assert result["title"] == "my-service"

    def test_description(self):
        """Test description is included."""
        params = {"description": "Test description"}
        result = _desired_payload(params)
        assert result["description"] == "Test description"

    def test_sec_grp(self):
        """Test sec_grp is included."""
        params = {"sec_grp": "my_team"}
        result = _desired_payload(params)
        assert result["sec_grp"] == "my_team"

    def test_entity_rules(self):
        """Test entity_rules is included."""
        rules = [{"rule_condition": "AND", "rule_items": []}]
        params = {"entity_rules": rules}
        result = _desired_payload(params)
        assert result["entity_rules"] == rules

    def test_base_service_template_id(self):
        """Test base_service_template_id is included."""
        params = {"base_service_template_id": "template-id"}
        result = _desired_payload(params)
        assert result["base_service_template_id"] == "template-id"

    def test_service_tags_wrapped(self):
        """Test service_tags list is wrapped in dict."""
        params = {"service_tags": ["prod", "payments"]}
        result = _desired_payload(params)
        assert result["service_tags"] == {"tags": ["prod", "payments"]}

    def test_enabled_true(self):
        """Test enabled True becomes 1."""
        params = {"enabled": True}
        result = _desired_payload(params)
        assert result["enabled"] == 1

    def test_enabled_false(self):
        """Test enabled False becomes 0."""
        params = {"enabled": False}
        result = _desired_payload(params)
        assert result["enabled"] == 0

    def test_extra_merged(self):
        """Test extra dict is merged."""
        params = {"name": "svc", "extra": {"custom_field": "custom_value"}}
        result = _desired_payload(params)
        assert result["title"] == "svc"
        assert result["custom_field"] == "custom_value"

    def test_extra_overrides(self):
        """Test extra can override managed fields."""
        params = {"name": "original", "extra": {"title": "overridden"}}
        result = _desired_payload(params)
        assert result["title"] == "overridden"

    def test_none_values_excluded(self):
        """Test None values are excluded."""
        params = {"name": "svc", "description": None, "sec_grp": None}
        result = _desired_payload(params)
        assert "description" not in result
        assert "sec_grp" not in result

    def test_empty_params(self):
        """Test empty params returns empty dict."""
        params = {}
        result = _desired_payload(params)
        assert result == {}

    def test_all_params(self):
        """Test all params together."""
        params = {
            "name": "full-service",
            "enabled": True,
            "description": "Full description",
            "sec_grp": "team-a",
            "entity_rules": [],
            "service_tags": ["tag1"],
            "base_service_template_id": "tmpl-id",
            "extra": {"priority": "high"},
        }
        result = _desired_payload(params)
        assert result["title"] == "full-service"
        assert result["enabled"] == 1
        assert result["description"] == "Full description"
        assert result["sec_grp"] == "team-a"
        assert result["entity_rules"] == []
        assert result["service_tags"] == {"tags": ["tag1"]}
        assert result["base_service_template_id"] == "tmpl-id"
        assert result["priority"] == "high"


class TestComputePatch:
    """Tests for _compute_patch helper function."""

    def test_no_changes(self):
        """Test no changes returns empty patch."""
        current = {"title": "svc", "enabled": 1, "description": "desc"}
        desired = {"title": "svc", "enabled": 1, "description": "desc"}
        patch, changed = _compute_patch(current, desired)
        assert patch == {}
        assert changed == []

    def test_title_change(self):
        """Test title change detected."""
        current = {"title": "old-name"}
        desired = {"title": "new-name"}
        patch, changed = _compute_patch(current, desired)
        assert patch["title"] == "new-name"
        assert "title" in changed

    def test_description_change(self):
        """Test description change detected."""
        current = {"description": "old desc"}
        desired = {"description": "new desc"}
        patch, changed = _compute_patch(current, desired)
        assert patch["description"] == "new desc"
        assert "description" in changed

    def test_sec_grp_change(self):
        """Test sec_grp change detected."""
        current = {"sec_grp": "team-a"}
        desired = {"sec_grp": "team-b"}
        patch, changed = _compute_patch(current, desired)
        assert patch["sec_grp"] == "team-b"
        assert "sec_grp" in changed

    def test_enabled_change_bool_to_int(self):
        """Test enabled change with bool vs int."""
        current = {"enabled": 0}
        desired = {"enabled": 1}
        patch, changed = _compute_patch(current, desired)
        assert patch["enabled"] == 1
        assert "enabled" in changed

    def test_enabled_same_as_bool(self):
        """Test enabled True equals 1."""
        current = {"enabled": 1}
        desired = {"enabled": True}
        patch, changed = _compute_patch(current, desired)
        # Should be no change since True == 1 after normalization
        assert "enabled" not in patch
        assert "enabled" not in changed

    def test_service_tags_change(self):
        """Test service_tags change detected."""
        current = {"service_tags": {"tags": ["old"]}}
        desired = {"service_tags": {"tags": ["new"]}}
        patch, changed = _compute_patch(current, desired)
        assert patch["service_tags"] == {"tags": ["new"]}
        assert "service_tags" in changed

    def test_service_tags_no_change_different_order(self):
        """Test service_tags same with different order."""
        current = {"service_tags": {"tags": ["b", "a"]}}
        desired = {"service_tags": {"tags": ["a", "b"]}}
        patch, changed = _compute_patch(current, desired)
        assert "service_tags" not in patch

    def test_entity_rules_change(self):
        """Test entity_rules change detected."""
        current = {"entity_rules": []}
        desired = {"entity_rules": [{"rule_condition": "AND", "rule_items": []}]}
        patch, changed = _compute_patch(current, desired)
        assert "entity_rules" in patch
        assert "entity_rules" in changed

    def test_extra_field_added(self):
        """Test extra field added is detected."""
        current = {"title": "svc"}
        desired = {"title": "svc", "custom_field": "value"}
        patch, changed = _compute_patch(current, desired)
        assert patch["custom_field"] == "value"
        assert "custom_field" in changed

    def test_extra_field_changed(self):
        """Test extra field change detected."""
        current = {"title": "svc", "custom": "old"}
        desired = {"title": "svc", "custom": "new"}
        patch, changed = _compute_patch(current, desired)
        assert patch["custom"] == "new"
        assert "custom" in changed

    def test_base_service_template_id_ignored(self):
        """Test base_service_template_id is not in patch (creation only)."""
        current = {"title": "svc", "base_service_template_id": "old"}
        desired = {"title": "svc", "base_service_template_id": "new"}
        patch, changed = _compute_patch(current, desired)
        # base_service_template_id should be in managed set and ignored
        assert "base_service_template_id" not in patch

    def test_system_fields_ignored(self):
        """Test system fields like kpis, permissions are ignored."""
        current = {"title": "svc", "kpis": [{"id": "kpi1"}], "permissions": {"read": "*"}}
        desired = {"title": "svc"}
        patch, changed = _compute_patch(current, desired)
        assert "kpis" not in patch
        assert "permissions" not in patch

    def test_underscore_fields_ignored(self):
        """Test fields starting with underscore are ignored."""
        current = {"title": "svc", "_version": "123", "_user": "admin"}
        desired = {"title": "svc"}
        patch, changed = _compute_patch(current, desired)
        assert "_version" not in patch
        assert "_user" not in patch

    def test_multiple_changes(self):
        """Test multiple changes at once."""
        current = {"title": "old", "enabled": 0, "description": "old desc"}
        desired = {"title": "new", "enabled": 1, "description": "new desc"}
        patch, changed = _compute_patch(current, desired)
        assert patch["title"] == "new"
        assert patch["enabled"] == 1
        assert patch["description"] == "new desc"
        assert len(changed) == 3


class TestGetByKey:
    """Tests for _get_by_key helper function."""

    def test_get_by_key_success(self):
        """Test successful get by key."""
        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_SERVICE))

        doc = _get_by_key(
            ItsiRequest(mock_conn, _mock_module()),
            "a2961217-9728-4e9f-b67b-15bf4a40ad7c",
        )

        assert doc is not None
        assert doc["title"] == "api-gateway"

    def test_get_by_key_not_found(self):
        """Test get by key not found."""
        mock_conn = make_mock_conn(404, json.dumps({"error": "Not found"}))

        doc = _get_by_key(ItsiRequest(mock_conn, _mock_module()), "nonexistent")

        assert doc is None

    def test_get_by_key_with_fields_string(self):
        """Test get by key with fields as string."""
        mock_conn = make_mock_conn(200, json.dumps({"_key": "test", "title": "svc"}))

        _get_by_key(ItsiRequest(mock_conn, _mock_module()), "test", fields="_key,title")

        call_args = mock_conn.send_request.call_args
        assert "fields=_key%2Ctitle" in call_args[0][0]

    def test_get_by_key_with_fields_list(self):
        """Test get by key with fields as list."""
        mock_conn = make_mock_conn(200, json.dumps({"_key": "test"}))

        _get_by_key(ItsiRequest(mock_conn, _mock_module()), "test", fields=["_key", "title"])

        call_args = mock_conn.send_request.call_args
        assert "fields=_key%2Ctitle" in call_args[0][0]


class TestFindByTitle:
    """Tests for _find_by_title helper function."""

    def test_find_by_title_found(self):
        """Test find by title when service exists."""
        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_SERVICE]))

        doc = _find_by_title(ItsiRequest(mock_conn, _mock_module()), "api-gateway")

        assert doc is not None
        assert doc["title"] == "api-gateway"

    def test_find_by_title_not_found(self):
        """Test find by title when service doesn't exist."""
        mock_conn = make_mock_conn(200, json.dumps([]))

        doc = _find_by_title(ItsiRequest(mock_conn, _mock_module()), "nonexistent")

        assert doc is None

    def test_find_by_title_filters_exact_match(self):
        """Test find by title filters for exact match."""
        mock_conn = make_mock_conn(
            200,
            json.dumps(
                [
                    {"_key": "1", "title": "api-gateway"},
                    {"_key": "2", "title": "api-gateway-v2"},
                ],
            ),
        )

        doc = _find_by_title(ItsiRequest(mock_conn, _mock_module()), "api-gateway")

        assert doc is not None
        assert doc["_key"] == "1"

    def test_find_by_title_non_list_response(self):
        """Test find by title with non-list response."""
        mock_conn = make_mock_conn(200, json.dumps({"error": "unexpected"}))

        doc = _find_by_title(ItsiRequest(mock_conn, _mock_module()), "test")

        assert doc is None


class TestCreate:
    """Tests for _create helper function."""

    def test_create_success(self):
        """Test successful create."""
        mock_conn = make_mock_conn(200, json.dumps({"_key": "new-uuid"}))

        body = _create(
            ItsiRequest(mock_conn, _mock_module()),
            {"title": "new-service"},
        )

        assert body is not None
        assert body["_key"] == "new-uuid"
        call_args = mock_conn.send_request.call_args
        # Module calls: conn.send_request(path, method=method, body=body)
        assert call_args.kwargs["method"] == "POST"

    def test_create_with_full_payload(self):
        """Test create with full payload."""
        mock_conn = make_mock_conn(200, json.dumps({"_key": "new"}))

        payload = {
            "title": "full-service",
            "enabled": 1,
            "description": "Full description",
            "service_tags": {"tags": ["tag1"]},
        }
        _create(ItsiRequest(mock_conn, _mock_module()), payload)

        call_args = mock_conn.send_request.call_args
        # Module calls: conn.send_request(path, method=method, body=body)
        sent_payload = json.loads(call_args.kwargs["body"])
        assert sent_payload["title"] == "full-service"
        assert sent_payload["enabled"] == 1


class TestUpdate:
    """Tests for _update helper function."""

    def test_update_partial(self):
        """Test partial update."""
        mock_conn = make_mock_conn(200, json.dumps({"_key": "test"}))

        _update(ItsiRequest(mock_conn, _mock_module()), "test-key", {"enabled": 0})

        call_args = mock_conn.send_request.call_args
        # Module calls: conn.send_request(path, method=method, body=body)
        sent_payload = json.loads(call_args.kwargs["body"])
        assert sent_payload["_key"] == "test-key"
        assert sent_payload["enabled"] == 0

    def test_update_with_current_doc(self):
        """Test update merges with current doc."""
        mock_conn = make_mock_conn(200, json.dumps({"_key": "test"}))

        current = {"title": "svc", "enabled": 1, "description": "old"}
        patch = {"description": "new"}
        _update(ItsiRequest(mock_conn, _mock_module()), "test-key", patch, current_doc=current)

        call_args = mock_conn.send_request.call_args
        # Module calls: conn.send_request(path, method=method, body=body)
        sent_payload = json.loads(call_args.kwargs["body"])
        assert sent_payload["title"] == "svc"
        assert sent_payload["enabled"] == 1
        assert sent_payload["description"] == "new"
        assert sent_payload["_key"] == "test-key"

    def test_update_removes_system_fields(self):
        """Test update removes system fields from payload."""
        mock_conn = make_mock_conn(200, "{}")

        current = {
            "title": "svc",
            "_user": "admin",
            "_version": "123",
            "kpis": [{"id": "kpi1"}],
            "permissions": {"read": "*"},
        }
        _update(ItsiRequest(mock_conn, _mock_module()), "key", {"title": "svc"}, current_doc=current)

        call_args = mock_conn.send_request.call_args
        # Module calls: conn.send_request(path, method=method, body=body)
        sent_payload = json.loads(call_args.kwargs["body"])
        assert "_user" not in sent_payload
        assert "_version" not in sent_payload
        assert "kpis" not in sent_payload
        assert "permissions" not in sent_payload


class TestDelete:
    """Tests for _delete helper function."""

    def test_delete_success(self):
        """Test successful delete."""
        mock_conn = make_mock_conn(200, "")

        body = _delete(ItsiRequest(mock_conn, _mock_module()), "test-key")

        # Empty body returns {} from ItsiRequest
        assert body is not None
        call_args = mock_conn.send_request.call_args
        # Module calls: conn.send_request(path, method=method, body=body)
        assert call_args.kwargs["method"] == "DELETE"
        assert "test-key" in call_args[0][0]  # path is positional


class TestResolveBaseServiceTemplateId:
    """Tests for _resolve_base_service_template_id helper function."""

    def test_resolve_uuid_passthrough(self):
        """Test UUID is returned as-is."""
        mock_conn = MagicMock()
        mock_module = MagicMock()
        result = {}

        resolved = _resolve_base_service_template_id(
            client=ItsiRequest(mock_conn, mock_module),
            template_ref="a2961217-9728-4e9f-b67b-15bf4a40ad7c",
            module=mock_module,
            result=result,
        )

        assert resolved == "a2961217-9728-4e9f-b67b-15bf4a40ad7c"
        mock_conn.send_request.assert_not_called()

    def test_resolve_title_success(self):
        """Test title resolution succeeds."""
        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_TEMPLATE]))
        mock_module = MagicMock()
        result = {}

        resolved = _resolve_base_service_template_id(
            client=ItsiRequest(mock_conn, mock_module),
            template_ref="My Service Template",
            module=mock_module,
            result=result,
        )

        assert resolved == "12345678-1234-5678-90ab-cdef12345678"

    def test_resolve_title_not_found(self):
        """Test title resolution fails when not found."""
        mock_conn = make_mock_conn(200, json.dumps([]))
        mock_module = MagicMock()
        # Make fail_json raise an exception to stop execution
        mock_module.fail_json.side_effect = AnsibleFailJson
        result = {}

        with pytest.raises(AnsibleFailJson):
            _resolve_base_service_template_id(
                client=ItsiRequest(mock_conn, mock_module),
                template_ref="Nonexistent Template",
                module=mock_module,
                result=result,
            )

        mock_module.fail_json.assert_called_once()
        assert "not found" in mock_module.fail_json.call_args[1]["msg"].lower()

    def test_resolve_title_multiple_matches(self):
        """Test title resolution fails with multiple matches."""
        mock_conn = make_mock_conn(
            200,
            json.dumps(
                [
                    {"_key": "tmpl1", "title": "Duplicate Template"},
                    {"_key": "tmpl2", "title": "Duplicate Template"},
                ],
            ),
        )
        mock_module = MagicMock()
        # Make fail_json raise an exception to stop execution
        mock_module.fail_json.side_effect = AnsibleFailJson
        result = {}

        with pytest.raises(AnsibleFailJson):
            _resolve_base_service_template_id(
                client=ItsiRequest(mock_conn, mock_module),
                template_ref="Duplicate Template",
                module=mock_module,
                result=result,
            )

        mock_module.fail_json.assert_called_once()
        assert "multiple" in mock_module.fail_json.call_args[1]["msg"].lower()


class TestDiscoverCurrent:
    """Tests for _discover_current helper function."""

    def test_discover_by_key_found(self):
        """Test discover by key when service exists."""
        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_SERVICE))
        mock_module = MagicMock()

        doc = _discover_current(
            client=ItsiRequest(mock_conn, mock_module),
            key="a2961217-9728-4e9f-b67b-15bf4a40ad7c",
            name=None,
        )

        assert doc is not None
        assert doc["title"] == "api-gateway"

    def test_discover_by_key_not_found(self):
        """Test discover by key when service doesn't exist."""
        mock_conn = make_mock_conn(404, json.dumps({"error": "Not found"}))
        mock_module = MagicMock()

        doc = _discover_current(
            client=ItsiRequest(mock_conn, mock_module),
            key="nonexistent",
            name=None,
        )

        assert doc is None

    def test_discover_by_name_found(self):
        """Test discover by name when service exists."""
        mock_conn = MagicMock()
        # First call: find by title returns list
        # Second call: get by key returns full doc
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([SAMPLE_SERVICE])},
            {"status": 200, "body": json.dumps(SAMPLE_SERVICE_FULL)},
        ]
        mock_module = MagicMock()

        doc = _discover_current(
            client=ItsiRequest(mock_conn, mock_module),
            key=None,
            name="api-gateway",
        )

        assert doc is not None
        assert doc["title"] == "api-gateway"
        # Full document should have entity_rules
        assert "entity_rules" in doc

    def test_discover_by_name_not_found(self):
        """Test discover by name when service doesn't exist."""
        mock_conn = make_mock_conn(200, json.dumps([]))
        mock_module = MagicMock()

        doc = _discover_current(
            client=ItsiRequest(mock_conn, mock_module),
            key=None,
            name="nonexistent",
        )

        assert doc is None


class TestMain:
    """Tests for main module execution."""

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_no_socket_path(self, mock_module_class, mock_connection):
        """Test main fails without socket path."""
        mock_module = MagicMock()
        mock_module._socket_path = None
        mock_module.params = {}
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "httpapi" in mock_module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_create_new_service(self, mock_module_class, mock_connection):
        """Test main creates new service."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "new-service",
            "enabled": True,
            "description": "New service",
            "sec_grp": "default_itsi_security_group",
            "entity_rules": [],
            "service_tags": ["prod"],
            "base_service_template_id": None,
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        # First call: find by title (not found)
        # Second call: create
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([])},
            {"status": 200, "body": json.dumps({"_key": "new-uuid"})},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["after"]["_key"] == "new-uuid"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_create_check_mode(self, mock_module_class, mock_connection):
        """Test main create in check mode."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "new-service",
            "enabled": True,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["before"] == {}

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_update_existing_service(self, mock_module_class, mock_connection):
        """Test main updates existing service."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "api-gateway",
            "enabled": False,
            "description": "Updated description",
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            # Find by title
            {"status": 200, "body": json.dumps([SAMPLE_SERVICE])},
            # Get full doc by key
            {"status": 200, "body": json.dumps(SAMPLE_SERVICE_FULL)},
            # Update
            {"status": 200, "body": json.dumps({"_key": SAMPLE_SERVICE["_key"]})},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert "enabled" in call_kwargs["diff"]
        assert "description" in call_kwargs["diff"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_update_no_changes(self, mock_module_class, mock_connection):
        """Test main with no changes needed."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "api-gateway",
            "enabled": True,
            "description": "API Gateway Service",
            "sec_grp": "default_itsi_security_group",
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([SAMPLE_SERVICE])},
            {"status": 200, "body": json.dumps(SAMPLE_SERVICE_FULL)},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_update_check_mode(self, mock_module_class, mock_connection):
        """Test main update in check mode."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "api-gateway",
            "enabled": False,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([SAMPLE_SERVICE])},
            {"status": 200, "body": json.dumps(SAMPLE_SERVICE_FULL)},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert "enabled" in call_kwargs["diff"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_delete_existing_service(self, mock_module_class, mock_connection):
        """Test main deletes existing service."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "api-gateway",
            "enabled": None,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "absent",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([SAMPLE_SERVICE])},
            {"status": 200, "body": json.dumps(SAMPLE_SERVICE_FULL)},
            {"status": 200, "body": ""},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["before"]  # delete: before contains the deleted service

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_delete_nonexistent_service(self, mock_module_class, mock_connection):
        """Test main delete when service doesn't exist (no-op)."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "nonexistent",
            "enabled": None,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "absent",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_delete_check_mode(self, mock_module_class, mock_connection):
        """Test main delete in check mode."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "api-gateway",
            "enabled": None,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "absent",
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([SAMPLE_SERVICE])},
            {"status": 200, "body": json.dumps(SAMPLE_SERVICE_FULL)},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["after"] == {}

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_create_with_template_by_title(self, mock_module_class, mock_connection):
        """Test main create service with template specified by title."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "templated-service",
            "enabled": None,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": "My Service Template",
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            # Find by title (not found)
            {"status": 200, "body": json.dumps([])},
            # Resolve template by title
            {"status": 200, "body": json.dumps([SAMPLE_TEMPLATE])},
            # Create
            {"status": 200, "body": json.dumps({"_key": "new-uuid"})},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_create_with_template_by_uuid(self, mock_module_class, mock_connection):
        """Test main create service with template specified by UUID."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "templated-service",
            "enabled": None,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            # Use a valid UUID format (8-4-4-4-12 hex chars)
            "base_service_template_id": "12345678-1234-5678-90ab-cdef12345678",
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            # Find by title (not found)
            {"status": 200, "body": json.dumps([])},
            # Create (no template lookup needed for UUID)
            {"status": 200, "body": json.dumps({"_key": "new-uuid"})},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_get_by_service_id(self, mock_module_class, mock_connection):
        """Test main uses service_id when provided."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": "a2961217-9728-4e9f-b67b-15bf4a40ad7c",
            "name": None,
            "enabled": False,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            # Get by key
            {"status": 200, "body": json.dumps(SAMPLE_SERVICE_FULL)},
            # Update
            {"status": 200, "body": json.dumps({"_key": SAMPLE_SERVICE["_key"]})},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_create_http_error(self, mock_module_class, mock_connection):
        """Test main handles HTTP error on create."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "new-service",
            "enabled": True,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([])},
            {"status": 400, "body": json.dumps({"error": "Bad request"})},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "400" in mock_module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_update_http_error(self, mock_module_class, mock_connection):
        """Test main handles HTTP error on update."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "api-gateway",
            "enabled": False,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([SAMPLE_SERVICE])},
            {"status": 200, "body": json.dumps(SAMPLE_SERVICE_FULL)},
            {"status": 500, "body": json.dumps({"error": "Server error"})},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "500" in mock_module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_service_tags_update(self, mock_module_class, mock_connection):
        """Test main updates service_tags correctly."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "api-gateway",
            "enabled": None,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": ["new-tag", "another-tag"],
            "base_service_template_id": None,
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([SAMPLE_SERVICE])},
            {"status": 200, "body": json.dumps(SAMPLE_SERVICE_FULL)},
            {"status": 200, "body": json.dumps({"_key": SAMPLE_SERVICE["_key"]})},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert "service_tags" in call_kwargs["diff"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_entity_rules_update(self, mock_module_class, mock_connection):
        """Test main updates entity_rules correctly."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        new_rules = [
            {
                "rule_condition": "OR",
                "rule_items": [
                    {"field": "host", "field_type": "alias", "rule_type": "matches", "value": "db-*"},
                ],
            },
        ]
        mock_module.params = {
            "service_id": None,
            "name": "api-gateway",
            "enabled": None,
            "description": None,
            "sec_grp": None,
            "entity_rules": new_rules,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([SAMPLE_SERVICE])},
            {"status": 200, "body": json.dumps(SAMPLE_SERVICE_FULL)},
            {"status": 200, "body": json.dumps({"_key": SAMPLE_SERVICE["_key"]})},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert "entity_rules" in call_kwargs["diff"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service.AnsibleModule")
    def test_main_with_extra_fields(self, mock_module_class, mock_connection):
        """Test main handles extra fields correctly."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "name": "new-service",
            "enabled": True,
            "description": None,
            "sec_grp": None,
            "entity_rules": None,
            "service_tags": None,
            "base_service_template_id": None,
            "extra": {"custom_field": "custom_value", "priority": "high"},
            "state": "present",
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps([])},
            {"status": 200, "body": json.dumps({"_key": "new-uuid"})},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        # Verify extra fields were in the create payload
        # Module calls: conn.send_request(path, method=method, body=body)
        create_call = mock_conn.send_request.call_args_list[1]
        payload = json.loads(create_call.kwargs["body"])
        assert payload["custom_field"] == "custom_value"
        assert payload["priority"] == "high"
