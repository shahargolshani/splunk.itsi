.. _splunk.itsi.itsi_glass_table_info_module:


*********************************
splunk.itsi.itsi_glass_table_info
*********************************

**Read Splunk ITSI glass table objects via itoa_interface**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Reads a single glass table by ``_key`` or lists glass tables with optional server-side filtering, pagination, and sorting.
- Uses the splunk.itsi.itsi_api_client httpapi plugin for authentication and transport.



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
                    <b>count</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Maximum number of glass tables to return (page size).</div>
                        <div>Only applies when listing (no <code>glass_table_id</code>).</div>
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
                        <div>Comma-separated list of field names to include in the response.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>filter</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">raw</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>MongoDB-style filter for listing glass tables.</div>
                        <div>Accepts a dict or a JSON string.</div>
                        <div>Only applies when <code>glass_table_id</code> is not provided.</div>
                        <div>Example: <code>{&quot;title&quot;: &quot;My Table&quot;}</code>.</div>
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
                        <div>The glass table <code>_key</code>.</div>
                        <div>When provided, fetches a single glass table and returns it as a one-element list.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>offset</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Number of results to skip from the start.</div>
                        <div>Only applies when listing (no <code>glass_table_id</code>).</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>sort_dir</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>asc</li>
                                    <li>desc</li>
                        </ul>
                </td>
                <td>
                        <div>Sort direction: <code>asc</code> for ascending, <code>desc</code> for descending.</div>
                        <div>Only applies when listing (no <code>glass_table_id</code>).</div>
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
                        <div>Field name to sort results by.</div>
                        <div>Only applies when listing (no <code>glass_table_id</code>).</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - Connection/auth/SSL config is provided by httpapi (inventory), not by this module.
   - This is a read-only module. It never changes remote state.



Examples
--------

.. code-block:: yaml

    - name: List all glass tables
      splunk.itsi.itsi_glass_table_info:
      register: all_tables

    - name: Get a single glass table by key
      splunk.itsi.itsi_glass_table_info:
        glass_table_id: 6992e850280636204503b3f6
      register: one

    - name: List glass tables with pagination
      splunk.itsi.itsi_glass_table_info:
        count: 10
        offset: 0
      register: page1

    - name: Filter glass tables by title
      splunk.itsi.itsi_glass_table_info:
        filter: '{"title": "My Dashboard"}'
      register: filtered

    - name: List glass tables sorted by modification time
      splunk.itsi.itsi_glass_table_info:
        sort_key: mod_time
        sort_dir: desc
        count: 5
      register: recent

    - name: Retrieve only specific fields
      splunk.itsi.itsi_glass_table_info:
        fields: "_key,title,description,mod_time"
      register: summary



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
                    <b>glass_tables</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>List of glass table objects matching the query.</div>
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
