.. _splunk.itsi.itsi_aggregation_policy_info_module:


****************************************
splunk.itsi.itsi_aggregation_policy_info
****************************************

**Get information about Splunk ITSI aggregation policies**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Retrieve information about aggregation policies in Splunk IT Service Intelligence (ITSI).
- Query by policy_id for a specific policy, by title for all matching policies, or list all policies.
- This is a read-only module that does not modify any policies.
- Uses the ITSI Event Management Interface REST API.



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
                    <b>fields</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Comma-separated list of field names to include in response.</div>
                        <div>Useful for retrieving only specific fields.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>filter_data</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>MongoDB-style JSON filter for listing aggregation policies.</div>
                        <div>Only applies when listing multiple items (no title or policy_id specified).</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>limit</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Maximum number of aggregation policies to return when listing.</div>
                        <div>Only applies when listing multiple items.</div>
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
                        <div>Provides direct lookup by unique ID.</div>
                        <div>Returns a single policy in <code>aggregation_policy</code>.</div>
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
                        <div>The title/name of the aggregation policy to search for.</div>
                        <div>Note that multiple policies can have the same title.</div>
                        <div>Returns all matching policies in <code>aggregation_policies</code> list.</div>
                        <div>If exactly one match, <code>aggregation_policy</code> is also set for convenience.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - This module retrieves ITSI aggregation policies using the event_management_interface/notable_event_aggregation_policy endpoint.
   - When querying by ``policy_id``, returns a single policy in ``aggregation_policy``.
   - When querying by ``title``, returns all matching policies in ``aggregation_policies`` list since titles are not unique.
   - Without any identifier, lists all aggregation policies.
   - This is a read-only module and will never modify policies.



Examples
--------

.. code-block:: yaml

    # List all aggregation policies
    - name: Get all aggregation policies
      splunk.itsi.itsi_aggregation_policy_info:
      register: all_policies
    # Access: all_policies.aggregation_policies

    # Get aggregation policy by ID (returns single policy)
    - name: Get aggregation policy by ID
      splunk.itsi.itsi_aggregation_policy_info:
        policy_id: "itsi_default_policy"
      register: policy_by_id
    # Access: policy_by_id.aggregation_policy

    # Get aggregation policies by title (may return multiple)
    - name: Get all aggregation policies with a specific title
      splunk.itsi.itsi_aggregation_policy_info:
        title: "Default Policy"
      register: policies_by_title
    # Access: policies_by_title.aggregation_policies (list of all matching)
    # If exactly one match: policies_by_title.aggregation_policy also available

    # Get aggregation policy with specific fields only
    - name: Get aggregation policy with field projection
      splunk.itsi.itsi_aggregation_policy_info:
        policy_id: "itsi_default_policy"
        fields: "title,disabled,priority,group_severity"
      register: policy_details

    # List aggregation policies with filtering
    - name: List enabled aggregation policies
      splunk.itsi.itsi_aggregation_policy_info:
        filter_data: '{"disabled": 0}'
        limit: 10
      register: enabled_policies

    # List policies with specific fields
    - name: List all policies with minimal fields
      splunk.itsi.itsi_aggregation_policy_info:
        fields: "_key,title,disabled"
      register: policy_list



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
                    </div>
                </td>
                <td>when listing policies or querying by title</td>
                <td>
                            <div>List of aggregation policies</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[{&#x27;title&#x27;: &#x27;Policy 1&#x27;, &#x27;_key&#x27;: &#x27;policy1&#x27;}, {&#x27;title&#x27;: &#x27;Policy 2&#x27;, &#x27;_key&#x27;: &#x27;policy2&#x27;}]</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>aggregation_policy</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>when querying by policy_id, or when exactly one policy matches the title</td>
                <td>
                            <div>The aggregation policy data (single policy query by ID, or single match by title)</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;title&#x27;: &#x27;Default Policy&#x27;, &#x27;description&#x27;: &#x27;Default aggregation policy&#x27;, &#x27;disabled&#x27;: 0, &#x27;_key&#x27;: &#x27;itsi_default_policy&#x27;}</div>
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
