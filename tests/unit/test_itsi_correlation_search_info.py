# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_correlation_search_info module."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from unittest.mock import MagicMock, patch

import pytest


# Exception classes to simulate Ansible module exit behavior
# Inherit from SystemExit so they're not caught by "except Exception"
class AnsibleExitJson(SystemExit):
    """Exception raised when module.exit_json() is called."""

    pass


class AnsibleFailJson(SystemExit):
    """Exception raised when module.fail_json() is called."""

    pass


# Import module functions for testing
# Note: Tests for shared itsi_utils functions (flatten_search_entry, flatten_search_object,
# normalize_to_list, parse_response_body, validate_api_response, handle_request_exception,
# process_api_response) are in test_itsi_correlation_search.py to avoid duplication.
from ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info import (
    _send_request,
    get_correlation_search,
    get_correlation_search_by_name,
    list_correlation_searches,
    main,
)

# Sample response payloads for testing
SAMPLE_ENTRY = {
    "name": "Test Search",
    "id": "test-search-id",
    "content": {
        "search": "index=main | head 1",
        "disabled": "0",
        "cron_schedule": "*/5 * * * *",
        "description": "Test description",
    },
    "links": {"edit": "/test/edit"},
    "acl": {"app": "SA-ITOA", "owner": "admin"},
}

SAMPLE_API_RESPONSE = {
    "entry": [SAMPLE_ENTRY],
    "paging": {"offset": 0, "total": 1},
}

SAMPLE_FLAT_RESPONSE = {
    "search": "index=main | head 1",
    "disabled": "0",
    "cron_schedule": "*/5 * * * *",
    "description": "Test description",
    "_meta": {
        "name": "Test Search",
        "id": "test-search-id",
        "links": {"edit": "/test/edit"},
        "acl": {"app": "SA-ITOA", "owner": "admin"},
    },
}


class TestSendRequest:
    """Tests for _send_request helper function."""

    def test_send_request_success_json_response(self):
        """Test successful request with JSON response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps({"name": "test"}),
            "headers": {"Content-Type": "application/json"},
        }

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 200
        assert data["name"] == "test"
        assert "_response_headers" in data

    def test_send_request_with_params(self):
        """Test request with query parameters."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        _send_request(mock_conn, "GET", "/test/path", params={"foo": "bar", "empty": ""})

        # Verify the path includes only non-empty params
        call_args = mock_conn.send_request.call_args
        assert "foo=bar" in call_args[0][0]
        assert "empty" not in call_args[0][0]

    def test_send_request_with_existing_query_string(self):
        """Test request with path that already has query string."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        _send_request(mock_conn, "GET", "/test/path?existing=param", params={"new": "value"})

        call_args = mock_conn.send_request.call_args
        assert "&new=value" in call_args[0][0]

    def test_send_request_list_response(self):
        """Test request with list response gets wrapped."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([{"name": "item1"}, {"name": "item2"}]),
            "headers": {},
        }

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 200
        assert "results" in data
        assert len(data["results"]) == 2

    def test_send_request_non_json_response(self):
        """Test request with non-JSON response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "plain text response",
            "headers": {},
        }

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 200
        assert data["raw_response"] == "plain text response"

    def test_send_request_empty_body(self):
        """Test request with empty body."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 204,
            "body": "",
            "headers": {},
        }

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 204
        assert "_response_headers" in data

    def test_send_request_invalid_response_format(self):
        """Test request with invalid response format."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = "invalid"

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 500
        assert "error" in data

    def test_send_request_missing_status(self):
        """Test request with missing status in response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {"body": "{}"}

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 500
        assert "error" in data

    def test_send_request_401_error(self):
        """Test request with 401 authentication error."""
        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = Exception("401 Unauthorized")

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 401
        assert "Authentication failed" in data["error"]

    def test_send_request_404_error(self):
        """Test request with 404 not found error."""
        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = Exception("404 Not Found")

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 404
        assert "not found" in data["error"].lower()

    def test_send_request_generic_exception(self):
        """Test request with generic exception."""
        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = Exception("Connection timeout")

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 500
        assert "Connection timeout" in data["error"]

    def test_send_request_method_uppercase(self):
        """Test that method is converted to uppercase."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        _send_request(mock_conn, "get", "/test/path")

        call_args = mock_conn.send_request.call_args
        assert call_args[1]["method"] == "GET"

    def test_send_request_scalar_json_response(self):
        """Test request with scalar JSON response (not dict or list)."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps("scalar string"),
            "headers": {},
        }

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 200
        assert data["raw_response"] == "scalar string"


