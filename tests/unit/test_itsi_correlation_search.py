# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_correlation_search module."""

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
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_utils import (
    _flatten_search_entry,
    flatten_search_object,
    handle_request_exception,
    normalize_to_list,
    parse_response_body,
    process_api_response,
    validate_api_response,
)
from ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search import (
    _canonicalize,
    _diff_canonical,
    _send_request,
    create_correlation_search,
    delete_correlation_search,
    ensure_present,
    get_correlation_search,
    main,
    update_correlation_search,
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
        "dispatch.earliest_time": "-15m",
        "dispatch.latest_time": "now",
        "is_scheduled": "1",
        "actions": "itsi_event_generator",
    },
    "links": {"edit": "/test/edit"},
    "acl": {"app": "SA-ITOA", "owner": "admin"},
}

SAMPLE_API_RESPONSE = {
    "entry": [SAMPLE_ENTRY],
    "paging": {"offset": 0, "total": 1},
}


class TestFlattenSearchEntry:
    """Tests for _flatten_search_entry helper function."""

    def test_flatten_entry_with_content(self):
        """Test flattening an entry with content dict."""
        result = _flatten_search_entry(SAMPLE_ENTRY)
        assert result["search"] == "index=main | head 1"
        assert result["disabled"] == "0"
        assert result["_meta"]["name"] == "Test Search"

    def test_flatten_entry_empty_content(self):
        """Test flattening an entry with empty content."""
        entry = {"name": "Empty", "id": "empty-id"}
        result = _flatten_search_entry(entry)
        assert result["_meta"]["name"] == "Empty"

    def test_flatten_entry_missing_optional_fields(self):
        """Test flattening entry with missing optional fields."""
        entry = {"name": "Minimal", "content": {"search": "test"}}
        result = _flatten_search_entry(entry)
        assert result["search"] == "test"
        assert result["_meta"]["links"] == {}
        assert result["_meta"]["acl"] == {}


class TestFlattenSearchObject:
    """Tests for flatten_search_object helper function."""

    def test_flatten_with_entry_list(self):
        """Test flattening response with entry list."""
        result = flatten_search_object(SAMPLE_API_RESPONSE)
        assert result["search"] == "index=main | head 1"
        assert result["_meta"]["name"] == "Test Search"

    def test_flatten_with_content_dict(self):
        """Test flattening response with content dict directly."""
        obj = {
            "content": {"search": "test query"},
            "name": "Direct Content",
            "id": "direct-id",
        }
        result = flatten_search_object(obj)
        assert result["search"] == "test query"
        assert result["_meta"]["name"] == "Direct Content"

    def test_flatten_already_flat_dict(self):
        """Test flattening already flat dict."""
        obj = {"search": "flat query", "disabled": "0"}
        result = flatten_search_object(obj)
        assert result["search"] == "flat query"
        assert "_meta" in result

    def test_flatten_empty_entry_list(self):
        """Test flattening with empty entry list."""
        obj = {"entry": []}
        result = flatten_search_object(obj)
        assert "_meta" in result

    def test_flatten_non_dict(self):
        """Test flattening non-dict value."""
        result = flatten_search_object("string value")
        assert result["_meta"] == {}
        assert result["raw"] == "string value"

    def test_flatten_none_value(self):
        """Test flattening None value."""
        result = flatten_search_object(None)
        assert result["_meta"] == {}
        assert result["raw"] is None


