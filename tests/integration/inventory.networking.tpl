[itsi]
${ITSI_HOSTNAME}

[itsi:vars]
ansible_connection=ansible.netcommon.httpapi
ansible_network_os=splunk.itsi.itsi_api_client
ansible_user=${ITSI_USERNAME}
ansible_httpapi_pass=${ITSI_PASSWORD}
ansible_httpapi_port=8089
ansible_httpapi_use_ssl=True
ansible_httpapi_validate_certs=False
