# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_episode_details_info module."""


import json
from unittest.mock import MagicMock, patch

import pytest

# Import shared utilities from module_utils
from ansible_collections.splunk.itsi.plugins.module_utils.episode_details import (
    BASE_EPISODE_ENDPOINT,
    get_episode_by_id,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

# Import module functions for testing
from ansible_collections.splunk.itsi.plugins.modules.itsi_episode_details_info import (
    _build_list_params,
    _get_episode_count,
    _list_episodes,
    main,
)
from conftest import AnsibleExitJson, AnsibleFailJson, make_mock_conn


def _mock_module():
    """Create a MagicMock AnsibleModule for ItsiRequest."""
    module = MagicMock()
    module.fail_json.side_effect = AnsibleFailJson
    return module


# Sample data fixtures
SAMPLE_EPISODE = {
    "_key": "abc-123-def-456",
    "title": "Test Episode",
    "severity": "4",
    "status": "2",
    "owner": "admin",
    "mod_time": "1700000000",
    "instruction": "Investigate host",
}

SAMPLE_EPISODE_2 = {
    "_key": "ghi-789-jkl-012",
    "title": "Second Episode",
    "severity": "6",
    "status": "1",
    "owner": "unassigned",
    "mod_time": "1700001000",
    "instruction": "",
}

SAMPLE_COUNT_RESPONSE = {"count": "42"}

MODULE_PATH = "ansible_collections.splunk.itsi.plugins.modules.itsi_episode_details_info"


# get_episode_by_id (shared utility from episode_details.py)
class TestGetEpisodeById:
    """Tests for the shared get_episode_by_id utility."""

    def test_returns_episode_dict(self):
        """Test successful retrieval returns episode dict."""
        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))
        data = get_episode_by_id(ItsiRequest(mock_conn, _mock_module()), "abc-123-def-456")

        assert data is not None
        assert isinstance(data, dict)
        assert data["_key"] == "abc-123-def-456"
        assert data["title"] == "Test Episode"

    def test_not_found_returns_none(self):
        """Test 404 response returns None."""
        mock_conn = make_mock_conn(404, json.dumps({"error": "Not found"}))
        data = get_episode_by_id(ItsiRequest(mock_conn, _mock_module()), "nonexistent")

        assert data is None

    def test_url_path_includes_episode_id(self):
        """Test the correct API path is built."""
        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))
        get_episode_by_id(ItsiRequest(mock_conn, _mock_module()), "abc-123")

        call_path = mock_conn.send_request.call_args[0][0]
        assert f"{BASE_EPISODE_ENDPOINT}/abc-123" in call_path

    def test_url_encodes_episode_id(self):
        """Test that special characters in the ID are URL-encoded."""
        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))
        get_episode_by_id(ItsiRequest(mock_conn, _mock_module()), "id with spaces")

        call_path = mock_conn.send_request.call_args[0][0]
        assert "id+with+spaces" in call_path

    def test_episode_id_with_slashes(self):
        """Test that slashes in the ID are URL-encoded."""
        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))
        get_episode_by_id(ItsiRequest(mock_conn, _mock_module()), "id/with/slashes")

        call_path = mock_conn.send_request.call_args[0][0]
        assert "id%2Fwith%2Fslashes" in call_path


# _get_episode_count
class TestGetEpisodeCount:
    """Tests for _get_episode_count module helper."""

    def test_returns_count_as_int(self):
        """Test count is parsed as integer."""
        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_COUNT_RESPONSE))
        result = _get_episode_count(ItsiRequest(mock_conn, _mock_module()), None)

        assert result["count"] == 42

    def test_with_filter_data(self):
        """Test filter_data is passed as query parameter."""
        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_COUNT_RESPONSE))
        _get_episode_count(ItsiRequest(mock_conn, _mock_module()), '{"status":"2"}')

        call_path = mock_conn.send_request.call_args[0][0]
        assert "filter_data" in call_path

    def test_without_filter_data(self):
        """Test no filter_data when None."""
        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_COUNT_RESPONSE))
        _get_episode_count(ItsiRequest(mock_conn, _mock_module()), None)

        call_path = mock_conn.send_request.call_args[0][0]
        assert "filter_data" not in call_path

    def test_count_endpoint_path(self):
        """Test the /count endpoint is used."""
        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_COUNT_RESPONSE))
        _get_episode_count(ItsiRequest(mock_conn, _mock_module()), None)

        call_path = mock_conn.send_request.call_args[0][0]
        assert "/count" in call_path

    def test_non_dict_body_returns_zero_count(self):
        """Test non-dict body returns count=0."""
        mock_conn = make_mock_conn(200, json.dumps("not a dict"))
        result = _get_episode_count(ItsiRequest(mock_conn, _mock_module()), None)

        assert result["count"] == 0

    def test_missing_count_key_returns_zero(self):
        """Test missing 'count' key returns 0."""
        mock_conn = make_mock_conn(200, json.dumps({"other_key": "value"}))
        result = _get_episode_count(ItsiRequest(mock_conn, _mock_module()), None)

        assert result["count"] == 0

    def test_invalid_count_value_returns_zero(self):
        """Test invalid count value returns 0."""
        mock_conn = make_mock_conn(200, json.dumps({"count": "not_a_number"}))
        result = _get_episode_count(ItsiRequest(mock_conn, _mock_module()), None)

        assert result["count"] == 0

    def test_count_as_string_integer(self):
        """Test count returned as string integer."""
        mock_conn = make_mock_conn(200, json.dumps({"count": "100"}))
        result = _get_episode_count(ItsiRequest(mock_conn, _mock_module()), None)

        assert result["count"] == 100

    def test_count_as_native_integer(self):
        """Test count returned as native integer."""
        mock_conn = make_mock_conn(200, json.dumps({"count": 7}))
        result = _get_episode_count(ItsiRequest(mock_conn, _mock_module()), None)

        assert result["count"] == 7


