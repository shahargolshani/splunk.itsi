# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_correlation_search_info module."""


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
# Note: Tests for shared correlation_search_utils functions (flatten_search_entry, flatten_search_object,
# normalize_to_list) are in test_itsi_correlation_search.py to avoid duplication.
# Tests for ItsiRequest (request, response parsing, error handling) are in test_itsi_request.py.
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest


def _mock_module():
    """Create a MagicMock AnsibleModule for ItsiRequest."""
    module = MagicMock()
    module.fail_json.side_effect = AnsibleFailJson
    return module


from ansible_collections.splunk.itsi.plugins.module_utils.correlation_search_utils import (
    get_correlation_search,
    list_correlation_searches,
)
from ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search_info import (
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

        status, headers, data = get_correlation_search(ItsiRequest(mock_conn, _mock_module()), "test-search-id")

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

        get_correlation_search(ItsiRequest(mock_conn, _mock_module()), "test-id", fields="name,disabled")

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

        get_correlation_search(ItsiRequest(mock_conn, _mock_module()), "test-id", fields=["name", "disabled"])

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

        result = get_correlation_search(ItsiRequest(mock_conn, _mock_module()), "nonexistent")

        assert result is None

    def test_get_returns_headers_separately(self):
        """Test that response headers are returned as separate tuple element."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {"X-Custom": "header"},
        }

        status, headers, data = get_correlation_search(
            ItsiRequest(mock_conn, _mock_module()),
            "test-id",
        )

        assert status == 200
        assert headers.get("X-Custom") == "header"


class TestGetCorrelationSearchByName:
    """Tests for get_correlation_search with use_name_encoding=True (by-name lookup)."""

    def test_get_by_name_success(self):
        """Test getting correlation search by name successfully."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        status, headers, data = get_correlation_search(
            ItsiRequest(mock_conn, _mock_module()),
            "Test Search",
            use_name_encoding=True,
        )

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

        get_correlation_search(ItsiRequest(mock_conn, _mock_module()), "Test", fields="search,disabled", use_name_encoding=True)

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

        get_correlation_search(ItsiRequest(mock_conn, _mock_module()), "Test", fields=["search", "disabled"], use_name_encoding=True)

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

        result = get_correlation_search(
            ItsiRequest(mock_conn, _mock_module()),
            "Nonexistent",
            use_name_encoding=True,
        )

        assert result is None


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

        status, headers, data = list_correlation_searches(ItsiRequest(mock_conn, _mock_module()))

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

        list_correlation_searches(ItsiRequest(mock_conn, _mock_module()), fields="name,search")

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

        list_correlation_searches(ItsiRequest(mock_conn, _mock_module()), fields=("name", "search"))

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

        list_correlation_searches(ItsiRequest(mock_conn, _mock_module()), filter_data='{"disabled": "0"}')

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

        list_correlation_searches(ItsiRequest(mock_conn, _mock_module()), count=10)

        call_args = mock_conn.send_request.call_args
        assert "count=10" in call_args[0][0]

    def test_list_error_response(self):
        """Test listing with error response (500 triggers fail_json)."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 500,
            "body": json.dumps({"error": "Server error"}),
            "headers": {},
        }

        with pytest.raises(AnsibleFailJson):
            list_correlation_searches(ItsiRequest(mock_conn, _mock_module()))

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

        status, headers, data = list_correlation_searches(ItsiRequest(mock_conn, _mock_module()))

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

        with pytest.raises(Exception):
            main()

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
