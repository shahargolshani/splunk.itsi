# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_aggregation_policy_info module."""


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


# Import shared utilities from module_utils
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_utils import (
    flatten_policy_object,
    get_aggregation_policies_by_title,
    get_aggregation_policy_by_id,
    list_aggregation_policies,
    normalize_policy_list,
)

# Import module functions for testing
from ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info import (
    _list_all_policies,
    _normalize_response_data,
    _query_by_policy_id,
    _query_by_title,
    main,
)

# Sample response payloads for testing
SAMPLE_POLICY = {
    "_key": "test_policy_id",
    "title": "Test Policy",
    "description": "Test aggregation policy",
    "disabled": 0,
    "priority": 5,
    "group_severity": "medium",
}

SAMPLE_POLICY_2 = {
    "_key": "test_policy_id_2",
    "title": "Test Policy",  # Same title as SAMPLE_POLICY
    "description": "Second test policy",
    "disabled": 1,
    "priority": 3,
    "group_severity": "low",
}

SAMPLE_POLICY_3 = {
    "_key": "test_policy_id_3",
    "title": "Different Policy",
    "description": "Third test policy",
    "disabled": 0,
    "priority": 7,
    "group_severity": "high",
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


class TestNormalizePolicyList:
    """Tests for normalize_policy_list helper function."""

    def test_normalize_list_input(self):
        """Test normalizing list input returns as-is."""
        data = [{"_key": "policy1"}, {"_key": "policy2"}]
        result = normalize_policy_list(data)
        assert len(result) == 2

    def test_normalize_dict_with_entry(self):
        """Test normalizing dict with entry list."""
        data = {"entry": [{"_key": "policy1"}]}
        result = normalize_policy_list(data)
        assert len(result) == 1

    def test_normalize_dict_with_single_entry(self):
        """Test normalizing dict with single entry (not list)."""
        data = {"entry": {"_key": "policy1"}}
        result = normalize_policy_list(data)
        assert len(result) == 1

    def test_normalize_single_dict(self):
        """Test normalizing single dict without entry."""
        data = {"_key": "policy1"}
        result = normalize_policy_list(data)
        assert len(result) == 1

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

        status, data = get_aggregation_policy_by_id(ItsiRequest(mock_conn), "test_policy_id")

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

        get_aggregation_policy_by_id(ItsiRequest(mock_conn), "test_policy_id", fields="title,disabled")

        call_args = mock_conn.send_request.call_args
        assert "fields=title%2Cdisabled" in call_args[0][0]

    def test_get_by_id_not_found(self):
        """Test getting non-existent policy."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 404,
            "body": json.dumps({"error": "Not found"}),
            "headers": {},
        }

        status, data = get_aggregation_policy_by_id(ItsiRequest(mock_conn), "nonexistent")

        assert status == 404

    def test_get_by_id_url_encoding(self):
        """Test policy_id is URL encoded."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }

        get_aggregation_policy_by_id(ItsiRequest(mock_conn), "policy with spaces")

        call_args = mock_conn.send_request.call_args
        assert "policy+with+spaces" in call_args[0][0]


class TestListAggregationPolicies:
    """Tests for list_aggregation_policies function."""

    def test_list_basic(self):
        """Test basic listing."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY, SAMPLE_POLICY_2]),
            "headers": {},
        }

        status, data = list_aggregation_policies(ItsiRequest(mock_conn))

        assert status == 200
        assert "aggregation_policies" in data
        assert len(data["aggregation_policies"]) == 2

    def test_list_with_fields(self):
        """Test listing with specific fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }

        list_aggregation_policies(ItsiRequest(mock_conn), fields="_key,title")

        call_args = mock_conn.send_request.call_args
        assert "fields=_key%2Ctitle" in call_args[0][0]

    def test_list_with_filter_data(self):
        """Test listing with filter_data."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }

        list_aggregation_policies(ItsiRequest(mock_conn), filter_data='{"disabled": 0}')

        call_args = mock_conn.send_request.call_args
        assert "filter_data" in call_args[0][0]

    def test_list_with_limit(self):
        """Test listing with limit."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }

        list_aggregation_policies(ItsiRequest(mock_conn), limit=5)

        call_args = mock_conn.send_request.call_args
        assert "limit=5" in call_args[0][0]

    def test_list_empty_result(self):
        """Test listing with empty result."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([]),
            "headers": {},
        }

        status, data = list_aggregation_policies(ItsiRequest(mock_conn))

        assert status == 200
        assert data["aggregation_policies"] == []

    def test_list_error(self):
        """Test listing with error."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 500,
            "body": json.dumps({"error": "Server error"}),
            "headers": {},
        }

        status, data = list_aggregation_policies(ItsiRequest(mock_conn))

        assert status == 500