# _list_episodes
class TestListEpisodes:
    """Tests for _list_episodes module helper."""

    def test_returns_list(self):
        """Test list endpoint returns episodes list."""
        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_EPISODE, SAMPLE_EPISODE_2]))
        result = _list_episodes(ItsiRequest(mock_conn, _mock_module()), {})

        assert len(result["episodes"]) == 2

    def test_empty_list(self):
        """Test empty list response."""
        mock_conn = make_mock_conn(200, json.dumps([]))
        result = _list_episodes(ItsiRequest(mock_conn, _mock_module()), {})

        assert result["episodes"] == []

    def test_non_list_body_returns_empty(self):
        """Test non-list body returns empty episodes list."""
        mock_conn = make_mock_conn(200, json.dumps({"error": "unexpected"}))
        result = _list_episodes(ItsiRequest(mock_conn, _mock_module()), {})

        assert result["episodes"] == []

    def test_endpoint_ends_with_slash(self):
        """Test list endpoint ends with trailing slash."""
        mock_conn = make_mock_conn(200, json.dumps([]))
        _list_episodes(ItsiRequest(mock_conn, _mock_module()), {})

        call_path = mock_conn.send_request.call_args[0][0]
        assert f"{BASE_EPISODE_ENDPOINT}/" in call_path

    def test_params_forwarded(self):
        """Test query parameters are forwarded."""
        mock_conn = make_mock_conn(200, json.dumps([]))
        _list_episodes(ItsiRequest(mock_conn, _mock_module()), {"limit": 10, "skip": 5})

        call_path = mock_conn.send_request.call_args[0][0]
        assert "limit=10" in call_path
        assert "skip=5" in call_path


# _build_list_params
class TestBuildListParams:
    """Tests for _build_list_params helper."""

    def test_all_defaults(self):
        """Test default module params produce empty dict."""
        params = {
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
        }
        result = _build_list_params(params)
        assert result == {}

    def test_limit_positive(self):
        """Test positive limit is included."""
        params = {
            "limit": 10,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
        }
        result = _build_list_params(params)
        assert result["limit"] == 10

    def test_limit_zero_excluded(self):
        """Test limit=0 is excluded."""
        params = {
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
        }
        result = _build_list_params(params)
        assert "limit" not in result

    def test_skip_included(self):
        """Test skip is included when set."""
        params = {
            "limit": 0,
            "skip": 5,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
        }
        result = _build_list_params(params)
        assert result["skip"] == 5

    def test_skip_zero_included(self):
        """Test skip=0 is included (not None)."""
        params = {
            "limit": 0,
            "skip": 0,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
        }
        result = _build_list_params(params)
        assert result["skip"] == 0

    def test_fields_included(self):
        """Test fields parameter is included."""
        params = {
            "limit": 0,
            "skip": None,
            "fields": "_key,title,severity",
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
        }
        result = _build_list_params(params)
        assert result["fields"] == "_key,title,severity"

    def test_filter_data_included(self):
        """Test filter_data is included."""
        params = {
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": '{"status":"2"}',
            "sort_key": None,
            "sort_dir": None,
        }
        result = _build_list_params(params)
        assert result["filter_data"] == '{"status":"2"}'

    def test_sort_key_included(self):
        """Test sort_key is included."""
        params = {
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": "mod_time",
            "sort_dir": None,
        }
        result = _build_list_params(params)
        assert result["sort_key"] == "mod_time"

    def test_sort_dir_included(self):
        """Test sort_dir is included."""
        params = {
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": 1,
        }
        result = _build_list_params(params)
        assert result["sort_dir"] == 1

    def test_sort_dir_zero_included(self):
        """Test sort_dir=0 (descending) is included."""
        params = {
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": 0,
        }
        result = _build_list_params(params)
        assert result["sort_dir"] == 0

    def test_all_params_set(self):
        """Test all parameters present."""
        params = {
            "limit": 20,
            "skip": 10,
            "fields": "_key,title",
            "filter_data": '{"severity":"6"}',
            "sort_key": "mod_time",
            "sort_dir": 0,
        }
        result = _build_list_params(params)
        assert result == {
            "limit": 20,
            "skip": 10,
            "fields": "_key,title",
            "filter_data": '{"severity":"6"}',
            "sort_key": "mod_time",
            "sort_dir": 0,
        }


