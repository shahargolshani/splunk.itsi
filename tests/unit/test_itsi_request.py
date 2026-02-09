# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for ItsiRequest class (plugins/module_utils/itsi_request.py)."""


import json
from unittest.mock import MagicMock

from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_conn(status: int = 200, body: str = "{}", headers: dict | None = None) -> MagicMock:
    """Create a MagicMock Connection with a preconfigured send_request return value."""
    conn = MagicMock()
    conn.send_request.return_value = {
        "status": status,
        "body": body,
        "headers": headers or {},
    }
    return conn


# ===========================================================================
# TestItsiRequestInit
# ===========================================================================


class TestItsiRequestInit:
    """Tests for ItsiRequest initialisation."""

    def test_stores_connection(self):
        """Test that the connection object is stored."""
        conn = MagicMock()
        client = ItsiRequest(conn)
        assert client.connection is conn


# ===========================================================================
# TestRequest – core request() method
# ===========================================================================


class TestRequest:
    """Tests for the generic request() entry-point."""

    def test_success_json_dict(self):
        """Test successful request with JSON dict response."""
        conn = _mock_conn(body=json.dumps({"_key": "abc"}))
        client = ItsiRequest(conn)

        status, data = client.request("GET", "/test/path")

        assert status == 200
        assert data["_key"] == "abc"
        assert "_response_headers" in data

    def test_method_uppercased(self):
        """Test that the HTTP method is converted to uppercase."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.request("get", "/test")

        call_kw = conn.send_request.call_args[1]
        assert call_kw["method"] == "GET"

    def test_passes_body_and_headers(self):
        """Test that body and headers are forwarded to send_request."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.request("POST", "/api", payload={"k": "v"})

        call_kw = conn.send_request.call_args[1]
        assert json.loads(call_kw["body"]) == {"k": "v"}


# ===========================================================================
# TestGet / TestPost / TestDelete – convenience wrappers
# ===========================================================================


class TestGet:
    """Tests for the get() convenience method."""

    def test_delegates_to_request(self):
        """Test get delegates to request with GET method."""
        conn = _mock_conn(body=json.dumps({"ok": True}))
        client = ItsiRequest(conn)

        status, data = client.get("/items")

        assert status == 200
        call_kw = conn.send_request.call_args[1]
        assert call_kw["method"] == "GET"

    def test_with_params(self):
        """Test GET with query parameters."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.get("/items", params={"output_mode": "json", "count": 10})

        path = conn.send_request.call_args[0][0]
        assert "output_mode=json" in path
        assert "count=10" in path


class TestPost:
    """Tests for the post() convenience method."""

    def test_delegates_to_request(self):
        """Test post delegates to request with POST method."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.post("/items", payload={"title": "svc"})

        call_kw = conn.send_request.call_args[1]
        assert call_kw["method"] == "POST"
        assert json.loads(call_kw["body"]) == {"title": "svc"}

    def test_with_form_data(self):
        """Test POST with form data encoding."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.post("/items", payload={"key": "value"}, use_form_data=True)

        call_kw = conn.send_request.call_args[1]
        assert "key=value" in call_kw["body"]
        assert call_kw["headers"]["Content-Type"] == "application/x-www-form-urlencoded"


class TestDelete:
    """Tests for the delete() convenience method."""

    def test_delegates_to_request(self):
        """Test delete delegates to request with DELETE method."""
        conn = _mock_conn(status=204, body="")
        client = ItsiRequest(conn)

        status, data = client.delete("/items/abc")

        assert status == 204
        call_kw = conn.send_request.call_args[1]
        assert call_kw["method"] == "DELETE"


# ===========================================================================
# TestGetByPath / TestDeleteByPath / TestCreateUpdate – high-level helpers
# ===========================================================================


class TestGetByPath:
    """Tests for get_by_path() helper."""

    def test_adds_output_mode_json(self):
        """Test that output_mode=json is automatically added."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.get_by_path("/servicesNS/nobody/SA-ITOA/itoa_interface/service")

        path = conn.send_request.call_args[0][0]
        assert "output_mode=json" in path

    def test_merges_extra_params(self):
        """Test that extra query_params are merged."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.get_by_path("/endpoint", query_params={"fields": "_key,title"})

        path = conn.send_request.call_args[0][0]
        assert "output_mode=json" in path
        assert "fields=_key" in path

    def test_omits_none_params(self):
        """Test that None query_params values are omitted."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.get_by_path("/endpoint", query_params={"keep": "yes", "skip": None})

        path = conn.send_request.call_args[0][0]
        assert "keep=yes" in path
        assert "skip" not in path