class TestCanonicalize:
    """Tests for _canonicalize helper function."""

    def test_canonicalize_basic_fields(self):
        """Test canonicalizing basic fields."""
        payload = {
            "search": "index=main",
            "description": "Test",
            "cron_schedule": "*/5 * * * *",
            "actions": "itsi_event_generator",
        }
        result = _canonicalize(payload)
        assert result["search"] == "index=main"
        assert result["description"] == "Test"
        assert result["cron_schedule"] == "*/5 * * * *"
        assert result["actions"] == "itsi_event_generator"

    def test_canonicalize_time_fields_dispatch(self):
        """Test canonicalizing dispatch time fields."""
        payload = {
            "dispatch.earliest_time": "-15m",
            "dispatch.latest_time": "now",
        }
        result = _canonicalize(payload)
        assert result["dispatch.earliest_time"] == "-15m"
        assert result["dispatch.latest_time"] == "now"

    def test_canonicalize_time_fields_simple(self):
        """Test canonicalizing simple time fields."""
        payload = {
            "earliest_time": "-1h",
            "latest_time": "now",
        }
        result = _canonicalize(payload)
        assert result["dispatch.earliest_time"] == "-1h"
        assert result["dispatch.latest_time"] == "now"

    def test_canonicalize_disabled_bool_true(self):
        """Test canonicalizing disabled=True."""
        payload = {"disabled": True}
        result = _canonicalize(payload)
        assert result["disabled"] == "1"

    def test_canonicalize_disabled_bool_false(self):
        """Test canonicalizing disabled=False."""
        payload = {"disabled": False}
        result = _canonicalize(payload)
        assert result["disabled"] == "0"

    def test_canonicalize_disabled_string(self):
        """Test canonicalizing disabled as string."""
        payload = {"disabled": "1"}
        result = _canonicalize(payload)
        assert result["disabled"] == "1"

    def test_canonicalize_non_dict(self):
        """Test canonicalizing non-dict value."""
        result = _canonicalize("not a dict")
        assert result == {}

    def test_canonicalize_none(self):
        """Test canonicalizing None value."""
        result = _canonicalize(None)
        assert result == {}

    def test_canonicalize_with_entry_format(self):
        """Test canonicalizing Splunk entry format."""
        result = _canonicalize(SAMPLE_API_RESPONSE)
        assert result["search"] == "index=main | head 1"
        assert result["disabled"] == "0"

    def test_canonicalize_empty_time_fields(self):
        """Test canonicalizing without time fields."""
        payload = {"search": "test"}
        result = _canonicalize(payload)
        assert "dispatch.earliest_time" not in result
        assert "dispatch.latest_time" not in result


class TestDiffCanonical:
    """Tests for _diff_canonical helper function."""

    def test_diff_no_changes(self):
        """Test diff with no changes."""
        desired = {"search": "test", "disabled": "0"}
        current = {"search": "test", "disabled": "0"}
        result = _diff_canonical(desired, current)
        assert result == {}

    def test_diff_with_changes(self):
        """Test diff with changes."""
        desired = {"search": "new query", "disabled": "1"}
        current = {"search": "old query", "disabled": "0"}
        result = _diff_canonical(desired, current)
        assert "search" in result
        assert result["search"] == ("old query", "new query")
        assert result["disabled"] == ("0", "1")

    def test_diff_only_compares_desired_keys(self):
        """Test that diff only compares keys in desired."""
        desired = {"search": "test"}
        current = {"search": "test", "disabled": "0", "extra": "value"}
        result = _diff_canonical(desired, current)
        assert result == {}

    def test_diff_time_fields_none_equal_empty(self):
        """Test that None and empty string are equal for time fields."""
        desired = {"dispatch.earliest_time": None}
        current = {"dispatch.earliest_time": ""}
        result = _diff_canonical(desired, current)
        assert result == {}

    def test_diff_time_fields_empty_equal_none(self):
        """Test that empty string and None are equal for time fields."""
        desired = {"dispatch.latest_time": ""}
        current = {"dispatch.latest_time": None}
        result = _diff_canonical(desired, current)
        assert result == {}

    def test_diff_string_conversion(self):
        """Test that values are compared as strings."""
        desired = {"disabled": 1}
        current = {"disabled": "1"}
        result = _diff_canonical(desired, current)
        assert result == {}


