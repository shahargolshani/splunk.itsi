# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for ItsiRequest class (plugins/module_utils/itsi_request.py)."""

import json
from unittest.mock import MagicMock

import pytest
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_module() -> MagicMock:
    """Create a MagicMock AnsibleModule."""
    module = MagicMock()
    module.fail_json.side_effect = SystemExit(1)
    return module


def _mock_conn(status: int = 200, body: str = "{}", headers: dict | None = None) -> MagicMock:
    """Create a MagicMock Connection with a preconfigured send_request return value."""
    conn = MagicMock()
    conn.send_request.return_value = {
        "status": status,
        "body": body,
        "headers": headers or {},
    }
    return conn


def _client(status=200, body="{}", headers=None):
    """Shorthand: build an ItsiRequest with mocked connection and module."""
    return ItsiRequest(_mock_conn(status, body, headers), _mock_module())


# ===========================================================================
# TestItsiRequestInit
# ===========================================================================


class TestItsiRequestInit:
    """Tests for ItsiRequest initialisation."""

    def test_stores_connection_and_module(self):
        conn = MagicMock()
        module = MagicMock()
        client = ItsiRequest(conn, module)
        assert client.connection is conn
        assert client.module is module


# ===========================================================================
# TestRequest – core request() method
# ===========================================================================


class TestRequest:
    """Tests for the generic request() entry-point."""

    def test_success_json_dict(self):
        client = _client(body=json.dumps({"_key": "abc"}))
        result = client.request("GET", "/test/path")
        assert result is not None
        status, headers, body = result
        assert status == 200
        assert body["_key"] == "abc"

    def test_method_uppercased(self):
        client = _client()
        client.request("get", "/test")
        call_kw = client.connection.send_request.call_args[1]
        assert call_kw["method"] == "GET"

    def test_passes_body_and_headers(self):
        client = _client()
        client.request("POST", "/api", payload={"k": "v"})
        call_kw = client.connection.send_request.call_args[1]
        assert json.loads(call_kw["body"]) == {"k": "v"}

    def test_404_returns_none(self):
        client = _client(status=404, body='{"error": "not found"}')
        result = client.request("GET", "/missing")
        assert result is None

    def test_non_2xx_calls_fail_json(self):
        client = _client(status=500, body="Internal Server Error")
        with pytest.raises(SystemExit):
            client.request("GET", "/fail")
        client.module.fail_json.assert_called_once()
        assert "500" in client.module.fail_json.call_args[1]["msg"]

    def test_exception_calls_fail_json(self):
        conn = MagicMock()
        conn.send_request.side_effect = Exception("Network error")
        module = _mock_module()
        client = ItsiRequest(conn, module)
        with pytest.raises(SystemExit):
            client.request("GET", "/anything")
        module.fail_json.assert_called_once()
        assert "Network error" in module.fail_json.call_args[1]["msg"]

    def test_invalid_result_format_calls_fail_json(self):
        conn = MagicMock()
        conn.send_request.return_value = "invalid"
        module = _mock_module()
        client = ItsiRequest(conn, module)
        with pytest.raises(SystemExit):
            client.get("/test")
        module.fail_json.assert_called_once()

    def test_missing_status_key_calls_fail_json(self):
        conn = MagicMock()
        conn.send_request.return_value = {"body": "{}"}
        module = _mock_module()
        client = ItsiRequest(conn, module)
        with pytest.raises(SystemExit):
            client.get("/test")
        module.fail_json.assert_called_once()


# ===========================================================================
# TestGet / TestPost / TestDelete – convenience wrappers
# ===========================================================================


class TestGet:
    def test_delegates_to_request(self):
        client = _client(body=json.dumps({"ok": True}))
        result = client.get("/items")
        assert result is not None
        status, headers, body = result
        assert status == 200
        assert client.connection.send_request.call_args[1]["method"] == "GET"

    def test_with_params(self):
        client = _client()
        client.get("/items", params={"output_mode": "json", "count": 10})
        path = client.connection.send_request.call_args[0][0]
        assert "output_mode=json" in path
        assert "count=10" in path


class TestPost:
    def test_delegates_to_request(self):
        client = _client()
        client.post("/items", payload={"title": "svc"})
        call_kw = client.connection.send_request.call_args[1]
        assert call_kw["method"] == "POST"
        assert json.loads(call_kw["body"]) == {"title": "svc"}

    def test_with_form_data(self):
        client = _client()
        client.post("/items", payload={"key": "value"}, use_form_data=True)
        call_kw = client.connection.send_request.call_args[1]
        assert "key=value" in call_kw["body"]
        assert call_kw["headers"]["Content-Type"] == "application/x-www-form-urlencoded"


class TestDelete:
    def test_delegates_to_request(self):
        client = _client(status=204, body="")
        result = client.delete("/items/abc")
        assert result is not None
        status, headers, body = result
        assert status == 204
        assert client.connection.send_request.call_args[1]["method"] == "DELETE"


# ===========================================================================
# TestGetByPath / TestDeleteByPath / TestCreateUpdate
# ===========================================================================


class TestGetByPath:
    def test_adds_output_mode_json(self):
        client = _client()
        client.get_by_path("/endpoint")
        path = client.connection.send_request.call_args[0][0]
        assert "output_mode=json" in path

    def test_merges_extra_params(self):
        client = _client()
        client.get_by_path("/endpoint", query_params={"fields": "_key,title"})
        path = client.connection.send_request.call_args[0][0]
        assert "output_mode=json" in path
        assert "fields=_key" in path

    def test_omits_none_params(self):
        client = _client()
        client.get_by_path("/endpoint", query_params={"keep": "yes", "skip": None})
        path = client.connection.send_request.call_args[0][0]
        assert "keep=yes" in path
        assert "skip" not in path


