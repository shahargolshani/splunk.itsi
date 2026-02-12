.. _splunk.itsi.itsi_episode_details_info_module:


*************************************
splunk.itsi.itsi_episode_details_info
*************************************

**Read Splunk ITSI notable_event_group (episodes)**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Reads a single episode by _key, lists episodes, or returns only a count using the ITSI Event Management Interface. Requires ansible_connection=httpapi and ansible_network_os=splunk.itsi.itsi_api_client.




Requirements
------------
The below requirements are needed on the host that executes this module.

- ansible.netcommon


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
                    <b>count_only</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>If true, call the &#x27;/count&#x27; endpoint and return only a numeric count.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>episode_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>ITSI notable_event_group _key. When provided, fetches a single episode.</div>
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
                        <div>Comma-separated list of field names to include (ITSI parameter &#x27;fields&#x27;).</div>
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
                        <div>MongoDB-style JSON string to filter results (ITSI parameter &#x27;filter_data&#x27;). Example: &#x27;{&quot;status&quot;:&quot;2&quot;}&#x27;.</div>
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
                        <b>Default:</b><br/><div style="color: blue">0</div>
                </td>
                <td>
                        <div>Max entries to return when listing (ITSI parameter &#x27;limit&#x27;). 0 means no limit param is sent.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>skip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Number of entries to skip from the start (ITSI parameter &#x27;skip&#x27;).</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>sort_dir</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>0</li>
                                    <li>1</li>
                        </ul>
                </td>
                <td>
                        <div>Sort direction (ITSI parameter &#x27;sort_dir&#x27;). Use 1 for ascending, 0 for descending.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>sort_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Field name to sort by (ITSI parameter &#x27;sort_key&#x27;).</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - Connection/auth/SSL config is provided by httpapi (inventory), not by this module.



Examples
--------

.. code-block:: yaml

    - name: List first 10 episodes
      splunk.itsi.itsi_episode_details_info:
        limit: 10
      register: out

    - name: Count open episodes (status=2)
      splunk.itsi.itsi_episode_details_info:
        count_only: true
        filter_data: '{"status":"2"}'
      register: cnt

    - name: Get one episode by _key
      splunk.itsi.itsi_episode_details_info:
        episode_id: 000f91af-ac7d-45e2-a498-5c4b6fe96431
      register: one

    - name: Advanced filtering with pagination
      splunk.itsi.itsi_episode_details_info:
        filter_data: '{"severity": {"$in": ["1", "2", "3"]}}'
        sort_key: "mod_time"
        sort_dir: 0
        limit: 20
        skip: 0
        fields: "_key,title,severity,status,mod_time"
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
                    <b>changed</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Always false (read-only).</div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>count</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>when count_only is true</td>
                <td>
                            <div>Count of objects matching filter (when count_only=true).</div>
                    <br/>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>episodes</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>when count_only is false</td>
                <td>
                            <div>Episode list (empty when count_only=true).</div>
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