class TestSendRequest:
    """Tests for _send_request helper function."""

    def test_send_request_success(self):
        """Test successful request."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps({"name": "test"}),
            "headers": {},
        }

        status, data = _send_request(mock_conn, "GET", "/test/path")

        assert status == 200
        assert data["name"] == "test"

    def test_send_request_with_json_payload(self):
        """Test request with JSON payload."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        _send_request(mock_conn, "POST", "/test", payload={"key": "value"})

        call_args = mock_conn.send_request.call_args
        assert json.loads(call_args[1]["body"]) == {"key": "value"}

    def test_send_request_with_form_data(self):
        """Test request with form data."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        _send_request(mock_conn, "POST", "/test", payload={"key": "value"}, use_form_data=True)

        call_args = mock_conn.send_request.call_args
        assert "key=value" in call_args[1]["body"]
        assert call_args[1]["headers"]["Content-Type"] == "application/x-www-form-urlencoded"

    def test_send_request_with_string_payload(self):
        """Test request with string payload."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        _send_request(mock_conn, "POST", "/test", payload="raw string")

        call_args = mock_conn.send_request.call_args
        assert call_args[1]["body"] == "raw string"

    def test_send_request_with_none_payload(self):
        """Test request with None payload."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        _send_request(mock_conn, "GET", "/test", payload=None)

        call_args = mock_conn.send_request.call_args
        assert call_args[1]["body"] == ""

    def test_send_request_with_list_payload(self):
        """Test request with list payload."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        _send_request(mock_conn, "POST", "/test", payload=[{"a": 1}, {"b": 2}])

        call_args = mock_conn.send_request.call_args
        assert json.loads(call_args[1]["body"]) == [{"a": 1}, {"b": 2}]

    def test_send_request_list_response(self):
        """Test request with list response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([{"name": "item1"}]),
            "headers": {},
        }

        status, data = _send_request(mock_conn, "GET", "/test")

        assert "results" in data
        assert len(data["results"]) == 1

    def test_send_request_non_json_response(self):
        """Test request with non-JSON response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "plain text",
            "headers": {},
        }

        status, data = _send_request(mock_conn, "GET", "/test")

        assert data["raw_response"] == "plain text"

    def test_send_request_scalar_json_response(self):
        """Test request with scalar JSON response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(42),
            "headers": {},
        }

        status, data = _send_request(mock_conn, "GET", "/test")

        assert data["raw_response"] == 42

    def test_send_request_empty_body(self):
        """Test request with empty body."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 204,
            "body": "",
            "headers": {},
        }

        status, data = _send_request(mock_conn, "DELETE", "/test")

        assert status == 204

    def test_send_request_invalid_response(self):
        """Test request with invalid response format."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = "invalid"

        status, data = _send_request(mock_conn, "GET", "/test")

        assert status == 500
        assert "error" in data

    def test_send_request_401_error(self):
        """Test request with 401 error."""
        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = Exception("401 Unauthorized")

        status, data = _send_request(mock_conn, "GET", "/test")

        assert status == 401

    def test_send_request_404_error(self):
        """Test request with 404 error."""
        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = Exception("404 Not Found")

        status, data = _send_request(mock_conn, "GET", "/test")

        assert status == 404

    def test_send_request_generic_error(self):
        """Test request with generic error."""
        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = Exception("Network error")

        status, data = _send_request(mock_conn, "GET", "/test")

        assert status == 500
        assert "Network error" in data["error"]


class TestNormalizeToList:
    """Tests for normalize_to_list helper function."""

    def test_normalize_dict_with_entry(self):
        """Test normalizing dict with entry list."""
        data = {"entry": [{"name": "Search1"}]}
        result = normalize_to_list(data)
        assert len(result) == 1

    def test_normalize_dict_with_results(self):
        """Test normalizing dict with results list."""
        data = {"results": [{"name": "Result1"}]}
        result = normalize_to_list(data)
        assert len(result) == 1

    def test_normalize_single_dict(self):
        """Test normalizing single dict."""
        data = {"name": "Single"}
        result = normalize_to_list(data)
        assert len(result) == 1

    def test_normalize_list(self):
        """Test normalizing list input."""
        data = [{"name": "List1"}]
        result = normalize_to_list(data)
        assert len(result) == 1

    def test_normalize_empty_list(self):
        """Test normalizing empty list."""
        result = normalize_to_list([])
        assert result == []

    def test_normalize_non_dict_non_list(self):
        """Test normalizing non-dict non-list."""
        result = normalize_to_list("string")
        assert result == []

    def test_normalize_none(self):
        """Test normalizing None value."""
        result = normalize_to_list(None)
        assert result == []

    def test_normalize_empty_entry_list(self):
        """Test normalizing dict with empty entry list."""
        data = {"entry": []}
        result = normalize_to_list(data)
        assert result == []

    def test_normalize_empty_results_list(self):
        """Test normalizing dict with empty results list."""
        data = {"results": []}
        result = normalize_to_list(data)
        assert result == []


class TestParseResponseBody:
    """Tests for parse_response_body helper function."""

    def test_parse_empty_body(self):
        """Test parsing empty body."""
        result = parse_response_body("")
        assert result == {}

    def test_parse_none_body(self):
        """Test parsing None body."""
        result = parse_response_body(None)
        assert result == {}

    def test_parse_json_dict(self):
        """Test parsing JSON dict."""
        result = parse_response_body('{"name": "test", "value": 123}')
        assert result["name"] == "test"
        assert result["value"] == 123

    def test_parse_json_list(self):
        """Test parsing JSON list wraps in results."""
        result = parse_response_body('[{"name": "item1"}, {"name": "item2"}]')
        assert "results" in result
        assert len(result["results"]) == 2

    def test_parse_json_scalar_string(self):
        """Test parsing JSON scalar string."""
        result = parse_response_body('"scalar string"')
        assert result["raw_response"] == "scalar string"

    def test_parse_json_scalar_number(self):
        """Test parsing JSON scalar number."""
        result = parse_response_body("42")
        assert result["raw_response"] == 42

    def test_parse_json_scalar_bool(self):
        """Test parsing JSON scalar boolean."""
        result = parse_response_body("true")
        assert result["raw_response"] is True

    def test_parse_json_null(self):
        """Test parsing JSON null."""
        result = parse_response_body("null")
        assert result["raw_response"] is None

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON falls back to raw_response."""
        result = parse_response_body("not valid json")
        assert result["raw_response"] == "not valid json"

    def test_parse_partial_json(self):
        """Test parsing partial/truncated JSON."""
        result = parse_response_body('{"name": "incomplete')
        assert result["raw_response"] == '{"name": "incomplete'


