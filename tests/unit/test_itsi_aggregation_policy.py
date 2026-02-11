# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2025 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_aggregation_policy module."""


import json
from unittest.mock import MagicMock, patch

import pytest


# Exception classes to simulate Ansible module exit behavior
class AnsibleExitJson(SystemExit):
    """Exception raised when module.exit_json() is called."""

    pass


class AnsibleFailJson(SystemExit):
    """Exception raised when module.fail_json() is called."""

    pass


from ansible_collections.splunk.itsi.plugins.module_utils.aggregation_policy_utils import (
    flatten_policy_object,
    get_aggregation_policy_by_id,
    normalize_policy_list,
)

# Import shared utilities from module_utils
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

# Import module functions for testing
from ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy import (
    _canonicalize_policy,
    _diff_canonical,
    create_aggregation_policy,
    delete_aggregation_policy,
    main,
    update_aggregation_policy,
)

# Sample response payloads for testing
SAMPLE_POLICY = {
    "_key": "test_policy_id",
    "title": "Test Policy",
    "description": "Test aggregation policy",
    "disabled": 0,
    "priority": 5,
    "group_severity": "medium",
    "group_status": "new",
    "group_title": "%title%",
    "group_description": "%description%",
    "filter_criteria": {"condition": "AND", "items": []},
    "breaking_criteria": {"condition": "AND", "items": []},
    "rules": [],
}

SAMPLE_API_RESPONSE = {
    "entry": [SAMPLE_POLICY],
}

SAMPLE_POLICY_WITH_CONTENT = {
    "name": "test_policy_id",
    "content": {
        "title": "Test Policy",
        "description": "Test aggregation policy",
        "disabled": 0,
    },
    "links": {},
    "acl": {},
}


def _mock_module():
    """Create a MagicMock AnsibleModule for ItsiRequest."""
    module = MagicMock()
    module.fail_json.side_effect = AnsibleFailJson
    return module


class TestNormalizePolicyList:
    """Tests for normalize_policy_list helper function."""

    def test_normalize_list_input(self):
        """Test normalizing list input returns as-is."""
        data = [{"_key": "policy1"}, {"_key": "policy2"}]
        result = normalize_policy_list(data)
        assert len(result) == 2
        assert result == data

    def test_normalize_dict_with_entry(self):
        """Test normalizing dict with entry list."""
        data = {"entry": [{"_key": "policy1"}]}
        result = normalize_policy_list(data)
        assert len(result) == 1
        assert result[0]["_key"] == "policy1"

    def test_normalize_dict_with_single_entry(self):
        """Test normalizing dict with single entry (not list)."""
        data = {"entry": {"_key": "policy1"}}
        result = normalize_policy_list(data)
        assert len(result) == 1
        assert result[0]["_key"] == "policy1"

    def test_normalize_single_dict(self):
        """Test normalizing single dict without entry."""
        data = {"_key": "policy1", "title": "Test"}
        result = normalize_policy_list(data)
        assert len(result) == 1
        assert result[0]["_key"] == "policy1"

    def test_normalize_empty_list(self):
        """Test normalizing empty list."""
        result = normalize_policy_list([])
        assert result == []

    def test_normalize_non_dict_non_list(self):
        """Test normalizing non-dict non-list returns empty."""
        result = normalize_policy_list("string")
        assert result == []

    def test_normalize_none(self):
        """Test normalizing None returns empty."""
        result = normalize_policy_list(None)
        assert result == []

    def test_normalize_empty_entry_list(self):
        """Test normalizing dict with empty entry list."""
        data = {"entry": []}
        result = normalize_policy_list(data)
        assert result == []


