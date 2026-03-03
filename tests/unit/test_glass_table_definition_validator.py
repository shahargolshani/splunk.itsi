# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026 Splunk ITSI Ansible Collection maintainers
"""Unit tests for GlassTableDefinitionValidator."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from ansible_collections.splunk.itsi.plugins.module_utils.glass_table import (
    HAS_JSONSCHEMA,
    GlassTableDefinitionValidator,
)

VALID_DEFINITION = {
    "title": "Test Glass Table",
    "description": "A test definition",
    "visualizations": {
        "viz_1": {
            "type": "splunk.singlevalue",
            "dataSources": {"primary": "ds_1"},
        },
    },
    "dataSources": {
        "ds_1": {
            "type": "ds.search",
            "options": {"query": "| makeresults"},
        },
    },
    "inputs": {
        "input_trp": {
            "type": "input.timerange",
            "options": {"token": "global_time"},
        },
    },
    "layout": {
        "type": "absolute",
        "structure": [
            {"item": "viz_1", "type": "block", "position": {"x": 0, "y": 0, "w": 300, "h": 200}},
        ],
        "tabs": {
            "items": [{"layoutId": "layout_1"}],
        },
        "layoutDefinitions": {
            "layout_1": {
                "type": "absolute",
                "structure": [
                    {"item": "input_trp", "type": "block", "position": {"x": 0, "y": 0, "w": 300, "h": 50}},
                ],
            },
        },
    },
}


@pytest.fixture
def validator():
    return GlassTableDefinitionValidator()


class TestValidateFullDefinition:
    def test_valid_definition_returns_no_errors(self, validator):
        errors = validator.validate(VALID_DEFINITION)
        assert errors == []

    def test_empty_definition_returns_no_errors(self, validator):
        errors = validator.validate({})
        assert errors == []


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
class TestSchemaValidation:
    def test_invalid_top_level_property(self, validator):
        defn = {**VALID_DEFINITION, "bogus_key": True}
        errors = validator._validate_schema(defn)
        assert any("bogus_key" in e for e in errors)

    def test_invalid_visualization_type(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["visualizations"]["viz_1"]["type"] = 12345
        errors = validator._validate_schema(defn)
        assert len(errors) > 0

    def test_datasource_missing_type(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        del defn["dataSources"]["ds_1"]["type"]
        errors = validator._validate_schema(defn)
        assert any("type" in e for e in errors)

    def test_input_missing_type(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        del defn["inputs"]["input_trp"]["type"]
        errors = validator._validate_schema(defn)
        assert any("type" in e for e in errors)

    def test_valid_definition_no_schema_errors(self, validator):
        errors = validator._validate_schema(VALID_DEFINITION)
        assert errors == []


class TestSchemaValidationWithoutJsonschema:
    def test_graceful_skip_when_missing(self, validator):
        with patch(
            "ansible_collections.splunk.itsi.plugins.module_utils.glass_table.HAS_JSONSCHEMA",
            False,
        ):
            errors = validator._validate_schema(VALID_DEFINITION)
            assert errors == []


class TestReferentialIntegrityLayoutItems:
    def test_broken_layout_structure_item(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["layout"]["structure"] = [
            {"item": "viz_missing", "type": "block"},
        ]
        errors = validator._validate_referential_integrity(defn)
        assert any("viz_missing" in e and "layout.structure[0]" in e for e in errors)

    def test_broken_layout_definition_structure_item(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["layout"]["layoutDefinitions"]["layout_1"]["structure"] = [
            {"item": "viz_gone", "type": "block"},
        ]
        errors = validator._validate_referential_integrity(defn)
        assert any("viz_gone" in e and "layout_1" in e for e in errors)

    def test_valid_items_pass(self, validator):
        errors = validator._validate_referential_integrity(VALID_DEFINITION)
        assert errors == []


class TestReferentialIntegrityTabLayouts:
    def test_broken_tab_layout_ref(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["layout"]["tabs"]["items"] = [{"layoutId": "layout_missing"}]
        errors = validator._validate_referential_integrity(defn)
        assert any("layout_missing" in e for e in errors)

    def test_no_tabs_is_fine(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        del defn["layout"]["tabs"]
        errors = validator._validate_referential_integrity(defn)
        assert errors == []


class TestReferentialIntegrityDataSources:
    def test_broken_viz_datasource_ref(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["visualizations"]["viz_1"]["dataSources"]["primary"] = "ds_missing"
        errors = validator._validate_referential_integrity(defn)
        assert any("ds_missing" in e and "visualizations" in e for e in errors)

    def test_broken_input_datasource_ref(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["inputs"]["input_trp"]["dataSources"] = {"primary": "ds_nope"}
        errors = validator._validate_referential_integrity(defn)
        assert any("ds_nope" in e and "inputs" in e for e in errors)


class TestReferentialIntegrityExtends:
    def test_broken_extend_ref(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["dataSources"]["ds_chain"] = {
            "type": "ds.chain",
            "options": {"extend": "ds_nonexistent"},
        }
        errors = validator._validate_referential_integrity(defn)
        assert any("ds_nonexistent" in e for e in errors)

    def test_valid_extend_ref(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["dataSources"]["ds_chain"] = {
            "type": "ds.chain",
            "options": {"extend": "ds_1"},
        }
        errors = validator._validate_referential_integrity(defn)
        assert errors == []


class TestReferentialIntegrityVisibilityConditions:
    def test_broken_visibility_condition(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["visualizations"]["viz_1"]["containerOptions"] = {
            "visibility": {"conditions": ["cond_missing"]},
        }
        errors = validator._validate_referential_integrity(defn)
        assert any("cond_missing" in e for e in errors)

    def test_valid_visibility_condition(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["expressions"] = {
            "conditions": {"cond_1": {"value": "$tok$ > 0"}},
        }
        defn["visualizations"]["viz_1"]["containerOptions"] = {
            "visibility": {"showConditions": ["cond_1"]},
        }
        errors = validator._validate_referential_integrity(defn)
        assert errors == []

    def test_hide_conditions_also_checked(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["visualizations"]["viz_1"]["containerOptions"] = {
            "visibility": {"hideConditions": ["cond_nope"]},
        }
        errors = validator._validate_referential_integrity(defn)
        assert any("cond_nope" in e for e in errors)


class TestMultipleErrors:
    def test_collects_all_errors(self, validator):
        defn = deepcopy(VALID_DEFINITION)
        defn["visualizations"]["viz_1"]["dataSources"]["primary"] = "ds_bad"
        defn["layout"]["structure"] = [{"item": "viz_bad", "type": "block"}]
        defn["layout"]["tabs"]["items"] = [{"layoutId": "layout_bad"}]
        errors = validator._validate_referential_integrity(defn)
        assert len(errors) >= 3
