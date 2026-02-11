# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_api_client httpapi plugin."""


import base64
import io
from unittest.mock import MagicMock, patch


class MockConnection:
    """Mock connection object for testing HttpApi."""

    def __init__(self):
        self.messages = []
        self._options = {}

    def queue_message(self, level, message):
        """Mock queue_message method."""
        self.messages.append((level, message))

    def get_option(self, name):
        """Mock get_option method."""
        if name in self._options:
            return self._options[name]
        raise KeyError(f"Option {name} not found")

    def set_option(self, name, value):
        """Set an option for testing."""
        self._options[name] = value

    def send(self, path, data, method="GET", headers=None):
        """Mock send method - should be overridden in tests."""
        raise NotImplementedError("send should be mocked in tests")


class MockHttpError(Exception):
    """Mock HTTP error with code attribute."""

    def __init__(self, code, message="HTTP Error"):
        self.code = code
        super().__init__(message)


# Import the HttpApi class for testing
from ansible_collections.splunk.itsi.plugins.httpapi.itsi_api_client import (
    BASE_HEADERS,
    HttpApi,
)


class TestHttpApiInit:
    """Tests for HttpApi.__init__ method."""

    def test_init_with_connection(self):
        """Test initialization with connection argument."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        assert api._connection == mock_conn
        assert api._cached_session_key is None
        assert api._cached_auth_headers is None
        assert api._auth_retry_attempted is False
        assert api._auth_method is None
        assert api._fallback_to_auto_session is False

    def test_init_with_kwargs(self):
        """Test initialization with connection in kwargs."""
        mock_conn = MockConnection()
        api = HttpApi(connection=mock_conn)

        assert api._connection == mock_conn


class TestHttpApiLogout:
    """Tests for HttpApi.logout method."""

    def test_logout_clears_cache(self):
        """Test that logout clears authentication cache."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        # Set some cached values
        api._cached_session_key = "test_key"
        api._cached_auth_headers = {"Authorization": "Bearer test"}

        api.logout()

        assert api._cached_session_key is None
        assert api._cached_auth_headers is None


class TestHttpApiHandleHttpError:
    """Tests for HttpApi.handle_httperror method."""

    def test_handle_401_with_session_key_auth_returns_true(self):
        """Test 401 with session_key auth triggers retry."""
        mock_conn = MockConnection()
        mock_conn.set_option("remote_user", "admin")
        mock_conn.set_option("password", "secret")
        api = HttpApi(mock_conn)
        api._auth_method = "session_key"
        api._auth_retry_attempted = False

        error = MockHttpError(401)
        result = api.handle_httperror(error)

        assert result is True
        assert api._auth_retry_attempted is True
        assert api._fallback_to_auto_session is True

    def test_handle_401_with_auto_session_auth_returns_true(self):
        """Test 401 with auto_session auth triggers retry."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._auth_method = "auto_session"
        api._auth_retry_attempted = False

        error = MockHttpError(401)
        result = api.handle_httperror(error)

        assert result is True
        assert api._auth_retry_attempted is True

    def test_handle_401_already_retried_returns_false(self):
        """Test 401 after retry attempt returns False."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._auth_method = "session_key"
        api._auth_retry_attempted = True  # Already attempted

        error = MockHttpError(401)
        result = api.handle_httperror(error)

        assert result is False

    def test_handle_401_with_bearer_token_returns_false(self):
        """Test 401 with bearer_token auth doesn't retry."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._auth_method = "bearer_token"
        api._auth_retry_attempted = False

        error = MockHttpError(401)
        result = api.handle_httperror(error)

        assert result is False

    def test_handle_401_with_basic_auth_returns_false(self):
        """Test 401 with basic_auth doesn't retry."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._auth_method = "basic_auth"
        api._auth_retry_attempted = False

        error = MockHttpError(401)
        result = api.handle_httperror(error)

        assert result is False

    def test_handle_non_401_error_returns_false(self):
        """Test non-401 errors return False."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._auth_method = "session_key"

        error = MockHttpError(500)
        result = api.handle_httperror(error)

        assert result is False

    def test_handle_error_without_code_attribute(self):
        """Test error without code attribute."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        error = Exception("Generic error")
        result = api.handle_httperror(error)

        assert result is False

    def test_handle_401_fallback_without_credentials(self):
        """Test 401 fallback when no credentials available."""
        mock_conn = MockConnection()
        # Don't set any credentials
        api = HttpApi(mock_conn)
        api._auth_method = "session_key"
        api._auth_retry_attempted = False

        error = MockHttpError(401)
        result = api.handle_httperror(error)

        assert result is True
        assert api._fallback_to_auto_session is False  # No fallback without creds