class TestFlattenPolicyObject:
    """Tests for flatten_policy_object helper function."""

    def test_flatten_with_content(self):
        """Test flattening object with content dict."""
        result = flatten_policy_object(SAMPLE_POLICY_WITH_CONTENT)
        assert result["title"] == "Test Policy"
        assert result["name"] == "test_policy_id"

    def test_flatten_with_entry(self):
        """Test flattening object with entry key."""
        obj = {"entry": {"title": "Test", "_key": "test123"}}
        result = flatten_policy_object(obj)
        assert result["title"] == "Test"

    def test_flatten_already_flat(self):
        """Test flattening already flat dict."""
        result = flatten_policy_object(SAMPLE_POLICY)
        assert result == SAMPLE_POLICY

    def test_flatten_non_dict(self):
        """Test flattening non-dict returns as-is."""
        result = flatten_policy_object("string value")
        assert result == "string value"

    def test_flatten_none(self):
        """Test flattening None returns None."""
        result = flatten_policy_object(None)
        assert result is None


class TestCanonicalizePolicy:
    """Tests for _canonicalize_policy helper function."""

    def test_canonicalize_basic_fields(self):
        """Test canonicalizing basic fields."""
        payload = {
            "title": "Test Policy",
            "description": "Test description",
            "priority": 5,
            "group_severity": "high",
        }
        result = _canonicalize_policy(payload)
        assert result["title"] == "Test Policy"
        assert result["description"] == "Test description"
        assert result["priority"] == 5
        assert result["group_severity"] == "high"

    def test_canonicalize_all_supported_fields(self):
        """Test canonicalizing all supported fields."""
        payload = {
            "title": "Test",
            "description": "Desc",
            "priority": 1,
            "split_by_field": "host",
            "group_severity": "medium",
            "group_status": "new",
            "group_assignee": "admin",
            "group_title": "%title%",
            "group_description": "%description%",
        }
        result = _canonicalize_policy(payload)
        assert len(result) == 9

    def test_canonicalize_complex_fields(self):
        """Test canonicalizing complex fields."""
        payload = {
            "filter_criteria": {"condition": "AND", "items": [{"field": "test"}]},
            "breaking_criteria": {"condition": "OR", "items": []},
            "rules": [{"name": "rule1"}],
        }
        result = _canonicalize_policy(payload)
        assert result["filter_criteria"]["condition"] == "AND"
        assert result["breaking_criteria"]["condition"] == "OR"
        assert len(result["rules"]) == 1

    def test_canonicalize_disabled_bool_true(self):
        """Test canonicalizing disabled=True."""
        payload = {"disabled": True}
        result = _canonicalize_policy(payload)
        assert result["disabled"] == 1

    def test_canonicalize_disabled_bool_false(self):
        """Test canonicalizing disabled=False."""
        payload = {"disabled": False}
        result = _canonicalize_policy(payload)
        assert result["disabled"] == 0

    def test_canonicalize_disabled_string_one(self):
        """Test canonicalizing disabled='1'."""
        payload = {"disabled": "1"}
        result = _canonicalize_policy(payload)
        assert result["disabled"] == 1

    def test_canonicalize_disabled_string_zero(self):
        """Test canonicalizing disabled='0'."""
        payload = {"disabled": "0"}
        result = _canonicalize_policy(payload)
        assert result["disabled"] == 0

    def test_canonicalize_disabled_string_true(self):
        """Test canonicalizing disabled='true'."""
        payload = {"disabled": "true"}
        result = _canonicalize_policy(payload)
        assert result["disabled"] == 1

    def test_canonicalize_disabled_string_false(self):
        """Test canonicalizing disabled='false'."""
        payload = {"disabled": "false"}
        result = _canonicalize_policy(payload)
        assert result["disabled"] == 0

    def test_canonicalize_non_dict(self):
        """Test canonicalizing non-dict returns empty dict."""
        result = _canonicalize_policy("not a dict")
        assert result == {}

    def test_canonicalize_none(self):
        """Test canonicalizing None returns empty dict."""
        result = _canonicalize_policy(None)
        assert result == {}

    def test_canonicalize_with_entry_format(self):
        """Test canonicalizing Splunk entry format."""
        result = _canonicalize_policy(SAMPLE_POLICY_WITH_CONTENT)
        assert result["title"] == "Test Policy"
        assert result["disabled"] == 0

    def test_canonicalize_ignores_unknown_fields(self):
        """Test canonicalizing ignores unknown fields."""
        payload = {"title": "Test", "unknown_field": "value"}
        result = _canonicalize_policy(payload)
        assert "title" in result
        assert "unknown_field" not in result


