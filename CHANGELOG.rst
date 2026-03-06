====================================
Splunk ITSI Collection Release Notes
====================================

.. contents:: Topics

v1.0.1
======

Release Summary
---------------

Release summary for v1.0.1

Bugfixes
--------

- Added required ``future imports`` and ``__metaclass__ = type`` boilerplate to all plugin and module Python files for ansible-test sanity compliance.
- Fixed ``requirements.txt`` and remove ansible-core dependency.
- Updated README.md according to Ansible Certified Collections README Template.

v1.0.0
======

Release Summary
---------------

Release summary for v1.0.0

Minor Changes
-------------

- Add comprehensive unit tests for ``ItsiRequest`` in ``tests/unit/test_itsi_request.py``
- Add integration tests for itsi_aggregation_policy and itsi_aggregation_policy_info modules.
- Add integration tests for itsi_correlation_search and itsi_correlation_search_info modules.
- Add new ``ItsiRequest`` class in ``module_utils/itsi_request.py`` as the unified HTTP abstraction layer for all ITSI modules.
- Add new module ``itsi_add_episode_comments`` for adding comments to ITSI episodes.
- Add new module ``itsi_aggregation_policy_info`` for querying ITSI aggregation policies by ID, title, or listing all.
- Add new module ``itsi_aggregation_policy`` for managing ITSI aggregation policies (create, update, delete).
- Add new module ``itsi_correlation_search_info`` for querying ITSI correlation searches.
- Add new module ``itsi_correlation_search`` for managing ITSI correlation searches (create, update, delete).
- Add new module ``itsi_episode_details_info`` for querying ITSI episodes by ID, listing with filters, or retrieving a count.
- Add new module ``itsi_glass_table_info`` for querying ITSI Glass Table objects.
- Add new module ``itsi_glass_table`` for managing ITSI Glass Table objects (create, update, delete).
- Add new module ``itsi_service_info`` for querying ITSI Service objects.
- Add new module ``itsi_service`` for managing ITSI Service objects (create, update, delete).
- Add new module ``itsi_update_episode_details`` for updating specific fields of ITSI episodes (severity, status, owner, instruction).
- Add unit tests for itsi_aggregation_policy and itsi_aggregation_policy_info modules.
- Add unit tests for itsi_correlation_search and itsi_correlation_search_info modules.
- Add validated content for Event-Driven Ansible (EDA) rulebook activation with Splunk ITSI webhook integration.
- Align all modules to use a unified diff implementation for consistent change detection.
- Centralize HTTP response status handling in ``ItsiRequest`` class.
- Refactor all ITSI modules to use ``ItsiRequest`` instead of the previous standalone functions
- Refactor shared utility functions into module_utils/itsi_utils.py for code reuse.
- Remove deprecated ``_send``, ``_send_request``, and ``send_itsi_request`` functions
- Standardize return result across all info modules `(changed, response)`
- Standardize return result across all modules `(changed, before, after, diff, response)`
- itsi_aggregation_policy - Use dedicated function for handling empty lists in ``filter_criteria`` and ``breaking_criteria``.

New Plugins
-----------

Httpapi
~~~~~~~

- splunk.itsi.itsi_api_client - HttpApi Plugin for Splunk ITSI.

New Modules
-----------

- splunk.itsi.itsi_add_episode_comments - Add comments to Splunk ITSI episodes.
- splunk.itsi.itsi_aggregation_policy - Manage Splunk ITSI aggregation policies.
- splunk.itsi.itsi_aggregation_policy_info - Get information about Splunk ITSI aggregation policies.
- splunk.itsi.itsi_correlation_search - Manage Splunk ITSI correlation searches.
- splunk.itsi.itsi_correlation_search_info - Query Splunk ITSI correlation searches.
- splunk.itsi.itsi_episode_details_info - Read Splunk ITSI notable_event_group (episodes).
- splunk.itsi.itsi_glass_table - Manage Splunk ITSI Glass Table objects via itoa_interface.
- splunk.itsi.itsi_glass_table_info - Read Splunk ITSI glass table objects via itoa_interface.
- splunk.itsi.itsi_service - Manage Splunk ITSI Service objects via itoa_interface.
- splunk.itsi.itsi_service_info - Gather facts about Splunk ITSI Service objects via itoa_interface.
- splunk.itsi.itsi_update_episode_details - Update specific fields of Splunk ITSI episodes.
