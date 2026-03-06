# Splunk ITSI Collection Release Notes

**Topics**

- <a href="#v1-0-1">v1\.0\.1</a>
  - <a href="#release-summary">Release Summary</a>
  - <a href="#bugfixes">Bugfixes</a>
- <a href="#v1-0-0">v1\.0\.0</a>
  - <a href="#release-summary-1">Release Summary</a>
  - <a href="#minor-changes">Minor Changes</a>
  - <a href="#new-plugins">New Plugins</a>
    - <a href="#httpapi">Httpapi</a>
  - <a href="#new-modules">New Modules</a>

<a id="v1-0-1"></a>

## v1\.0\.1

<a id="release-summary"></a>

### Release Summary

Release summary for v1\.0\.1

<a id="bugfixes"></a>

### Bugfixes

- Added required <code>future imports</code> and <code>\_\_metaclass\_\_ \= type</code> boilerplate to all plugin and module Python files for ansible\-test sanity compliance\.
- Fixed <code>requirements\.txt</code> and remove ansible\-core dependency\.
- Updated README\.md according to Ansible Certified Collections README Template\.

<a id="v1-0-0"></a>

## v1\.0\.0

<a id="release-summary-1"></a>

### Release Summary

Release summary for v1\.0\.0

<a id="minor-changes"></a>

### Minor Changes

- Add comprehensive unit tests for <code>ItsiRequest</code> in <code>tests/unit/test_itsi_request\.py</code>
- Add integration tests for itsi_aggregation_policy and itsi_aggregation_policy_info modules\.
- Add integration tests for itsi_correlation_search and itsi_correlation_search_info modules\.
- Add new <code>ItsiRequest</code> class in <code>module_utils/itsi_request\.py</code> as the unified HTTP abstraction layer for all ITSI modules\.
- Add new module <code>itsi_add_episode_comments</code> for adding comments to ITSI episodes\.
- Add new module <code>itsi_aggregation_policy_info</code> for querying ITSI aggregation policies by ID\, title\, or listing all\.
- Add new module <code>itsi_aggregation_policy</code> for managing ITSI aggregation policies \(create\, update\, delete\)\.
- Add new module <code>itsi_correlation_search_info</code> for querying ITSI correlation searches\.
- Add new module <code>itsi_correlation_search</code> for managing ITSI correlation searches \(create\, update\, delete\)\.
- Add new module <code>itsi_episode_details_info</code> for querying ITSI episodes by ID\, listing with filters\, or retrieving a count\.
- Add new module <code>itsi_glass_table_info</code> for querying ITSI Glass Table objects\.
- Add new module <code>itsi_glass_table</code> for managing ITSI Glass Table objects \(create\, update\, delete\)\.
- Add new module <code>itsi_service_info</code> for querying ITSI Service objects\.
- Add new module <code>itsi_service</code> for managing ITSI Service objects \(create\, update\, delete\)\.
- Add new module <code>itsi_update_episode_details</code> for updating specific fields of ITSI episodes \(severity\, status\, owner\, instruction\)\.
- Add unit tests for itsi_aggregation_policy and itsi_aggregation_policy_info modules\.
- Add unit tests for itsi_correlation_search and itsi_correlation_search_info modules\.
- Add validated content for Event\-Driven Ansible \(EDA\) rulebook activation with Splunk ITSI webhook integration\.
- Align all modules to use a unified diff implementation for consistent change detection\.
- Centralize HTTP response status handling in <code>ItsiRequest</code> class\.
- Refactor all ITSI modules to use <code>ItsiRequest</code> instead of the previous standalone functions
- Refactor shared utility functions into module_utils/itsi_utils\.py for code reuse\.
- Remove deprecated <code>\_send</code>\, <code>\_send_request</code>\, and <code>send_itsi_request</code> functions
- Standardize return result across all info modules <em class="title-reference">\(changed\, response\)</em>
- Standardize return result across all modules <em class="title-reference">\(changed\, before\, after\, diff\, response\)</em>
- itsi_aggregation_policy \- Use dedicated function for handling empty lists in <code>filter_criteria</code> and <code>breaking_criteria</code>\.

<a id="new-plugins"></a>

### New Plugins

<a id="httpapi"></a>

#### Httpapi

- splunk\.itsi\.itsi_api_client \- HttpApi Plugin for Splunk ITSI\.

<a id="new-modules"></a>

### New Modules

- splunk\.itsi\.itsi_add_episode_comments \- Add comments to Splunk ITSI episodes\.
- splunk\.itsi\.itsi_aggregation_policy \- Manage Splunk ITSI aggregation policies\.
- splunk\.itsi\.itsi_aggregation_policy_info \- Get information about Splunk ITSI aggregation policies\.
- splunk\.itsi\.itsi_correlation_search \- Manage Splunk ITSI correlation searches\.
- splunk\.itsi\.itsi_correlation_search_info \- Query Splunk ITSI correlation searches\.
- splunk\.itsi\.itsi_episode_details_info \- Read Splunk ITSI notable_event_group \(episodes\)\.
- splunk\.itsi\.itsi_glass_table \- Manage Splunk ITSI Glass Table objects via itoa_interface\.
- splunk\.itsi\.itsi_glass_table_info \- Read Splunk ITSI glass table objects via itoa_interface\.
- splunk\.itsi\.itsi_service \- Manage Splunk ITSI Service objects via itoa_interface\.
- splunk\.itsi\.itsi_service_info \- Gather facts about Splunk ITSI Service objects via itoa_interface\.
- splunk\.itsi\.itsi_update_episode_details \- Update specific fields of Splunk ITSI episodes\.
