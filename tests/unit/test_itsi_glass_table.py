# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_glass_table module."""


import json
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest
from ansible_collections.splunk.itsi.plugins.modules.itsi_glass_table import (
    _build_create_payload,
    _build_desired,
    _sync_title_desc_into_definition,
    main,
)
from conftest import (
    AnsibleExitJson,
    AnsibleFailJson,
    make_mock_conn,
)

MODULE_PATH = "ansible_collections.splunk.itsi.plugins.modules.itsi_glass_table"
VALIDATOR_PATH = f"{MODULE_PATH}._validate_definition_or_fail"

SAMPLE_DEFINITION = {"title": "My GT", "description": "desc", "layout": {"tabs": []}}

SAMPLE_GT_API = {
    "_key": "abc123",
    "title": "My GT",
    "description": "desc",
    "definition": SAMPLE_DEFINITION,
    "acl": {"sharing": "user"},
    "gt_version": "beta",
    "_owner": "nobody",
}

# Default module params for present state
DEFAULT_PRESENT_PARAMS = {
    "glass_table_id": None,
    "title": None,
    "description": None,
    "definition": None,
    "sharing": None,
    "state": "present",
}


def _make_main_module(params, conn_body="{}", conn_status=200):
    """Build mock module + connection for main() tests."""
    mock_module = MagicMock()
    mock_module._socket_path = "/tmp/socket"
    mock_module.params = {**DEFAULT_PRESENT_PARAMS, **params}
    mock_module.check_mode = False
    mock_module.fail_json.side_effect = AnsibleFailJson
    mock_module.exit_json.side_effect = AnsibleExitJson
    mock_conn = make_mock_conn(conn_status, conn_body)
    return mock_module, mock_conn


# -- _build_desired --


class TestBuildDesired:
    def test_all_none_returns_empty(self):
        assert _build_desired(DEFAULT_PRESENT_PARAMS) == {}

    def test_includes_non_none_fields(self):
        params = {**DEFAULT_PRESENT_PARAMS, "title": "T", "description": "D"}
        result = _build_desired(params)
        assert result == {"title": "T", "description": "D"}

    def test_includes_definition(self):
        params = {**DEFAULT_PRESENT_PARAMS, "definition": {"layout": {}}}
        result = _build_desired(params)
        assert result == {"definition": {"layout": {}}}

    def test_includes_sharing(self):
        params = {**DEFAULT_PRESENT_PARAMS, "sharing": "app"}
        result = _build_desired(params)
        assert result == {"sharing": "app"}


# -- _build_create_payload --


class TestBuildCreatePayload:
    def test_basic_payload(self):
        desired = {"title": "T", "definition": {"title": "T"}}
        payload = _build_create_payload(desired)
        assert payload["title"] == "T"
        assert payload["gt_version"] == "beta"
        assert payload["_owner"] == "nobody"
        assert payload["_user"] == "nobody"

    def test_syncs_title_into_definition(self):
        desired = {"title": "New Title", "definition": {"title": "Old"}}
        payload = _build_create_payload(desired)
        assert payload["definition"]["title"] == "New Title"

    def test_syncs_description_into_definition(self):
        desired = {
            "title": "T",
            "description": "New desc",
            "definition": {"title": "T", "description": "Old"},
        }
        payload = _build_create_payload(desired)
        assert payload["definition"]["description"] == "New desc"

    def test_sharing_maps_to_acl(self):
        desired = {"title": "T", "sharing": "app"}
        payload = _build_create_payload(desired)
        assert payload["acl"] == {"sharing": "app"}

    def test_no_sharing_no_acl(self):
        desired = {"title": "T"}
        payload = _build_create_payload(desired)
        assert "acl" not in payload

    def test_no_definition_no_sync(self):
        desired = {"title": "T", "description": "D"}
        payload = _build_create_payload(desired)
        assert "definition" not in payload


# -- _sync_title_desc_into_definition --