class TestHttpApiUpdateAuth:
    """Tests for HttpApi.update_auth method."""

    def test_update_auth_resets_retry_flag_on_success(self):
        """Test update_auth resets retry flag on successful response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._auth_retry_attempted = True

        mock_response = MagicMock()
        mock_response.status = 200

        result = api.update_auth(mock_response, "response text")

        assert result is None
        assert api._auth_retry_attempted is False

    def test_update_auth_keeps_retry_flag_on_error(self):
        """Test update_auth keeps retry flag on error response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._auth_retry_attempted = True

        mock_response = MagicMock()
        mock_response.status = 401

        result = api.update_auth(mock_response, "error text")

        assert result is None
        assert api._auth_retry_attempted is True

    def test_update_auth_response_without_status(self):
        """Test update_auth with response missing status attribute."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._auth_retry_attempted = True

        mock_response = MagicMock(spec=[])  # No status attribute

        result = api.update_auth(mock_response, "text")

        assert result is None


class TestHttpApiClearAuthCache:
    """Tests for HttpApi._clear_auth_cache method."""

    def test_clear_auth_cache(self):
        """Test _clear_auth_cache clears all cached data."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        api._cached_session_key = "cached_key"
        api._cached_auth_headers = {"Authorization": "Splunk cached_key"}

        api._clear_auth_cache()

        assert api._cached_session_key is None
        assert api._cached_auth_headers is None


