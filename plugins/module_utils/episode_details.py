# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026, Splunk ITSI Ansible Collection maintainers
"""Episode details utilities for Splunk ITSI Ansible modules."""


from typing import Any, Optional
from urllib.parse import quote_plus

from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

# API endpoint for ITSI notable event groups (episodes)
BASE_EPISODE_ENDPOINT = "servicesNS/nobody/SA-ITOA/event_management_interface/notable_event_group"


def get_episode_by_id(
    client: ItsiRequest,
    episode_id: str,
) -> Optional[dict[str, Any]]:
    """Fetch a single ITSI episode by its _key.

    Args:
        client: ItsiRequest instance for API requests.
        episode_id: The episode _key to retrieve.

    Returns:
        Episode dictionary from the API response, or None if not found (404).
    """
    path = f"{BASE_EPISODE_ENDPOINT}/{quote_plus(episode_id)}"
    result = client.get(path)
    if result is None:
        return None
    _status, _headers, body = result
    return body