class TestDiffCanonical:
    """Tests for _diff_canonical helper function."""

    def test_diff_no_changes(self):
        """Test diff with no changes."""
        desired = {"title": "Test", "disabled": 0}
        current = {"title": "Test", "disabled": 0}
        result = _diff_canonical(desired, current)
        assert result == {}

    def test_diff_with_changes(self):
        """Test diff with changes."""
        desired = {"title": "New Title", "disabled": 1}
        current = {"title": "Old Title", "disabled": 0}
        result = _diff_canonical(desired, current)
        assert "title" in result
        assert result["title"] == ("Old Title", "New Title")
        assert result["disabled"] == (0, 1)

    def test_diff_only_compares_desired_keys(self):
        """Test that diff only compares keys in desired."""
        desired = {"title": "Test"}
        current = {"title": "Test", "disabled": 0, "extra": "value"}
        result = _diff_canonical(desired, current)
        assert result == {}

    def test_diff_complex_fields_json_comparison(self):
        """Test diff uses JSON comparison for complex fields."""
        desired = {"filter_criteria": {"condition": "AND", "items": []}}
        current = {"filter_criteria": {"condition": "OR", "items": []}}
        result = _diff_canonical(desired, current)
        assert "filter_criteria" in result

    def test_diff_complex_fields_no_change(self):
        """Test diff complex fields when no change."""
        desired = {"filter_criteria": {"condition": "AND", "items": []}}
        current = {"filter_criteria": {"condition": "AND", "items": []}}
        result = _diff_canonical(desired, current)
        assert result == {}

    def test_diff_string_conversion(self):
        """Test that values are compared as strings."""
        desired = {"disabled": 1}
        current = {"disabled": "1"}
        result = _diff_canonical(desired, current)
        assert result == {}

    def test_diff_rules_field(self):
        """Test diff for rules field."""
        desired = {"rules": [{"name": "rule1"}]}
        current = {"rules": [{"name": "rule2"}]}
        result = _diff_canonical(desired, current)
        assert "rules" in result


class TestGetAggregationPolicyById:
    """Tests for get_aggregation_policy_by_id function."""

    def test_get_by_id_success(self):
        """Test getting policy by ID."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }

        status, headers, data = get_aggregation_policy_by_id(
            ItsiRequest(mock_conn, _mock_module()),
            "test_policy_id",
        )

        assert status == 200
        assert data["title"] == "Test Policy"

    def test_get_by_id_with_fields(self):
        """Test getting policy with specific fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }

        get_aggregation_policy_by_id(
            ItsiRequest(mock_conn, _mock_module()),
            "test_policy_id",
            fields="title,disabled",
        )

        call_args = mock_conn.send_request.call_args
        assert "fields=title%2Cdisabled" in call_args[0][0]

    def test_get_by_id_not_found(self):
        """Test getting non-existent policy returns None."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 404,
            "body": json.dumps({"error": "Not found"}),
            "headers": {},
        }

        result = get_aggregation_policy_by_id(
            ItsiRequest(mock_conn, _mock_module()),
            "nonexistent",
        )

        assert result is None

    def test_get_by_id_url_encoding(self):
        """Test policy_id is URL encoded."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }

        get_aggregation_policy_by_id(
            ItsiRequest(mock_conn, _mock_module()),
            "policy with spaces",
        )

        call_args = mock_conn.send_request.call_args
        assert "policy+with+spaces" in call_args[0][0]