class TestSyncTitleDescIntoDefinition:
    def test_syncs_title_into_existing_definition(self):
        data = {"title": "New", "definition": {"title": "Old", "layout": {}}}
        _sync_title_desc_into_definition(data)
        assert data["definition"]["title"] == "New"
        assert data["definition"]["layout"] == {}

    def test_syncs_description_into_existing_definition(self):
        data = {"description": "New", "definition": {"description": "Old"}}
        _sync_title_desc_into_definition(data)
        assert data["definition"]["description"] == "New"

    def test_uses_base_definition_when_no_definition_in_data(self):
        base = {"title": "Base", "layout": {"tabs": []}}
        data = {"title": "Updated"}
        _sync_title_desc_into_definition(data, base_definition=base)
        assert data["definition"]["title"] == "Updated"
        assert data["definition"]["layout"] == {"tabs": []}

    def test_noop_when_no_title_or_description(self):
        data = {"sharing": "app", "definition": {"title": "T"}}
        _sync_title_desc_into_definition(data)
        assert data["definition"]["title"] == "T"

    def test_noop_when_no_definition_and_no_base(self):
        data = {"title": "T"}
        _sync_title_desc_into_definition(data)
        assert "definition" not in data

    def test_does_not_mutate_original_definition(self):
        original_def = {"title": "Old", "layout": {}}
        data = {"title": "New", "definition": original_def}
        _sync_title_desc_into_definition(data)
        assert original_def["title"] == "Old"


# -- main(): create --


class TestMainCreate:
    @patch(VALIDATOR_PATH)
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_create_success(self, mock_mod_cls, mock_conn_cls, _mock_validate):
        api_resp = {"_key": "new123", "title": "T"}
        mock_mod, mock_conn = _make_main_module(
            {"title": "T", "description": "D", "definition": SAMPLE_DEFINITION},
            conn_body=json.dumps(api_resp),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["after"]["title"] == "T"

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_create_requires_title(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"definition": SAMPLE_DEFINITION},
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        assert "title" in mock_mod.fail_json.call_args[1]["msg"]

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_create_requires_definition(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module({"title": "T"})
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        assert "definition" in mock_mod.fail_json.call_args[1]["msg"]

    @patch(VALIDATOR_PATH)
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_create_check_mode(self, mock_mod_cls, mock_conn_cls, _mock_validate):
        mock_mod, mock_conn = _make_main_module(
            {"title": "T", "definition": SAMPLE_DEFINITION},
        )
        mock_mod.check_mode = True
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is True
        # API should NOT have been called
        mock_conn.send_request.assert_not_called()

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_create_validation_failure(self, mock_mod_cls, mock_conn_cls):
        """Invalid definition triggers fail_json with validation_errors."""
        bad_definition = {
            "visualizations": {
                "viz_1": {
                    "type": "splunk.singlevalue",
                    "dataSources": {"primary": "ds_nonexistent"},
                },
            },
        }
        mock_mod, mock_conn = _make_main_module(
            {"title": "T", "definition": bad_definition},
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        call_kw = mock_mod.fail_json.call_args[1]
        assert "validation" in call_kw["msg"].lower()
        assert "validation_errors" in call_kw
        assert len(call_kw["validation_errors"]) > 0


# -- main(): update --


class TestMainUpdate:
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_update_with_changes(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "description": "updated"},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is True
        assert "description" in kw["diff"]

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_update_idempotent(self, mock_mod_cls, mock_conn_cls):
        """No diff when desired matches current."""
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "description": "desc"},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is False

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_update_not_found(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "missing", "title": "T"},
            conn_status=404,
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        assert "not found" in mock_mod.fail_json.call_args[1]["msg"]

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_update_check_mode(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "description": "updated"},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod.check_mode = True
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is True
        # Only the GET to fetch current state, no POST for update
        assert mock_conn.send_request.call_count == 1

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_update_no_desired_fields(self, mock_mod_cls, mock_conn_cls):
        """If glass_table_id provided but no fields to update, no change."""
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123"},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is False

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_update_sharing(self, mock_mod_cls, mock_conn_cls):
        """Sharing change maps to acl.sharing in the update payload."""
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "sharing": "app"},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["diff"]["sharing"] == "app"

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_update_definition_validation_failure(self, mock_mod_cls, mock_conn_cls):
        """Invalid definition on update triggers fail_json."""
        bad_definition = {
            "visualizations": {
                "viz_1": {
                    "type": "splunk.singlevalue",
                    "dataSources": {"primary": "ds_nonexistent"},
                },
            },
        }
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "definition": bad_definition},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        call_kw = mock_mod.fail_json.call_args[1]
        assert "validation" in call_kw["msg"].lower()
        assert "validation_errors" in call_kw


