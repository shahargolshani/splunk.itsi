# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_glass_table_info module."""


import json
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest
from ansible_collections.splunk.itsi.plugins.module_utils.glass_table import (
    BASE_GLASS_TABLE_ENDPOINT,
    get_glass_table_by_id,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest
from ansible_collections.splunk.itsi.plugins.modules.itsi_glass_table_info import (
    _build_list_params,
    _list_glass_tables,
    main,
)
from conftest import (
    AnsibleExitJson,
    AnsibleFailJson,
    make_mock_conn,
)

SAMPLE_GT = {
    "_key": "abc123",
    "title": "Test Glass Table",
    "description": "A test table",
    "definition": {"title": "Test Glass Table"},
}

SAMPLE_GT_2 = {
    "_key": "def456",
    "title": "Second Table",
    "description": "Another table",
    "definition": {"title": "Second Table"},
}

MODULE_PATH = "ansible_collections.splunk.itsi.plugins.modules.itsi_glass_table_info"

# Default module params (all None except glass_table_id)
DEFAULT_PARAMS = {
    "glass_table_id": None,
    "filter": None,
    "fields": None,
    "count": None,
    "offset": None,
    "sort_key": None,
    "sort_dir": None,
}


def _mock_module():
    """Create a MagicMock AnsibleModule for ItsiRequest."""
    module = MagicMock()
    module.fail_json.side_effect = AnsibleFailJson
    return module


def _make_main_module(params, conn_body="[]", conn_status=200):
    """Build mock module + connection for main() tests.

    Returns (mock_module, mock_conn) after patching AnsibleModule and Connection.
    """
    mock_module = MagicMock()
    mock_module._socket_path = "/tmp/socket"
    mock_module.params = {**DEFAULT_PARAMS, **params}
    mock_module.check_mode = False
    mock_module.fail_json.side_effect = AnsibleFailJson
    mock_module.exit_json.side_effect = AnsibleExitJson
    mock_conn = make_mock_conn(conn_status, conn_body)
    return mock_module, mock_conn


# -- get_glass_table_by_id (shared utility) --


class TestGetGlassTableById:
    def test_returns_dict(self):
        conn = make_mock_conn(200, json.dumps(SAMPLE_GT))
        result = get_glass_table_by_id(ItsiRequest(conn, _mock_module()), "abc123")
        assert result == SAMPLE_GT

    def test_not_found_returns_none(self):
        conn = make_mock_conn(404, "")
        result = get_glass_table_by_id(ItsiRequest(conn, _mock_module()), "missing")
        assert result is None

    def test_path_includes_id(self):
        conn = make_mock_conn(200, json.dumps(SAMPLE_GT))
        get_glass_table_by_id(ItsiRequest(conn, _mock_module()), "abc123")
        call_path = conn.send_request.call_args[0][0]
        assert f"{BASE_GLASS_TABLE_ENDPOINT}/abc123" in call_path

    def test_url_encodes_special_chars(self):
        conn = make_mock_conn(200, json.dumps(SAMPLE_GT))
        get_glass_table_by_id(ItsiRequest(conn, _mock_module()), "id/with/slashes")
        call_path = conn.send_request.call_args[0][0]
        assert "id%2Fwith%2Fslashes" in call_path

    def test_non_dict_body_returns_none(self):
        conn = make_mock_conn(200, json.dumps([SAMPLE_GT]))
        result = get_glass_table_by_id(ItsiRequest(conn, _mock_module()), "abc123")
        assert result is None


# -- _build_list_params --


class TestBuildListParams:
    def test_all_none_returns_empty(self):
        assert _build_list_params(DEFAULT_PARAMS) == {}

    def test_single_param(self):
        params = {**DEFAULT_PARAMS, "count": 10}
        assert _build_list_params(params) == {"count": 10}

    def test_all_params_set(self):
        params = {
            "glass_table_id": None,
            "filter": '{"title":"x"}',
            "fields": "_key,title",
            "count": 5,
            "offset": 10,
            "sort_key": "mod_time",
            "sort_dir": "desc",
        }
        result = _build_list_params(params)
        assert result == {
            "filter": '{"title":"x"}',
            "fields": "_key,title",
            "count": 5,
            "offset": 10,
            "sort_key": "mod_time",
            "sort_dir": "desc",
        }

    def test_zero_values_included(self):
        """Zero is not None, so count=0 and offset=0 should be included."""
        params = {**DEFAULT_PARAMS, "count": 0, "offset": 0}
        result = _build_list_params(params)
        assert result["count"] == 0
        assert result["offset"] == 0


# -- _list_glass_tables --


class TestListGlassTables:
    def test_returns_list(self):
        conn = make_mock_conn(200, json.dumps([SAMPLE_GT, SAMPLE_GT_2]))
        result = _list_glass_tables(ItsiRequest(conn, _mock_module()), {})
        assert len(result) == 2

    def test_empty_list(self):
        conn = make_mock_conn(200, json.dumps([]))
        result = _list_glass_tables(ItsiRequest(conn, _mock_module()), {})
        assert result == []

    def test_non_list_body_returns_empty(self):
        conn = make_mock_conn(200, json.dumps({"unexpected": True}))
        result = _list_glass_tables(ItsiRequest(conn, _mock_module()), {})
        assert result == []

    def test_params_forwarded(self):
        conn = make_mock_conn(200, json.dumps([]))
        _list_glass_tables(ItsiRequest(conn, _mock_module()), {"count": 5, "offset": 10})
        call_path = conn.send_request.call_args[0][0]
        assert "count=5" in call_path
        assert "offset=10" in call_path


# -- main() --


class TestMain:
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_get_by_id(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123"},
            conn_body=json.dumps(SAMPLE_GT),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is False
        assert len(kw["glass_tables"]) == 1
        assert kw["glass_tables"][0]["_key"] == "abc123"

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_get_by_id_not_found(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "missing"},
            conn_status=404,
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["glass_tables"] == []

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_list_all(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {},
            conn_body=json.dumps([SAMPLE_GT, SAMPLE_GT_2]),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is False
        assert len(kw["glass_tables"]) == 2

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_list_empty(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module({}, conn_body=json.dumps([]))
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["glass_tables"] == []

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_list_with_filter_and_pagination(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"filter": '{"title":"x"}', "count": 5, "offset": 10},
            conn_body=json.dumps([SAMPLE_GT]),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_path = mock_conn.send_request.call_args[0][0]
        assert "filter=" in call_path
        assert "count=5" in call_path
        assert "offset=10" in call_path

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_list_with_sort(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"sort_key": "mod_time", "sort_dir": "desc"},
            conn_body=json.dumps([SAMPLE_GT]),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        call_path = mock_conn.send_request.call_args[0][0]
        assert "sort_key=mod_time" in call_path
        assert "sort_dir=desc" in call_path

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_exception_calls_fail_json(self, mock_mod_cls, mock_conn_cls):
        mock_mod, _mock_conn = _make_main_module({"glass_table_id": "abc123"})
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.side_effect = Exception("Connection failed")

        with pytest.raises(AnsibleFailJson):
            main()

        assert "Failed to establish connection" in mock_mod.fail_json.call_args[1]["msg"]

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_api_error_calls_fail_json(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module({}, conn_status=500, conn_body='{"error":"bad"}')
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        mock_mod.fail_json.assert_called_once()
