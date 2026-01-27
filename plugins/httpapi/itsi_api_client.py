# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers

from __future__ import annotations

__metaclass__ = type

DOCUMENTATION = r"""
---
author: Ansible Ecosystem Engineering team (@ansible)
name: itsi_api_client
short_description: HttpApi Plugin for Splunk ITSI
description:
  - Provides a persistent HTTP(S) connection and authentication for the Splunk ITSI REST API.
  - Modules call C(conn.send_request(path, data, method="GET")) and this plugin injects authentication and JSON headers.
  - Returns response format with status, headers, and body structure for full HTTP metadata access.
  - Automatically adds C(output_mode=json) to GET requests for consistent JSON responses from Splunk.
  - Compatible with both core httpapi and ansible.netcommon.httpapi connections for advanced features.
version_added: "1.0.0"
options:
  token:
    description:
      - Pre-created Splunk authentication token to be sent as C(Authorization Bearer <token>).
      - Use for direct endpoint access with Splunk authentication tokens (Splunk Enterprise 7.3+).
      - These tokens must be created in Splunk and have token authentication enabled.
      - This is the highest priority authentication method.
    type: str
    vars:
      - name: ansible_httpapi_token
  session_key:
    description:
      - Pre-created Splunk session key from C(/services/auth/login) to be sent as C(Authorization Splunk <sessionKey>).
      - Use when you have already obtained a session key through external means.
      - If this authentication fails with 401, the plugin will automatically fallback to auto-retrieved session key.
    type: str
    vars:
      - name: ansible_httpapi_session_key
  remote_user:
    description:
      - Username for Splunk authentication.
      - Used for auto-retrieved session key authentication via C(/services/auth/login) endpoint.
      - Also used as fallback for Basic authentication if session key retrieval fails.
      - When combined with password, enables automatic session key management with caching and refresh.
    type: str
    vars:
      - name: ansible_user
  password:
    description:
      - Password for Splunk authentication.
      - Used with remote_user for auto-retrieved session key authentication.
      - Also used as fallback for Basic authentication if session key retrieval fails.
      - Session keys obtained this way are automatically cached and refreshed on 401 errors.
    type: str
    vars:
      - name: ansible_httpapi_pass
notes:
  - Basic configuration requires C(ansible_connection=httpapi) and C(ansible_network_os=splunk.itsi.itsi_api_client).
  - Advanced configuration uses C(ansible_connection=ansible.netcommon.httpapi) for proxy, SSL certs, timeouts, and connection persistence.
  - Always returns enhanced response format with structure containing status code, headers dict, and body string.
  - Authentication methods tried in priority order are Bearer token, explicit session key, auto-retrieved session key, Basic auth.
  - Auto-retrieved session keys are obtained via C(/services/auth/login) using remote_user and password credentials.
  - Session keys are automatically cached per connection instance and refreshed on 401 Unauthorized errors.
  - If explicit session_key fails with 401, the plugin will fallback to auto-retrieved session key if credentials are available.
  - Basic authentication is used as final fallback when session key methods are not available or fail.
  - Response body text has leading/trailing whitespace stripped by default for clean JSON parsing.
"""

EXAMPLES = r"""
# Basic HTTP API Configuration (Core Ansible)
# [splunk]
# splunk.example.com
# [splunk:vars]
# ansible_connection=httpapi
# ansible_network_os=splunk.itsi.itsi_api_client
# ansible_httpapi_use_ssl=true
# ansible_httpapi_port=8089
# ansible_httpapi_validate_certs=false

# Advanced HTTP API Configuration (ansible.netcommon.httpapi)
# Provides proxy support, client certificates, custom timeouts, connection persistence
# [splunk_advanced]
# splunk-enterprise.example.com
# [splunk_advanced:vars]
# ansible_connection=ansible.netcommon.httpapi
# ansible_network_os=splunk.itsi.itsi_api_client
# ansible_httpapi_use_ssl=true
# ansible_httpapi_port=8089
# ansible_httpapi_validate_certs=true
# ansible_httpapi_ca_path=/etc/ssl/certs/ca-bundle.crt
# ansible_httpapi_client_cert=/path/to/client.pem
# ansible_httpapi_client_key=/path/to/client-key.pem
# ansible_httpapi_use_proxy=true
# ansible_httpapi_http_agent="SplunkITSI-Ansible/1.0.0"
# ansible_command_timeout=60
# ansible_connect_timeout=30

# Choose one auth method for either configuration:

# Method 1: Bearer Token (highest priority)
# ansible_httpapi_token=eyJraWQiOiJzcGx1bmsuc2VjcmV0IiwiYWxnIjoiSFM1MTIi...

# Method 2: Pre-created Session Key
# ansible_httpapi_session_key=192fd3e470d2b0cc...

# Method 3: Auto-retrieved Session Key (recommended for username/password)
# ansible_user=admin
# ansible_httpapi_pass=secret
# (Plugin automatically calls /services/auth/login, caches and refreshes session key)

# Method 4: Basic Auth (fallback)
# ansible_user=admin
# ansible_httpapi_pass=secret
# (Used only if session key retrieval fails)
"""

