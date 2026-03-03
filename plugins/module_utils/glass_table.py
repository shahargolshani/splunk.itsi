# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026, Splunk ITSI Ansible Collection maintainers
"""Glass table utilities for Splunk ITSI Ansible modules."""


from typing import Any, Optional
from urllib.parse import quote_plus

from ansible_collections.splunk.itsi.plugins.module_utils.glass_table_definition_schema import (
    SCHEMA,
)
from ansible_collections.splunk.itsi.plugins.module_utils.itsi_request import ItsiRequest

try:
    from jsonschema import Draft7Validator

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# API endpoint for ITSI glass tables
BASE_GLASS_TABLE_ENDPOINT = "servicesNS/nobody/SA-ITOA/itoa_interface/glass_table"


def get_glass_table_by_id(
    client: ItsiRequest,
    glass_table_id: str,
) -> Optional[dict[str, Any]]:
    """Fetch a single ITSI glass table by its _key.

    Args:
        client: ItsiRequest instance for API requests.
        glass_table_id: The glass table _key to retrieve.

    Returns:
        Glass table dictionary from the API response, or None if not found (404).
    """
    path = f"{BASE_GLASS_TABLE_ENDPOINT}/{quote_plus(glass_table_id)}"
    result = client.get(path)
    if result is None:
        return None
    _status, _headers, body = result
    return body if isinstance(body, dict) else None


