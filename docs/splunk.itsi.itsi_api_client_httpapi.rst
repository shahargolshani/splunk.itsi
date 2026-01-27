.. _splunk.itsi.itsi_api_client_httpapi:


***************************
splunk.itsi.itsi_api_client
***************************

**HttpApi Plugin for Splunk ITSI**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Provides a persistent HTTP(S) connection and authentication for the Splunk ITSI REST API.
- Modules call ``conn.send_request(path, data, method="GET"``) and this plugin injects authentication and JSON headers.
- Returns response format with status, headers, and body structure for full HTTP metadata access.
- Automatically adds ``output_mode=json`` to GET requests for consistent JSON responses from Splunk.
- Compatible with both core httpapi and ansible.netcommon.httpapi connections for advanced features.




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
                <th>Configuration</th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                                <div>var: ansible_httpapi_pass</div>
                    </td>
                <td>
                        <div>Password for Splunk authentication.</div>
                        <div>Used with remote_user for auto-retrieved session key authentication.</div>
                        <div>Also used as fallback for Basic authentication if session key retrieval fails.</div>
                        <div>Session keys obtained this way are automatically cached and refreshed on 401 errors.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>remote_user</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                                <div>var: ansible_user</div>
                    </td>
                <td>
                        <div>Username for Splunk authentication.</div>
                        <div>Used for auto-retrieved session key authentication via <code>/services/auth/login</code> endpoint.</div>
                        <div>Also used as fallback for Basic authentication if session key retrieval fails.</div>
                        <div>When combined with password, enables automatic session key management with caching and refresh.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>session_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                                <div>var: ansible_httpapi_session_key</div>
                    </td>
                <td>
                        <div>Pre-created Splunk session key from <code>/services/auth/login</code> to be sent as <code>Authorization Splunk &lt;sessionKey&gt;</code>.</div>
                        <div>Use when you have already obtained a session key through external means.</div>
                        <div>If this authentication fails with 401, the plugin will automatically fallback to auto-retrieved session key.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>token</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                                <div>var: ansible_httpapi_token</div>
                    </td>
                <td>
                        <div>Pre-created Splunk authentication token to be sent as <code>Authorization Bearer &lt;token&gt;</code>.</div>
                        <div>Use for direct endpoint access with Splunk authentication tokens (Splunk Enterprise 7.3+).</div>
                        <div>These tokens must be created in Splunk and have token authentication enabled.</div>
                        <div>This is the highest priority authentication method.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - Basic configuration requires ``ansible_connection=httpapi`` and ``ansible_network_os=splunk.itsi.itsi_api_client``.
   - Advanced configuration uses ``ansible_connection=ansible.netcommon.httpapi`` for proxy, SSL certs, timeouts, and connection persistence.
   - Always returns enhanced response format with structure containing status code, headers dict, and body string.
   - Authentication methods tried in priority order are Bearer token, explicit session key, auto-retrieved session key, Basic auth.
   - Auto-retrieved session keys are obtained via ``/services/auth/login`` using remote_user and password credentials.
   - Session keys are automatically cached per connection instance and refreshed on 401 Unauthorized errors.
   - If explicit session_key fails with 401, the plugin will fallback to auto-retrieved session key if credentials are available.
   - Basic authentication is used as final fallback when session key methods are not available or fail.
   - Response body text has leading/trailing whitespace stripped by default for clean JSON parsing.



Examples
--------

.. code-block:: yaml

    # Basic HTTP API Configuration (Core Ansible)
    # [splunk]
    # splunk.example.com
    # [splunk:vars]
    # ansible_connection=httpapi
    # ansible_network_os=splunk.itsi.itsi_api_client
    # ansible_httpapi_use_ssl=true
    # ansible_httpapi_port=8089
    # ansible_httpapi_validate_certs=false

    # Advanced HTTP API Configuration (ansible.netcommon.httpapi)
    # Provides proxy support, client certificates, custom timeouts, connection persistence
    # [splunk_advanced]
    # splunk-enterprise.example.com
    # [splunk_advanced:vars]
    # ansible_connection=ansible.netcommon.httpapi
    # ansible_network_os=splunk.itsi.itsi_api_client
    # ansible_httpapi_use_ssl=true
    # ansible_httpapi_port=8089
    # ansible_httpapi_validate_certs=true
    # ansible_httpapi_ca_path=/etc/ssl/certs/ca-bundle.crt
    # ansible_httpapi_client_cert=/path/to/client.pem
    # ansible_httpapi_client_key=/path/to/client-key.pem
    # ansible_httpapi_use_proxy=true
    # ansible_httpapi_http_agent="SplunkITSI-Ansible/1.0.0"
    # ansible_command_timeout=60
    # ansible_connect_timeout=30

    # Choose one auth method for either configuration:

    # Method 1: Bearer Token (highest priority)
    # ansible_httpapi_token=eyJraWQiOiJzcGx1bmsuc2VjcmV0IiwiYWxnIjoiSFM1MTIi...

    # Method 2: Pre-created Session Key
    # ansible_httpapi_session_key=192fd3e470d2b0cc...

    # Method 3: Auto-retrieved Session Key (recommended for username/password)
    # ansible_user=admin
    # ansible_httpapi_pass=secret
    # (Plugin automatically calls /services/auth/login, caches and refreshes session key)

    # Method 4: Basic Auth (fallback)
    # ansible_user=admin
    # ansible_httpapi_pass=secret
    # (Used only if session key retrieval fails)




Status
------


Authors
~~~~~~~

- Ansible Ecosystem Engineering team (@ansible)


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