import base64
import json

from ansible.plugins.httpapi import HttpApiBase

BASE_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}


class HttpApi(HttpApiBase):
    """HttpApi plugin for Splunk ITSI with token/session_key/basic auth and JSON defaults.

    Compatible with both core httpapi and ansible.netcommon.httpapi connections.
    """

    def __init__(self, *args, **kwargs):
        """Initialize per-instance authentication cache.

        Compatible with both core httpapi and ansible.netcommon.httpapi constructors.
        """
        # Call parent constructor with all provided arguments
        super().__init__(*args, **kwargs)

        # Store connection reference if provided (for netcommon compatibility)
        self._connection = args[0] if args else kwargs.get("connection")

        # Authentication cache to avoid repeated logins (instance-level attributes)
        self._cached_session_key = None
        self._cached_auth_headers = None
        self._auth_retry_attempted = False  # Track if we've already tried refresh
        self._auth_method = None  # Track which auth method we're using
        self._fallback_to_auto_session = False  # Flag for explicit session_key 401 fallback

    def logout(self):
        """Logout method for ansible.netcommon.httpapi compatibility."""
        # Clear cached authentication on logout
        self._clear_auth_cache()

    def handle_httperror(self, exc):
        """Handle HTTP errors for ansible.netcommon.httpapi compatibility.

        Returns:
        - True: Retry the request once with refreshed authentication
        - False: Raise the original exception
        - Response-like object: Use this as the response
        """
        error_status = getattr(exc, "code", None)

        # Only handle 401 errors with retry logic
        if not self._should_retry_401(error_status or 0):
            if error_status == 401:
                self.connection.queue_message(
                    "vvv",
                    "ITSI HttpApi: 401 after refresh attempt or non-session auth, propagating error",
                )
            return False

        self.connection.queue_message("vvv", "ITSI HttpApi: 401 detected, attempting auth refresh")
        self._auth_retry_attempted = True
        self._setup_session_fallback()
        self._clear_auth_cache()
        return True

    def update_auth(self, response, response_text):
        """Update authentication tokens for ansible.netcommon.httpapi compatibility.

        Args:
            response: HTTP response object
            response_text: Response text content

        Returns:
            dict: New authentication headers or None
        """
        # Reset retry flag on successful response
        if hasattr(response, "status") and 200 <= response.status < 300:
            self._auth_retry_attempted = False

        # ITSI doesn't provide auth token refresh in responses
        # Authentication refresh is handled in handle_httperror()
        return None

    def _clear_auth_cache(self):
        """Clear cached authentication data."""
        self.connection.queue_message("vvv", "ITSI HttpApi: Clearing authentication cache")
        self._cached_session_key = None
        self._cached_auth_headers = None

    def _extract_status_headers_text(self, resp, strip_whitespace=True):
        """Extract HTTP status, headers, and body text from response.

        Args:
            resp: Response from connection.send() - format varies by connection type
            strip_whitespace: If True, strip leading/trailing whitespace from response body

        Returns:
            tuple: (status_code, headers_dict, response_text)
        """
        status = None
        headers_map = {}

        # netcommon: (response, buffer)
        if isinstance(resp, tuple) and len(resp) == 2:
            meta, _unused_buffer = resp
            # status extraction across variants
            status = (
                getattr(meta, "status", None)
                or getattr(meta, "code", None)
                or (callable(getattr(meta, "getcode", None)) and meta.getcode())
            )
            # headers normalization
            raw_headers = getattr(meta, "headers", None) or getattr(meta, "msg", None)
            try:
                if raw_headers and hasattr(raw_headers, "items"):
                    # HTTPMessage-like: use .items() to build a dict of str->str
                    headers_map = {str(k): str(v) for k, v in raw_headers.items()}
            except Exception:
                headers_map = {}

        text = self._handle_response(resp, strip_whitespace=strip_whitespace)
        # fall back to 200 if transport doesn't expose status
        return (int(status) if status is not None else 200), headers_map, text

    def _ensure_output_mode_json(self, path: str, method: str) -> str:
        """Ensure JSON output mode for GET requests."""
        if method == "GET" and "output_mode=" not in path:
            sep = "&" if "?" in path else "?"
            path = f"{path}{sep}output_mode=json"
        return path

    def _get_session_key(self, username: str, password: str, force_refresh: bool = False) -> str:
        """Get Splunk session key using /services/auth/login endpoint.

        Args:
            username: Splunk username
            password: Splunk password
            force_refresh: If True, bypass cache and get new session key

        Returns:
            str: Session key or empty string if failed
        """
        # Return cached session key unless force refresh
        if not force_refresh and self._cached_session_key:
            self.connection.queue_message("vvv", "ITSI HttpApi: Using cached session key")
            return self._cached_session_key

        try:
            import urllib.parse
            import xml.etree.ElementTree as ET

            self.connection.queue_message(
                "vvv",
                f"ITSI HttpApi: Attempting to get session key for user: {username} (force_refresh={force_refresh})",
            )

            # Prepare login data
            login_data = urllib.parse.urlencode(
                {
                    "username": username,
                    "password": password,
                },
            ).encode("utf-8")

            # Login request Basic headers
            login_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/xml",
            }

            # Get session key via /services/auth/login
            response = self.connection.send("/services/auth/login", login_data, method="POST", headers=login_headers)

            # Extract response content
            if isinstance(response, tuple) and len(response) == 2:
                _unused_meta, buffer = response
                response_text = buffer.getvalue() if hasattr(buffer, "getvalue") else str(buffer)  # type: ignore
            elif hasattr(response, "getvalue"):
                response_text = response.getvalue()  # type: ignore
            elif isinstance(response, (str, bytes)):
                response_text = response.decode("utf-8") if isinstance(response, bytes) else response
            else:
                response_text = str(response)

            # Parse XML response to extract session key
            root = ET.fromstring(response_text)
            session_key_elem = root.find(".//sessionKey")
            if session_key_elem is not None and session_key_elem.text:
                session_key = session_key_elem.text.strip()

                # Cache the new session key
                self._cached_session_key = session_key
                self.connection.queue_message("vvv", "ITSI HttpApi: Successfully obtained and cached session key")
                return session_key
            else:
                self.connection.queue_message("vvv", "ITSI HttpApi: No sessionKey found in response")
                return ""

        except Exception as e:
            self.connection.queue_message("vvv", f"ITSI HttpApi: Session key retrieval failed: {e}")
            return ""

    def get_headers(self, force_refresh: bool = False):
        """Get headers with authentication for Splunk ITSI API requests.

        Args:
            force_refresh: If True, bypass cache and refresh authentication

        Returns:
            dict: Headers with authentication (always returns a copy)
        """
        # Return cached headers unless force refresh
        if not force_refresh and self._cached_auth_headers:
            self.connection.queue_message("vvv", "ITSI HttpApi: Using cached authentication headers")
            return self._cached_auth_headers.copy()

        headers = BASE_HEADERS.copy()

        # 1. Try Bearer token first (highest priority) - pre-created Splunk tokens
        try:
            token = self.get_option("token")
            if token:
                self.connection.queue_message("vvv", "ITSI HttpApi: Using Bearer token authentication")
                headers["Authorization"] = f"Bearer {token}"
                self._auth_method = "bearer_token"
                self._cached_auth_headers = headers.copy()
                return headers.copy()
        except Exception as e:
            self.connection.queue_message("vvv", f"ITSI HttpApi: Token retrieval failed: {e}")

        # 2. Try explicit pre-defined session key (ansible_httpapi_session_key)
        # Skip this if we're falling back due to 401 with explicit session key
        if not self._fallback_to_auto_session:
            try:
                session_key = self.connection.get_option("session_key")
                if session_key:
                    self.connection.queue_message("vvv", "ITSI HttpApi: Using explicit session key")
                    headers["Authorization"] = f"Splunk {session_key}"
                    self._auth_method = "session_key"
                    self._cached_auth_headers = headers.copy()
                    return headers.copy()
            except Exception:
                pass

        # 3. Try auto-session or basic auth using credentials
        try:
            user = self.connection.get_option("remote_user")
            password = self.connection.get_option("password")
            if user and password:
                # Try auto-session first
                session_key = self._get_session_key(user, password, force_refresh=force_refresh)
                if session_key:
                    self.connection.queue_message("vvv", "ITSI HttpApi: Using auto-retrieved session key")
                    headers["Authorization"] = f"Splunk {session_key}"
                    self._auth_method = "auto_session"
                    self._fallback_to_auto_session = False
                else:
                    # Fallback to basic auth
                    self.connection.queue_message("vvv", "ITSI HttpApi: Using Basic authentication")
                    credentials = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
                    headers["Authorization"] = f"Basic {credentials}"
                    self._auth_method = "basic_auth"
                self._cached_auth_headers = headers.copy()
                return headers.copy()
        except Exception:
            pass

        return headers.copy()

    # ---------- Response formatting helpers ----------

    def _filter_sensitive_headers(self, headers_map: dict) -> dict:
        """Filter out sensitive headers from response."""
        sensitive_keys = ["authorization", "set-cookie", "cookie"]
        return {k: v for k, v in headers_map.items() if k.lower() not in sensitive_keys}

    def _build_response(self, status: int, headers_map: dict, body: str, return_enhanced: bool):
        """Build response in either enhanced or plain format."""
        if return_enhanced:
            return {
                "status": status,
                "headers": self._filter_sensitive_headers(headers_map),
                "body": body,
            }
        return body

    def _build_error_response(self, status: int, error_info: dict, return_enhanced: bool):
        """Build error response in either enhanced or plain format."""
        error_body = json.dumps(error_info)
        if return_enhanced:
            return {
                "status": status,
                "headers": {},
                "body": error_body,
            }
        return error_body

    def _should_retry_401(self, error_status: int) -> bool:
        """Check if a 401 error should trigger an auth retry."""
        return error_status == 401 and not self._auth_retry_attempted and self._auth_method in ["session_key", "auto_session"]

    def _setup_session_fallback(self):
        """Setup fallback to auto-session if explicit session_key fails."""
        if self._auth_method != "session_key":
            return
        try:
            user = self.connection.get_option("remote_user")
            password = self.connection.get_option("password")
            if user and password:
                self.connection.queue_message("vvv", "ITSI HttpApi: Explicit session_key failed, falling back to auto-login")
                self._fallback_to_auto_session = True
        except Exception:
            pass

    def _attempt_auth_retry(self, path: str, body: str, method: str, message_kwargs: dict, strip_whitespace: bool):
        """Attempt to retry request with refreshed authentication.

        Returns:
            tuple: (success: bool, result: response or None, error_status: int or None)
        """
        self.connection.queue_message("vvv", "ITSI HttpApi: 401 detected, attempting auth refresh")
        self._auth_retry_attempted = True
        self._setup_session_fallback()

        # Clear cache and get fresh headers
        self._clear_auth_cache()
        fresh_auth_headers = self.get_headers(force_refresh=True)
        fresh_headers = {**fresh_auth_headers, **message_kwargs.get("headers", {})}

        try:
            self.connection.queue_message("vvv", "ITSI HttpApi: Retrying request with refreshed auth")
            retry_response = self.connection.send(path, body, method=method, headers=fresh_headers)
            retry_status, retry_headers, retry_text = self._extract_status_headers_text(
                retry_response,
                strip_whitespace=strip_whitespace,
            )
            self.connection.queue_message("vvv", f"ITSI HttpApi: Retry successful, status {retry_status}")
            self._auth_retry_attempted = False
            return True, (retry_status, retry_headers, retry_text), None
        except Exception as retry_error:
            retry_status = getattr(retry_error, "code", 500)
            self.connection.queue_message("vvv", f"ITSI HttpApi: Retry also failed: {str(retry_error)}")
            return False, None, retry_status

    def _handle_http_error(
        self,
        http_error: Exception,
        path: str,
        body: str,
        method: str,
        message_kwargs: dict,
        strip_whitespace: bool,
        return_enhanced: bool,
    ):
        """Handle HTTP request errors including 401 retry logic."""
        error_msg = str(http_error)
        self.connection.queue_message("vvv", f"ITSI HttpApi: HTTP request failed: {error_msg}")

        error_status = getattr(http_error, "code", None) or 500

        # Attempt 401 retry if applicable
        if self._should_retry_401(error_status):
            success, result, new_status = self._attempt_auth_retry(
                path,
                body,
                method,
                message_kwargs,
                strip_whitespace,
            )
            if success:
                retry_status, retry_headers, retry_text = result
                return self._build_response(retry_status, retry_headers, retry_text, return_enhanced)
            if new_status:
                error_status = new_status

        # Return error response
        error_info = {"error": "HTTP request failed", "details": error_msg, "path": path, "method": method}
        return self._build_error_response(int(error_status), error_info, return_enhanced)

    # ---------- main override ----------

    def send_request(self, data, *extra_args, **message_kwargs):  # type: ignore[override]
        """HttpApiBase.send_request implementation.

        Note: HttpApiBase.send_request is declared to return None, but for RPC compatibility
        we need to return the response data as a string. The type: ignore comment suppresses
        the type checker warning while maintaining functional compatibility.
        """
        self.connection.queue_message("vvv", "ITSI HttpApi: Starting send_request")
        self._auth_retry_attempted = False

        try:
            return self._execute_request(data, message_kwargs)
        except Exception as e:
            return self._handle_unexpected_error(e, message_kwargs)

    def _execute_request(self, data, message_kwargs: dict):
        """Execute the HTTP request with proper setup and error handling."""
        # Extract and prepare parameters
        path = data
        method = message_kwargs.get("method", "GET").upper()
        body = message_kwargs.get("body", "")
        return_enhanced = bool(message_kwargs.get("return_enhanced_response", True))
        strip_whitespace = bool(message_kwargs.get("strip_whitespace", True))

        self.connection.queue_message("vvv", f"ITSI HttpApi: method={method}, path={path}")

        # Prepare path and headers
        path = self._ensure_output_mode_json(path, method)
        if not path.startswith("/"):
            path = "/" + path

        auth_headers = self.get_headers()
        headers = {**auth_headers, **message_kwargs.get("headers", {})}

        self.connection.queue_message("vvv", "ITSI HttpApi: Making HTTP request")

        try:
            response = self.connection.send(path, body, method=method, headers=headers)
            status, headers_map, response_text = self._extract_status_headers_text(
                response,
                strip_whitespace=strip_whitespace,
            )
            self.connection.queue_message("vvv", f"ITSI HttpApi: Status {status}, response length: {len(response_text)}")
            self._auth_retry_attempted = False
            return self._build_response(status, headers_map, response_text, return_enhanced)

        except Exception as http_error:
            return self._handle_http_error(
                http_error,
                path,
                body,
                method,
                message_kwargs,
                strip_whitespace,
                return_enhanced,
            )

    def _handle_unexpected_error(self, error: Exception, message_kwargs: dict):
        """Handle unexpected errors in send_request."""
        import traceback

        error_details = traceback.format_exc()
        self.connection.queue_message("vvv", f"ITSI HttpApi: Exception caught: {str(error)}")
        self.connection.queue_message("vvv", f"ITSI HttpApi: Traceback: {error_details}")

        return_enhanced = bool(message_kwargs.get("return_enhanced_response", False))
        error_info = {"error": "Internal error", "details": str(error).replace('"', '\\"')}
        return self._build_error_response(500, error_info, return_enhanced)

    def _to_string(self, content) -> str:
        """Convert content to string, decoding bytes if necessary."""
        if isinstance(content, bytes):
            return content.decode("utf-8")
        if isinstance(content, (list, dict)):
            return json.dumps(content)
        return str(content) if content is not None else ""

    def _seek_buffer(self, buffer):
        """Try to rewind buffer to beginning, ignoring errors."""
        try:
            buffer.seek(0)
        except (AttributeError, OSError):
            pass

    def _read_buffer(self, buffer) -> str:
        """Read content from a buffer object."""
        self._seek_buffer(buffer)
        if hasattr(buffer, "getvalue"):
            return self._to_string(buffer.getvalue())
        if hasattr(buffer, "read"):
            return self._to_string(buffer.read())
        return self._to_string(buffer)

    def _handle_response(self, response_content, strip_whitespace=True):
        """Handle response content from Splunk ITSI API.

        Args:
            response_content: Response content from connection.send()
            strip_whitespace: If True, strip leading/trailing whitespace (default True)

        Compatible with both core httpapi and ansible.netcommon.httpapi response formats.
        """
        self.connection.queue_message("vvv", f"ITSI HttpApi: _handle_response received type: {type(response_content)}")

        # Handle different response formats
        if isinstance(response_content, (str, bytes)):
            response_text = self._to_string(response_content)
        elif isinstance(response_content, tuple) and len(response_content) == 2:
            # ansible.netcommon.httpapi returns (response, buffer)
            _unused_meta, buffer = response_content
            response_text = self._read_buffer(buffer)
        elif hasattr(response_content, "getvalue") or hasattr(response_content, "read"):
            response_text = self._read_buffer(response_content)
        else:
            response_text = self._to_string(response_content)

        if strip_whitespace:
            response_text = response_text.strip()

        self.connection.queue_message("vvv", f"ITSI HttpApi: _handle_response returning: {repr(response_text)[:200]}")
        return response_text