class TestGetAggregationPoliciesByTitle:
    """Tests for get_aggregation_policies_by_title function."""

    def test_get_by_title_single_match(self):
        """Test getting policy by title with single match."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY, SAMPLE_POLICY_3]),
            "headers": {},
        }

        status, data = get_aggregation_policies_by_title(ItsiRequest(mock_conn), "Test Policy")

        assert status == 200
        assert len(data["aggregation_policies"]) == 1
        assert data["aggregation_policies"][0]["_key"] == "test_policy_id"

    def test_get_by_title_multiple_matches(self):
        """Test getting policy by title with multiple matches."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY, SAMPLE_POLICY_2, SAMPLE_POLICY_3]),
            "headers": {},
        }

        status, data = get_aggregation_policies_by_title(ItsiRequest(mock_conn), "Test Policy")

        assert status == 200
        assert len(data["aggregation_policies"]) == 2  # Both SAMPLE_POLICY and SAMPLE_POLICY_2

    def test_get_by_title_no_match(self):
        """Test getting policy by title with no match."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }

        status, data = get_aggregation_policies_by_title(ItsiRequest(mock_conn), "Nonexistent Title")

        assert status == 200
        assert len(data["aggregation_policies"]) == 0

    def test_get_by_title_with_fields(self):
        """Test getting policy by title with fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }

        get_aggregation_policies_by_title(ItsiRequest(mock_conn), "Test Policy", fields="_key,title")

        call_args = mock_conn.send_request.call_args
        assert "fields=_key%2Ctitle" in call_args[0][0]

    def test_get_by_title_error(self):
        """Test getting policy by title with error."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 500,
            "body": json.dumps({"error": "Server error"}),
            "headers": {},
        }

        status, data = get_aggregation_policies_by_title(ItsiRequest(mock_conn), "Test Policy")

        assert status == 500

    def test_get_by_title_exact_match(self):
        """Test getting policy by title uses exact match."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(
                [
                    {"_key": "1", "title": "Test"},
                    {"_key": "2", "title": "Test Policy"},
                    {"_key": "3", "title": "Test Policy Extended"},
                ],
            ),
            "headers": {},
        }

        status, data = get_aggregation_policies_by_title(ItsiRequest(mock_conn), "Test Policy")

        assert status == 200
        assert len(data["aggregation_policies"]) == 1
        assert data["aggregation_policies"][0]["_key"] == "2"


class TestNormalizeResponseData:
    """Tests for _normalize_response_data helper function."""

    def test_normalize_dict_input(self):
        """Test normalizing dict input returns as-is."""
        data = {"aggregation_policies": [SAMPLE_POLICY], "_response_headers": {"X-Test": "value"}}
        result = _normalize_response_data(data)
        assert result == data

    def test_normalize_non_dict_returns_default(self):
        """Test normalizing non-dict returns default structure."""
        result = _normalize_response_data("string")
        assert result == {"aggregation_policies": [], "_response_headers": {}}

    def test_normalize_none_returns_default(self):
        """Test normalizing None returns default structure."""
        result = _normalize_response_data(None)
        assert result == {"aggregation_policies": [], "_response_headers": {}}

    def test_normalize_list_returns_default(self):
        """Test normalizing list returns default structure."""
        result = _normalize_response_data([SAMPLE_POLICY])
        assert result == {"aggregation_policies": [], "_response_headers": {}}

    def test_normalize_empty_dict(self):
        """Test normalizing empty dict returns it as-is."""
        result = _normalize_response_data({})
        assert result == {}