class TestValidateApiResponse:
    """Tests for validate_api_response helper function."""

    def test_validate_valid_response(self):
        """Test validating a valid response."""
        response = {"status": 200, "body": "{}", "headers": {}}
        is_valid, error = validate_api_response(response)
        assert is_valid is True
        assert error == ""

    def test_validate_non_dict(self):
        """Test validating non-dict response."""
        is_valid, error = validate_api_response("string")
        assert is_valid is False
        assert "Expected dict" in error

    def test_validate_list_response(self):
        """Test validating list response."""
        is_valid, error = validate_api_response([1, 2, 3])
        assert is_valid is False
        assert "Expected dict" in error

    def test_validate_missing_status(self):
        """Test validating response missing status."""
        response = {"body": "{}"}
        is_valid, error = validate_api_response(response)
        assert is_valid is False
        assert "status" in error.lower()

    def test_validate_missing_body(self):
        """Test validating response missing body."""
        response = {"status": 200}
        is_valid, error = validate_api_response(response)
        assert is_valid is False
        assert "body" in error.lower()

    def test_validate_none(self):
        """Test validating None response."""
        is_valid, error = validate_api_response(None)
        assert is_valid is False

    def test_validate_empty_dict(self):
        """Test validating empty dict."""
        is_valid, error = validate_api_response({})
        assert is_valid is False


class TestHandleRequestException:
    """Tests for handle_request_exception helper function."""

    def test_handle_401_exception(self):
        """Test handling 401 Unauthorized exception."""
        exc = Exception("401 Unauthorized")
        status, data = handle_request_exception(exc)
        assert status == 401
        assert "Authentication failed" in data["error"]

    def test_handle_unauthorized_exception(self):
        """Test handling Unauthorized exception without status code."""
        exc = Exception("Unauthorized access denied")
        status, data = handle_request_exception(exc)
        assert status == 401

    def test_handle_404_exception(self):
        """Test handling 404 Not Found exception."""
        exc = Exception("404 Not Found")
        status, data = handle_request_exception(exc)
        assert status == 404
        assert "not found" in data["error"].lower()

    def test_handle_not_found_exception(self):
        """Test handling Not Found exception without status code."""
        exc = Exception("Resource Not Found")
        status, data = handle_request_exception(exc)
        assert status == 404

    def test_handle_generic_exception(self):
        """Test handling generic exception."""
        exc = Exception("Connection timeout")
        status, data = handle_request_exception(exc)
        assert status == 500
        assert "Connection timeout" in data["error"]

    def test_handle_empty_exception(self):
        """Test handling exception with empty message."""
        exc = Exception("")
        status, data = handle_request_exception(exc)
        assert status == 500

    def test_handle_network_error(self):
        """Test handling network error exception."""
        exc = Exception("Network unreachable")
        status, data = handle_request_exception(exc)
        assert status == 500
        assert "Network unreachable" in data["error"]


