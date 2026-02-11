# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026, Splunk ITSI Ansible Collection maintainers
"""Splunk ITSI request utilities for Ansible modules."""


import json
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urlencode


class ItsiRequest:
    """Handle HTTP requests to the Splunk ITSI REST API.

    Provides a consistent interface for modules to interact with the ITSI API
    via the itsi_api_client httpapi plugin.  Error handling is built-in:
    non-2xx responses (except 404) trigger ``module.fail_json`` so callers
    never need to inspect status codes.

    Returns:
        All request methods return ``(status, headers, body)`` for 2xx
        responses, ``None`` for 404 (resource not found), or call
        ``module.fail_json`` and never return for other errors.

    Args:
        connection: The Ansible Connection object for API requests.
        module: The AnsibleModule instance (used for ``fail_json`` on errors).
    """

    def __init__(self, connection: Any, module: Any) -> None:
        self.connection = connection
        self.module = module

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Union[dict, list, str]] = None,
        use_form_data: bool = False,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Optional[Tuple[int, dict, Any]]:
        """Send a request via the itsi_api_client httpapi plugin.

        Args:
            method: HTTP method (GET, POST, DELETE).
            path: API path.
            params: Query parameters dict. None/empty values are filtered out.
            payload: Request body data (dict, list, or string).
            use_form_data: If True, send payload as URL-encoded form data.
            extra_headers: Additional headers to include in the request.

        Returns:
            ``(status, resp_headers, body)`` for 2xx responses, or ``None``
            for 404 (not found).  All other errors call ``module.fail_json``.
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
        except Exception as exc:
            self.module.fail_json(msg=f"Request to {path} failed: {exc}")
            return None  # unreachable, fail_json raises

        if not isinstance(result, dict) or "status" not in result:
            self.module.fail_json(
                msg=f"Invalid response format from {path}, got: {type(result)}",
            )
            return None

        status = int(result.get("status", 0))
        resp_headers = result.get("headers", {})
        body_text = result.get("body", "")

        # 404 – resource not found (normal business-logic signal)
        if status == 404:
            return None

        # Any other non-2xx – hard failure
        if not 200 <= status < 300:
            self.module.fail_json(
                msg=f"Splunk API returned error {status}: {body_text}",
            )
            return None

        # Parse JSON body
        if not body_text:
            return status, resp_headers, {}

        try:
            parsed = json.loads(body_text)
            return status, resp_headers, parsed
        except (json.JSONDecodeError, ValueError):
            return status, resp_headers, body_text

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[int, dict, Any]]:
        """Perform a GET request."""
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Union[dict, list, str]] = None,
        use_form_data: bool = False,
    ) -> Optional[Tuple[int, dict, Any]]:
        """Perform a POST request."""
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
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[int, dict, Any]]:
        """Perform a DELETE request."""
        return self.request("DELETE", path, params=params)

    def get_by_path(
        self,
        rest_path: str,
        query_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[int, dict, Any]]:
        """GET with automatic output_mode=json."""
        params: Dict[str, Any] = {"output_mode": "json"}
        if query_params:
            for key, value in query_params.items():
                if value is not None:
                    params[key] = value
        return self.get(rest_path, params=params)

    def delete_by_path(self, rest_path: str) -> Optional[Tuple[int, dict, Any]]:
        """DELETE with automatic output_mode=json."""
        return self.delete(rest_path, params={"output_mode": "json"})

    def create_update(
        self,
        rest_path: str,
        data: Optional[Union[dict, list, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        use_form_data: bool = False,
    ) -> Optional[Tuple[int, dict, Any]]:
        """POST for create/update with automatic output_mode=json."""
        params: Dict[str, Any] = {"output_mode": "json"}
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

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_query_string(path: str, params: Optional[Dict[str, Any]]) -> str:
        """Append query parameters to a path."""
        if not params:
            return path
        query_params = {k: v for k, v in params.items() if v is not None and v != ""}
        if not query_params:
            return path
        sep = "&" if "?" in path else "?"
        return f"{path}{sep}{urlencode(query_params, doseq=True)}"

    @staticmethod
    def _prepare_request(
        payload: Optional[Union[dict, list, str]],
        use_form_data: bool,
        extra_headers: Optional[Dict[str, str]],
    ) -> Tuple[str, Dict[str, str]]:
        """Prepare request body and headers."""
        headers: Dict[str, str] = {}

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
