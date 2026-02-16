.. _splunk.itsi.itsi_add_episode_comments_module:


*************************************
splunk.itsi.itsi_add_episode_comments
*************************************

**Add comments to Splunk ITSI episodes**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Add comments to existing episodes in Splunk IT Service Intelligence (ITSI).
- Comments are associated with a specific episode and can provide context or status updates.
- Every invocation creates a new comment; comments cannot be updated or deleted via the API.



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
                    <b>comment</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The text content of the comment to add to the episode.</div>
                        <div>Can contain any text describing actions taken, status updates, or other relevant information.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>episode_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The episode _key to add a comment to.</div>
                        <div>This is the <code>_key</code> field from an episode, as returned by <span class='module'>splunk.itsi.itsi_episode_details_info</span>.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>is_group</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li><div style="color: blue"><b>yes</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>Whether this comment is for an episode group.</div>
                        <div>Should be set to <code>true</code> for ITSI episodes (notable event groups).</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - This module adds comments to existing ITSI episodes using the notable_event_comment endpoint.
   - The episode must exist before adding comments to it.
   - Comments are permanently associated with the episode and cannot be deleted via the API.
   - Use :ref:`splunk.itsi.itsi_episode_details_info <splunk.itsi.itsi_episode_details_info_module>` to retrieve episode ``_key`` values for commenting.
   - This module always returns ``changed=true`` because every run creates a new comment. Idempotency does not apply.
   - Check mode is supported. In check mode the module reports ``changed=true`` without actually calling the API.



Examples
--------

.. code-block:: yaml

    # Add a simple comment to an episode
    - name: Add comment to episode
      splunk.itsi.itsi_add_episode_comments:
        episode_key: "ff942149-4e70-42ff-94d3-6fdf5c5f95f3"
        comment: "Investigating root cause - checking application logs"

    # Add a comment with variable content
    - name: Add dynamic comment to episode
      splunk.itsi.itsi_add_episode_comments:
        episode_key: "{{ episode_key }}"
        comment: "{{ comment_text }}"
        is_group: true

    # Add comment using episode data from a previous task
    - name: Get episodes and add comment to first one
      block:
        - name: Get episode list
          splunk.itsi.itsi_episode_details_info:
            limit: 1
          register: episodes_result

        - name: Add comment to first episode
          splunk.itsi.itsi_add_episode_comments:
            episode_key: "{{ episodes_result.episodes[0]._key }}"
            comment: "Automated comment from Ansible playbook"
          when: episodes_result.episodes | length > 0

    # Check mode -- preview without posting a comment
    - name: Preview comment (check mode)
      splunk.itsi.itsi_add_episode_comments:
        episode_key: "{{ episode_key }}"
        comment: "Dry-run comment"
      check_mode: true
      register: preview

    - name: Show preview result
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
                            <div>The comment payload that was (or would be) sent to the API.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;comment&#x27;: &#x27;Investigating root cause&#x27;, &#x27;event_id&#x27;: &#x27;ff942149-4e70-42ff-94d3-6fdf5c5f95f3&#x27;, &#x27;is_group&#x27;: True}</div>
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
                            <div>The state before the operation.</div>
                            <div>Always an empty dict because comments are newly created.</div>
                    <br/>
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
                            <div>Always true (every run creates a new comment).</div>
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
                            <div>Dictionary of fields that differ between before and after.</div>
                            <div>Always equal to after because comments are newly created.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;comment&#x27;: &#x27;Investigating root cause&#x27;, &#x27;event_id&#x27;: &#x27;ff942149-4e70-42ff-94d3-6fdf5c5f95f3&#x27;, &#x27;is_group&#x27;: True}</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>episode_key</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>The episode _key that was targeted.</div>
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
                            <div>Raw JSON response returned by the Splunk ITSI comment API.</div>
                            <div>Empty dict when no API call was made (check mode).</div>
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
