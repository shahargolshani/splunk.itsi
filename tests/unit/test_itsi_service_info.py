# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_service_info module."""


import json
from unittest.mock import MagicMock, patch

import pytest

# Import module functions for testing
from ansible_collections.splunk.itsi.plugins.modules.itsi_service_info import (
    _build_filter,
    main,
)
from conftest import AnsibleExitJson, AnsibleFailJson, make_mock_conn

# Sample test data
SAMPLE_SERVICE = {
    "_key": "a2961217-9728-4e9f-b67b-15bf4a40ad7c",
    "title": "api-gateway",
    "enabled": 1,
    "description": "API Gateway Service",
    "sec_grp": "default_itsi_security_group",
    "service_tags": {"tags": ["prod", "payments"]},
    "entity_rules": [],
}

SAMPLE_SERVICE_2 = {
    "_key": "b3072328-0839-5f0g-c78c-26cg5b51be8d",
    "title": "database-service",
    "enabled": 0,
    "description": "Database Service",
    "sec_grp": "team-db",
    "service_tags": {"tags": ["staging"]},
    "entity_rules": [],
}

SAMPLE_SERVICE_LIST = [SAMPLE_SERVICE, SAMPLE_SERVICE_2]


class TestBuildFilter:
    """Tests for _build_filter helper function."""

    def test_build_filter_empty(self):
        """Test empty params returns None."""
        params = {}
        result = _build_filter(params)
        assert result is None

    def test_build_filter_title_only(self):
        """Test filter with title only."""
        params = {"title": "api-gateway"}
        result = _build_filter(params)
        assert result == {"title": "api-gateway"}

    def test_build_filter_enabled_true(self):
        """Test filter with enabled=True becomes 1."""
        params = {"enabled": True}
        result = _build_filter(params)
        assert result == {"enabled": 1}

    def test_build_filter_enabled_false(self):
        """Test filter with enabled=False becomes 0."""
        params = {"enabled": False}
        result = _build_filter(params)
        assert result == {"enabled": 0}

    def test_build_filter_sec_grp(self):
        """Test filter with sec_grp."""
        params = {"sec_grp": "team-a"}
        result = _build_filter(params)
        assert result == {"sec_grp": "team-a"}

    def test_build_filter_combined(self):
        """Test filter with multiple params."""
        params = {
            "title": "api-gateway",
            "enabled": True,
            "sec_grp": "default_itsi_security_group",
        }
        result = _build_filter(params)
        assert result == {
            "title": "api-gateway",
            "enabled": 1,
            "sec_grp": "default_itsi_security_group",
        }

    def test_build_filter_raw_filter_only(self):
        """Test raw filter object is used."""
        params = {"filter": {"custom_field": "value"}}
        result = _build_filter(params)
        assert result == {"custom_field": "value"}

    def test_build_filter_raw_filter_takes_precedence(self):
        """Test raw filter takes precedence over simple params."""
        params = {
            "title": "simple-title",
            "filter": {"title": "filter-title"},
        }
        result = _build_filter(params)
        # Raw filter's title should take precedence
        assert result["title"] == "filter-title"

    def test_build_filter_raw_filter_merged(self):
        """Test raw filter merged with simple params."""
        params = {
            "enabled": True,
            "filter": {"custom_field": "value"},
        }
        result = _build_filter(params)
        assert result["enabled"] == 1
        assert result["custom_field"] == "value"

    def test_build_filter_none_values_ignored(self):
        """Test None values are ignored."""
        params = {
            "title": None,
            "enabled": None,
            "sec_grp": "team-a",
        }
        result = _build_filter(params)
        assert result == {"sec_grp": "team-a"}

    def test_build_filter_empty_filter_dict(self):
        """Test empty filter dict."""
        params = {"filter": {}}
        result = _build_filter(params)
        assert result is None