# -- main(): delete --


class TestMainDelete:
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_delete_existing(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "state": "absent"},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is True

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_delete_not_found_idempotent(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "missing", "state": "absent"},
            conn_status=404,
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is False

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_delete_requires_id_via_argspec(self, mock_mod_cls, mock_conn_cls):
        """Verify required_if enforces glass_table_id for state=absent."""
        mock_mod, mock_conn = _make_main_module({"state": "absent"})
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        try:
            main()
        except (AnsibleExitJson, AnsibleFailJson):
            pass

        call_kwargs = mock_mod_cls.call_args[1]
        assert ("state", "absent", ("glass_table_id",)) in call_kwargs["required_if"]

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_delete_check_mode(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "state": "absent"},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod.check_mode = True
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is True
        # Only the GET to check existence, no DELETE call
        assert mock_conn.send_request.call_count == 1


# -- main(): error handling --


class TestMainErrors:
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_no_socket_path(self, mock_mod_cls, mock_conn_cls):
        mock_mod = MagicMock()
        mock_mod._socket_path = None
        mock_mod.params = {**DEFAULT_PRESENT_PARAMS}
        mock_mod.fail_json.side_effect = AnsibleFailJson
        mock_mod.exit_json.side_effect = AnsibleExitJson
        mock_mod_cls.return_value = mock_mod

        with pytest.raises(AnsibleFailJson):
            main()

        assert "httpapi" in mock_mod.fail_json.call_args[1]["msg"]

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_connection_exception(self, mock_mod_cls, mock_conn_cls):
        mock_mod, _mock_conn = _make_main_module(
            {"title": "T", "definition": SAMPLE_DEFINITION},
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.side_effect = Exception("Connection failed")

        with pytest.raises(AnsibleFailJson):
            main()

        assert "Failed to establish connection" in mock_mod.fail_json.call_args[1]["msg"]


class TestEarlyValidation:
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_empty_definition_rejected_before_connection(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"title": "T", "definition": {}},
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        assert "must not be empty" in mock_mod.fail_json.call_args[1]["msg"]
        mock_conn_cls.assert_not_called()

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_create_no_title_rejected_before_connection(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"definition": SAMPLE_DEFINITION},
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        assert "title" in mock_mod.fail_json.call_args[1]["msg"]
        mock_conn_cls.assert_not_called()

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_create_no_definition_rejected_before_connection(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module({"title": "T"})
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        assert "definition" in mock_mod.fail_json.call_args[1]["msg"]
        mock_conn_cls.assert_not_called()

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_empty_definition_rejected_on_update(self, mock_mod_cls, mock_conn_cls):
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "definition": {}},
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleFailJson):
            main()

        assert "must not be empty" in mock_mod.fail_json.call_args[1]["msg"]
        mock_conn_cls.assert_not_called()


# -- update: title/description sync into definition --


class TestUpdateDefinitionSync:
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_update_title_syncs_into_definition(self, mock_mod_cls, mock_conn_cls):
        """Updating title also updates definition.title."""
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "title": "Renamed GT"},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["after"]["title"] == "Renamed GT"
        assert kw["after"]["definition"]["title"] == "Renamed GT"

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_update_description_syncs_into_definition(self, mock_mod_cls, mock_conn_cls):
        """Updating description also updates definition.description."""
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "description": "new desc"},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["after"]["description"] == "new desc"
        assert kw["after"]["definition"]["description"] == "new desc"

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_update_title_idempotent_with_matching_definition(
        self,
        mock_mod_cls,
        mock_conn_cls,
    ):
        """No change when title already matches definition.title."""
        mock_mod, mock_conn = _make_main_module(
            {"glass_table_id": "abc123", "title": "My GT"},
            conn_body=json.dumps(SAMPLE_GT_API),
        )
        mock_mod_cls.return_value = mock_mod
        mock_conn_cls.return_value = mock_conn

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_mod.exit_json.call_args[1]
        assert kw["changed"] is False