class TestDeleteByPath:
    """Tests for delete_by_path() helper."""

    def test_adds_output_mode_json(self):
        """Test that output_mode=json is automatically added."""
        conn = _mock_conn(status=200, body="{}")
        client = ItsiRequest(conn)

        client.delete_by_path("/endpoint/abc")

        path = conn.send_request.call_args[0][0]
        assert "output_mode=json" in path


class TestCreateUpdate:
    """Tests for create_update() helper."""

    def test_posts_with_output_mode_json(self):
        """Test that output_mode=json is added and POST is used."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.create_update("/endpoint", data={"title": "new"})

        path = conn.send_request.call_args[0][0]
        call_kw = conn.send_request.call_args[1]
        assert "output_mode=json" in path
        assert call_kw["method"] == "POST"
        assert json.loads(call_kw["body"]) == {"title": "new"}

    def test_with_form_data(self):
        """Test create_update with form-data encoding."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.create_update("/endpoint", data={"k": "v"}, use_form_data=True)

        call_kw = conn.send_request.call_args[1]
        assert "k=v" in call_kw["body"]
        assert call_kw["headers"]["Content-Type"] == "application/x-www-form-urlencoded"

    def test_merges_extra_params(self):
        """Test that extra query_params are merged."""
        conn = _mock_conn()
        client = ItsiRequest(conn)

        client.create_update("/endpoint", data=None, query_params={"is_partial_data": "1"})

        path = conn.send_request.call_args[0][0]
        assert "output_mode=json" in path
        assert "is_partial_data=1" in path


# ===========================================================================
# TestBuildQueryString – static helper
# ===========================================================================


class TestBuildQueryString:
    """Tests for _build_query_string static method."""

    def test_no_params_returns_path(self):
        """Test path is returned unchanged when params is None."""
        assert ItsiRequest._build_query_string("/test", None) == "/test"

    def test_empty_dict_returns_path(self):
        """Test path is returned unchanged when params is empty."""
        assert ItsiRequest._build_query_string("/test", {}) == "/test"

    def test_filters_none_and_empty(self):
        """Test None and empty-string values are filtered out."""
        result = ItsiRequest._build_query_string(
            "/test",
            {"keep": "yes", "drop_none": None, "drop_empty": ""},
        )
        assert "keep=yes" in result
        assert "drop_none" not in result
        assert "drop_empty" not in result

    def test_keeps_zero_and_false(self):
        """Test that 0 and False are kept as valid values."""
        result = ItsiRequest._build_query_string(
            "/test",
            {"count": 0, "enabled": False},
        )
        assert "count=0" in result
        assert "enabled=False" in result

    def test_appends_to_existing_query(self):
        """Test params are appended with & when path already has ?."""
        result = ItsiRequest._build_query_string(
            "/test?existing=1",
            {"new": "2"},
        )
        assert "existing=1" in result
        assert "&new=2" in result

    def test_starts_with_question_mark(self):
        """Test params start with ? when path has no query string."""
        result = ItsiRequest._build_query_string("/test", {"a": "b"})
        assert "?" in result
        assert "a=b" in result


# ===========================================================================
# TestPrepareRequest – static helper
# ===========================================================================


class TestPrepareRequest:
    """Tests for _prepare_request static method."""

    def test_dict_payload_json(self):
        """Test dict payload is JSON-serialised."""
        body, headers = ItsiRequest._prepare_request({"k": "v"}, False, None)
        assert json.loads(body) == {"k": "v"}
        assert headers == {}

    def test_list_payload_json(self):
        """Test list payload is JSON-serialised."""
        body, headers = ItsiRequest._prepare_request([{"a": 1}], False, None)
        assert json.loads(body) == [{"a": 1}]

    def test_string_payload_passthrough(self):
        """Test string payload is passed through unchanged."""
        body, headers = ItsiRequest._prepare_request("raw data", False, None)
        assert body == "raw data"

    def test_none_payload_empty_string(self):
        """Test None payload becomes empty string."""
        body, headers = ItsiRequest._prepare_request(None, False, None)
        assert body == ""

    def test_form_data_encoding(self):
        """Test form-data encoding of dict payload."""
        body, headers = ItsiRequest._prepare_request({"k": "v"}, True, None)
        assert "k=v" in body
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"

    def test_extra_headers_merged(self):
        """Test extra headers are merged into result."""
        _body, headers = ItsiRequest._prepare_request(None, False, {"X-Custom": "val"})
        assert headers["X-Custom"] == "val"


# ===========================================================================
# TestParseResponse – static helper
# ===========================================================================