class TestGetCorrelationSearch:
    """Tests for get_correlation_search function."""

    def test_get_by_id_success(self):
        """Test getting correlation search by ID successfully."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {"Content-Type": "application/json"},
        }

        status, data = get_correlation_search(mock_conn, "test-search-id")

        assert status == 200
        assert data["search"] == "index=main | head 1"
        assert "_meta" in data

    def test_get_by_id_with_fields(self):
        """Test getting correlation search with specific fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        get_correlation_search(mock_conn, "test-id", fields="name,disabled")

        call_args = mock_conn.send_request.call_args
        assert "fields=name%2Cdisabled" in call_args[0][0]

    def test_get_by_id_with_fields_list(self):
        """Test getting correlation search with fields as list."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        get_correlation_search(mock_conn, "test-id", fields=["name", "disabled"])

        call_args = mock_conn.send_request.call_args
        assert "fields=name%2Cdisabled" in call_args[0][0]

    def test_get_by_id_not_found(self):
        """Test getting non-existent correlation search."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 404,
            "body": json.dumps({"error": "Not found"}),
            "headers": {},
        }

        status, data = get_correlation_search(mock_conn, "nonexistent")

        assert status == 404

    def test_get_includes_response_headers(self):
        """Test that response headers are included in result."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {"X-Custom": "header"},
        }

        status, data = get_correlation_search(mock_conn, "test-id")

        assert "_response_headers" in data


class TestGetCorrelationSearchByName:
    """Tests for get_correlation_search_by_name function."""

    def test_get_by_name_success(self):
        """Test getting correlation search by name successfully."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        status, data = get_correlation_search_by_name(mock_conn, "Test Search")

        assert status == 200
        # Verify URL encoding uses %20 for spaces
        call_args = mock_conn.send_request.call_args
        assert "Test%20Search" in call_args[0][0]

    def test_get_by_name_with_fields(self):
        """Test getting by name with specific fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        get_correlation_search_by_name(mock_conn, "Test", fields="search,disabled")

        call_args = mock_conn.send_request.call_args
        assert "fields=search%2Cdisabled" in call_args[0][0]

    def test_get_by_name_with_fields_list(self):
        """Test getting by name with fields as list."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        get_correlation_search_by_name(mock_conn, "Test", fields=["search", "disabled"])

        call_args = mock_conn.send_request.call_args
        assert "fields=search%2Cdisabled" in call_args[0][0]

    def test_get_by_name_not_found(self):
        """Test getting non-existent search by name."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 404,
            "body": json.dumps({"error": "Not found"}),
            "headers": {},
        }

        status, data = get_correlation_search_by_name(mock_conn, "Nonexistent")

        assert status == 404


class TestListCorrelationSearches:
    """Tests for list_correlation_searches function."""

    def test_list_all_success(self):
        """Test listing all correlation searches successfully."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        status, data = list_correlation_searches(mock_conn)

        assert status == 200
        assert "correlation_searches" in data
        assert len(data["correlation_searches"]) == 1

    def test_list_with_fields(self):
        """Test listing with specific fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        list_correlation_searches(mock_conn, fields="name,search")

        call_args = mock_conn.send_request.call_args
        assert "fields=name%2Csearch" in call_args[0][0]

    def test_list_with_fields_as_tuple(self):
        """Test listing with fields as tuple."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        list_correlation_searches(mock_conn, fields=("name", "search"))

        call_args = mock_conn.send_request.call_args
        assert "fields=name%2Csearch" in call_args[0][0]

    def test_list_with_filter(self):
        """Test listing with filter."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        list_correlation_searches(mock_conn, filter_data='{"disabled": "0"}')

        call_args = mock_conn.send_request.call_args
        assert "filter_data" in call_args[0][0]

    def test_list_with_count(self):
        """Test listing with count limit."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        list_correlation_searches(mock_conn, count=10)

        call_args = mock_conn.send_request.call_args
        assert "count=10" in call_args[0][0]

    def test_list_error_response(self):
        """Test listing with error response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 500,
            "body": json.dumps({"error": "Server error"}),
            "headers": {},
        }

        status, data = list_correlation_searches(mock_conn)

        assert status == 500

    def test_list_with_results_list(self):
        """Test listing when response has results list."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(
                {
                    "results": [{"name": "Result1"}, {"name": "Result2"}],
                },
            ),
            "headers": {},
        }

        status, data = list_correlation_searches(mock_conn)

        assert status == 200
        assert len(data["correlation_searches"]) == 2