class TestProcessApiResponse:
    """Tests for process_api_response helper function."""

    def test_process_valid_json_dict_response(self):
        """Test processing valid JSON dict response."""
        result = {
            "status": 200,
            "body": '{"name": "test"}',
            "headers": {"Content-Type": "application/json"},
        }
        status, data = process_api_response(result)
        assert status == 200
        assert data["name"] == "test"
        assert "_response_headers" in data

    def test_process_valid_json_list_response(self):
        """Test processing valid JSON list response."""
        result = {
            "status": 200,
            "body": '[{"name": "item1"}]',
            "headers": {},
        }
        status, data = process_api_response(result)
        assert status == 200
        assert "results" in data
        assert len(data["results"]) == 1

    def test_process_empty_body_response(self):
        """Test processing response with empty body."""
        result = {
            "status": 204,
            "body": "",
            "headers": {},
        }
        status, data = process_api_response(result)
        assert status == 204
        assert "_response_headers" in data

    def test_process_non_json_response(self):
        """Test processing non-JSON response."""
        result = {
            "status": 200,
            "body": "plain text",
            "headers": {},
        }
        status, data = process_api_response(result)
        assert status == 200
        assert data["raw_response"] == "plain text"

    def test_process_invalid_response_format(self):
        """Test processing invalid response format."""
        status, data = process_api_response("not a dict")
        assert status == 500
        assert "error" in data

    def test_process_missing_status(self):
        """Test processing response missing status."""
        result = {"body": "{}"}
        status, data = process_api_response(result)
        assert status == 500
        assert "error" in data

    def test_process_missing_body(self):
        """Test processing response missing body."""
        result = {"status": 200}
        status, data = process_api_response(result)
        assert status == 500
        assert "error" in data

    def test_process_headers_included(self):
        """Test that headers are included in processed response."""
        result = {
            "status": 200,
            "body": '{"key": "value"}',
            "headers": {"X-Custom": "header-value"},
        }
        status, data = process_api_response(result)
        assert data["_response_headers"]["X-Custom"] == "header-value"

    def test_process_missing_headers_uses_empty_dict(self):
        """Test that missing headers defaults to empty dict."""
        result = {
            "status": 200,
            "body": '{"key": "value"}',
        }
        status, data = process_api_response(result)
        assert data["_response_headers"] == {}

    def test_process_scalar_json_response(self):
        """Test processing scalar JSON response."""
        result = {
            "status": 200,
            "body": "42",
            "headers": {},
        }
        status, data = process_api_response(result)
        assert status == 200
        assert data["raw_response"] == 42


class TestGetCorrelationSearch:
    """Tests for get_correlation_search function."""

    def test_get_by_id_success(self):
        """Test getting correlation search by ID."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        status, data = get_correlation_search(mock_conn, "test-id")

        assert status == 200
        assert data["search"] == "index=main | head 1"

    def test_get_with_name_encoding(self):
        """Test getting with name encoding (%20 for spaces)."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        get_correlation_search(mock_conn, "Test Search", use_name_encoding=True)

        call_args = mock_conn.send_request.call_args
        # Should use %20 encoding
        assert "Test%20Search" in call_args[0][0]

    def test_get_without_name_encoding(self):
        """Test getting without name encoding (+ for spaces)."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        get_correlation_search(mock_conn, "Test Search", use_name_encoding=False)

        call_args = mock_conn.send_request.call_args
        # Should use + encoding
        assert "Test+Search" in call_args[0][0]

    def test_get_with_fields(self):
        """Test getting with specific fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        get_correlation_search(mock_conn, "test-id", fields="name,search")

        call_args = mock_conn.send_request.call_args
        assert "fields=name%2Csearch" in call_args[0][0]

    def test_get_with_fields_list(self):
        """Test getting with fields as list."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        get_correlation_search(mock_conn, "test-id", fields=["name", "search"])

        call_args = mock_conn.send_request.call_args
        assert "fields=name%2Csearch" in call_args[0][0]

    def test_get_not_found(self):
        """Test getting non-existent search."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 404,
            "body": json.dumps({"error": "Not found"}),
            "headers": {},
        }

        status, data = get_correlation_search(mock_conn, "nonexistent")

        assert status == 404


