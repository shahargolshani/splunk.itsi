# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2026, Splunk ITSI Ansible Collection maintainers
"""JSON Schema for ITSI Glass Table / Dashboard Studio definitions.

Auto-generated from glass_table_definition_schema.json.
Do not edit by hand -- update the source JSON and regenerate.
"""

from __future__ import (
    absolute_import,
    division,
    print_function,
)

__metaclass__ = type

import json
from typing import Any

_SCHEMA_JSON = r"""
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://splunk.com/schemas/dashboard-studio/10.2/dashboard-definition.json",
  "title": "Splunk Dashboard Studio Definition",
  "description": "JSON Schema for Dashboard Studio and ITSI Glass Table definitions.",
  "type": "object",
  "properties": {
    "$schema": {
      "type": "string",
      "description": "JSON Schema reference URI. Used by IDEs for validation and IntelliSense."
    },
    "title": {
      "type": "string",
      "description": "The title of the dashboard."
    },
    "description": {
      "type": "string",
      "description": "A description of the dashboard."
    },
    "inputs": {
      "$ref": "#/definitions/inputs"
    },
    "defaults": {
      "$ref": "#/definitions/defaults"
    },
    "visualizations": {
      "$ref": "#/definitions/visualizations"
    },
    "dataSources": {
      "$ref": "#/definitions/dataSources"
    },
    "layout": {
      "$ref": "#/definitions/layout"
    },
    "expressions": {
      "$ref": "#/definitions/expressions"
    },
    "applicationProperties": {
      "$ref": "#/definitions/applicationProperties"
    }
  },
  "additionalProperties": false,
  "definitions": {
    "inputs": {
      "type": "object",
      "description": "Define input types and options, such as a multiselect dropdown. Each key is a unique input ID (e.g. 'input_global_trp').",
      "additionalProperties": {
        "$ref": "#/definitions/inputStanza"
      }
    },
    "inputStanza": {
      "type": "object",
      "description": "A single input definition.",
      "properties": {
        "type": {
          "type": "string",
          "description": "The type of input.",
          "enum": [
            "input.timerange",
            "input.dropdown",
            "input.multiselect",
            "input.text",
            "input.number",
            "input.button"
          ]
        },
        "title": {
          "type": "string",
          "description": "Title of the input displayed in Edit and View modes."
        },
        "options": {
          "type": "object",
          "description": "Configuration options for the input.",
          "properties": {
            "token": {
              "type": "string",
              "description": "Assign token values or options created by a connected data source query."
            },
            "defaultValue": {
              "description": "Default value of the input on dashboard load. Remains the value until the user changes it.",
              "oneOf": [
                {
                  "type": "string"
                },
                {
                  "type": "number"
                },
                {
                  "type": "boolean"
                }
              ]
            },
            "items": {
              "description": "Static label/value pairs for input.multiselect and input.dropdown, or a dynamic options syntax string.",
              "oneOf": [
                {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "label": {
                        "type": "string"
                      },
                      "value": {
                        "oneOf": [
                          {
                            "type": "string"
                          },
                          {
                            "type": "number"
                          }
                        ]
                      }
                    },
                    "required": [
                      "label",
                      "value"
                    ]
                  }
                },
                {
                  "type": "string"
                }
              ]
            },
            "min": {
              "type": "number",
              "description": "Minimum number a user can select (input.number only)."
            },
            "max": {
              "type": "number",
              "description": "Maximum number a user can select (input.number only)."
            },
            "step": {
              "type": "number",
              "description": "Interval for up/down arrows (input.number only)."
            },
            "clearDefaultOnSelection": {
              "type": "boolean",
              "default": true,
              "description": "When false, the defaultValue remains selected when a user selects other options (input.multiselect). Default is true."
            },
            "labelField": {
              "type": "string",
              "description": "Field from the connected data source to use as the display label (input.dropdown, input.multiselect)."
            },
            "valueField": {
              "type": "string",
              "description": "Field from the connected data source to use as the submitted value (input.dropdown, input.multiselect)."
            },
            "tokenPrefix": {
              "type": "string",
              "description": "Characters prepended to each selected value in the token string (input.multiselect). Example: '\"' for SPL IN() syntax."
            },
            "tokenSuffix": {
              "type": "string",
              "description": "Characters appended to each selected value in the token string (input.multiselect). Example: '\"' for SPL IN() syntax."
            },
            "tokenSeparator": {
              "type": "string",
              "const": ",",
              "description": "Separator between selected values (input.multiselect). Only comma is supported."
            },
            "selectFirstSearchResult": {
              "type": "boolean",
              "description": "Automatically select the first result from the connected data source (input.dropdown)."
            },
            "placeholder": {
              "type": "string",
              "description": "Placeholder text shown when no value is selected (input.dropdown, input.text, input.number)."
            },
            "encoding": {
              "type": "object",
              "description": "Field encoding for search-based inputs (input.dropdown, input.multiselect).",
              "properties": {
                "label": {
                  "type": "string",
                  "description": "Dynamic options syntax for the display label. Example: 'primary[0]' to use the first field from the primary data source."
                },
                "value": {
                  "type": "string",
                  "description": "Dynamic options syntax for the submitted value. Example: 'primary[0]' or 'primary[1]'."
                }
              },
              "additionalProperties": true
            }
          },
          "additionalProperties": true
        },
        "dataSources": {
          "type": "object",
          "description": "Data sources connected to this input. ID references should point to keys that exist in the top-level 'dataSources' object.",
          "properties": {
            "primary": {
              "type": "string",
              "description": "The unique ID of the primary data source. Must reference an existing key in the top-level 'dataSources' object."
            }
          },
          "additionalProperties": true
        },
        "context": {
          "type": "object",
          "description": "Dynamic variable context for dynamic options syntax.",
          "additionalProperties": true
        },
        "containerOptions": {
          "$ref": "#/definitions/containerOptions"
        },
        "hideWhenNoData": {
          "type": "boolean",
          "description": "Set to true to conceal the input if no data is available to populate the input options."
        },
        "hideInViewMode": {
          "type": "boolean",
          "description": "Set to true to conceal any input from users observing the dashboard from View mode."
        }
      },
      "required": [
        "type"
      ],
      "additionalProperties": true
    },
    "defaults": {
      "type": "object",
      "description": "Global defaults for visualizations, data sources, and tokens.",
      "examples": [
        {
          "dataSources": {
            "global": {
              "options": {
                "queryParameters": {
                  "earliest": "$global_time.earliest$",
                  "latest": "$global_time.latest$"
                },
                "refreshType": "delay",
                "refresh": "$global_refresh_rate$"
              }
            }
          }
        }
      ],
      "properties": {
        "dataSources": {
          "type": "object",
          "description": "Default settings for data source types. Use 'global' key to apply to all data sources.",
          "additionalProperties": {
            "$ref": "#/definitions/defaultsDataSourceStanza"
          }
        },
        "visualizations": {
          "type": "object",
          "description": "Default settings for visualization types (e.g. 'splunk.pie').",
          "additionalProperties": {
            "$ref": "#/definitions/defaultsVisualizationStanza"
          }
        },
        "tokens": {
          "type": "object",
          "description": "Default token values grouped by namespace.",
          "properties": {
            "default": {
              "type": "object",
              "description": "Default namespace for token values. Keys are token names, values are defaults on load.",
              "additionalProperties": {
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "number"
                  },
                  {
                    "type": "boolean"
                  },
                  {
                    "type": "object",
                    "properties": {
                      "value": {
                        "oneOf": [
                          {
                            "type": "string"
                          },
                          {
                            "type": "number"
                          },
                          {
                            "type": "boolean"
                          }
                        ]
                      }
                    },
                    "required": [
                      "value"
                    ],
                    "additionalProperties": false
                  }
                ]
              }
            }
          },
          "additionalProperties": true
        }
      },
      "additionalProperties": true
    },
    "defaultsDataSourceStanza": {
      "type": "object",
      "description": "Defaults stanza for a data source type key under defaults.dataSources (including the special 'global' key).",
      "properties": {
        "options": {
          "$ref": "#/definitions/defaultsDataSourceOptions"
        }
      },
      "additionalProperties": true
    },
    "defaultsDataSourceOptions": {
      "type": "object",
      "description": "Common defaults options used in ITSI Glass Tables and Dashboard Studio data sources.",
      "properties": {
        "query": {
          "type": "string",
          "description": "Default SPL search query expression. Usually omitted for global defaults."
        },
        "queryParameters": {
          "type": "object",
          "description": "Default query parameters, including time bounds.",
          "properties": {
            "earliest": {
              "type": "string",
              "description": "Default earliest bound (for example '$global_time.earliest$')."
            },
            "latest": {
              "type": "string",
              "description": "Default latest bound (for example '$global_time.latest$')."
            },
            "sampleRatio": {
              "type": "string"
            },
            "timezone": {
              "type": "string"
            }
          },
          "additionalProperties": true
        },
        "refresh": {
          "type": "string",
          "description": "Default refresh interval (for example '60s' or '$global_refresh_rate$')."
        },
        "refreshType": {
          "type": "string",
          "enum": [
            "delay",
            "interval"
          ],
          "description": "Default refresh behavior."
        },
        "enableSmartSources": {
          "type": "boolean"
        }
      },
      "additionalProperties": true
    },
    "defaultsVisualizationStanza": {
      "type": "object",
      "description": "Defaults stanza for a visualization type key under defaults.visualizations.",
      "properties": {
        "options": {
          "type": "object",
          "additionalProperties": true
        }
      },
      "additionalProperties": true
    },
    "visualizations": {
      "type": "object",
      "description": "Customize visualization options. Each key is a unique visualization ID (conventionally prefixed 'viz_', e.g. 'viz_BHTFSi0R').",
      "propertyNames": {
        "type": "string",
        "pattern": "^viz_"
      },
      "additionalProperties": {
        "$ref": "#/definitions/visualizationStanza"
      }
    },
    "visualizationStanza": {
      "type": "object",
      "description": "A single visualization definition.",
      "properties": {
        "type": {
          "description": "The visualization type.",
          "anyOf": [
            {
              "type": "string",
              "enum": [
                "splunk.area",
                "splunk.bar",
                "splunk.bubble",
                "splunk.choropleth.svg",
                "splunk.column",
                "splunk.ellipse",
                "splunk.events",
                "splunk.fillergauge",
                "splunk.icon",
                "splunk.image",
                "splunk.img",
                "splunk.line",
                "abslayout.line",
                "splunk.linkgraph",
                "splunk.map",
                "splunk.markdown",
                "splunk.markergauge",
                "splunk.parallelcoordinates",
                "splunk.pie",
                "splunk.punchcard",
                "splunk.rectangle",
                "splunk.sankey",
                "splunk.scatter",
                "splunk.singlevalueicon",
                "splunk.singlevalue",
                "splunk.singlevalueradial",
                "splunk.table",
                "splunk.timeline",
                "viz.custom"
              ]
            },
            {
              "type": "string",
              "pattern": "^(splunk\\..+|viz\\..+|abslayout\\..+)$"
            }
          ]
        },
        "title": {
          "type": "string",
          "description": "Title name displayed on the visualization."
        },
        "description": {
          "type": "string",
          "description": "Additional context displayed within the visualization panel."
        },
        "options": {
          "type": "object",
          "description": "Visualization-specific options.",
          "additionalProperties": true
        },
        "containerOptions": {
          "$ref": "#/definitions/containerOptions"
        },
        "dataSources": {
          "type": "object",
          "description": "Data sources linked to this visualization by unique ID reference.",
          "properties": {
            "primary": {
              "type": "string",
              "description": "The unique ID of the primary data source that drives this visualization."
            },
            "annotation": {
              "type": "string",
              "description": "The unique ID of the annotation (secondary) data source for event annotations."
            }
          },
          "additionalProperties": {
            "type": "string"
          }
        },
        "context": {
          "type": "object",
          "description": "Dynamic variable context for conditional formatting.",
          "additionalProperties": true
        },
        "showLastUpdated": {
          "type": "boolean",
          "description": "Whether to show the last-updated timestamp on the visualization."
        },
        "showProgressBar": {
          "type": "boolean",
          "description": "Whether to show a progress bar while the search is running."
        },
        "hideWhenNoData": {
          "type": "boolean",
          "description": "Set to true to conceal the visualization if no data is available."
        },
        "eventHandlers": {
          "type": "array",
          "description": "Event handlers for interactions.",
          "items": {
            "$ref": "#/definitions/eventHandler"
          }
        }
      },
      "required": [
        "type"
      ],
      "additionalProperties": true
    },
    "dataSources": {
      "type": "object",
      "description": "Specify your data sources, searches, and options. Each key is a unique data source ID prefixed 'ds_'.",
      "propertyNames": {
        "type": "string",
        "pattern": "^ds_"
      },
      "additionalProperties": {
        "$ref": "#/definitions/dataSourceStanza"
      }
    },
    "dataSourceStanza": {
      "type": "object",
      "description": "A single data source definition.",
      "properties": {
        "type": {
          "type": "string",
          "description": "The type of data source.",
          "enum": [
            "ds.search",
            "ds.chain",
            "ds.savedSearch",
            "ds.test"
          ]
        },
        "name": {
          "type": "string",
          "description": "A human-readable name for the data source."
        },
        "options": {
          "type": "object",
          "description": "Data source configuration options.",
          "properties": {
            "query": {
              "type": "string",
              "description": "The SPL search query."
            },
            "queryParameters": {
              "type": "object",
              "description": "Time range and other query parameters.",
              "properties": {
                "earliest": {
                  "type": "string"
                },
                "latest": {
                  "type": "string"
                },
                "sampleRatio": {
                  "type": "string",
                  "default": "1"
                },
                "timezone": {
                  "type": "string"
                }
              },
              "additionalProperties": true
            },
            "ref": {
              "type": "string",
              "description": "Only for ds.savedSearch. The exact name of the saved report."
            },
            "app": {
              "type": "string",
              "description": "Only for ds.savedSearch. The app associated with the saved report.",
              "default": "search"
            },
            "refresh": {
              "type": "string",
              "description": "Refresh interval as a time expression (e.g. '5s', '1m', '30s')."
            },
            "refreshType": {
              "type": "string",
              "enum": [
                "delay",
                "interval"
              ],
              "default": "delay"
            },
            "enableSmartSources": {
              "type": "boolean"
            },
            "extend": {
              "type": "string",
              "description": "For ds.chain only: the ID of the base/parent data source to extend."
            },
            "data": {
              "type": "object",
              "description": "Inline mock data for ds.test data sources.",
              "properties": {
                "fields": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "name": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "name"
                    ]
                  }
                },
                "columns": {
                  "type": "array",
                  "items": {
                    "type": "array",
                    "items": {
                      "oneOf": [
                        {
                          "type": "string"
                        },
                        {
                          "type": "number"
                        },
                        {
                          "type": "boolean"
                        },
                        {
                          "type": "null"
                        }
                      ]
                    }
                  }
                }
              },
              "additionalProperties": true
            },
            "meta": {
              "type": "object",
              "description": "Metadata for ITSI KPI data sources.",
              "properties": {
                "kpiID": {
                  "type": "string"
                },
                "serviceID": {
                  "type": "string"
                },
                "skipAggregation": {
                  "type": "boolean"
                }
              },
              "additionalProperties": true
            }
          },
          "additionalProperties": true
        }
      },
      "required": [
        "type"
      ],
      "additionalProperties": true
    },
    "layout": {
      "type": "object",
      "description": "Layout section: list inputs, change canvas size, define tab structure, and position visualizations.",
      "properties": {
        "type": {
          "type": "string",
          "enum": [
            "absolute",
            "grid"
          ]
        },
        "structure": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/structureBlock"
          }
        },
        "options": {
          "type": "object",
          "properties": {
            "backgroundColor": {
              "type": "string"
            },
            "display": {
              "type": "string",
              "enum": [
                "auto",
                "actual-size",
                "fit-to-width"
              ]
            },
            "width": {
              "type": "number",
              "default": 1140
            },
            "height": {
              "type": "number",
              "default": 960
            },
            "gutterSize": {
              "type": "number",
              "minimum": 8,
              "maximum": 16,
              "default": 8
            },
            "backgroundImage": {
              "type": "object",
              "properties": {
                "src": {
                  "type": "string"
                },
                "x": {
                  "type": "number"
                },
                "y": {
                  "type": "number"
                },
                "w": {
                  "type": "number"
                },
                "h": {
                  "type": "number"
                },
                "sizeType": {
                  "type": "string",
                  "enum": [
                    "auto",
                    "contain",
                    "cover"
                  ],
                  "default": "contain"
                }
              },
              "additionalProperties": true
            },
            "submitButton": {
              "type": "boolean",
              "default": false
            },
            "submitOnDashboardLoad": {
              "type": "boolean",
              "default": false
            },
            "showTitleAndDescription": {
              "type": "boolean"
            }
          },
          "additionalProperties": true
        },
        "globalInputs": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "tabs": {
          "type": "object",
          "properties": {
            "items": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "label": {
                    "type": "string"
                  },
                  "layoutId": {
                    "type": "string"
                  },
                  "icon": {
                    "type": "string"
                  }
                },
                "required": [
                  "layoutId"
                ]
              }
            },
            "options": {
              "type": "object",
              "properties": {
                "barPosition": {
                  "type": "string",
                  "enum": [
                    "top",
                    "left"
                  ]
                },
                "showTabBar": {
                  "type": "boolean"
                }
              },
              "additionalProperties": true
            }
          },
          "additionalProperties": true
        },
        "layoutDefinitions": {
          "type": "object",
          "additionalProperties": {
            "$ref": "#/definitions/layoutDefinition"
          }
        }
      },
      "additionalProperties": true
    },
    "layoutDefinition": {
      "type": "object",
      "description": "A single layout definition for a tab.",
      "properties": {
        "type": {
          "type": "string",
          "enum": [
            "absolute",
            "grid"
          ]
        },
        "options": {
          "type": "object",
          "properties": {
            "backgroundColor": {
              "type": "string"
            },
            "display": {
              "type": "string",
              "enum": [
                "auto",
                "actual-size",
                "fit-to-width"
              ]
            },
            "width": {
              "type": "number",
              "default": 1140
            },
            "height": {
              "type": "number",
              "default": 960
            },
            "gutterSize": {
              "type": "number",
              "minimum": 8,
              "maximum": 16,
              "default": 8
            },
            "backgroundImage": {
              "type": "object",
              "properties": {
                "src": {
                  "type": "string"
                },
                "x": {
                  "type": "number"
                },
                "y": {
                  "type": "number"
                },
                "w": {
                  "type": "number"
                },
                "h": {
                  "type": "number"
                },
                "sizeType": {
                  "type": "string",
                  "enum": [
                    "auto",
                    "contain",
                    "cover"
                  ],
                  "default": "contain"
                }
              },
              "additionalProperties": true
            }
          },
          "additionalProperties": true
        },
        "structure": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/structureBlock"
          }
        }
      },
      "required": [
        "type"
      ],
      "additionalProperties": true
    },
    "structureBlock": {
      "type": "object",
      "description": "A positioned element in the layout structure.",
      "properties": {
        "item": {
          "type": "string",
          "description": "The unique ID of the visualization or input to place.",
          "pattern": "^(viz_|input_)"
        },
        "type": {
          "type": "string",
          "enum": [
            "block",
            "line"
          ]
        },
        "position": {
          "type": "object",
          "properties": {
            "x": {
              "type": "number"
            },
            "y": {
              "type": "number"
            },
            "w": {
              "type": "number"
            },
            "h": {
              "type": "number"
            },
            "from": {
              "type": "object",
              "oneOf": [
                {
                  "properties": {
                    "item": {
                      "type": "string"
                    },
                    "port": {
                      "type": "string",
                      "enum": [
                        "n",
                        "s",
                        "e",
                        "w"
                      ]
                    }
                  },
                  "required": [
                    "item",
                    "port"
                  ]
                },
                {
                  "properties": {
                    "x": {
                      "type": "number"
                    },
                    "y": {
                      "type": "number"
                    }
                  },
                  "required": [
                    "x",
                    "y"
                  ]
                }
              ]
            },
            "to": {
              "type": "object",
              "oneOf": [
                {
                  "properties": {
                    "item": {
                      "type": "string"
                    },
                    "port": {
                      "type": "string",
                      "enum": [
                        "n",
                        "s",
                        "e",
                        "w"
                      ]
                    }
                  },
                  "required": [
                    "item",
                    "port"
                  ]
                },
                {
                  "properties": {
                    "x": {
                      "type": "number"
                    },
                    "y": {
                      "type": "number"
                    }
                  },
                  "required": [
                    "x",
                    "y"
                  ]
                }
              ]
            }
          }
        },
        "inputs": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "item",
        "type"
      ]
    },
    "expressions": {
      "type": "object",
      "description": "Specify expressions for conditional panel visibility or token evaluation.",
      "properties": {
        "conditions": {
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "name": {
                "type": "string"
              },
              "value": {
                "type": "string"
              }
            },
            "required": [
              "value"
            ]
          }
        }
      },
      "additionalProperties": true
    },
    "applicationProperties": {
      "type": "object",
      "description": "Dashboard-level view mode settings.",
      "properties": {
        "collapseNavigation": {
          "type": "boolean",
          "default": false
        },
        "downsampleVisualizations": {
          "type": "boolean",
          "default": true
        },
        "hideViewModeActionMenu": {
          "type": "boolean",
          "default": false
        },
        "hideEdit": {
          "type": "boolean",
          "default": false
        },
        "hideOpenInSearch": {
          "type": "boolean",
          "default": false
        },
        "hideExport": {
          "type": "boolean",
          "default": false
        }
      },
      "additionalProperties": false
    },
    "containerOptions": {
      "type": "object",
      "description": "Options for the container around a visualization or input.",
      "properties": {
        "title": {
          "type": "object",
          "properties": {
            "color": {
              "type": "string"
            }
          },
          "additionalProperties": true
        },
        "description": {
          "type": "object",
          "properties": {
            "color": {
              "type": "string"
            }
          },
          "additionalProperties": true
        },
        "visibility": {
          "type": "object",
          "properties": {
            "conditions": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "showConditions": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "hideConditions": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "additionalProperties": true
        }
      },
      "additionalProperties": true
    },
    "eventHandler": {
      "type": "object",
      "description": "An event handler attached to a visualization.",
      "oneOf": [
        {
          "$ref": "#/definitions/eventHandlerSetToken"
        },
        {
          "$ref": "#/definitions/eventHandlerLinkToDashboard"
        },
        {
          "$ref": "#/definitions/eventHandlerCustomUrl"
        }
      ]
    },
    "eventHandlerSetToken": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "const": "drilldown.setToken"
        },
        "options": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string"
            },
            "key": {
              "type": "string"
            },
            "value": {
              "type": "string"
            },
            "tokens": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "token": {
                    "type": "string"
                  },
                  "key": {
                    "type": "string"
                  },
                  "value": {
                    "type": "string"
                  }
                },
                "required": [
                  "token"
                ]
              },
              "minItems": 1
            }
          },
          "additionalProperties": true
        }
      },
      "required": [
        "type",
        "options"
      ],
      "additionalProperties": true
    },
    "eventHandlerLinkToDashboard": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "const": "drilldown.linkToDashboard"
        },
        "options": {
          "type": "object",
          "properties": {
            "app": {
              "type": "string"
            },
            "dashboard": {
              "type": "string"
            },
            "newTab": {
              "type": "boolean",
              "default": false
            },
            "tokens": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "token": {
                    "type": "string"
                  },
                  "value": {
                    "type": "string"
                  }
                },
                "required": [
                  "token",
                  "value"
                ]
              }
            }
          },
          "required": [
            "dashboard"
          ],
          "additionalProperties": true
        }
      },
      "required": [
        "type",
        "options"
      ],
      "additionalProperties": true
    },
    "eventHandlerCustomUrl": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "const": "drilldown.customUrl"
        },
        "options": {
          "type": "object",
          "properties": {
            "url": {
              "type": "string"
            },
            "newTab": {
              "type": "boolean",
              "default": false
            }
          },
          "required": [
            "url"
          ],
          "additionalProperties": true
        }
      },
      "required": [
        "type",
        "options"
      ],
      "additionalProperties": true
    }
  }
}
"""

SCHEMA: dict[str, Any] = json.loads(_SCHEMA_JSON)