class TestMain:
    """Tests for main module execution."""

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
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

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_get_by_service_id_found(self, mock_module_class, mock_connection):
        """Test main getting service by service_id (found)."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": "a2961217-9728-4e9f-b67b-15bf4a40ad7c",
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_SERVICE))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["service"]["title"] == "api-gateway"

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_get_by_service_id_not_found(self, mock_module_class, mock_connection):
        """Test main getting service by service_id (not found).

        When API returns 404, ItsiRequest returns None; module exits
        with exit_json (no fail_json) and default empty result.
        """
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": "nonexistent-key",
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(404, json.dumps({"message": "Not found"}))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        # 404 returns defaults — no service set, raw stays as default
        assert "service" not in call_kwargs
        assert call_kwargs["changed"] is False

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_all_services(self, mock_module_class, mock_connection):
        """Test main listing all services."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_SERVICE_LIST))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert len(call_kwargs["items"]) == 2

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_with_title_filter(self, mock_module_class, mock_connection):
        """Test main listing with title filter."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": "api-gateway",
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_SERVICE]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        # Verify filter was passed
        call_args = mock_conn.send_request.call_args
        assert "filter=" in call_args[0][0]
        assert "api-gateway" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_with_enabled_filter(self, mock_module_class, mock_connection):
        """Test main listing with enabled filter."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": True,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_SERVICE]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_with_sec_grp_filter(self, mock_module_class, mock_connection):
        """Test main listing with sec_grp filter."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": "default_itsi_security_group",
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_SERVICE]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_args = mock_conn.send_request.call_args
        assert "filter=" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_with_raw_filter(self, mock_module_class, mock_connection):
        """Test main listing with raw filter object."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": {"custom_field": {"$regex": "pattern.*"}},
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_args = mock_conn.send_request.call_args
        assert "filter=" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_with_fields_projection(self, mock_module_class, mock_connection):
        """Test main listing with fields projection."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": ["_key", "title", "enabled"],
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([{"_key": "test", "title": "svc", "enabled": 1}]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_args = mock_conn.send_request.call_args
        assert "fields=" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_with_pagination_count(self, mock_module_class, mock_connection):
        """Test main listing with count pagination."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": 10,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_SERVICE_LIST))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_args = mock_conn.send_request.call_args
        assert "count=10" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_with_pagination_offset(self, mock_module_class, mock_connection):
        """Test main listing with offset pagination."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": 20,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_args = mock_conn.send_request.call_args
        assert "offset=20" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_with_pagination_both(self, mock_module_class, mock_connection):
        """Test main listing with count and offset pagination."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": 5,
            "offset": 10,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_SERVICE_LIST))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_args = mock_conn.send_request.call_args
        assert "count=5" in call_args[0][0]
        assert "offset=10" in call_args[0][0]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_error_response(self, mock_module_class, mock_connection):
        """Test main handles error response on list.

        Non-2xx (except 404) causes ItsiRequest to call module.fail_json().
        """
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(500, json.dumps({"message": "Internal server error"}))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "500" in mock_module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_paging_envelope(self, mock_module_class, mock_connection):
        """Test main handles paging envelope response."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(
            200,
            json.dumps({"items": SAMPLE_SERVICE_LIST, "size": 2}),
        )
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert len(call_kwargs["items"]) == 2
        assert call_kwargs["paging"]["size"] == 2

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_get_by_key_with_error_context(self, mock_module_class, mock_connection):
        """Test main fails on non-2xx when getting by key.

        ItsiRequest calls module.fail_json() for 400 and other non-2xx errors.
        """
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": "invalid-key",
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(
            400,
            json.dumps({"error": "Bad Request", "context": "Invalid key format"}),
        )
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "400" in mock_module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_combined_filters(self, mock_module_class, mock_connection):
        """Test main listing with combined filters."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": "api-gateway",
            "enabled": True,
            "sec_grp": "default_itsi_security_group",
            "filter": None,
            "fields": ["_key", "title"],
            "count": 10,
            "offset": 0,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_SERVICE]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_args = mock_conn.send_request.call_args
        path = call_args[0][0]
        assert "filter=" in path
        assert "fields=" in path
        assert "count=10" in path
        assert "offset=0" in path

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_fields_dedupe(self, mock_module_class, mock_connection):
        """Test main deduplicates fields parameter."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": ["_key", "title", "_key", "enabled"],
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        # The fields should be deduped
        call_args = mock_conn.send_request.call_args
        # _key should only appear once
        path = call_args[0][0]
        # Count occurrences of _key in the fields param
        assert path.count("_key") == 1

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_always_changed_false(self, mock_module_class, mock_connection):
        """Test main always returns changed=False (info module)."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_SERVICE_LIST))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_unknown_response_shape(self, mock_module_class, mock_connection):
        """Test main handles unknown response shape."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps({"unexpected": "shape"}))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_kwargs = mock_module.exit_json.call_args[1]
        # Should still return items (empty since response wasn't a list)
        assert "items" in call_kwargs

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_get_by_key_details_in_error(self, mock_module_class, mock_connection):
        """Test main fails with fail_json for 403 on get by key."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": "test-key",
            "title": None,
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(
            403,
            json.dumps({"message": "Forbidden", "details": "Insufficient permissions"}),
        )
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "403" in mock_module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.Connection")
    @patch("ansible_collections.splunk.itsi.plugins.modules.itsi_service_info.AnsibleModule")
    def test_main_list_error_includes_request_info(self, mock_module_class, mock_connection):
        """Test main fails with fail_json for 500 on list (error in msg)."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "service_id": None,
            "title": "test",
            "enabled": None,
            "sec_grp": None,
            "filter": None,
            "fields": None,
            "count": None,
            "offset": None,
        }
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(500, json.dumps({"error": "Server error"}))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "500" in mock_module.fail_json.call_args[1]["msg"]
        assert "Server error" in mock_module.fail_json.call_args[1]["msg"]