class TestParseResponse:
    """Tests for _parse_response static method."""

    def test_valid_json_dict(self):
        """Test parsing a valid JSON dict body."""
        result = {"status": 200, "body": '{"_key": "abc"}', "headers": {}}
        status, data = ItsiRequest._parse_response(result)
        assert status == 200
        assert data["_key"] == "abc"
        assert "_response_headers" in data

    def test_empty_body(self):
        """Test parsing an empty body."""
        result = {"status": 204, "body": "", "headers": {}}
        status, data = ItsiRequest._parse_response(result)
        assert status == 204
        assert "_response_headers" in data

    def test_non_json_body(self):
        """Test parsing a non-JSON body."""
        result = {"status": 200, "body": "plain text", "headers": {}}
        status, data = ItsiRequest._parse_response(result)
        assert status == 200
        assert data["raw_response"] == "plain text"

    def test_json_list_body(self):
        """Test parsing a JSON list body (no _response_headers injection)."""
        result = {"status": 200, "body": '[{"a": 1}]', "headers": {}}
        status, data = ItsiRequest._parse_response(result)
        assert status == 200
        assert isinstance(data, list)

    def test_invalid_result_format(self):
        """Test invalid (non-dict) result returns 500."""
        status, data = ItsiRequest._parse_response("invalid")
        assert status == 500
        assert "error" in data

    def test_missing_status_key(self):
        """Test result without 'status' key returns 500."""
        status, data = ItsiRequest._parse_response({"body": "{}"})
        assert status == 500
        assert "error" in data

    def test_response_headers_forwarded(self):
        """Test response headers are included in parsed data."""
        result = {
            "status": 200,
            "body": '{"ok": true}',
            "headers": {"X-Request-Id": "abc123"},
        }
        status, data = ItsiRequest._parse_response(result)
        assert data["_response_headers"]["X-Request-Id"] == "abc123"


# ===========================================================================
# TestHandleException – static helper
# ===========================================================================


class TestHandleException:
    """Tests for _handle_exception static method."""

    def test_401_unauthorized(self):
        """Test 401 Unauthorized exception."""
        status, data = ItsiRequest._handle_exception(Exception("401 Unauthorized"))
        assert status == 401
        assert "Authentication failed" in data["error"]

    def test_404_not_found(self):
        """Test 404 Not Found exception."""
        status, data = ItsiRequest._handle_exception(Exception("404 Not Found"))
        assert status == 404
        assert "not found" in data["error"].lower()

    def test_generic_exception(self):
        """Test generic exception returns 500."""
        status, data = ItsiRequest._handle_exception(Exception("Connection timeout"))
        assert status == 500
        assert "Connection timeout" in data["error"]

    def test_unauthorized_keyword(self):
        """Test exception containing 'Unauthorized' keyword."""
        status, data = ItsiRequest._handle_exception(Exception("Unauthorized access"))
        assert status == 401

    def test_not_found_keyword(self):
        """Test exception containing 'Not Found' keyword."""
        status, data = ItsiRequest._handle_exception(Exception("Not Found"))
        assert status == 404


# ===========================================================================
# TestEndToEnd – integration-style round-trip tests
# ===========================================================================


class TestEndToEnd:
    """Integration-style tests exercising full request → response cycle."""

    def test_get_json_round_trip(self):
        """Test full GET → JSON dict round trip."""
        payload = {"_key": "p1", "title": "My Policy"}
        conn = _mock_conn(body=json.dumps(payload))
        client = ItsiRequest(conn)

        status, data = client.get("/itoa_interface/notable_event_aggregation_policy/p1")

        assert status == 200
        assert data["title"] == "My Policy"

    def test_post_create_round_trip(self):
        """Test full POST create round trip."""
        conn = _mock_conn(body=json.dumps({"_key": "new123"}))
        client = ItsiRequest(conn)

        status, data = client.create_update(
            "/itoa_interface/notable_event_aggregation_policy",
            data={"title": "New Policy"},
        )

        assert status == 200
        assert data["_key"] == "new123"
        path = conn.send_request.call_args[0][0]
        assert "output_mode=json" in path

    def test_delete_round_trip(self):
        """Test full DELETE round trip."""
        conn = _mock_conn(status=200, body='{"deleted": true}')
        client = ItsiRequest(conn)

        status, data = client.delete_by_path("/itoa_interface/service/svc123")

        assert status == 200
        path = conn.send_request.call_args[0][0]
        assert "output_mode=json" in path

    def test_connection_exception_handled(self):
        """Test that connection exceptions are caught and normalised."""
        conn = MagicMock()
        conn.send_request.side_effect = Exception("Network error")
        client = ItsiRequest(conn)

        status, data = client.get("/anything")

        assert status == 500
        assert "Network error" in data["error"]

    def test_auth_exception_handled(self):
        """Test that 401 exceptions are caught and normalised."""
        conn = MagicMock()
        conn.send_request.side_effect = Exception("401 Unauthorized")
        client = ItsiRequest(conn)

        status, data = client.get("/anything")

        assert status == 401
        assert "Authentication failed" in data["error"]