class GlassTableDefinitionValidator:
    """Validates an ITSI Glass Table definition against the JSON Schema
    and checks referential integrity between sections.
    """

    def validate(self, definition: dict[str, Any]) -> list[str]:
        """Run all validations and return a list of error strings.

        Args:
            definition: The glass table definition dict to validate.

        Returns:
            List of human-readable error strings. Empty means valid.
        """
        errors: list[str] = []
        errors.extend(self._validate_schema(definition))
        errors.extend(self._validate_referential_integrity(definition))
        return errors

    def _validate_schema(self, definition: dict[str, Any]) -> list[str]:
        """Validate definition against the JSON Schema using Draft7Validator.

        Returns an empty list when jsonschema is not installed.
        """
        if not HAS_JSONSCHEMA:
            return []

        validator = Draft7Validator(SCHEMA)
        schema_errors = sorted(
            validator.iter_errors(definition),
            key=lambda e: tuple(e.path),
        )
        return [f"{_format_path(err.path)}: {err.message}" for err in schema_errors]

    def _validate_referential_integrity(
        self,
        definition: dict[str, Any],
    ) -> list[str]:
        """Check cross-references between definition sections."""
        viz_ids = set((definition.get("visualizations") or {}).keys())
        input_ids = set((definition.get("inputs") or {}).keys())
        ds_ids = set((definition.get("dataSources") or {}).keys())
        condition_ids = set(
            (definition.get("expressions") or {}).get("conditions", {}).keys(),
        )
        layout = definition.get("layout") or {}
        layout_def_ids = set((layout.get("layoutDefinitions") or {}).keys())

        errors: list[str] = []
        errors.extend(self._check_layout_items(layout, viz_ids, input_ids))
        errors.extend(self._check_tab_layout_refs(layout, layout_def_ids))

        for section in ("visualizations", "inputs"):
            stanzas = definition.get(section) or {}
            errors.extend(self._check_datasource_refs(stanzas, section, ds_ids))
            errors.extend(
                self._check_visibility_conditions(stanzas, section, condition_ids),
            )

        errors.extend(
            self._check_datasource_extends(
                definition.get("dataSources") or {},
                ds_ids,
            ),
        )
        return errors

    @staticmethod
    def _check_layout_items(
        layout: dict[str, Any],
        viz_ids: set[str],
        input_ids: set[str],
    ) -> list[str]:
        """Verify layout structure items reference existing viz/input IDs."""
        errors: list[str] = []
        valid_ids = viz_ids | input_ids

        structure = layout.get("structure") or []
        for idx, block in enumerate(structure):
            if not isinstance(block, dict):
                continue
            item = block.get("item")
            if isinstance(item, str) and item not in valid_ids:
                errors.append(
                    f"$.layout.structure[{idx}].item: '{item}' " "is not defined in visualizations or inputs",
                )

        for ld_id, ld in (layout.get("layoutDefinitions") or {}).items():
            if not isinstance(ld, dict):
                continue
            for idx, block in enumerate(ld.get("structure") or []):
                if not isinstance(block, dict):
                    continue
                item = block.get("item")
                if isinstance(item, str) and item not in valid_ids:
                    errors.append(
                        f"$.layout.layoutDefinitions.{ld_id}"
                        f".structure[{idx}].item: '{item}' "
                        "is not defined in visualizations or inputs",
                    )
        return errors

    @staticmethod
    def _check_tab_layout_refs(
        layout: dict[str, Any],
        layout_def_ids: set[str],
    ) -> list[str]:
        """Verify tab layoutId references point to existing layout definitions."""
        errors: list[str] = []
        tabs = layout.get("tabs")
        if not isinstance(tabs, dict):
            return errors

        for idx, tab in enumerate(tabs.get("items") or []):
            if not isinstance(tab, dict):
                continue
            lid = tab.get("layoutId")
            if isinstance(lid, str) and lid not in layout_def_ids:
                errors.append(
                    f"$.layout.tabs.items[{idx}].layoutId: '{lid}' " "is not defined in layout.layoutDefinitions",
                )
        return errors

    @staticmethod
    def _check_datasource_refs(
        stanzas: dict[str, Any],
        section: str,
        ds_ids: set[str],
    ) -> list[str]:
        """Verify dataSources references in visualizations or inputs."""
        errors: list[str] = []
        for stanza_id, stanza in stanzas.items():
            if not isinstance(stanza, dict):
                continue
            ds_block = stanza.get("dataSources")
            if not isinstance(ds_block, dict):
                continue
            for ref_key, ref_val in ds_block.items():
                if isinstance(ref_val, str) and ref_val not in ds_ids:
                    errors.append(
                        f"$.{section}.{stanza_id}.dataSources.{ref_key}: " f"'{ref_val}' is not defined in dataSources",
                    )
        return errors

    @staticmethod
    def _check_datasource_extends(
        data_sources: dict[str, Any],
        ds_ids: set[str],
    ) -> list[str]:
        """Verify dataSource options.extend references exist."""
        errors: list[str] = []
        for ds_id, ds in data_sources.items():
            if not isinstance(ds, dict):
                continue
            options = ds.get("options")
            if not isinstance(options, dict):
                continue
            extend = options.get("extend")
            if isinstance(extend, str) and extend not in ds_ids:
                errors.append(
                    f"$.dataSources.{ds_id}.options.extend: " f"'{extend}' is not defined in dataSources",
                )
        return errors

    @staticmethod
    def _check_visibility_conditions(
        stanzas: dict[str, Any],
        section: str,
        condition_ids: set[str],
    ) -> list[str]:
        """Verify containerOptions visibility condition refs exist."""
        errors: list[str] = []
        for stanza_id, stanza in stanzas.items():
            if not isinstance(stanza, dict):
                continue
            container = stanza.get("containerOptions")
            if not isinstance(container, dict):
                continue
            visibility = container.get("visibility")
            if not isinstance(visibility, dict):
                continue

            for key in ("conditions", "showConditions", "hideConditions"):
                cond_list = visibility.get(key)
                if not isinstance(cond_list, list):
                    continue
                for idx, cond_val in enumerate(cond_list):
                    if isinstance(cond_val, str) and cond_val not in condition_ids:
                        errors.append(
                            f"$.{section}.{stanza_id}.containerOptions"
                            f".visibility.{key}[{idx}]: '{cond_val}' "
                            "is not defined in expressions.conditions",
                        )
        return errors


def _format_path(path_parts: Any) -> str:
    """Format a jsonschema error path as a readable JSON path string."""
    parts = ["$"]
    for item in path_parts:
        parts.append(f"[{item}]" if isinstance(item, int) else f".{item}")
    return "".join(parts)