# main() — full module execution
class TestMain:
    """Tests for main module execution."""

    # Single episode by ID
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_get_by_episode_id(self, mock_module_class, mock_connection):
        """Test main fetches a single episode by episode_id."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123",
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()
        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is False
        assert len(kw["episodes"]) == 1
        assert kw["episodes"][0]["_key"] == "abc-123-def-456"

    # Count-only mode
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_count_only(self, mock_module_class, mock_connection):
        """Test main count_only returns count."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": True,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_COUNT_RESPONSE))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is False
        assert kw["count"] == 42

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_count_only_with_filter(self, mock_module_class, mock_connection):
        """Test main count_only forwards filter_data."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": '{"status":"2"}',
            "sort_key": None,
            "sort_dir": None,
            "count_only": True,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_COUNT_RESPONSE))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_path = mock_conn.send_request.call_args[0][0]
        assert "filter_data" in call_path

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_count_only_overrides_episode_id(self, mock_module_class, mock_connection):
        """Test that count_only=true takes priority when episode_id is also set."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123",
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": True,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_COUNT_RESPONSE))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        # episode_id AND not count_only is False, falls through to count_only
        assert "count" in kw

    # List episodes
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_list_episodes(self, mock_module_class, mock_connection):
        """Test main lists episodes with default params."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_EPISODE, SAMPLE_EPISODE_2]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is False
        assert len(kw["episodes"]) == 2

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_list_with_limit_and_skip(self, mock_module_class, mock_connection):
        """Test main list with limit and skip."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 10,
            "skip": 5,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_EPISODE]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_path = mock_conn.send_request.call_args[0][0]
        assert "limit=10" in call_path
        assert "skip=5" in call_path

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_list_with_sort(self, mock_module_class, mock_connection):
        """Test main list with sort parameters."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": "mod_time",
            "sort_dir": 0,
            "count_only": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_EPISODE]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_path = mock_conn.send_request.call_args[0][0]
        assert "sort_key=mod_time" in call_path
        assert "sort_dir=0" in call_path

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_list_with_fields(self, mock_module_class, mock_connection):
        """Test main list with fields parameter."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 0,
            "skip": None,
            "fields": "_key,title,severity",
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_EPISODE]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_path = mock_conn.send_request.call_args[0][0]
        assert "fields=" in call_path

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_list_with_filter_data(self, mock_module_class, mock_connection):
        """Test main list with filter_data."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": '{"severity":"6"}',
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = MagicMock()
        mock_conn.send_request.return_value = {
            "status": 200,
            "body": json.dumps([SAMPLE_EPISODE]),
            "headers": {},
        }
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_path = mock_conn.send_request.call_args[0][0]
        assert "filter_data" in call_path

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_list_empty_result(self, mock_module_class, mock_connection):
        """Test main list with empty result."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["episodes"] == []

    # Check mode (read-only module — should work identically)
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_check_mode_supported(self, mock_module_class, mock_connection):
        """Test main supports check mode (read-only module)."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123",
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        mock_module.exit_json.assert_called_once()

    # Always returns changed=False
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_always_changed_false(self, mock_module_class, mock_connection):
        """Test main always returns changed=False."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(200, json.dumps([SAMPLE_EPISODE]))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is False

    # Exception handling
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_exception_handling(self, mock_module_class, mock_connection):
        """Test main handles exceptions and calls fail_json."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123",
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
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

    @patch(f"{MODULE_PATH}._list_episodes", side_effect=Exception("Timeout"))
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_exception_during_list(
        self,
        mock_module_class,
        mock_connection,
        mock_list,
    ):
        """Test main handles exception during list operation."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = MagicMock()

        with pytest.raises(AnsibleFailJson):
            main()

        assert "Exception occurred" in mock_module.fail_json.call_args[1]["msg"]

    # Error responses from API
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_api_error_response(self, mock_module_class, mock_connection):
        """Test main handles non-200 API response via fail_json."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": None,
            "limit": 0,
            "skip": None,
            "fields": None,
            "filter_data": None,
            "sort_key": None,
            "sort_dir": None,
            "count_only": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn = make_mock_conn(500, json.dumps({"error": "Server error"}))
        mock_connection.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