class TestMain:
    """Tests for main module execution."""

    def _set_module_args(self, args):
        """Set module arguments for testing."""
        if "_ansible_remote_tmp" not in args:
            args["_ansible_remote_tmp"] = "/tmp"
        if "_ansible_keep_remote_files" not in args:
            args["_ansible_keep_remote_files"] = False
        args_json = json.dumps({"ANSIBLE_MODULE_ARGS": args})
        return args_json

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.AnsibleModule")
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

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.AnsibleModule")
    def test_main_get_by_correlation_search_id(self, mock_module_class, mock_connection):
        """Test main getting search by correlation_search_id."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "correlation_search_id": "test-id",
            "name": None,
            "fields": None,
            "filter_data": None,
            "count": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["status"] == 200
        assert "correlation_search" in call_kwargs

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.AnsibleModule")
    def test_main_get_by_name(self, mock_module_class, mock_connection):
        """Test main getting search by name."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "correlation_search_id": None,
            "name": "Test Search",
            "fields": None,
            "filter_data": None,
            "count": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["status"] == 200

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.AnsibleModule")
    def test_main_list_all(self, mock_module_class, mock_connection):
        """Test main listing all searches."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "correlation_search_id": None,
            "name": None,
            "fields": None,
            "filter_data": None,
            "count": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert "correlation_searches" in call_kwargs

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.AnsibleModule")
    def test_main_search_not_found(self, mock_module_class, mock_connection):
        """Test main when search is not found."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "correlation_search_id": "nonexistent",
            "name": None,
            "fields": None,
            "filter_data": None,
            "count": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 404,
            "body": json.dumps({"error": "Not found"}),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["status"] == 404
        assert call_kwargs["correlation_search"] is None

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.AnsibleModule")
    def test_main_exception_handling(self, mock_module_class, mock_connection):
        """Test main handles exceptions properly."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "correlation_search_id": "test-id",
            "name": None,
            "fields": None,
            "filter_data": None,
            "count": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.side_effect = Exception("Connection failed")

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "Exception occurred" in mock_module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.AnsibleModule")
    def test_main_list_non_dict_response(self, mock_module_class, mock_connection):
        """Test main handles non-dict response when listing."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "correlation_search_id": None,
            "name": None,
            "fields": None,
            "filter_data": None,
            "count": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        # This triggers the non-dict data handling in main
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([{"name": "item1"}]),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.AnsibleModule")
    def test_main_with_fields_parameter(self, mock_module_class, mock_connection):
        """Test main passes fields parameter correctly."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "correlation_search_id": "test-id",
            "name": None,
            "fields": "name,search,disabled",
            "filter_data": None,
            "count": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.AnsibleModule")
    def test_main_list_with_filter_and_count(self, mock_module_class, mock_connection):
        """Test main listing with filter and count."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "correlation_search_id": None,
            "name": None,
            "fields": None,
            "filter_data": '{"disabled": "0"}',
            "count": 5,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info.AnsibleModule")
    def test_main_correlation_search_id_takes_precedence(self, mock_module_class, mock_connection):
        """Test that correlation_search_id takes precedence over name."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "correlation_search_id": "id-value",
            "name": "name-value",
            "fields": None,
            "filter_data": None,
            "count": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        # Verify the ID path was used, not the name path
        call_args = mock_conn.send_request.call_args
        assert "id-value" in call_args[0][0]
