.. _splunk.itsi.itsi_update_episode_details_module:


***************************************
splunk.itsi.itsi_update_episode_details
***************************************

**Update specific fields of Splunk ITSI episodes**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Update specific fields of existing episodes in Splunk IT Service Intelligence (ITSI).
- Uses partial data updates to modify only the specified fields without affecting other episode data.
- Supports common episode fields like severity, status, owner, and instruction.



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
                    <b>episode_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The episode ID (_key field) to update.</div>
                        <div>This should be the _key field from an episode, such as returned by notable_event_group_info.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>fields</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Dictionary of additional fields to update.</div>
                        <div>Allows updating any valid episode field not covered by specific parameters.</div>
                        <div>Field names should match ITSI episode schema.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>instruction</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Update the instruction field of the episode.</div>
                        <div>Contains guidance or notes about how to handle the episode.</div>
                        <div>Set to <code>all_instruction</code> to reset the instruction in the ITSI UI, effectively clearing it so the episode shows no instruction provided.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>owner</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Update the owner/assignee of the episode.</div>
                        <div>Can be a username or &#x27;unassigned&#x27; to clear assignment.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>severity</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Update the severity level of the episode.</div>
                        <div>Common values are 1 (Info), 2 (Normal), 3 (Low), 4 (Medium), 5 (High), 6 (Critical).</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>status</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Update the status of the episode.</div>
                        <div>Common values are 1 (New), 2 (In Progress), 3 (Pending), 4 (Resolved), 5 (Closed).</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - This module updates existing ITSI episodes using the event_management_interface/notable_event_group endpoint.
   - Uses partial data updates (is_partial_data=1) to modify only specified fields.
   - The episode must exist before updating it.
   - Use notable_event_group_info module to retrieve episode IDs and current field values.
   - At least one field parameter (severity, status, owner, instruction, or fields) must be provided.
   - This module is idempotent. If the desired field values already match the current episode state, no update is performed and ``changed`` is returned as ``false``.
   - Check mode is supported. In check mode the module reports whether changes would be made without actually calling the update API.



Examples
--------

.. code-block:: yaml

    # Update episode severity
    - name: Set episode to critical severity
      splunk.itsi.itsi_update_episode_details:
        episode_id: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
        severity: "6"

    # Update episode status and owner
    - name: Assign episode and mark in progress
      splunk.itsi.itsi_update_episode_details:
        episode_id: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
        status: "2"
        owner: "admin"

    # Update multiple fields at once
    - name: Update episode with multiple fields
      splunk.itsi.itsi_update_episode_details:
        episode_id: "{{ episode_id }}"
        severity: "4"
        status: "2"
        owner: "incident_team"
        instruction: "Check database performance and disk space"

    # Update using fields dictionary for custom fields
    - name: Update custom episode fields
      splunk.itsi.itsi_update_episode_details:
        episode_id: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
        fields:
          custom_field: "custom_value"
          priority: "high"

    # Close an episode (status 5 = Closed)
    - name: Close resolved episode
      splunk.itsi.itsi_update_episode_details:
        episode_id: "{{ target_episode_id }}"
        status: "5"
        instruction: "Issue resolved - monitoring system restored"

    # Idempotent update -- running this twice results in changed=false the second time
    - name: Ensure episode severity is set to 4
      splunk.itsi.itsi_update_episode_details:
        episode_id: "{{ episode_id }}"
        severity: "4"
      register: result

    - name: Show whether anything changed
      ansible.builtin.debug:
        msg: "Changed: {{ result.changed }}"

    # Check mode -- preview changes without applying them
    - name: Preview episode update (check mode)
      splunk.itsi.itsi_update_episode_details:
        episode_id: "{{ episode_id }}"
        status: "2"
        owner: "analyst"
      check_mode: true
      register: preview

    - name: Show what would change
      ansible.builtin.debug:
        msg: "Before: {{ preview.before }} / After: {{ preview.after }}"



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
                            <div>The desired values of the targeted fields after the update.</div>
                            <div>When changed is false, before and after are identical.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;severity&#x27;: &#x27;6&#x27;, &#x27;status&#x27;: &#x27;2&#x27;}</div>
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
                            <div>The current values of the targeted fields before the update.</div>
                            <div>Only contains the fields that were requested for update.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;severity&#x27;: &#x27;4&#x27;, &#x27;status&#x27;: &#x27;1&#x27;}</div>
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
                            <div>Whether the episode was actually modified.</div>
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
                            <div>Empty when no changes are needed.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;severity&#x27;: &#x27;6&#x27;, &#x27;status&#x27;: &#x27;2&#x27;}</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>episode_id</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>The episode ID that was targeted.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">ff942149-4e70-42ff-94d3-6fdf5c5f95f3</div>
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
                            <div>Raw JSON response returned by the Splunk ITSI update API.</div>
                            <div>Empty dict when no API call was made (no changes needed or check mode).</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;success&#x27;: True}</div>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Ansible Ecosystem Engineering team (@ansible)