class TestHttpApiExtractStatusHeadersText:
    """Tests for HttpApi._extract_status_headers_text method."""

    def test_extract_from_tuple_with_status(self):
        """Test extracting from tuple response with status."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {"Content-Type": "application/json"}

        mock_buffer = io.BytesIO(b'{"result": "success"}')

        response = (mock_meta, mock_buffer)
        status, headers, text = api._extract_status_headers_text(response)

        assert status == 200
        assert "Content-Type" in headers
        assert "result" in text

    def test_extract_from_tuple_with_code(self):
        """Test extracting from tuple response with code attribute."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock(spec=["code", "msg"])
        mock_meta.code = 404
        mock_meta.msg = MagicMock()
        mock_meta.msg.items.return_value = [("X-Custom", "value")]

        mock_buffer = io.BytesIO(b"Not found")

        response = (mock_meta, mock_buffer)
        status, headers, text = api._extract_status_headers_text(response)

        assert status == 404
        assert headers.get("X-Custom") == "value"

    def test_extract_from_tuple_with_getcode(self):
        """Test extracting from tuple response with getcode() method."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock(spec=["getcode"])
        mock_meta.getcode.return_value = 201

        mock_buffer = io.BytesIO(b"Created")

        response = (mock_meta, mock_buffer)
        status, headers, text = api._extract_status_headers_text(response)

        assert status == 201

    def test_extract_defaults_to_200_for_non_tuple_response(self):
        """Test that status defaults to 200 when response is not a tuple."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        # Non-tuple response - status remains None and defaults to 200
        response = io.BytesIO(b"OK")
        status, headers, text = api._extract_status_headers_text(response)

        assert status == 200
        assert headers == {}

    def test_extract_with_tuple_no_status_returns_0(self):
        """Test extraction when tuple meta has no status attributes returns 0.

        Note: This is an edge case in the implementation where the or-chain
        returns False (not None) when all status attributes are None/not callable,
        resulting in int(False) = 0.
        """
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = None
        mock_meta.code = None
        mock_meta.getcode = None  # Not callable, so callable() returns False

        mock_buffer = io.BytesIO(b"OK")

        response = (mock_meta, mock_buffer)
        status, headers, text = api._extract_status_headers_text(response)

        # The or-chain: None or None or False = False, and int(False) = 0
        assert status == 0

    def test_extract_with_strip_whitespace_true(self):
        """Test whitespace stripping when enabled."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {}

        mock_buffer = io.BytesIO(b"  \n  response text  \n  ")

        response = (mock_meta, mock_buffer)
        status, headers, text = api._extract_status_headers_text(response, strip_whitespace=True)

        assert text == "response text"

    def test_extract_with_strip_whitespace_false(self):
        """Test whitespace preserved when disabled."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {}

        mock_buffer = io.BytesIO(b"  response text  ")

        response = (mock_meta, mock_buffer)
        status, headers, text = api._extract_status_headers_text(response, strip_whitespace=False)

        assert text == "  response text  "

    def test_extract_with_non_iterable_headers(self):
        """Test extraction when headers can't be iterated."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = "not a dict"  # Invalid headers

        mock_buffer = io.BytesIO(b"response")

        response = (mock_meta, mock_buffer)
        status, headers, text = api._extract_status_headers_text(response)

        assert status == 200
        assert headers == {}


class TestHttpApiEnsureOutputModeJson:
    """Tests for HttpApi._ensure_output_mode_json method."""

    def test_adds_output_mode_to_get_without_query(self):
        """Test adding output_mode to GET without query string."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        result = api._ensure_output_mode_json("/api/path", "GET")

        assert result == "/api/path?output_mode=json"

    def test_adds_output_mode_to_get_with_query(self):
        """Test adding output_mode to GET with existing query string."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        result = api._ensure_output_mode_json("/api/path?existing=param", "GET")

        assert result == "/api/path?existing=param&output_mode=json"

    def test_does_not_add_to_post(self):
        """Test output_mode not added to POST requests."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        result = api._ensure_output_mode_json("/api/path", "POST")

        assert result == "/api/path"

    def test_does_not_duplicate_output_mode(self):
        """Test output_mode not duplicated if already present."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        result = api._ensure_output_mode_json("/api/path?output_mode=xml", "GET")

        assert result == "/api/path?output_mode=xml"


class TestHttpApiGetSessionKey:
    """Tests for HttpApi._get_session_key method."""

    def test_returns_cached_key_when_available(self):
        """Test returning cached session key."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._cached_session_key = "cached_key_123"

        result = api._get_session_key("admin", "secret")

        assert result == "cached_key_123"

    def test_bypasses_cache_on_force_refresh(self):
        """Test force_refresh bypasses cache."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._cached_session_key = "old_key"

        # Mock the connection.send to return XML response
        xml_response = b"<?xml version='1.0'?><response><sessionKey>new_key_456</sessionKey></response>"
        mock_buffer = io.BytesIO(xml_response)
        mock_meta = MagicMock()
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        result = api._get_session_key("admin", "secret", force_refresh=True)

        assert result == "new_key_456"
        assert api._cached_session_key == "new_key_456"

    def test_parses_xml_session_key(self):
        """Test parsing session key from XML response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        xml_response = b"<?xml version='1.0'?><response><sessionKey>test_session_key</sessionKey></response>"
        mock_buffer = io.BytesIO(xml_response)
        mock_meta = MagicMock()
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        result = api._get_session_key("admin", "secret")

        assert result == "test_session_key"

    def test_returns_empty_on_missing_session_key(self):
        """Test returning empty string when sessionKey not in response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        xml_response = b"<?xml version='1.0'?><response><error>Invalid credentials</error></response>"
        mock_buffer = io.BytesIO(xml_response)
        mock_meta = MagicMock()
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        result = api._get_session_key("admin", "wrongpassword")

        assert result == ""

    def test_returns_empty_on_exception(self):
        """Test returning empty string on exception."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        mock_conn.send = MagicMock(side_effect=Exception("Connection error"))

        result = api._get_session_key("admin", "secret")

        assert result == ""

    def test_handles_string_response(self):
        """Test handling direct string response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        xml_response = "<?xml version='1.0'?><response><sessionKey>string_key</sessionKey></response>"
        mock_conn.send = MagicMock(return_value=xml_response)

        result = api._get_session_key("admin", "secret")

        assert result == "string_key"

    def test_handles_bytes_response(self):
        """Test handling direct bytes response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        xml_response = b"<?xml version='1.0'?><response><sessionKey>bytes_key</sessionKey></response>"
        mock_conn.send = MagicMock(return_value=xml_response)

        result = api._get_session_key("admin", "secret")

        assert result == "bytes_key"

    def test_handles_buffer_with_getvalue(self):
        """Test handling buffer object with getvalue()."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        xml_response = b"<?xml version='1.0'?><response><sessionKey>buffer_key</sessionKey></response>"
        mock_buffer = io.BytesIO(xml_response)
        mock_conn.send = MagicMock(return_value=mock_buffer)

        result = api._get_session_key("admin", "secret")

        assert result == "buffer_key"


class TestHttpApiGetHeaders:
    """Tests for HttpApi.get_headers method."""

    def test_returns_cached_headers(self):
        """Test returning cached headers."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._cached_auth_headers = {"Authorization": "Bearer cached", "Accept": "application/json"}

        result = api.get_headers()

        assert result["Authorization"] == "Bearer cached"
        assert api._cached_auth_headers is not result  # Should return a copy

    def test_bearer_token_priority(self):
        """Test Bearer token has highest priority."""
        mock_conn = MockConnection()
        mock_conn.set_option("remote_user", "admin")
        mock_conn.set_option("password", "secret")
        api = HttpApi(mock_conn)

        with patch.object(api, "get_option", return_value="test_bearer_token"):
            result = api.get_headers()

        assert result["Authorization"] == "Bearer test_bearer_token"
        assert api._auth_method == "bearer_token"

    def test_explicit_session_key(self):
        """Test explicit session key authentication."""
        mock_conn = MockConnection()
        mock_conn.set_option("session_key", "explicit_session_key")
        api = HttpApi(mock_conn)

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.get_headers()

        assert result["Authorization"] == "Splunk explicit_session_key"
        assert api._auth_method == "session_key"

    def test_auto_session_key(self):
        """Test auto-retrieved session key."""
        mock_conn = MockConnection()
        mock_conn.set_option("remote_user", "admin")
        mock_conn.set_option("password", "secret")
        api = HttpApi(mock_conn)

        xml_response = b"<?xml version='1.0'?><response><sessionKey>auto_key</sessionKey></response>"
        mock_buffer = io.BytesIO(xml_response)
        mock_meta = MagicMock()
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.get_headers()

        assert result["Authorization"] == "Splunk auto_key"
        assert api._auth_method == "auto_session"

    def test_basic_auth_fallback(self):
        """Test Basic auth as fallback."""
        mock_conn = MockConnection()
        mock_conn.set_option("remote_user", "admin")
        mock_conn.set_option("password", "secret")
        api = HttpApi(mock_conn)

        # Mock session key retrieval to fail
        mock_conn.send = MagicMock(side_effect=Exception("Connection error"))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.get_headers()

        expected_creds = base64.b64encode(b"admin:secret").decode("ascii")
        assert result["Authorization"] == f"Basic {expected_creds}"
        assert api._auth_method == "basic_auth"

    def test_no_auth_returns_base_headers(self):
        """Test no auth returns base headers only."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.get_headers()

        assert "Authorization" not in result
        assert result["Accept"] == "application/json"

    def test_force_refresh_bypasses_cache(self):
        """Test force_refresh bypasses header cache."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._cached_auth_headers = {"Authorization": "Bearer old_token"}

        with patch.object(api, "get_option", return_value="new_token"):
            result = api.get_headers(force_refresh=True)

        assert result["Authorization"] == "Bearer new_token"

    def test_fallback_to_auto_session_skips_explicit_key(self):
        """Test _fallback_to_auto_session skips explicit session_key."""
        mock_conn = MockConnection()
        mock_conn.set_option("session_key", "explicit_key")
        mock_conn.set_option("remote_user", "admin")
        mock_conn.set_option("password", "secret")
        api = HttpApi(mock_conn)
        api._fallback_to_auto_session = True

        xml_response = b"<?xml version='1.0'?><response><sessionKey>auto_key</sessionKey></response>"
        mock_buffer = io.BytesIO(xml_response)
        mock_meta = MagicMock()
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.get_headers()

        # Should use auto session, not explicit session_key
        assert result["Authorization"] == "Splunk auto_key"
        assert api._fallback_to_auto_session is False  # Reset after success


