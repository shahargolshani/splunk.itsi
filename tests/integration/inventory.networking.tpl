[itsi]
splunk-itsi-9.4 ansible_host=${SPLUNK_ITSI_9_4}
splunk-itsi-10.4 ansible_host=${SPLUNK_ITSI_10_4}

[itsi:vars]
ansible_connection=httpapi
ansible_network_os=splunk.itsi.itsi_api_client
ansible_user=${ITSI_USERNAME}
ansible_httpapi_pass=${ITSI_PASSWORD}
ansible_httpapi_port=8089
ansible_httpapi_use_ssl=True
ansible_httpapi_validate_certs=False
