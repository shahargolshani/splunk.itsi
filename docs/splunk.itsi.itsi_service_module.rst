.. _splunk.itsi.itsi_service_module:


************************
splunk.itsi.itsi_service
************************

**Manage Splunk ITSI Service objects via itoa_interface**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Create, update, or delete Splunk ITSI Service objects using the itoa_interface REST API.
Idempotent by comparing stable fields on the service: title, enabled, description, sec_grp,
base_service_template_id, service_tags, entity_rules, plus any keys provided in "extra".
Uses the splunk.itsi.itsi_api_client httpapi plugin for authentication and transport.





Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>base_service_template_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Service template identifier to base this service on. You can pass either the template ID (_key) or the template title. If a non-UUID value is provided, the module will look up an ITSI base service template (object_type=base_service_template) by exact title and use its _key as base_service_template_id. Note: For ITSI default/built-in service templates (e.g., &quot;Cloud KPIs - AWS EBS (SAI)&quot;), use the template title rather than the ID, as default template IDs are not stable across ITSI installations. Only applied during creation; ignored on updates (read-only after creation). Mutually exclusive with entity_rules - you cannot specify both. The template&#x27;s configuration (including entity_rules, KPIs) is inherited during creation.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Service description (free text).</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enabled</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Enable/disable the service (true/false or 1/0).</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>entity_rules</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>List of entity rule objects defining which entities belong to this service. Each rule has rule_condition (AND/OR) and rule_items array with field, field_type, rule_type (matches/is/contains), and value. Mutually exclusive with base_service_template_id - you cannot specify both. To customize entity_rules on a templated service, first create with the template, then update with entity_rules (without the template field).</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>extra</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                <td>
                        <div>Additional JSON fields to include in payload (merged on top of managed fields). Keys present in extra will override first-class options on conflicts.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Exact service title (service.title). Required if service_id is not provided.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>sec_grp</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>ITSI team (security group) key to assign the service to.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>service_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>ITSI service _key. When provided, used as the primary identifier.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>service_tags</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>List of user-assigned tags for this service. Comparison is order-insensitive. Note: template_tags (inherited from service template) are managed by ITSI and cannot be set through this module.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>state</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>present</b>&nbsp;&larr;</div></li>
                                    <li>absent</li>
                        </ul>
                </td>
                <td>
                        <div>Desired state.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - Requires ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client.
   - Update operations must include a valid title; this module will inject the current title if you do not supply one.
   - When creating a service with base_service_template_id, the template configuration (entity_rules, KPIs, etc.) takes precedence over module parameters. After creation, these fields can be updated independently.
   - The base_service_template_id is only applied during creation and is ignored on subsequent updates.



Examples
--------

.. code-block:: yaml

    - name: Ensure a service exists (idempotent upsert by title)
      splunk.itsi.itsi_service:
        name: api-gateway
        enabled: true
        description: Frontend + API
        sec_grp: default_itsi_security_group
        service_tags: [prod, payments]
        entity_rules: []
        state: present

    - name: Create a service based on a template (pass template title or ID)
      splunk.itsi.itsi_service:
        name: api-gateway-from-template
        base_service_template_id: "My Service Template"
        state: present

    - name: Remove a service by title
      splunk.itsi.itsi_service:
        name: old-dev-service
        state: absent

    - name: Update specific service by key
      splunk.itsi.itsi_service:
        service_id: a2961217-9728-4e9f-b67b-15bf4a40ad7c
        enabled: false
        description: "Disabled for maintenance"



Return Values
-------------
Common return values are documented `here <https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>changed</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Whether any change was made.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>changed_fields</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>when state=present and an update occurred</td>
                <td>
                            <div>Keys that changed during update.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>diff</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>when check_mode is true or an update/delete occurs</td>
                <td>
                            <div>Structured before/after for managed fields.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>raw</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">raw</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Raw JSON from Splunk for the last call.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>service</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>when not bulk</td>
                <td>
                            <div>Service document after the operation when available.</div>
                    <br/>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Ansible Ecosystem Engineering team (@ansible)