class TestCreateCorrelationSearch:
    """Tests for create_correlation_search function."""

    def test_create_basic(self):
        """Test basic creation."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        search_data = {
            "name": "New Search",
            "search": "index=main | head 1",
        }
        status, data = create_correlation_search(mock_conn, search_data)

        assert status == 200
        call_args = mock_conn.send_request.call_args
        assert call_args[1]["method"] == "POST"

    def test_create_with_dispatch_time_fields(self):
        """Test creation with dispatch time fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        search_data = {
            "name": "New Search",
            "search": "test",
            "dispatch.earliest_time": "-15m",
            "dispatch.latest_time": "now",
        }
        create_correlation_search(mock_conn, search_data)

        call_args = mock_conn.send_request.call_args
        payload = json.loads(call_args[1]["body"])
        # Should have both formats
        assert payload["earliest_time"] == "-15m"
        assert payload["dispatch.earliest_time"] == "-15m"

    def test_create_with_simple_time_fields(self):
        """Test creation with simple time fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        search_data = {
            "name": "New Search",
            "search": "test",
            "earliest_time": "-1h",
            "latest_time": "now",
        }
        create_correlation_search(mock_conn, search_data)

        call_args = mock_conn.send_request.call_args
        payload = json.loads(call_args[1]["body"])
        # Should have both formats
        assert payload["earliest_time"] == "-1h"
        assert payload["dispatch.earliest_time"] == "-1h"


class TestUpdateCorrelationSearch:
    """Tests for update_correlation_search function."""

    def test_update_basic(self):
        """Test basic update."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        update_data = {"disabled": "1"}
        status, data = update_correlation_search(mock_conn, "test-id", update_data)

        assert status == 200
        call_args = mock_conn.send_request.call_args
        assert "is_partial_data=1" in call_args[0][0]

    def test_update_includes_name_in_payload(self):
        """Test that update includes name in payload."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        update_correlation_search(mock_conn, "test-id", {"disabled": "0"})

        call_args = mock_conn.send_request.call_args
        payload = json.loads(call_args[1]["body"])
        assert payload["name"] == "test-id"

    def test_update_with_dispatch_time_fields(self):
        """Test update with dispatch time fields."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        update_data = {
            "dispatch.earliest_time": "-30m",
            "dispatch.latest_time": "now",
        }
        update_correlation_search(mock_conn, "test-id", update_data)

        call_args = mock_conn.send_request.call_args
        payload = json.loads(call_args[1]["body"])
        assert payload["earliest_time"] == "-30m"

    def test_update_empty_data(self):
        """Test update with empty data."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": "{}",
            "headers": {},
        }

        update_correlation_search(mock_conn, "test-id", None)

        call_args = mock_conn.send_request.call_args
        payload = json.loads(call_args[1]["body"])
        assert payload["name"] == "test-id"


class TestDeleteCorrelationSearch:
    """Tests for delete_correlation_search function."""

    def test_delete_basic(self):
        """Test basic deletion."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 204,
            "body": "",
            "headers": {},
        }

        status, data = delete_correlation_search(mock_conn, "test-id")

        assert status == 204
        call_args = mock_conn.send_request.call_args
        assert call_args[1]["method"] == "DELETE"

    def test_delete_with_name_encoding(self):
        """Test deletion with name encoding."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 204,
            "body": "",
            "headers": {},
        }

        delete_correlation_search(mock_conn, "Test Search", use_name_encoding=True)

        call_args = mock_conn.send_request.call_args
        assert "Test%20Search" in call_args[0][0]

    def test_delete_without_name_encoding(self):
        """Test deletion without name encoding."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 204,
            "body": "",
            "headers": {},
        }

        delete_correlation_search(mock_conn, "Test Search", use_name_encoding=False)

        call_args = mock_conn.send_request.call_args
        assert "Test+Search" in call_args[0][0]


