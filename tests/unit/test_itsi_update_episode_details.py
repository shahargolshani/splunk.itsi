# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for itsi_update_episode_details module."""


import json
from unittest.mock import MagicMock, patch

import pytest

# Import module functions for testing
from ansible_collections.splunk.itsi.plugins.modules.itsi_update_episode_details import (
    NAMED_FIELD_PARAMS,
    _build_update_data,
    main,
)
from conftest import AnsibleExitJson, AnsibleFailJson, make_mock_conn

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

MODULE_PATH = "ansible_collections.splunk.itsi.plugins.modules.itsi_update_episode_details"


# NAMED_FIELD_PARAMS constant
class TestNamedFieldParams:
    """Tests for the NAMED_FIELD_PARAMS constant."""

    def test_contains_expected_fields(self):
        """Test expected field names are present."""
        assert "severity" in NAMED_FIELD_PARAMS
        assert "status" in NAMED_FIELD_PARAMS
        assert "owner" in NAMED_FIELD_PARAMS
        assert "instruction" in NAMED_FIELD_PARAMS

    def test_length(self):
        """Test exactly 4 named fields."""
        assert len(NAMED_FIELD_PARAMS) == 4


# _build_update_data
class TestBuildUpdateData:
    """Tests for _build_update_data helper."""

    def test_severity_only(self):
        """Test building with severity only."""
        module = MagicMock()
        module.params = {
            "episode_id": "abc",
            "severity": "6",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        result = _build_update_data(module)
        assert result == {"severity": "6"}

    def test_all_named_params(self):
        """Test building with all named parameters."""
        module = MagicMock()
        module.params = {
            "episode_id": "abc",
            "severity": "4",
            "status": "2",
            "owner": "admin",
            "instruction": "Check logs",
            "fields": None,
        }
        result = _build_update_data(module)
        assert result == {
            "severity": "4",
            "status": "2",
            "owner": "admin",
            "instruction": "Check logs",
        }

    def test_fields_dict_only(self):
        """Test building with only the fields dict."""
        module = MagicMock()
        module.params = {
            "episode_id": "abc",
            "severity": None,
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": {"custom_field": "value", "priority": "high"},
        }
        result = _build_update_data(module)
        assert result == {"custom_field": "value", "priority": "high"}

    def test_named_and_fields_merged(self):
        """Test named params merged with fields dict."""
        module = MagicMock()
        module.params = {
            "episode_id": "abc",
            "severity": "6",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": {"custom": "val"},
        }
        result = _build_update_data(module)
        assert result == {"severity": "6", "custom": "val"}

    def test_empty_fields_dict(self):
        """Test empty fields dict is ignored."""
        module = MagicMock()
        module.params = {
            "episode_id": "abc",
            "severity": "4",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": {},
        }
        result = _build_update_data(module)
        assert result == {"severity": "4"}

    def test_no_params_returns_empty(self):
        """Test no update params returns empty dict."""
        module = MagicMock()
        module.params = {
            "episode_id": "abc",
            "severity": None,
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        result = _build_update_data(module)
        assert result == {}

    def test_fields_override_named_param(self):
        """Test that fields dict can override a named param key."""
        module = MagicMock()
        module.params = {
            "episode_id": "abc",
            "severity": "4",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": {"severity": "6"},
        }
        result = _build_update_data(module)
        # fields dict updates after named params → overrides
        assert result["severity"] == "6"


# main() — full module execution
class TestMain:
    """Tests for main module execution."""

    # Fail when no update fields are provided
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_fail_no_update_fields(self, mock_module_class, mock_connection):
        """Test main fails when no update fields are provided."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123",
            "severity": None,
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "At least one field" in mock_module.fail_json.call_args[1]["msg"]

    # Idempotent — no changes needed
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_idempotent_no_change(self, mock_module_class, mock_connection):
        """Test main returns changed=False when desired state matches current."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "4",
            "status": "2",
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is False
        assert kw["episode_id"] == "abc-123-def-456"
        assert kw["diff"] == {}
        assert kw["before"] == {"severity": "4", "status": "2"}
        assert kw["after"] == {"severity": "4", "status": "2"}
        assert kw["response"] == {}

    # Changed — fields differ
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_changed(self, mock_module_class, mock_connection):
        """Test main returns changed=True when update is applied."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "6",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn_obj = MagicMock()
        mock_conn_obj.send_request.side_effect = [
            {
                "status": 200,
                "body": json.dumps(SAMPLE_EPISODE),
                "headers": {},
            },
            {
                "status": 200,
                "body": json.dumps({"success": True}),
                "headers": {},
            },
        ]
        mock_connection.return_value = mock_conn_obj

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["episode_id"] == "abc-123-def-456"
        assert kw["before"]["severity"] == "4"
        assert kw["after"]["severity"] == "6"
        assert "severity" in kw["diff"]
        assert kw["response"] == {"success": True}

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_changed_multiple_fields(self, mock_module_class, mock_connection):
        """Test main updates multiple fields at once."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "6",
            "status": "5",
            "owner": "new_owner",
            "instruction": "New instructions",
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn_obj = MagicMock()
        mock_conn_obj.send_request.side_effect = [
            {
                "status": 200,
                "body": json.dumps(SAMPLE_EPISODE),
                "headers": {},
            },
            {
                "status": 200,
                "body": json.dumps({"success": True}),
                "headers": {},
            },
        ]
        mock_connection.return_value = mock_conn_obj

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["after"]["severity"] == "6"
        assert kw["after"]["status"] == "5"
        assert kw["after"]["owner"] == "new_owner"
        assert kw["after"]["instruction"] == "New instructions"

    # Check mode
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_check_mode_change_needed(self, mock_module_class, mock_connection):
        """Test check mode reports changes without calling update API."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "6",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mc = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))
        mock_connection.return_value = mc

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["before"]["severity"] == "4"
        assert kw["after"]["severity"] == "6"
        assert kw["response"] == {}

        # Verify only 1 API call (GET), no POST
        assert mc.send_request.call_count == 1

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_check_mode_no_change(self, mock_module_class, mock_connection):
        """Test check mode with no changes needed."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "4",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is False
        assert kw["diff"] == {}
        assert kw["response"] == {}

    # fields dict parameter
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_with_fields_dict(self, mock_module_class, mock_connection):
        """Test main uses fields dict for custom field updates."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": None,
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": {"custom_field": "new_value"},
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn_obj = MagicMock()
        mock_conn_obj.send_request.side_effect = [
            {
                "status": 200,
                "body": json.dumps(SAMPLE_EPISODE),
                "headers": {},
            },
            {
                "status": 200,
                "body": json.dumps({"success": True}),
                "headers": {},
            },
        ]
        mock_connection.return_value = mock_conn_obj

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["after"]["custom_field"] == "new_value"

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_named_and_fields_combined(self, mock_module_class, mock_connection):
        """Test main combines named params and fields dict."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "6",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": {"custom": "value"},
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn_obj = MagicMock()
        mock_conn_obj.send_request.side_effect = [
            {
                "status": 200,
                "body": json.dumps(SAMPLE_EPISODE),
                "headers": {},
            },
            {
                "status": 200,
                "body": json.dumps({"success": True}),
                "headers": {},
            },
        ]
        mock_connection.return_value = mock_conn_obj

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["after"]["severity"] == "6"
        assert kw["after"]["custom"] == "value"

    # Exception handling
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_exception_on_connection(self, mock_module_class, mock_connection):
        """Test main handles connection exceptions."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123",
            "severity": "6",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
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
        assert mock_module.fail_json.call_args[1]["episode_id"] == "abc-123"

    @patch(f"{MODULE_PATH}.get_episode_by_id", side_effect=Exception("API timeout"))
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_exception_during_get(
        self,
        mock_module_class,
        mock_connection,
        mock_get_episode,
    ):
        """Test main handles exception during GET of current episode."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123",
            "severity": "6",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = MagicMock()

        with pytest.raises(AnsibleFailJson):
            main()

        assert "Exception occurred" in mock_module.fail_json.call_args[1]["msg"]

    @patch(f"{MODULE_PATH}._update_episode", side_effect=Exception("Write timeout"))
    @patch(f"{MODULE_PATH}.get_episode_by_id", return_value=SAMPLE_EPISODE)
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_exception_during_update(
        self,
        mock_module_class,
        mock_connection,
        mock_get_episode,
        mock_update,
    ):
        """Test main handles exception during POST update."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "6",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = MagicMock()

        with pytest.raises(AnsibleFailJson):
            main()

        assert "Exception occurred" in mock_module.fail_json.call_args[1]["msg"]

    # episode_id always in result
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_episode_id_in_success_result(self, mock_module_class, mock_connection):
        """Test episode_id is always present in successful result."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "4",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["episode_id"] == "abc-123-def-456"

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_episode_id_in_error_result(self, mock_module_class, mock_connection):
        """Test episode_id is present in fail_json result."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123",
            "severity": "6",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.side_effect = Exception("Boom")

        with pytest.raises(AnsibleFailJson):
            main()

        assert mock_module.fail_json.call_args[1]["episode_id"] == "abc-123"

    # before / after / diff structure
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_before_after_structure_on_change(
        self,
        mock_module_class,
        mock_connection,
    ):
        """Test before/after/diff structure when changes are made."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "6",
            "status": "5",
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn_obj = MagicMock()
        mock_conn_obj.send_request.side_effect = [
            {
                "status": 200,
                "body": json.dumps(SAMPLE_EPISODE),
                "headers": {},
            },
            {
                "status": 200,
                "body": json.dumps({"success": True}),
                "headers": {},
            },
        ]
        mock_connection.return_value = mock_conn_obj

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]

        # before should contain only the targeted fields
        assert set(kw["before"].keys()) == {"severity", "status"}
        assert kw["before"]["severity"] == "4"
        assert kw["before"]["status"] == "2"

        # after should reflect desired state
        assert kw["after"]["severity"] == "6"
        assert kw["after"]["status"] == "5"

        # diff should contain the differing fields
        assert "severity" in kw["diff"]
        assert "status" in kw["diff"]

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_before_after_identical_when_no_change(
        self,
        mock_module_class,
        mock_connection,
    ):
        """Test before and after are identical when no change is needed."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "4",
            "owner": "admin",
            "status": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["before"] == kw["after"]
        assert kw["diff"] == {}

    # Partial changes (some fields match, some differ)
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_partial_change(self, mock_module_class, mock_connection):
        """Test that only differing fields appear in the diff."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "4",  # same as current
            "status": "5",  # different from current "2"
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn_obj = MagicMock()
        mock_conn_obj.send_request.side_effect = [
            {
                "status": 200,
                "body": json.dumps(SAMPLE_EPISODE),
                "headers": {},
            },
            {
                "status": 200,
                "body": json.dumps({"success": True}),
                "headers": {},
            },
        ]
        mock_connection.return_value = mock_conn_obj

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert "severity" not in kw["diff"]
        assert "status" in kw["diff"]

    # Owner update
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_update_owner(self, mock_module_class, mock_connection):
        """Test updating only the owner field."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": None,
            "status": None,
            "owner": "new_analyst",
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn_obj = MagicMock()
        mock_conn_obj.send_request.side_effect = [
            {
                "status": 200,
                "body": json.dumps(SAMPLE_EPISODE),
                "headers": {},
            },
            {
                "status": 200,
                "body": json.dumps({"success": True}),
                "headers": {},
            },
        ]
        mock_connection.return_value = mock_conn_obj

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["after"]["owner"] == "new_analyst"

    # Instruction update
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_update_instruction(self, mock_module_class, mock_connection):
        """Test updating only the instruction field."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": None,
            "status": None,
            "owner": None,
            "instruction": "New instruction text",
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn_obj = MagicMock()
        mock_conn_obj.send_request.side_effect = [
            {
                "status": 200,
                "body": json.dumps(SAMPLE_EPISODE),
                "headers": {},
            },
            {
                "status": 200,
                "body": json.dumps({"success": True}),
                "headers": {},
            },
        ]
        mock_connection.return_value = mock_conn_obj

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["after"]["instruction"] == "New instruction text"

    # Update actually calls the API
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_update_calls_api(self, mock_module_class, mock_connection):
        """Test that main calls the update API (2 send_request calls)."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "6",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn_obj = MagicMock()
        mock_conn_obj.send_request.side_effect = [
            {
                "status": 200,
                "body": json.dumps(SAMPLE_EPISODE),
                "headers": {},
            },
            {
                "status": 200,
                "body": json.dumps({"success": True}),
                "headers": {},
            },
        ]
        mock_connection.return_value = mock_conn_obj

        with pytest.raises(AnsibleExitJson):
            main()

        assert mock_conn_obj.send_request.call_count == 2

        update_call = mock_conn_obj.send_request.call_args_list[1]
        assert update_call[1]["method"] == "POST"
        assert "is_partial_data=1" in update_call[0][0]

    # No change skips API update call
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_no_change_skips_update_call(
        self,
        mock_module_class,
        mock_connection,
    ):
        """Test that when no change is needed, only GET is called."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_id": "abc-123-def-456",
            "severity": "4",
            "status": None,
            "owner": None,
            "instruction": None,
            "fields": None,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mc = make_mock_conn(200, json.dumps(SAMPLE_EPISODE))
        mock_connection.return_value = mc

        with pytest.raises(AnsibleExitJson):
            main()

        assert mc.send_request.call_count == 1
