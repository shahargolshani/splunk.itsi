# -*- coding: utf-8 -*-
# Copyright 2026 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
"""Unit tests for itsi_add_episode_comments module."""


import json
from unittest.mock import MagicMock, patch

import pytest
from ansible_collections.splunk.itsi.plugins.modules.itsi_add_episode_comments import (
    _build_comment_data,
    main,
)
from conftest import AnsibleExitJson, AnsibleFailJson, make_mock_conn

MODULE_PATH = "ansible_collections.splunk.itsi.plugins.modules.itsi_add_episode_comments"

SAMPLE_EPISODE_KEY = "84cb0211-6235-4058-acfc-80780649c6b8"
SAMPLE_COMMENT = "Test comment from Ansible"


# _build_comment_data
class TestBuildCommentData:
    """Tests for _build_comment_data helper."""

    def test_default_is_group(self):
        """Test building comment data with is_group=True (default)."""
        result = _build_comment_data(SAMPLE_EPISODE_KEY, SAMPLE_COMMENT, True)
        assert result == {
            "comment": SAMPLE_COMMENT,
            "event_id": SAMPLE_EPISODE_KEY,
            "is_group": True,
        }

    def test_is_group_false(self):
        """Test building comment data with is_group=False."""
        result = _build_comment_data(SAMPLE_EPISODE_KEY, SAMPLE_COMMENT, False)
        assert result["is_group"] is False
        assert result["event_id"] == SAMPLE_EPISODE_KEY

    def test_maps_episode_key_to_event_id(self):
        """Test that episode_key is mapped to event_id in the payload."""
        result = _build_comment_data("my-key-123", "some comment", True)
        assert "event_id" in result
        assert result["event_id"] == "my-key-123"
        assert "episode_key" not in result

    def test_comment_text_preserved(self):
        """Test that comment text is preserved as-is."""
        text = "Special chars: <>&\"' and unicode \u2603"
        result = _build_comment_data(SAMPLE_EPISODE_KEY, text, True)
        assert result["comment"] == text


# main() -- full module execution
class TestMain:
    """Tests for main module execution."""

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_success(self, mock_module_class, mock_connection):
        """Test successful comment addition returns changed=True."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_key": SAMPLE_EPISODE_KEY,
            "comment": SAMPLE_COMMENT,
            "is_group": True,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = make_mock_conn(
            200,
            json.dumps({"success": True}),
        )

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["episode_key"] == SAMPLE_EPISODE_KEY
        assert kw["before"] == {}
        assert kw["after"]["comment"] == SAMPLE_COMMENT
        assert kw["after"]["event_id"] == SAMPLE_EPISODE_KEY
        assert kw["after"]["is_group"] is True
        assert kw["diff"] == kw["after"]
        assert kw["response"] == {"success": True}

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_success_is_group_false(self, mock_module_class, mock_connection):
        """Test comment with is_group=False."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_key": SAMPLE_EPISODE_KEY,
            "comment": SAMPLE_COMMENT,
            "is_group": False,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = make_mock_conn(
            200,
            json.dumps({"success": True}),
        )

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["after"]["is_group"] is False

    # Check mode
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_check_mode(self, mock_module_class, mock_connection):
        """Test check mode returns changed=True without calling the API."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_key": SAMPLE_EPISODE_KEY,
            "comment": SAMPLE_COMMENT,
            "is_group": True,
        }
        mock_module.check_mode = True
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["changed"] is True
        assert kw["episode_key"] == SAMPLE_EPISODE_KEY
        assert kw["before"] == {}
        assert kw["after"]["comment"] == SAMPLE_COMMENT
        assert kw["diff"] == kw["after"]
        assert kw["response"] == {}

        # Connection should never be instantiated in check mode
        mock_connection.assert_not_called()

    # Exception handling
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_exception_on_connection(self, mock_module_class, mock_connection):
        """Test main handles connection exceptions."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_key": SAMPLE_EPISODE_KEY,
            "comment": SAMPLE_COMMENT,
            "is_group": True,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.side_effect = Exception("Connection failed")

        with pytest.raises(AnsibleFailJson):
            main()

        mock_module.fail_json.assert_called_once()
        assert "Error adding episode comment" in mock_module.fail_json.call_args[1]["msg"]
        assert mock_module.fail_json.call_args[1]["episode_key"] == SAMPLE_EPISODE_KEY

    @patch(f"{MODULE_PATH}._add_comment", side_effect=Exception("API timeout"))
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_exception_during_post(
        self,
        mock_module_class,
        mock_connection,
        mock_add_comment,
    ):
        """Test main handles exception during POST."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_key": SAMPLE_EPISODE_KEY,
            "comment": SAMPLE_COMMENT,
            "is_group": True,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = MagicMock()

        with pytest.raises(AnsibleFailJson):
            main()

        assert "Error adding episode comment" in mock_module.fail_json.call_args[1]["msg"]
        assert mock_module.fail_json.call_args[1]["episode_key"] == SAMPLE_EPISODE_KEY

    # episode_key always in result
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_episode_key_in_success_result(
        self,
        mock_module_class,
        mock_connection,
    ):
        """Test episode_key is always present in successful result."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_key": SAMPLE_EPISODE_KEY,
            "comment": SAMPLE_COMMENT,
            "is_group": True,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.return_value = make_mock_conn(
            200,
            json.dumps({"success": True}),
        )

        with pytest.raises(AnsibleExitJson):
            main()

        kw = mock_module.exit_json.call_args[1]
        assert kw["episode_key"] == SAMPLE_EPISODE_KEY

    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_episode_key_in_error_result(
        self,
        mock_module_class,
        mock_connection,
    ):
        """Test episode_key is present in fail_json result."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_key": SAMPLE_EPISODE_KEY,
            "comment": SAMPLE_COMMENT,
            "is_group": True,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_connection.side_effect = Exception("Boom")

        with pytest.raises(AnsibleFailJson):
            main()

        assert mock_module.fail_json.call_args[1]["episode_key"] == SAMPLE_EPISODE_KEY

    # API call verification
    @patch(f"{MODULE_PATH}.Connection")
    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_main_calls_api(self, mock_module_class, mock_connection):
        """Test that main calls the comment API (1 send_request call)."""
        mock_module = MagicMock()
        mock_module._socket_path = "/tmp/socket"
        mock_module.params = {
            "episode_key": SAMPLE_EPISODE_KEY,
            "comment": SAMPLE_COMMENT,
            "is_group": True,
        }
        mock_module.check_mode = False
        mock_module.fail_json.side_effect = AnsibleFailJson
        mock_module.exit_json.side_effect = AnsibleExitJson
        mock_module_class.return_value = mock_module

        mock_conn_obj = make_mock_conn(200, json.dumps({"success": True}))
        mock_connection.return_value = mock_conn_obj

        with pytest.raises(AnsibleExitJson):
            main()

        assert mock_conn_obj.send_request.call_count == 1

        call_args = mock_conn_obj.send_request.call_args
        assert "notable_event_comment" in call_args[1].get(
            "path",
            call_args[0][0] if call_args[0] else "",
        )
        assert call_args[1]["method"] == "POST"