class TestEnsurePresent:
    """Tests for ensure_present function."""

    def test_ensure_present_create_new(self):
        """Test ensure_present creates new search when not found."""
        mock_conn = MagicMock()
        # First call returns 404 (not found), second returns 200 (created), third returns 200 (verify)
        mock_conn.send_request.side_effect = [
            {"status": 404, "body": "{}", "headers": {}},
            {"status": 200, "body": json.dumps(SAMPLE_API_RESPONSE), "headers": {}},
            {"status": 200, "body": json.dumps(SAMPLE_API_RESPONSE), "headers": {}},
        ]

        result = {}
        desired_data = {"name": "new-search", "search": "test"}
        ensure_present(mock_conn, "new-search", desired_data, result)

        assert result["operation"] == "create"
        assert result["changed"] is True

    def test_ensure_present_no_change_needed(self):
        """Test ensure_present when no change is needed."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps(SAMPLE_API_RESPONSE),
            "headers": {},
        }

        result = {}
        # Desired matches current
        desired_data = {
            "name": "Test Search",
            "search": "index=main | head 1",
            "disabled": False,
        }
        ensure_present(mock_conn, "Test Search", desired_data, result)

        assert result["operation"] == "no_change"
        assert result["changed"] is False

    def test_ensure_present_update_needed(self):
        """Test ensure_present when update is needed."""
        mock_conn = MagicMock()
        # First call returns existing, second is update
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps(SAMPLE_API_RESPONSE), "headers": {}},
            {"status": 200, "body": json.dumps(SAMPLE_API_RESPONSE), "headers": {}},
        ]

        result = {}
        # Change description
        desired_data = {
            "name": "Test Search",
            "description": "New description",
        }
        ensure_present(mock_conn, "Test Search", desired_data, result)

        assert result["operation"] == "update"
        assert result["changed"] is True

    def test_ensure_present_update_cron_schedule_sets_is_scheduled(self):
        """Test that updating cron_schedule sets is_scheduled."""
        # Create response without is_scheduled set
        response_without_scheduled = {
            "entry": [
                {
                    "name": "Test Search",
                    "id": "test-id",
                    "content": {
                        "search": "index=main | head 1",
                        "disabled": "0",
                        "cron_schedule": "*/5 * * * *",
                        "is_scheduled": "0",
                    },
                    "links": {},
                    "acl": {},
                },
            ],
        }

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps(response_without_scheduled), "headers": {}},
            {"status": 200, "body": json.dumps(SAMPLE_API_RESPONSE), "headers": {}},
        ]

        result = {}
        desired_data = {
            "name": "Test Search",
            "cron_schedule": "*/10 * * * *",  # Changed cron
        }
        ensure_present(mock_conn, "Test Search", desired_data, result)

        # Verify update was called with is_scheduled
        call_args = mock_conn.send_request.call_args_list[1]
        payload = json.loads(call_args[1]["body"])
        assert payload.get("is_scheduled") == "1"

    def test_ensure_present_error_response(self):
        """Test ensure_present with error response."""
        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 500,
            "body": json.dumps({"error": "Server error"}),
            "headers": {},
        }

        result = {}
        ensure_present(mock_conn, "test", {"name": "test"}, result)

        assert result["operation"] == "error"
        assert result["status"] == 500


class TestMain:
    """Tests for main module execution."""

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
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

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_present_no_identifier(self, mock_module_class, mock_connection):
        """Test main fails when no identifier provided for present state."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": None,
            "correlation_search_id": None,
            "state": "present",
            "search": None,
            "disabled": None,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called()
        assert "required" in mock_module.fail_json.call_args[1]["msg"].lower()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_present_create_requires_search(self, mock_module_class, mock_connection):
        """Test main requires search param for new correlation search."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": "new-search",
            "correlation_search_id": None,
            "state": "present",
            "search": None,  # Missing search
            "disabled": None,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": None,
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

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called()
        assert "search" in mock_module.fail_json.call_args[1]["msg"].lower()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_present_check_mode_create(self, mock_module_class, mock_connection):
        """Test main check mode for create operation."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": "new-search",
            "correlation_search_id": None,
            "state": "present",
            "search": "index=main",
            "disabled": False,
            "cron_schedule": "*/5 * * * *",
            "earliest_time": "-15m",
            "latest_time": "now",
            "description": "Test",
            "actions": "itsi_event_generator",
            "additional_fields": None,
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
        assert call_kwargs["changed"] is True
        assert call_kwargs["operation"] == "create"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_present_check_mode_update(self, mock_module_class, mock_connection):
        """Test main check mode for update operation."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": None,
            "correlation_search_id": "existing-search",
            "state": "present",
            "search": None,
            "disabled": True,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": None,
        }
        mock_module.check_mode = True
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
        assert call_kwargs["changed"] is True
        assert call_kwargs["operation"] == "update"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_absent_no_identifier(self, mock_module_class, mock_connection):
        """Test main fails when no identifier provided for absent state."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": None,
            "correlation_search_id": None,
            "state": "absent",
            "search": None,
            "disabled": None,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called()

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_absent_delete_existing(self, mock_module_class, mock_connection):
        """Test main deletes existing search."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": None,
            "correlation_search_id": "existing-search",
            "state": "absent",
            "search": None,
            "disabled": None,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.side_effect = [
            {"status": 200, "body": json.dumps(SAMPLE_API_RESPONSE), "headers": {}},
            {"status": 204, "body": "", "headers": {}},
        ]
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["operation"] == "delete"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_absent_already_absent(self, mock_module_class, mock_connection):
        """Test main handles already absent search."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": None,
            "correlation_search_id": "nonexistent",
            "state": "absent",
            "search": None,
            "disabled": None,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": None,
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
        assert call_kwargs["operation"] == "no_change"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_absent_check_mode(self, mock_module_class, mock_connection):
        """Test main check mode for delete operation."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": None,
            "correlation_search_id": "existing-search",
            "state": "absent",
            "search": None,
            "disabled": None,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": None,
        }
        mock_module.check_mode = True
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
        assert call_kwargs["changed"] is True
        assert call_kwargs["operation"] == "delete"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_exception_handling(self, mock_module_class, mock_connection):
        """Test main handles exceptions properly."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": "test",
            "correlation_search_id": None,
            "state": "present",
            "search": "test",
            "disabled": None,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": None,
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

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_with_additional_fields(self, mock_module_class, mock_connection):
        """Test main with additional_fields parameter."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": "test-search",
            "correlation_search_id": None,
            "state": "present",
            "search": "index=main",
            "disabled": None,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": {"custom_field": "custom_value"},
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
        body = json.loads(call_kwargs["body"])
        assert body["custom_field"] == "custom_value"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_correlation_search_id_takes_precedence(self, mock_module_class, mock_connection):
        """Test that correlation_search_id takes precedence over name."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": "name-value",
            "correlation_search_id": "id-value",
            "state": "present",
            "search": "test",
            "disabled": None,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": None,
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

        # Check that id-value was used
        call_args = mock_conn.send_request.call_args
        assert "id-value" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_use_name_encoding_with_name_only(self, mock_module_class, mock_connection):
        """Test that name encoding is used when only name is provided."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": "Test Search",
            "correlation_search_id": None,
            "state": "absent",
            "search": None,
            "disabled": None,
            "cron_schedule": None,
            "earliest_time": None,
            "latest_time": None,
            "description": None,
            "actions": None,
            "additional_fields": None,
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

        # Verify %20 encoding was used
        call_args = mock_conn.send_request.call_args
        assert "Test%20Search" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_correlation_search.AnsibleModule")
    def test_main_present_with_all_optional_fields(self, mock_module_class, mock_connection):
        """Test main present state with all optional fields."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "name": "complete-search",
            "correlation_search_id": None,
            "state": "present",
            "search": "index=main | head 1",
            "disabled": False,
            "cron_schedule": "*/5 * * * *",
            "earliest_time": "-15m",
            "latest_time": "now",
            "description": "Complete test search",
            "actions": "itsi_event_generator",
            "additional_fields": {"priority": "high"},
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
        body = json.loads(call_kwargs["body"])
        assert body["search"] == "index=main | head 1"
        assert body["disabled"] is False
        assert body["cron_schedule"] == "*/5 * * * *"
        assert body["earliest_time"] == "-15m"
        assert body["latest_time"] == "now"
        assert body["description"] == "Complete test search"
        assert body["actions"] == "itsi_event_generator"
        assert body["priority"] == "high"