class TestHttpApiSendRequest:
    """Tests for HttpApi.send_request method."""

    def test_send_request_success_enhanced_response(self):
        """Test successful request returns enhanced response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {"Content-Type": "application/json"}
        mock_buffer = io.BytesIO(b'{"result": "success"}')
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.send_request("/api/test", method="GET")

        assert result["status"] == 200
        assert "headers" in result
        assert result["body"] == '{"result": "success"}'

    def test_send_request_adds_leading_slash(self):
        """Test path gets leading slash added."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {}
        mock_buffer = io.BytesIO(b"{}")
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            api.send_request("api/test", method="GET")

        call_args = mock_conn.send.call_args
        assert call_args[0][0].startswith("/")

    def test_send_request_get_adds_output_mode(self):
        """Test GET requests get output_mode=json added."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {}
        mock_buffer = io.BytesIO(b"{}")
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            api.send_request("/api/test", method="GET")

        call_args = mock_conn.send.call_args
        assert "output_mode=json" in call_args[0][0]

    def test_send_request_post_no_output_mode(self):
        """Test POST requests don't get output_mode added."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {}
        mock_buffer = io.BytesIO(b"{}")
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            api.send_request("/api/test", method="POST", body='{"data": "test"}')

        call_args = mock_conn.send.call_args
        assert "output_mode" not in call_args[0][0]

    def test_send_request_merges_custom_headers(self):
        """Test custom headers are merged with auth headers."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {}
        mock_buffer = io.BytesIO(b"{}")
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            api.send_request("/api/test", method="GET", headers={"X-Custom": "value"})

        call_args = mock_conn.send.call_args
        headers = call_args[1]["headers"]
        assert headers["X-Custom"] == "value"
        assert headers["Accept"] == "application/json"

    def test_send_request_filters_sensitive_headers(self):
        """Test sensitive headers are filtered from response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = MagicMock()
        mock_meta.headers.items.return_value = [
            ("Content-Type", "application/json"),
            ("Authorization", "Bearer secret"),
            ("Set-Cookie", "session=abc"),
        ]
        mock_buffer = io.BytesIO(b"{}")
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.send_request("/api/test", method="GET")

        assert "Content-Type" in result["headers"]
        assert "Authorization" not in result["headers"]
        assert "Set-Cookie" not in result["headers"]

    def test_send_request_non_enhanced_response(self):
        """Test non-enhanced response returns body only."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {}
        mock_buffer = io.BytesIO(b"plain text response")
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.send_request("/api/test", method="GET", return_enhanced_response=False)

        assert result == "plain text response"

    def test_send_request_http_error_returns_error_response(self):
        """Test HTTP error returns error response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        mock_conn.send = MagicMock(side_effect=MockHttpError(500, "Server Error"))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.send_request("/api/test", method="GET")

        assert result["status"] == 500
        assert "error" in result["body"]

    def test_send_request_401_retry_success(self):
        """Test 401 error triggers retry with refreshed auth."""
        mock_conn = MockConnection()
        mock_conn.set_option("remote_user", "admin")
        mock_conn.set_option("password", "secret")
        api = HttpApi(mock_conn)
        api._auth_method = "auto_session"
        api._cached_session_key = "old_key"
        api._cached_auth_headers = {"Authorization": "Splunk old_key"}

        # First call raises 401, second succeeds
        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {}
        mock_buffer = io.BytesIO(b'{"success": true}')

        call_count = [0]

        def mock_send(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise MockHttpError(401, "Unauthorized")
            elif call_count[0] == 2:
                # Session key refresh call
                return io.BytesIO(b"<?xml version='1.0'?><response><sessionKey>new_key</sessionKey></response>")
            else:
                return (mock_meta, mock_buffer)

        mock_conn.send = MagicMock(side_effect=mock_send)

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.send_request("/api/test", method="GET")

        assert result["status"] == 200

    def test_send_request_401_retry_failure(self):
        """Test 401 retry that also fails returns error."""
        mock_conn = MockConnection()
        mock_conn.set_option("remote_user", "admin")
        mock_conn.set_option("password", "secret")
        api = HttpApi(mock_conn)
        api._auth_method = "auto_session"

        # Track calls to understand the flow:
        # 1. First API call -> raises 401
        # 2. Session key refresh call -> returns invalid XML (no sessionKey)
        # 3. Retry API call -> also raises 401
        call_count = [0]

        def mock_send(path, *args, **kwargs):
            call_count[0] += 1
            if "/services/auth/login" in path:
                # Session key refresh - return invalid response (no sessionKey)
                return io.BytesIO(b"<?xml version='1.0'?><response><error>Invalid</error></response>")
            # API calls raise 401
            raise MockHttpError(401, "Unauthorized")

        mock_conn.send = MagicMock(side_effect=mock_send)

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.send_request("/api/test", method="GET")

        assert result["status"] == 401

    def test_send_request_resets_retry_flag(self):
        """Test retry flag is reset at start of request."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)
        api._auth_retry_attempted = True

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {}
        mock_buffer = io.BytesIO(b"{}")
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            api.send_request("/api/test", method="GET")

        # After successful request, flag should be False
        assert api._auth_retry_attempted is False

    def test_send_request_exception_returns_error(self):
        """Test general exception returns error response (enhanced)."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        with patch.object(api, "get_headers", side_effect=Exception("Unexpected error")):
            # Must explicitly request enhanced response for outer exceptions
            # (the outer exception handler defaults to False for backward compatibility)
            result = api.send_request("/api/test", method="GET", return_enhanced_response=True)

        assert result["status"] == 500
        assert "Internal error" in result["body"]

    def test_send_request_exception_returns_string_by_default(self):
        """Test general exception returns string when enhanced not requested."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        with patch.object(api, "get_headers", side_effect=Exception("Unexpected error")):
            result = api.send_request("/api/test", method="GET")

        # Outer exception handler defaults to non-enhanced (string) response
        assert isinstance(result, str)
        assert "Internal error" in result

    def test_send_request_exception_non_enhanced(self):
        """Test exception with non-enhanced response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        with patch.object(api, "get_headers", side_effect=Exception("Error")):
            result = api.send_request("/api/test", method="GET", return_enhanced_response=False)

        assert "Internal error" in result

    def test_send_request_with_strip_whitespace_false(self):
        """Test strip_whitespace=False preserves whitespace."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_meta.status = 200
        mock_meta.headers = {}
        mock_buffer = io.BytesIO(b"  spaced content  ")
        mock_conn.send = MagicMock(return_value=(mock_meta, mock_buffer))

        with patch.object(api, "get_option", side_effect=KeyError("token")):
            result = api.send_request("/api/test", method="GET", strip_whitespace=False)

        assert result["body"] == "  spaced content  "


class TestHttpApiHandleResponse:
    """Tests for HttpApi._handle_response method."""

    def test_handle_string_response(self):
        """Test handling string response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        result = api._handle_response("string response")

        assert result == "string response"

    def test_handle_bytes_response(self):
        """Test handling bytes response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        result = api._handle_response(b"bytes response")

        assert result == "bytes response"

    def test_handle_tuple_with_buffer_getvalue(self):
        """Test handling tuple with buffer.getvalue()."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_buffer = io.BytesIO(b"buffer content")

        result = api._handle_response((mock_meta, mock_buffer))

        assert result == "buffer content"

    def test_handle_tuple_with_buffer_read(self):
        """Test handling tuple with buffer.read()."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_buffer = MagicMock(spec=["read", "seek"])
        mock_buffer.read.return_value = b"read content"

        result = api._handle_response((mock_meta, mock_buffer))

        assert result == "read content"

    def test_handle_tuple_with_string_buffer(self):
        """Test handling tuple with string buffer."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()

        result = api._handle_response((mock_meta, "string buffer"))

        assert result == "string buffer"

    def test_handle_tuple_with_bytes_buffer(self):
        """Test handling tuple with bytes buffer."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()

        result = api._handle_response((mock_meta, b"bytes buffer"))

        assert result == "bytes buffer"

    def test_handle_tuple_with_generic_buffer(self):
        """Test handling tuple with generic buffer (str conversion)."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_buffer = 12345  # Something that needs str() conversion

        result = api._handle_response((mock_meta, mock_buffer))

        assert result == "12345"

    def test_handle_stringio_response(self):
        """Test handling StringIO response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        response = io.StringIO("stringio content")

        result = api._handle_response(response)

        assert result == "stringio content"

    def test_handle_bytesio_response(self):
        """Test handling BytesIO response."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        response = io.BytesIO(b"bytesio content")

        result = api._handle_response(response)

        assert result == "bytesio content"

    def test_handle_file_like_response(self):
        """Test handling file-like response with read()."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_file = MagicMock(spec=["read"])
        mock_file.read.return_value = "file content"

        result = api._handle_response(mock_file)

        assert result == "file content"

    def test_handle_dict_response(self):
        """Test handling dict response (converts to JSON)."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        response = {"key": "value"}

        result = api._handle_response(response)

        assert result == '{"key": "value"}'

    def test_handle_list_response(self):
        """Test handling list response (converts to JSON)."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        response = [1, 2, 3]

        result = api._handle_response(response)

        assert result == "[1, 2, 3]"

    def test_handle_generic_response(self):
        """Test handling generic response (str conversion)."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        result = api._handle_response(12345)

        assert result == "12345"

    def test_handle_response_strip_whitespace_true(self):
        """Test whitespace stripping enabled."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        result = api._handle_response("  whitespace  ", strip_whitespace=True)

        assert result == "whitespace"

    def test_handle_response_strip_whitespace_false(self):
        """Test whitespace stripping disabled."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        result = api._handle_response("  whitespace  ", strip_whitespace=False)

        assert result == "  whitespace  "

    def test_handle_buffer_seek_failure(self):
        """Test handling buffer when seek fails."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_buffer = MagicMock()
        mock_buffer.seek.side_effect = OSError("Seek failed")
        mock_buffer.getvalue.return_value = b"content despite seek failure"

        result = api._handle_response((mock_meta, mock_buffer))

        assert result == "content despite seek failure"

    def test_handle_buffer_read_after_seek_failure(self):
        """Test handling buffer.read() after seek failure."""
        mock_conn = MockConnection()
        api = HttpApi(mock_conn)

        mock_meta = MagicMock()
        mock_buffer = MagicMock(spec=["read", "seek"])
        mock_buffer.seek.side_effect = AttributeError("No seek")
        mock_buffer.read.return_value = b"read after failed seek"

        result = api._handle_response((mock_meta, mock_buffer))

        assert result == "read after failed seek"


class TestBaseHeaders:
    """Tests for BASE_HEADERS constant."""

    def test_base_headers_content(self):
        """Test BASE_HEADERS has expected content."""
        assert BASE_HEADERS["Accept"] == "application/json"
        assert BASE_HEADERS["Content-Type"] == "application/json"
