.. _splunk.itsi.itsi_correlation_search_info_module:


****************************************
splunk.itsi.itsi_correlation_search_info
****************************************

**Query Splunk ITSI correlation searches**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Retrieve information about correlation searches in Splunk IT Service Intelligence (ITSI).
- Query a specific correlation search by ID or name, or list all correlation searches.
- This is a read-only info module that does not make any changes.
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
                        <div>This is the internal identifier (often the saved search name without spaces).</div>
                        <div>Takes precedence over name parameter.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>count</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Maximum number of correlation searches to return when listing.</div>
                        <div>Only applies when listing multiple items.</div>
                </td>
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
                        <div>MongoDB-style JSON filter for listing correlation searches.</div>
                        <div>Only applies when listing multiple items (no name or correlation_search_id specified).</div>
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
                        <div>The display name/title of the correlation search.</div>
                        <div>Used for lookup when correlation_search_id is not provided.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - This is an info module for querying ITSI correlation searches using the event_management_interface/correlation_search endpoint.
   - For creating, updating, or deleting correlation searches, use the ``itsi_correlation_search`` module.
   - Specify either ``name`` or ``correlation_search_id`` to fetch a specific search.
   - Without specifying a search identifier, the module lists all correlation searches.



Examples
--------

.. code-block:: yaml

    # List all correlation searches
    - name: Get all correlation searches
      splunk.itsi.itsi_correlation_search_info:
      register: all_searches

    - name: Display correlation search count
      debug:
        msg: "Found {{ all_searches.correlation_searches | length }} correlation searches"

    # Query specific correlation search by ID
    - name: Get correlation search by ID
      splunk.itsi.itsi_correlation_search_info:
        correlation_search_id: "Service_Monitoring_KPI_Degraded"
      register: search_by_id

    # Query correlation search by display name
    - name: Get correlation search by name
      splunk.itsi.itsi_correlation_search_info:
        name: "Service Monitoring - KPI Degraded"
      register: search_by_name

    # Query with specific fields only
    - name: Get correlation search with specific fields
      splunk.itsi.itsi_correlation_search_info:
        correlation_search_id: "my_correlation_search"
        fields: "name,disabled,is_scheduled,cron_schedule,actions"
      register: search_details

    # List correlation searches with filtering
    - name: List enabled correlation searches
      splunk.itsi.itsi_correlation_search_info:
        filter_data: '{"disabled": "0"}'
        count: 10
      register: enabled_searches

    # List with count limit
    - name: Get first 5 correlation searches
      splunk.itsi.itsi_correlation_search_info:
        count: 5
      register: limited_searches



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
                    <b>body</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Response body from the ITSI API</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&quot;name&quot;: &quot;test-search&quot;, &quot;disabled&quot;: &quot;0&quot;}</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>correlation_search</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>when specific search is requested</td>
                <td>
                            <div>Single correlation search details</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;name&#x27;: &#x27;test-search&#x27;, &#x27;disabled&#x27;: &#x27;0&#x27;, &#x27;search&#x27;: &#x27;index=main | head 1&#x27;}</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>correlation_searches</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>when no specific search is requested</td>
                <td>
                            <div>List of correlation searches (when listing multiple)</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">[{&#x27;name&#x27;: &#x27;Search 1&#x27;, &#x27;disabled&#x27;: &#x27;0&#x27;}, {&#x27;name&#x27;: &#x27;Search 2&#x27;, &#x27;disabled&#x27;: &#x27;1&#x27;}]</div>
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
                            <div>HTTP response headers from the ITSI API</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;Content-Type&#x27;: &#x27;application/json&#x27;, &#x27;Server&#x27;: &#x27;Splunkd&#x27;}</div>
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
                            <div>HTTP status code from the ITSI API response</div>
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