class TestQueryByPolicyId:
    """Tests for _query_by_policy_id helper function."""

    def test_query_success(self):
        """Test successful query by policy ID."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }

        result = _query_by_policy_id(ItsiRequest(mock_conn), "test_policy_id", None)

        assert result["status"] == 200
        assert result["aggregation_policy"]["_key"] == "test_policy_id"
        assert "headers" in result

    def test_query_not_found(self):
        """Test query when policy not found."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 404,
            "body": json.dumps({"error": "Not found"}),
            "headers": {},
        }

        result = _query_by_policy_id(ItsiRequest(mock_conn), "nonexistent", None)

        assert result["status"] == 404
        assert result["aggregation_policy"] is None

    def test_query_with_fields(self):
        """Test query with specific fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_POLICY),
            "headers": {},
        }

        _query_by_policy_id(ItsiRequest(mock_conn), "test_policy_id", "title,disabled")

        call_args = mock_conn.send_request.call_args
        assert "fields=title%2Cdisabled" in call_args[0][0]

    def test_query_non_dict_response(self):
        """Test query handles non-dict response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 500,
            "body": "error",
            "headers": {},
        }

        result = _query_by_policy_id(ItsiRequest(mock_conn), "test_policy_id", None)

        assert result["status"] == 500
        assert result["headers"] == {}


