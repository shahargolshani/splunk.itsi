# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026, Splunk ITSI Ansible Collection maintainers
"""Splunk ITSI request utilities for Ansible modules."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode


class ItsiRequest:
    """Handle HTTP requests to the Splunk ITSI REST API.

    Provides a consistent interface for modules to interact with the ITSI API
    via the itsi_api_client httpapi plugin. Handles query parameter building,
    request body preparation, response parsing, and error handling.

    Args:
        connection: The Ansible Connection object for API requests.
    """

    def __init__(self, connection: Any) -> None:
        """Initialize ItsiRequest.

        Args:
            connection: The Connection object for API requests.
        """
        self.connection = connection

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        payload: dict | list | str | None = None,
        use_form_data: bool = False,
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[int, Any]:
        """Send a request via the itsi_api_client httpapi plugin.

        Args:
            method: HTTP method (GET, POST, DELETE).
            path: API path.
            params: Query parameters dict. None/empty values are filtered out.
            payload: Request body data (dict, list, or string).
            use_form_data: If True, send payload as URL-encoded form data.
            extra_headers: Additional headers to include in the request.

        Returns:
            tuple: (status_code, parsed_response_data)
        """
        method = method.upper()
        path = self._build_query_string(path, params)
        body, headers = self._prepare_request(payload, use_form_data, extra_headers)

        try:
            result = self.connection.send_request(
                path,
                method=method,
                body=body,
                headers=headers,
            )
            return self._parse_response(result)
        except Exception as exc:
            return self._handle_exception(exc)

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        """Perform a GET request.

        Args:
            path: API path.
            params: Query parameters dict.

        Returns:
            tuple: (status_code, parsed_response_data)
        """
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        payload: dict | list | str | None = None,
        use_form_data: bool = False,
    ) -> tuple[int, Any]:
        """Perform a POST request.

        Args:
            path: API path.
            params: Query parameters dict.
            payload: Request body data.
            use_form_data: If True, send payload as URL-encoded form data.

        Returns:
            tuple: (status_code, parsed_response_data)
        """
        return self.request(
            "POST",
            path,
            params=params,
            payload=payload,
            use_form_data=use_form_data,
        )

    def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        """Perform a DELETE request.

        Args:
            path: API path.
            params: Query parameters dict.

        Returns:
            tuple: (status_code, parsed_response_data)
        """
        return self.request("DELETE", path, params=params)

    def get_by_path(
        self,
        rest_path: str,
        query_params: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        """GET with automatic output_mode=json.

        Args:
            rest_path: REST API path.
            query_params: Additional query parameters. Values of None are omitted.

        Returns:
            tuple: (status_code, parsed_response_data)
        """
        params: dict[str, Any] = {"output_mode": "json"}
        if query_params:
            for key, value in query_params.items():
                if value is not None:
                    params[key] = value
        return self.get(rest_path, params=params)

    def delete_by_path(self, rest_path: str) -> tuple[int, Any]:
        """DELETE with automatic output_mode=json.

        Args:
            rest_path: REST API path.

        Returns:
            tuple: (status_code, parsed_response_data)
        """
        return self.delete(rest_path, params={"output_mode": "json"})

    def create_update(
        self,
        rest_path: str,
        data: dict | list | str | None = None,
        query_params: dict[str, Any] | None = None,
        use_form_data: bool = False,
    ) -> tuple[int, Any]:
        """POST for create/update with automatic output_mode=json.

        Args:
            rest_path: REST API path.
            data: Request body data.
            query_params: Additional query parameters. Values of None are omitted.
            use_form_data: If True, send data as URL-encoded form data.

        Returns:
            tuple: (status_code, parsed_response_data)
        """
        params: dict[str, Any] = {"output_mode": "json"}
        if query_params:
            for key, value in query_params.items():
                if value is not None:
                    params[key] = value
        return self.post(
            rest_path,
            params=params,
            payload=data,
            use_form_data=use_form_data,
        )

    @staticmethod
    def _build_query_string(path: str, params: dict[str, Any] | None) -> str:
        """Append query parameters to a path.

        Args:
            path: API path.
            params: Query parameters. None/empty values are filtered out.

        Returns:
            Path with query string appended.
        """
        if not params:
            return path

        query_params = {k: v for k, v in params.items() if v is not None and v != ""}
        if not query_params:
            return path

        sep = "&" if "?" in path else "?"
        return f"{path}{sep}{urlencode(query_params, doseq=True)}"

    @staticmethod
    def _prepare_request(
        payload: dict | list | str | None,
        use_form_data: bool,
        extra_headers: dict[str, str] | None,
    ) -> tuple[str, dict[str, str]]:
        """Prepare request body and headers.

        Args:
            payload: Request body data.
            use_form_data: If True, encode payload as form data.
            extra_headers: Additional headers to include.

        Returns:
            tuple: (body_string, headers_dict)
        """
        headers: dict[str, str] = {}

        if use_form_data and isinstance(payload, dict):
            body = urlencode(payload, doseq=True)
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
        elif isinstance(payload, (dict, list)):
            body = json.dumps(payload)
        elif payload is None:
            body = ""
        else:
            body = str(payload)

        if extra_headers:
            headers.update(extra_headers)

        return body, headers

    @staticmethod
    def _parse_response(result: Any) -> tuple[int, Any]:
        """Parse response from the httpapi plugin.

        Args:
            result: Raw response from connection.send_request().
                Expected format: {"status": int, "headers": dict, "body": str}

        Returns:
            tuple: (status_code, parsed_response_data)
        """
        if not isinstance(result, dict) or "status" not in result:
            return 500, {
                "error": f"Invalid response format from send_request, got: {type(result)}",
            }

        status = int(result.get("status", 0))
        headers = result.get("headers", {})
        body_text = result.get("body", "")

        if not body_text:
            return status, {"_response_headers": headers}

        try:
            parsed = json.loads(body_text)
            if isinstance(parsed, dict):
                parsed["_response_headers"] = headers
            return status, parsed
        except (json.JSONDecodeError, ValueError):
            return status, {"raw_response": body_text, "_response_headers": headers}

    @staticmethod
    def _handle_exception(exc: Exception) -> tuple[int, dict[str, str]]:
        """Handle request exceptions with appropriate status codes.

        Args:
            exc: The exception that was raised.

        Returns:
            tuple: (status_code, error_dict)
        """
        error_text = str(exc)
        if "401" in error_text or "Unauthorized" in error_text:
            return 401, {"error": f"Authentication failed: {error_text}"}
        if "404" in error_text or "Not Found" in error_text:
            return 404, {"error": f"Resource not found: {error_text}"}
        return 500, {"error": f"Request failed: {error_text}"}
