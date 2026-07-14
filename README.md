# Splunk ITSI Ansible Collection

[![Collection Tests](https://github.com/ansible-collections/splunk.itsi/actions/workflows/tests.yml/badge.svg?event=schedule)](https://github.com/ansible-collections/splunk.itsi/actions/workflows/tests.yml)
[![Integration Tests](https://github.com/ansible-collections/splunk.itsi/actions/workflows/network_integration.yml/badge.svg?branch=main&event=schedule)](https://github.com/ansible-collections/splunk.itsi/actions/workflows/network_integration.yml)
[![SonarCloud Coverage](https://sonarcloud.io/api/project_badges/measure?project=ansible-collections_splunk.itsi&metric=coverage)](https://sonarcloud.io/project/overview?id=ansible-collections_splunk.itsi)

This is the [Ansible Collection](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html)
provided by the [Ansible Ecosystem Engineering team](https://github.com/ansible-collections)
for automating actions in [Splunk IT Service Intelligence (ITSI)](https://www.splunk.com/en_us/products/it-service-intelligence.html).

This Collection is meant for distribution through
[Ansible Galaxy](https://galaxy.ansible.com/) as is available for all
[Ansible](https://github.com/ansible/ansible) users to utilize, contribute to,
and provide feedback about.

## Description

This collection provides Ansible modules and plugins to automate IT service operations in [Splunk IT Service Intelligence](https://www.splunk.com/en_us/products/it-service-intelligence.html), including management of episodes, aggregation policies, correlation searches, glass tables, services, and Event-Driven Ansible (EDA) integrations.

## Communication

* Join the Ansible forum:
  * [Get Help](https://forum.ansible.com/c/help/6): get help or help others.
  * [Social Spaces](https://forum.ansible.com/c/chat/4): gather and interact with fellow enthusiasts.
  * [News & Announcements](https://forum.ansible.com/c/news/5): track project-wide announcements including social events.

* The Ansible [Bullhorn newsletter](https://docs.ansible.com/ansible/devel/community/communication.html#the-bullhorn): used to announce releases and important changes.

For more information about communication, see the [Ansible communication guide](https://docs.ansible.com/ansible/devel/community/communication.html).

## Support

As Red Hat Ansible Certified Content, this collection is entitled to support through the **Ansible Automation Platform (AAP)** using the **Create issue** button on the top right corner.\
Red Hat group support team - Ansible Ecosystem Engineering team (@eco-ansible-content)\
If a support case cannot be opened with Red Hat and the collection has been obtained either from Galaxy or GitHub,
there may community help available on the [Ansible Forum](https://forum.ansible.com/).

## Requirements

- **Ansible:** `ansible-core >= 2.16.0`
- **Python:** Python 3.10 or later on the controller node
- **Connection:** The collection communicates with Splunk ITSI via its REST API using the [`httpapi` connection plugin](https://docs.ansible.com/ansible/latest/plugins/connection/httpapi.html). The managed node must have the Splunk REST API reachable on port 8089 (or the configured `ansible_httpapi_port`).
- **Splunk ITSI:** A running Splunk IT Service Intelligence instance is required for integration tests and production use.
- **Optional — `jsonschema >= 4.0.0`:** Required only by the `itsi_glass_table` module for definition validation. Install with `pip install jsonschema`.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against the following Ansible versions: **>=2.16.0**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.
<!--end requires_ansible-->

## Collection Content

### Event Driven Ansible (EDA)
Name | Description
--- | ---
[Splunk ITSI EDA Rulebook Activation](https://github.com/ansible-collections/splunk.itsi/blob/main/extensions/eda/README.md)|Setup and configuration for EDA rulebook activation with Splunk ITSI webhook integration

<!--start collection content-->
### Httpapi plugins
Name | Description
--- | ---
[splunk.itsi.itsi_api_client](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_api_client_httpapi.rst)|HttpApi Plugin for Splunk ITSI

### Modules
Name | Description
--- | ---
[splunk.itsi.itsi_add_episode_comments](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_add_episode_comments_module.rst)|Add comments to Splunk ITSI episodes
[splunk.itsi.itsi_aggregation_policy](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_aggregation_policy_module.rst)|Manage Splunk ITSI aggregation policies
[splunk.itsi.itsi_aggregation_policy_info](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_aggregation_policy_info_module.rst)|Get information about Splunk ITSI aggregation policies
[splunk.itsi.itsi_correlation_search](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_correlation_search_module.rst)|Manage Splunk ITSI correlation searches
[splunk.itsi.itsi_correlation_search_info](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_correlation_search_info_module.rst)|Query Splunk ITSI correlation searches
[splunk.itsi.itsi_episode_details_info](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_episode_details_info_module.rst)|Read Splunk ITSI notable_event_group (episodes)
[splunk.itsi.itsi_glass_table](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_glass_table_module.rst)|Manage Splunk ITSI Glass Table objects via itoa_interface
[splunk.itsi.itsi_glass_table_info](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_glass_table_info_module.rst)|Read Splunk ITSI glass table objects via itoa_interface
[splunk.itsi.itsi_service](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_service_module.rst)|Manage Splunk ITSI Service objects via itoa_interface
[splunk.itsi.itsi_service_info](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_service_info_module.rst)|Gather facts about Splunk ITSI Service objects via itoa_interface
[splunk.itsi.itsi_update_episode_details](https://github.com/ansible-collections/splunk.itsi/blob/main/docs/splunk.itsi.itsi_update_episode_details_module.rst)|Update specific fields of Splunk ITSI episodes

<!--end collection content-->

### Supported connections

Use splunk.itsi modules with the [`httpapi` connection plugin](https://docs.ansible.com/ansible/latest/plugins/connection/httpapi.html).
Set certain attributes in the inventory as follows:

Example `inventory.ini`:

**NOTE:** The passwords should be stored in a secure location or an [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html)

**NOTE:** The default port for Splunk's REST API is 8089

    [itsi]
    splunk.itsi.example.com

    [itsi:vars]
    ansible_connection=httpapi
    ansible_network_os=splunk.itsi.itsi_api_client
    ansible_user=admin
    ansible_httpapi_pass=my_super_secret_admin_password
    ansible_httpapi_port=8089
    ansible_httpapi_use_ssl=true
    ansible_httpapi_validate_certs=false

## Installation

You can install the splunk.itsi collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install splunk.itsi

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: splunk.itsi
```

## Use Cases

### 1. Automate aggregation policy lifecycle management

Create, update, and enforce aggregation policies that group related ITSI episodes, replacing manual UI changes with version-controlled Ansible playbooks:

```yaml
- name: Create aggregation policy for high-severity network episodes
  splunk.itsi.itsi_aggregation_policy:
    title: "Network Critical Aggregation"
    description: "Groups high-severity network events"
    disabled: false
    priority: 5
    group_severity: "high"
    group_status: "new"
    group_title: "%title%"
    group_description: "%description%"
    filter_criteria:
      condition: "AND"
      items: []
    breaking_criteria:
      condition: "AND"
      items: []
    state: present
  register: policy_result

- name: Update policy filter to target critical severity only
  splunk.itsi.itsi_aggregation_policy:
    policy_id: "{{ policy_result.response._key }}"
    filter_criteria:
      condition: "OR"
      items:
        - type: clause
          config:
            condition: "AND"
            items:
              - type: notable_event_field
                config:
                  field: severity
                  operator: ">="
                  value: "5"
    state: present
```

### 2. Manage episode lifecycle programmatically

Update episode status, severity, and ownership from Ansible playbooks, enabling integration with external ticketing or SOAR systems:

```yaml
- name: Escalate high-severity episode to on-call engineer
  splunk.itsi.itsi_update_episode_details:
    episode_id: "{{ episode_id }}"
    severity: "5"
    status: "1"
    owner: "oncall-engineer"
    instruction: "Escalated automatically by Ansible — investigate immediately"

- name: Add investigation note to episode
  splunk.itsi.itsi_add_episode_comments:
    episode_key: "{{ episode_id }}"
    comment: "Auto-remediation attempted at {{ ansible_date_time.iso8601 }}"
```

### 3. Deploy and manage glass tables as code

Store glass table definitions in version control and let Ansible enforce the desired state across ITSI environments:

```yaml
- name: Ensure NOC overview glass table is present
  splunk.itsi.itsi_glass_table:
    title: "NOC Overview"
    description: "Managed by Ansible"
    state: present
    definition:
      title: "NOC Overview"
      description: "Managed by Ansible"
      dataSources: {}
      visualizations: {}
      layout:
        tabs:
          items:
            - label: "Main"
              layoutId: "layout_1"
        layoutDefinitions:
          layout_1:
            type: absolute
            options:
              width: 1920
              height: 1080
              backgroundColor: "#1b1b1b"
            structure: []
  register: glass_table_result
```

## Testing

### Test types

| Type | Tool | What is covered |
|---|---|---|
| Sanity | `ansible-test sanity` | Code style, documentation, import correctness |
| Unit | `pytest` via `ansible-test units` | Module utilities, argument validation, API mapping logic |
| Integration | `ansible-test network-integration` | End-to-end module behaviour against a live Splunk ITSI instance |

### Ansible core versions

Sanity and unit tests run automatically on every pull request and on a nightly schedule against:

- `stable-2.16`
- `stable-2.18`
- `stable-2.20`
- `stable-2.21`

### Splunk ITSI versions

Integration tests run against real Splunk ITSI instances:

| Splunk version | IT Service Intelligence (ITSI) app version |
|---|---|
| 9.4 | 4.21.0 |
| 10.4 | 4.21.0 |

### Known exceptions and workarounds

- **`jsonschema` required for `itsi_glass_table`:** The `itsi_glass_table` module requires the `jsonschema >= 4.0.0` Python package on the controller node for definition validation. If it is missing, the module fails immediately with an actionable install message: `pip install jsonschema`. All other modules have no extra Python dependencies beyond ansible-core.
- **`httpapi` connection required:** All modules communicate exclusively through the Splunk ITSI REST API using the `httpapi` connection plugin. SSH-based connections are not supported. Ensure `ansible_connection: httpapi` and `ansible_network_os: splunk.itsi.itsi_api_client` are set in the inventory.
- **Certificate validation:** Splunk installations with self-signed certificates require `ansible_httpapi_validate_certs: false` in the inventory. Use a trusted certificate in production.

## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Splunk ITSI collection repository](https://github.com/ansible-collections/splunk.itsi). See [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections) for complete details.

### Code of Conduct

This collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).
Please read and familiarize yourself with this document.

## Release notes

Release notes are available on the [GitHub Releases page](https://github.com/ansible-collections/splunk.itsi/releases).

## Related Information

- [Ansible network resources](https://docs.ansible.com/ansible/latest/network/getting_started/network_resources.html)
- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## License Information

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.

## Author Information

[Ansible Ecosystem Engineering team](https://github.com/ansible-collections)
