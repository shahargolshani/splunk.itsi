.. _splunk.itsi.itsi_correlation_search_module:


***********************************
splunk.itsi.itsi_correlation_search
***********************************

**Manage Splunk ITSI correlation searches**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Create, update, and delete correlation searches in Splunk IT Service Intelligence (ITSI).
- A correlation search is a recurring search that generates a notable event when search results meet specific conditions.
- Multi-KPI alerts are a type of correlation search.
- Uses the ITSI Event Management Interface REST API for full CRUD operations.
- For querying correlation searches, use the ``itsi_correlation_search_info`` module.



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
                    <b>actions</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"itsi_event_generator"</div>
                </td>
                <td>
                        <div>Comma-separated list of actions to trigger.</div>
                        <div>Required for correlation searches to appear in the ITSI GUI.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>additional_fields</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Dictionary of additional fields to set on the correlation search.</div>
                        <div>Allows setting any valid correlation search field not covered by specific parameters.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>correlation_search_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The correlation search ID for direct lookup.</div>
                        <div>This is the internal identifier (often the saved search name).</div>
                        <div>Takes precedence over name parameter for update/delete operations.</div>
                        <div>For new correlation searches, this becomes the search name.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cron_schedule</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Cron schedule for the correlation search execution.</div>
                        <div>Standard cron format (e.g., &quot;*/5 * * * *&quot; for every 5 minutes).</div>
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
                        <div>Description of the correlation search purpose and functionality.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disabled</b>
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
                        <div>Whether the correlation search is disabled.</div>
                        <div>Use <code>false</code> to enable, <code>true</code> to disable.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>earliest_time</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Earliest time for the search window (e.g., &quot;-15m&quot;, &quot;-1h&quot;).</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>latest_time</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Latest time for the search window (e.g., &quot;now&quot;, &quot;-5m&quot;).</div>
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
                        <div>The name/title of the correlation search.</div>
                        <div>Required for create operations.</div>
                        <div>Used for lookup when correlation_search_id is not provided.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>search</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The SPL search query for the correlation search.</div>
                        <div>Required when creating new correlation searches.</div>
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
                        <div>Desired state of the correlation search.</div>
                        <div><code>present</code> ensures the correlation search exists with specified configuration.</div>
                        <div><code>absent</code> ensures the correlation search is deleted.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - This module manages ITSI correlation searches using the event_management_interface/correlation_search endpoint.
   - When creating correlation searches, the ``name`` or ``correlation_search_id`` and ``search`` parameters are required.
   - Update operations modify only the specified fields, leaving other configuration unchanged.
   - The correlation search must exist before updating or deleting it.
   - For querying correlation searches, use the ``itsi_correlation_search_info`` module.



Examples
--------

.. code-block:: yaml

    # Create new correlation search
    - name: Create new correlation search
      splunk.itsi.itsi_correlation_search:
        name: "test-corrsearch-ansible"
        search: "index=itsi | head 1"
        description: "Test correlation search created by Ansible"
        disabled: false
        cron_schedule: "*/10 * * * *"
        earliest_time: "-15m"
        latest_time: "now"
        actions: "itsi_event_generator"
        state: present
      register: create_result

    # Update existing correlation search
    - name: Update correlation search schedule
      splunk.itsi.itsi_correlation_search:
        correlation_search_id: "test-corrsearch-ansible"
        cron_schedule: "*/5 * * * *"
        disabled: false
        state: present
      register: update_result

    # Update using additional fields
    - name: Update correlation search with custom fields
      splunk.itsi.itsi_correlation_search:
        correlation_search_id: "test-corrsearch-ansible"
        additional_fields:
          priority: "high"
          custom_field: "custom_value"
        state: present

    # Delete correlation search by ID
    - name: Remove correlation search
      splunk.itsi.itsi_correlation_search:
        correlation_search_id: "test-corrsearch-ansible"
        state: absent
      register: delete_result

    # Delete correlation search by name
    - name: Remove correlation search by name
      splunk.itsi.itsi_correlation_search:
        name: "test-corrsearch-ansible"
        state: absent

    # Error handling example
    - name: Create correlation search with error handling
      splunk.itsi.itsi_correlation_search:
        name: "monitoring-alert"
        search: "index=main error | stats count"
        state: present
      register: result



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
                            <div>Search state after the operation. Empty dict on delete.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;search&#x27;: &#x27;index=itsi | head 1&#x27;, &#x27;disabled&#x27;: &#x27;0&#x27;}</div>
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
                            <div>Search state before the operation. Empty dict on create or when already absent.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;search&#x27;: &#x27;index=itsi | head 1&#x27;, &#x27;disabled&#x27;: &#x27;0&#x27;}</div>
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
                            <div>Whether the correlation search was modified.</div>
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
                            <div>Fields that differ between before and after. Empty dict when unchanged.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;cron_schedule&#x27;: &#x27;*/5 * * * *&#x27;}</div>
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
                            <div>Raw HTTP API response body from the last API call.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;name&#x27;: &#x27;test-search&#x27;, &#x27;disabled&#x27;: &#x27;0&#x27;}</div>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Ansible Ecosystem Engineering team (@ansible)