class TestDeleteByPath:
    def test_adds_output_mode_json(self):
        client = _client(body="{}")
        client.delete_by_path("/endpoint/abc")
        path = client.connection.send_request.call_args[0][0]
        assert "output_mode=json" in path


class TestCreateUpdate:
    def test_posts_with_output_mode_json(self):
        client = _client()
        client.create_update("/endpoint", data={"title": "new"})
        path = client.connection.send_request.call_args[0][0]
        call_kw = client.connection.send_request.call_args[1]
        assert "output_mode=json" in path
        assert call_kw["method"] == "POST"
        assert json.loads(call_kw["body"]) == {"title": "new"}

    def test_with_form_data(self):
        client = _client()
        client.create_update("/endpoint", data={"k": "v"}, use_form_data=True)
        call_kw = client.connection.send_request.call_args[1]
        assert "k=v" in call_kw["body"]

    def test_merges_extra_params(self):
        client = _client()
        client.create_update("/endpoint", data=None, query_params={"is_partial_data": "1"})
        path = client.connection.send_request.call_args[0][0]
        assert "is_partial_data=1" in path


# ===========================================================================
# TestBuildQueryString
# ===========================================================================


class TestBuildQueryString:
    def test_no_params_returns_path(self):
        assert ItsiRequest._build_query_string("/test", None) == "/test"

    def test_empty_dict_returns_path(self):
        assert ItsiRequest._build_query_string("/test", {}) == "/test"

    def test_filters_none_and_empty(self):
        result = ItsiRequest._build_query_string("/test", {"keep": "yes", "drop_none": None, "drop_empty": ""})
        assert "keep=yes" in result
        assert "drop_none" not in result

    def test_keeps_zero_and_false(self):
        result = ItsiRequest._build_query_string("/test", {"count": 0, "enabled": False})
        assert "count=0" in result
        assert "enabled=False" in result

    def test_appends_to_existing_query(self):
        result = ItsiRequest._build_query_string("/test?existing=1", {"new": "2"})
        assert "existing=1" in result
        assert "&new=2" in result

    def test_starts_with_question_mark(self):
        result = ItsiRequest._build_query_string("/test", {"a": "b"})
        assert "?" in result
        assert "a=b" in result


# ===========================================================================
# TestPrepareRequest
# ===========================================================================


class TestPrepareRequest:
    def test_dict_payload_json(self):
        body, headers = ItsiRequest._prepare_request({"k": "v"}, False, None)
        assert json.loads(body) == {"k": "v"}
        assert headers == {}

    def test_list_payload_json(self):
        body, headers = ItsiRequest._prepare_request([{"a": 1}], False, None)
        assert json.loads(body) == [{"a": 1}]

    def test_string_payload_passthrough(self):
        body, _headers = ItsiRequest._prepare_request("raw data", False, None)
        assert body == "raw data"

    def test_none_payload_empty_string(self):
        body, _headers = ItsiRequest._prepare_request(None, False, None)
        assert body == ""

    def test_form_data_encoding(self):
        body, headers = ItsiRequest._prepare_request({"k": "v"}, True, None)
        assert "k=v" in body
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"

    def test_extra_headers_merged(self):
        _body, headers = ItsiRequest._prepare_request(None, False, {"X-Custom": "val"})
        assert headers["X-Custom"] == "val"


# ===========================================================================
# TestResponseParsing
# ===========================================================================


class TestResponseParsing:
    def test_valid_json_dict(self):
        client = _client(body='{"_key": "abc"}')
        result = client.get("/test")
        assert result is not None
        _status, _headers, body = result
        assert body["_key"] == "abc"

    def test_empty_body(self):
        client = _client(status=204, body="")
        result = client.get("/test")
        assert result is not None
        status, _headers, body = result
        assert status == 204
        assert body == {}

    def test_non_json_body(self):
        client = _client(body="plain text")
        result = client.get("/test")
        assert result is not None
        _status, _headers, body = result
        assert body == "plain text"

    def test_json_list_body(self):
        client = _client(body='[{"a": 1}]')
        result = client.get("/test")
        assert result is not None
        _status, _headers, body = result
        assert body == [{"a": 1}]

    def test_response_headers_returned_separately(self):
        client = _client(body='{"ok": true}', headers={"X-Request-Id": "abc123"})
        result = client.get("/test")
        assert result is not None
        _status, headers, body = result
        assert headers["X-Request-Id"] == "abc123"
        assert "_response_headers" not in body


# ===========================================================================
# TestEndToEnd
# ===========================================================================


class TestEndToEnd:
    def test_get_json_round_trip(self):
        payload = {"_key": "p1", "title": "My Policy"}
        client = _client(body=json.dumps(payload))
        result = client.get("/itoa_interface/notable_event_aggregation_policy/p1")
        assert result is not None
        _status, _headers, body = result
        assert body["title"] == "My Policy"

    def test_post_create_round_trip(self):
        client = _client(body=json.dumps({"_key": "new123"}))
        result = client.create_update("/endpoint", data={"title": "New"})
        assert result is not None
        _status, _headers, body = result
        assert body["_key"] == "new123"

    def test_delete_round_trip(self):
        client = _client(body='{"deleted": true}')
        result = client.delete_by_path("/endpoint/svc123")
        assert result is not None
        assert result[0] == 200

    def test_404_returns_none(self):
        client = _client(status=404, body='{"error": "not found"}')
        assert client.get("/anything") is None

    def test_500_calls_fail_json(self):
        client = _client(status=500, body="error")
        with pytest.raises(SystemExit):
            client.get("/anything")
        client.module.fail_json.assert_called_once()
