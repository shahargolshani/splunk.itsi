.. _splunk.itsi.itsi_aggregation_policy_module:


***********************************
splunk.itsi.itsi_aggregation_policy
***********************************

**Manage Splunk ITSI aggregation policies**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Create, update, and delete aggregation policies in Splunk IT Service Intelligence (ITSI).
- An aggregation policy determines how notable events are grouped together into episodes.
- Uses the ITSI Event Management Interface REST API for CRUD operations.
- For querying/listing policies, use the ``itsi_aggregation_policy_info`` module.



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
                    <b>additional_fields</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                <td>
                        <div>Dictionary of additional fields to set on the aggregation policy.</div>
                        <div>Allows setting any valid policy field not covered by specific parameters.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>breaking_criteria</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Breaking criteria that determines when to create a new episode.</div>
                        <div>Dictionary with &#x27;condition&#x27; (AND/OR) and &#x27;items&#x27; array.</div>
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
                        <div>Description of the aggregation policy purpose and functionality.</div>
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
                        <div>Whether the aggregation policy is disabled.</div>
                        <div>Use <code>false</code> to enable, <code>true</code> to disable.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>filter_criteria</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Filter criteria that determines which notable events this policy applies to.</div>
                        <div>Dictionary with &#x27;condition&#x27; (AND/OR) and &#x27;items&#x27; array.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>group_assignee</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Default assignee for episodes created by this policy.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>group_description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Template for episode descriptions created by this policy.</div>
                        <div>Can use field substitution like &#x27;%title%&#x27;, &#x27;%description%&#x27;.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>group_severity</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Default severity level for episodes created by this policy.</div>
                        <div>Common values are &#x27;info&#x27;, &#x27;low&#x27;, &#x27;medium&#x27;, &#x27;high&#x27;, &#x27;critical&#x27;.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>group_status</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Default status for episodes created by this policy.</div>
                        <div>Common values are &#x27;new&#x27;, &#x27;in_progress&#x27;, &#x27;pending&#x27;, &#x27;resolved&#x27;, &#x27;closed&#x27;.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>group_title</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Template for episode titles created by this policy.</div>
                        <div>Can use field substitution like &#x27;%title%&#x27;, &#x27;%description%&#x27;.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>policy_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The aggregation policy ID/key (unique identifier).</div>
                        <div>For <code>state=present</code> with <code>policy_id</code>, looks up the policy and updates only changed fields (idempotent).</div>
                        <div>For <code>state=present</code> without <code>policy_id</code>, a new policy is always created (<code>title</code> required).</div>
                        <div>For <code>state=absent</code>, required to identify which policy to delete.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>priority</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Priority level of the aggregation policy (1-10).</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rules</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>List of action rules to execute when episodes are created.</div>
                        <div>Each rule is a dictionary with activation criteria and actions.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>split_by_field</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Field to split episodes by (creates separate episodes per unique value).</div>
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
                        <div>Desired state of the aggregation policy.</div>
                        <div><code>present</code> ensures the aggregation policy exists with specified configuration.</div>
                        <div><code>absent</code> ensures the aggregation policy is deleted.</div>
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
                        <div>The title/name of the aggregation policy.</div>
                        <div>Required when creating a new policy (<code>state=present</code> without <code>policy_id</code>).</div>
                        <div>Optional when updating an existing policy (<code>state=present</code> with <code>policy_id</code>).</div>
                        <div>Note that multiple policies can have the same title.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - This module manages ITSI aggregation policies using the event_management_interface/notable_event_aggregation_policy endpoint.
   - For ``state=present`` with ``policy_id``, the module performs idempotent updates - only changes fields that differ. Title is optional.
   - For ``state=present`` without ``policy_id``, a new policy is always created. Title is required.
   - For ``state=absent``, ``policy_id`` is required to identify which policy to delete.
   - Update operations modify only the specified fields, leaving other configuration unchanged.
   - To query or list policies, use the ``itsi_aggregation_policy_info`` module.


See Also
--------

.. seealso::

   :ref:`splunk.itsi.itsi_aggregation_policy_info_module`
       Use this module to query and list aggregation policies.


Examples
--------

.. code-block:: yaml

    # Create new aggregation policy (no policy_id = always creates new)
    - name: Create new aggregation policy
      splunk.itsi.itsi_aggregation_policy:
        title: "Test Aggregation Policy (Ansible)"
        description: "Test policy created by Ansible"
        disabled: false
        priority: 5
        group_severity: "medium"
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
      register: create_result
    # Note: create_result.aggregation_policies[0]._key contains the generated policy_id

    # Update existing aggregation policy (policy_id required, title optional)
    - name: Update aggregation policy settings
      splunk.itsi.itsi_aggregation_policy:
        policy_id: "{{ create_result.aggregation_policies[0]._key }}"
        group_severity: "high"
        disabled: false
        state: present
      register: update_result
    # Only updates if group_severity or disabled actually changed
    # Title not required for updates - policy is identified by policy_id

    # Update using additional fields
    - name: Update aggregation policy with custom fields
      splunk.itsi.itsi_aggregation_policy:
        policy_id: "test_policy_key"
        additional_fields:
          split_by_field: "source"
          sub_group_limit: "100"
        state: present

    # Delete aggregation policy (policy_id required)
    - name: Remove aggregation policy
      splunk.itsi.itsi_aggregation_policy:
        policy_id: "{{ create_result.aggregation_policies[0]._key }}"
        state: absent
      register: delete_result

    # Error handling example
    - name: Create aggregation policy with error handling
      splunk.itsi.itsi_aggregation_policy:
        title: "Critical Service Alert Policy"
        description: "Groups critical service alerts"
        group_severity: "critical"
        state: present
      register: result
      failed_when: result.status >= 400 and result.status != 409



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
                    <b>aggregation_policies</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>when operation succeeded</td>
                <td>
                            <div>List containing the aggregation policy data after the operation</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[{&#x27;title&#x27;: &#x27;Default Policy&#x27;, &#x27;description&#x27;: &#x27;Default aggregation policy&#x27;, &#x27;disabled&#x27;: 0, &#x27;_key&#x27;: &#x27;itsi_default_policy&#x27;}]</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>body</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Raw response body from the API</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&quot;_key&quot;: &quot;policy123&quot;}</div>
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
                            <div>Whether the aggregation policy was modified</div>
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
                <td>when operation=update and changes detected</td>
                <td>
                            <div>Differences between current and desired state (update operations)</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;group_severity&#x27;: [&#x27;medium&#x27;, &#x27;high&#x27;], &#x27;disabled&#x27;: [&#x27;1&#x27;, &#x27;0&#x27;]}</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>headers</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>HTTP response headers from the API</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;content-type&#x27;: &#x27;application/json&#x27;}</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>operation</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>The operation performed (create, update, delete, no_change, error)</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">create</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>status</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>HTTP status code from the API response</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">200</div>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Ansible Ecosystem Engineering team (@ansible)
