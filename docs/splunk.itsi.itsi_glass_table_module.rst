.. _splunk.itsi.itsi_glass_table_module:


****************************
splunk.itsi.itsi_glass_table
****************************

**Manage Splunk ITSI Glass Table objects via itoa_interface**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Create, update, or delete Splunk ITSI Glass Table objects using the itoa_interface REST API.
- Glass table titles are NOT unique; multiple glass tables can share the same title.
- The glass table ``_key`` is the unique identifier. Provide ``glass_table_id`` to update or delete.
- When ``glass_table_id`` is omitted with ``state=present``, a new glass table is always created.
- Uses the splunk.itsi.itsi_api_client httpapi plugin for authentication and transport.
- For more information on glass tables see https://help.splunk.com/en/splunk-it-service-intelligence/splunk-it-service-intelligence/visualize-and-assess-service-health/4.19/glass-tables/overview-of-the-glass-table-editor-in-itsi.



Requirements
------------
The below requirements are needed on the host that executes this module.

- Connection configuration requires ``ansible_connection=httpapi`` and ``ansible_network_os=splunk.itsi.itsi_api_client``.
- Authentication via Bearer token, session key, or username/password as documented in the httpapi plugin.


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
                    <b>definition</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Raw JSON definition object for the glass table.</div>
                        <div>Contains the full layout, visualizations, data sources, and inputs configuration.</div>
                        <div>The module validates this value against the Splunk Dashboard Studio JSON Schema and checks referential integrity (e.g. layout items reference existing visualizations, data source IDs are valid) before sending it to the API.</div>
                        <div>The user is responsible for all fields within the definition, including <code>definition.title</code> and <code>definition.description</code> if desired.</div>
                        <div>Required when creating a new glass table (<code>state=present</code> without <code>glass_table_id</code>).</div>
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
                        <div>Description text for the glass table.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>glass_table_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The glass table <code>_key</code> for update or delete operations.</div>
                        <div>Required for <code>state=absent</code>.</div>
                        <div>When provided with <code>state=present</code>, the module updates the existing glass table.</div>
                        <div>When omitted with <code>state=present</code>, a new glass table is created.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>sharing</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>user</li>
                                    <li>app</li>
                        </ul>
                </td>
                <td>
                        <div>Controls the sharing level of the glass table via <code>acl.sharing</code>.</div>
                        <div><code>user</code> makes the glass table private to the owner.</div>
                        <div><code>app</code> makes the glass table available at the app level.</div>
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
                        <div>Desired state of the glass table.</div>
                        <div><code>present</code> ensures the glass table exists with the specified configuration.</div>
                        <div><code>absent</code> ensures the glass table is deleted.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>title</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The title of the glass table.</div>
                        <div>Required when creating a new glass table (<code>state=present</code> without <code>glass_table_id</code>).</div>
                        <div>Glass table titles are not unique; duplicates are allowed.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - This module manages ITSI glass tables using the itoa_interface/glass_table endpoint.
   - Glass table titles are NOT unique. Use ``glass_table_id`` to target a specific glass table for updates or deletion.
   - The ``definition`` parameter is validated against the Splunk Dashboard Studio / ITSI Glass Table JSON Schema before being sent to the API. Referential integrity between sections (visualizations, data sources, layout, inputs) is also checked.
   - The module does not auto-populate ``definition.title`` or ``definition.description``.
   - Update operations use ``is_partial_data=1`` and send only the fields that changed.
   - This module is idempotent. If the desired field values already match the current state, no update is performed and ``changed`` is returned as ``false``.
   - Check mode is supported. In check mode the module reports whether changes would be made without actually calling the API.
   - Diff detection uses recursive comparison via ``dict_diff`` from ansible.netcommon, so changes nested deep inside ``definition`` are properly detected.



Examples
--------

.. code-block:: yaml

    # Create a glass table with a full definition
    - name: Create glass table with definition
      splunk.itsi.itsi_glass_table:
        title: "Detailed Glass Table"
        description: "Glass table with custom layout"
        definition:
          title: "Detailed Glass Table"
          description: "Glass table with custom layout"
          defaults:
            dataSources:
              global:
                options:
                  queryParameters:
                    earliest: "$global_time.earliest$"
                    latest: "$global_time.latest$"
                  refreshType: delay
                  refresh: "$global_refresh_rate$"
          layout:
            options:
              showTitleAndDescription: true
            globalInputs:
              - input_global_trp
              - input_global_refresh_rate
            tabs:
              items:
                - layoutId: layout_1
                  label: "Layout 1"
            layoutDefinitions:
              layout_1:
                type: absolute
                options:
                  width: 1920
                  height: 1080
                  backgroundColor: "#FFFFFF"
                structure: []
          dataSources: {}
          visualizations: {}
          inputs:
            input_global_trp:
              options:
                defaultValue: "-60m@m, now"
                token: global_time
              type: input.timerange
              title: Global Time Range
            input_global_refresh_rate:
              options:
                items:
                  - value: "60s"
                    label: "1 Minute"
                  - value: "300s"
                    label: "5 Minutes"
                defaultValue: "60s"
                token: global_refresh_rate
              type: input.dropdown
              title: Global Refresh Rate
        state: present
      register: result

    # Update an existing glass table by ID
    - name: Update glass table description
      splunk.itsi.itsi_glass_table:
        glass_table_id: "{{ glass_table_id }}"
        description: "Updated description"
        state: present

    # Delete a glass table
    - name: Remove glass table
      splunk.itsi.itsi_glass_table:
        glass_table_id: "6992e850280636204503b3f6"
        state: absent

    # Check mode -- preview changes without applying them
    - name: Preview glass table update (check mode)
      splunk.itsi.itsi_glass_table:
        glass_table_id: "{{ glass_table_id }}"
        title: "Renamed Glass Table"
      check_mode: true
      register: preview

    - name: Show what would change
      ansible.builtin.debug:
        msg: "Before: {{ preview.before }} / After: {{ preview.after }} / Diff: {{ preview.diff }}"



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
                    <b>after</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>The desired values of the targeted fields after the operation.</div>
                            <div>When changed is false, before and after are identical.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;title&#x27;: &#x27;New Title&#x27;, &#x27;description&#x27;: &#x27;New description&#x27;, &#x27;sharing&#x27;: &#x27;app&#x27;}</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>before</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>The current values of the targeted fields before the operation.</div>
                            <div>Only contains the fields that were requested for update.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;title&#x27;: &#x27;Old Title&#x27;, &#x27;description&#x27;: &#x27;Old description&#x27;, &#x27;sharing&#x27;: &#x27;user&#x27;}</div>
                </td>
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
                            <div>Whether the glass table was actually modified.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">True</div>
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
                <td>always</td>
                <td>
                            <div>Dictionary of fields that differ between current and desired state.</div>
                            <div>For nested dicts like definition, shows only the changed nested keys (recursive).</div>
                            <div>Empty when no changes are needed.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;title&#x27;: &#x27;New Title&#x27;}</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>response</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Raw JSON response returned by the Splunk ITSI API.</div>
                            <div>Empty dict when no API call was made (no changes needed or check mode).</div>
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