class TestQueryByTitle:
    """Tests for _query_by_title helper function."""

    def test_query_single_match(self):
        """Test query with single matching policy."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }

        result = _query_by_title(ItsiRequest(mock_conn), "Test Policy", None)

        assert result["status"] == 200
        assert len(result["aggregation_policies"]) == 1
        assert result["aggregation_policy"]["_key"] == "test_policy_id"
        assert "headers" in result

    def test_query_multiple_matches(self):
        """Test query with multiple matching policies."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY, SAMPLE_POLICY_2]),
            "headers": {},
        }

        result = _query_by_title(ItsiRequest(mock_conn), "Test Policy", None)

        assert result["status"] == 200
        assert len(result["aggregation_policies"]) == 2
        assert result["aggregation_policy"] is None  # Multiple matches = None

    def test_query_no_match(self):
        """Test query with no matching policies."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY_3]),  # Different title
            "headers": {},
        }

        result = _query_by_title(ItsiRequest(mock_conn), "Test Policy", None)

        assert result["status"] == 200
        assert len(result["aggregation_policies"]) == 0
        assert result["aggregation_policy"] is None

    def test_query_with_fields(self):
        """Test query with specific fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }

        _query_by_title(ItsiRequest(mock_conn), "Test Policy", "_key,title")

        call_args = mock_conn.send_request.call_args
        assert "fields=_key%2Ctitle" in call_args[0][0]

    def test_query_non_dict_response(self):
        """Test query handles non-dict response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 500,
            "body": "error",
            "headers": {},
        }

        result = _query_by_title(ItsiRequest(mock_conn), "Test Policy", None)

        assert result["status"] == 500
        assert result["aggregation_policies"] == []


class TestListAllPolicies:
    """Tests for _list_all_policies helper function."""

    def test_list_basic(self):
        """Test basic listing."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY, SAMPLE_POLICY_2]),
            "headers": {},
        }

        result = _list_all_policies(ItsiRequest(mock_conn), None, None, None)

        assert result["status"] == 200
        assert len(result["aggregation_policies"]) == 2
        assert "headers" in result

    def test_list_with_fields(self):
        """Test listing with specific fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }

        _list_all_policies(ItsiRequest(mock_conn), "_key,title", None, None)

        call_args = mock_conn.send_request.call_args
        assert "fields=_key%2Ctitle" in call_args[0][0]

    def test_list_with_filter_data(self):
        """Test listing with filter_data."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }

        _list_all_policies(ItsiRequest(mock_conn), None, '{"disabled": 0}', None)

        call_args = mock_conn.send_request.call_args
        assert "filter_data" in call_args[0][0]

    def test_list_with_limit(self):
        """Test listing with limit."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }

        _list_all_policies(ItsiRequest(mock_conn), None, None, 5)

        call_args = mock_conn.send_request.call_args
        assert "limit=5" in call_args[0][0]

    def test_list_empty_result(self):
        """Test listing with empty result."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([]),
            "headers": {},
        }

        result = _list_all_policies(ItsiRequest(mock_conn), None, None, None)

        assert result["status"] == 200
        assert result["aggregation_policies"] == []

    def test_list_non_dict_response(self):
        """Test listing handles non-dict response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 500,
            "body": "error",
            "headers": {},
        }

        result = _list_all_policies(ItsiRequest(mock_conn), None, None, None)

        assert result["status"] == 500
        assert result["aggregation_policies"] == []


class TestMain:
    """Tests for main module execution."""

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_query_by_policy_id(self, mock_module_class, mock_connection):
        """Test main query by policy_id."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": "test_policy_id",
            "title": None,
            "fields": None,
            "filter_data": None,
            "limit": None,
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
        assert call_kwargs["changed"] is False
        assert call_kwargs["status"] == 200
        assert call_kwargs["aggregation_policy"]["_key"] == "test_policy_id"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_query_by_policy_id_not_found(self, mock_module_class, mock_connection):
        """Test main query by policy_id when not found."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": "nonexistent",
            "title": None,
            "fields": None,
            "filter_data": None,
            "limit": None,
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
        assert call_kwargs["aggregation_policy"] is None

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_query_by_title(self, mock_module_class, mock_connection):
        """Test main query by title."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": None,
            "title": "Test Policy",
            "fields": None,
            "filter_data": None,
            "limit": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False
        assert len(call_kwargs["aggregation_policies"]) == 1
        # Single match also sets aggregation_policy
        assert call_kwargs["aggregation_policy"]["_key"] == "test_policy_id"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_query_by_title_multiple_matches(self, mock_module_class, mock_connection):
        """Test main query by title with multiple matches."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": None,
            "title": "Test Policy",
            "fields": None,
            "filter_data": None,
            "limit": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY, SAMPLE_POLICY_2]),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert len(call_kwargs["aggregation_policies"]) == 2
        # Multiple matches don't set aggregation_policy
        assert "aggregation_policy" not in call_kwargs or call_kwargs.get("aggregation_policy") is None

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_query_by_title_no_match(self, mock_module_class, mock_connection):
        """Test main query by title with no match."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": None,
            "title": "Nonexistent",
            "fields": None,
            "filter_data": None,
            "limit": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert len(call_kwargs["aggregation_policies"]) == 0
        assert call_kwargs["aggregation_policy"] is None

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_list_all(self, mock_module_class, mock_connection):
        """Test main list all policies."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": None,
            "title": None,
            "fields": None,
            "filter_data": None,
            "limit": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY, SAMPLE_POLICY_2, SAMPLE_POLICY_3]),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False
        assert len(call_kwargs["aggregation_policies"]) == 3

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_list_with_filter_data(self, mock_module_class, mock_connection):
        """Test main list with filter_data."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": None,
            "title": None,
            "fields": None,
            "filter_data": '{"disabled": 0}',
            "limit": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_args = mock_conn.send_request.call_args
        assert "filter_data" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_list_with_limit(self, mock_module_class, mock_connection):
        """Test main list with limit."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": None,
            "title": None,
            "fields": None,
            "filter_data": None,
            "limit": 5,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_args = mock_conn.send_request.call_args
        assert "limit=5" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_list_with_fields(self, mock_module_class, mock_connection):
        """Test main list with fields."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": None,
            "title": None,
            "fields": "_key,title,disabled",
            "filter_data": None,
            "limit": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_POLICY]),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_args = mock_conn.send_request.call_args
        assert "fields=_key%2Ctitle%2Cdisabled" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_exception_handling(self, mock_module_class, mock_connection):
        """Test main handles exceptions properly."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": "test",
            "title": None,
            "fields": None,
            "filter_data": None,
            "limit": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.side_effect = Exception("Connection failed")

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "Exception occurred" in mock_module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_check_mode_supported(self, mock_module_class, mock_connection):
        """Test main supports check mode."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": "test_policy_id",
            "title": None,
            "fields": None,
            "filter_data": None,
            "limit": None,
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

        # Check mode should still work (read-only module)
        mock_module.exit_json.assert_called_once()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_always_returns_changed_false(self, mock_module_class, mock_connection):
        """Test main always returns changed=False (read-only module)."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": "test_policy_id",
            "title": None,
            "fields": None,
            "filter_data": None,
            "limit": None,
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

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_query_by_title_non_dict_response(self, mock_module_class, mock_connection):
        """Test main query by title handles non-dict response."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": None,
            "title": "Test Policy",
            "fields": None,
            "filter_data": None,
            "limit": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        # Return non-dict (which becomes an error response)
        mock_conn.send_request.return_value = {
            "status": 500,
            "body": "invalid",
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        # Should handle gracefully
        mock_module.exit_json.assert_called_once()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_aggregation_policy_info.AnsibleModule")
    def test_main_list_all_non_dict_response(self, mock_module_class, mock_connection):
        """Test main list all handles non-dict response."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "policy_id": None,
            "title": None,
            "fields": None,
            "filter_data": None,
            "limit": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        # Return error response
        mock_conn.send_request.return_value = {
            "status": 500,
            "body": "error",
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        # Should handle gracefully with empty list
        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["aggregation_policies"] == []