class TestCreateAggregationPolicy:
    """Tests for create_aggregation_policy function."""

    def test_create_basic(self):
        """Test basic policy creation."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }

        policy_data = {"title": "New Policy"}
        status, headers, data = create_aggregation_policy(
            ItsiRequest(mock_conn, _mock_module()),
            policy_data,
        )

        assert status == 200
        call_args = mock_conn.send_request.call_args
        assert call_args[1]["method"] == "POST"

    def test_create_with_defaults(self):
        """Test creation applies default values."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        create_aggregation_policy(ItsiRequest(mock_conn, _mock_module()), {"title": "Test"})

        call_args = mock_conn.send_request.call_args
        payload = json.loads(call_args[1]["body"])
        assert payload["title"] == "Test"
        assert "filter_criteria" in payload
        assert "breaking_criteria" in payload
        assert "rules" in payload

    def test_create_with_all_fields(self):
        """Test creation with all fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        policy_data = {
            "title": "Complete Policy",
            "description": "Full description",
            "disabled": 0,
            "priority": 8,
            "filter_criteria": {"condition": "OR", "items": []},
        }
        create_aggregation_policy(ItsiRequest(mock_conn, _mock_module()), policy_data)

        call_args = mock_conn.send_request.call_args
        payload = json.loads(call_args[1]["body"])
        assert payload["title"] == "Complete Policy"
        assert payload["priority"] == 8
        assert payload["filter_criteria"]["condition"] == "OR"


class TestUpdateAggregationPolicy:
    """Tests for update_aggregation_policy function."""

    def test_update_basic(self):
        """Test basic update."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }

        update_data = {"disabled": 1}
        status, headers, data = update_aggregation_policy(
            ItsiRequest(mock_conn, _mock_module()),
            "test_policy_id",
            update_data,
            SAMPLE_POLICY,
        )

        assert status == 200

    def test_update_uses_partial_data(self):
        """Test update uses is_partial_data parameter."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        update_aggregation_policy(
            ItsiRequest(mock_conn, _mock_module()),
            "test_policy_id",
            {"disabled": 0},
            SAMPLE_POLICY,
        )

        call_args = mock_conn.send_request.call_args
        assert "is_partial_data=1" in call_args[0][0]

    def test_update_merges_with_current(self):
        """Test update merges with current values."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        update_aggregation_policy(
            ItsiRequest(mock_conn, _mock_module()),
            "test_policy_id",
            {"description": "New desc"},
            SAMPLE_POLICY,
        )

        call_args = mock_conn.send_request.call_args
        payload = json.loads(call_args[1]["body"])
        assert payload["title"] == "Test Policy"  # From current
        assert payload["description"] == "New desc"  # Updated

    def test_update_not_found(self):
        """Test update when policy not found (POST returns 404)."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 404,
            "body": json.dumps({"error": "Not found"}),
            "headers": {},
        }

        result = update_aggregation_policy(
            ItsiRequest(mock_conn, _mock_module()),
            "nonexistent",
            {"disabled": 1},
            {},
        )

        assert result is None


class TestDeleteAggregationPolicy:
    """Tests for delete_aggregation_policy function."""

    def test_delete_basic(self):
        """Test basic deletion."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 204,
            "body": "",
            "headers": {},
        }

        status, headers, data = delete_aggregation_policy(
            ItsiRequest(mock_conn, _mock_module()),
            "test_policy_id",
        )

        assert status == 204
        call_args = mock_conn.send_request.call_args
        assert call_args[1]["method"] == "DELETE"

    def test_delete_url_encoding(self):
        """Test policy_id is URL encoded."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 204,
            "body": "",
            "headers": {},
        }

        delete_aggregation_policy(
            ItsiRequest(mock_conn, _mock_module()),
            "policy with spaces",
        )

        call_args = mock_conn.send_request.call_args
        assert "policy+with+spaces" in call_args[0][0]


class TestMain:
    """Tests for main module execution."""

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_present_create(self, mock_module_class, mock_connection):
        """Test main creates new policy without policy_id."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": "New Policy",
            "policy_id": None,
            "state": "present",
            "description": "Test description",
            "disabled": False,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": "medium",
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": 5,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert "aggregation_policies" in call_kwargs
        assert isinstance(call_kwargs["aggregation_policies"], list)
        assert len(call_kwargs["aggregation_policies"]) == 1

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_present_update(self, mock_module_class, mock_connection):
        """Test main updates existing policy with policy_id."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": None,
            "policy_id": "existing_policy",
            "state": "present",
            "description": "Updated description",
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps(SAMPLE_POLICY), "headers": {}},
            {"status": 200, "body": json.dumps(SAMPLE_POLICY), "headers": {}},
            {"status": 200, "body": json.dumps(SAMPLE_POLICY), "headers": {}},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert "diff" in call_kwargs

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_present_no_title_no_policy_id_fails(self, mock_module_class, mock_connection):
        """Test main fails when no title and no policy_id for present state."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": None,
            "policy_id": None,
            "state": "present",
            "description": None,
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "title" in mock_module.fail_json.call_args[1]["msg"].lower()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_absent_delete_existing(self, mock_module_class, mock_connection):
        """Test main deletes existing policy."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": None,
            "policy_id": "existing_policy",
            "state": "absent",
            "description": None,
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps(SAMPLE_POLICY), "headers": {}},
            {"status": 204, "body": "", "headers": {}},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_absent_already_absent(self, mock_module_class, mock_connection):
        """Test main handles already absent policy."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": None,
            "policy_id": "nonexistent",
            "state": "absent",
            "description": None,
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 404,
            "body": "{}",
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False
        assert "msg" in call_kwargs

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_absent_no_policy_id_fails(self, mock_module_class, mock_connection):
        """Test main fails when no policy_id for absent state."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": "Some Title",
            "policy_id": None,
            "state": "absent",
            "description": None,
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "policy_id" in mock_module.fail_json.call_args[1]["msg"].lower()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_check_mode_create(self, mock_module_class, mock_connection):
        """Test main check mode for create operation."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": "New Policy",
            "policy_id": None,
            "state": "present",
            "description": "Test",
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["operation"] == "create"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_check_mode_update(self, mock_module_class, mock_connection):
        """Test main check mode for update operation."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": None,
            "policy_id": "existing_policy",
            "state": "present",
            "description": "Updated",
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["operation"] == "update"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_check_mode_delete(self, mock_module_class, mock_connection):
        """Test main check mode for delete operation."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": None,
            "policy_id": "existing_policy",
            "state": "absent",
            "description": None,
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["check_mode"] is True

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_exception_handling(self, mock_module_class, mock_connection):
        """Test main handles exceptions properly."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": "Test",
            "policy_id": None,
            "state": "present",
            "description": None,
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            main()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_with_additional_fields(self, mock_module_class, mock_connection):
        """Test main with additional_fields parameter."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": "New Policy",
            "policy_id": None,
            "state": "present",
            "description": None,
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {"custom_field": "custom_value"},
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        body = call_kwargs["body"]
        assert isinstance(body, dict)
        assert body["custom_field"] == "custom_value"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_check_mode_policy_not_found_treats_as_create(self, mock_module_class, mock_connection):
        """Test main check mode treats not-found policy_id as create."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": None,
            "policy_id": "nonexistent",
            "state": "present",
            "description": "Test",
            "disabled": None,
            "filter_criteria": None,
            "breaking_criteria": None,
            "group_severity": None,
            "group_status": None,
            "group_assignee": None,
            "group_title": None,
            "group_description": None,
            "split_by_field": None,
            "priority": None,
            "rules": None,
            "additional_fields": {},
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 404,
            "body": "{}",
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["operation"] == "create"
        assert call_kwargs["check_mode"] is True

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy.AnsibleModule")
    def test_main_with_all_optional_fields(self, mock_module_class, mock_connection):
        """Test main present state with all optional fields."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "title": "Complete Policy",
            "policy_id": None,
            "state": "present",
            "description": "Full description",
            "disabled": True,
            "filter_criteria": {"condition": "AND", "items": []},
            "breaking_criteria": {"condition": "OR", "items": []},
            "group_severity": "high",
            "group_status": "new",
            "group_assignee": "admin",
            "group_title": "%title%",
            "group_description": "%description%",
            "split_by_field": "host",
            "priority": 10,
            "rules": [{"name": "rule1"}],
            "additional_fields": {"extra": "value"},
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        body = call_kwargs["body"]
        assert isinstance(body, dict)
        assert body["title"] == "Complete Policy"
        assert body["disabled"] is True
        assert body["group_severity"] == "high"
        assert body["priority"] == 10
        assert body["extra"] == "value"
