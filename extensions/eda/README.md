# Splunk ITSI Event-Driven Ansible (EDA) Rulebook Activation

Follow the steps below to configure the Splunk ITSI server Webhook trigger to activate Ansible Automation Platform (AAP) Event-Driven Ansible (EDA).

---

## Scenario #1 — Splunk ITSI Webhook - AAP Event Stream

### Ansible Automation Platform (AAP) Configurations

All steps below are performed on your AAP instance.

### 1. Create Project

Navigate to:
`Automation Decisions` → `Projects` → `Create project`

&emsp; a. Give the project a name and fill in all the required fields.\
&emsp; b. **Source control URL:**
```
https://github.com/ansible-collections/splunk.itsi.git
```
&emsp; c. **Source control branch/tag/commit:** `main`

### 2. Create Credential

Navigate to:
`Automation Decisions` → `Infrastructure` → `Credentials` → `Create credential`

&emsp; a. Give the credential a name.\
&emsp; b. **Credential type:** `Token Event Stream`\
&emsp; c. **Token:** Create a Token - for example `12345678`

### 3. Create Event Stream

Navigate to:
`Automation Decisions` → `Event Streams` → `Create event stream`

&emsp; a. Give the event stream a name.\
&emsp; b. **Event stream type:** `Token Event Stream`\
&emsp; c. **Credentials:** Use the credential created in [Step 2](#2-create-credential).

> **Important:** After the event stream is created, copy the **URL** from the Event Stream Details page.
> It should look similar to:
>
> `
> https://eco.ansible.aap.gateway:443/eda-event-streams/api/eda/v1/external_event_stream/6d280107-145a-451e-b8c6-7912ef1a7450/post/
> `
>
> **Note:** Your Splunk server must have the correct DNS to resolve the AAP gateway FQDN and have the AAP CA certificate installed.

### 4. Create Rulebook Activation

Navigate to:
`Automation Decisions` → `Rulebook Activations` → `Create rulebook activation`

&emsp; a. Give the rulebook activation a name.\
&emsp; b. **Project:** Choose the project created in [Step 1](#1-create-project).\
&emsp; c. **Rulebook:** Choose `splunk-itsi-webhook.yml`.\
&emsp; d. **Event streams:** Choose the event stream created in [Step 3](#3-create-event-stream).

> **Verify:** After the Rulebook Activation is created, check that the Rulebook state is **Running** on the Rulebook Activations page.

- Click on the Rulebook Activation name and go to the **History** tab.
- Click on the running Rulebook Activation instance to view the log.

---

### Splunk ITSI Server Configurations

### Install the Red Hat Event-Driven Ansible Add-on for Splunk

In order to configure Webhooks on the Splunk ITSI server, you must install the **Red Hat Event-Driven Ansible Add-on for Splunk**.

| Resource   | Link                                            |
| ---------- | ----------------------------------------------- |
| GitHub     | <https://github.com/ansible/splunk-eda-ta>      |
| Splunkbase | <https://splunkbase.splunk.com/app/7868>        |

### 1. Configure the Webhook

After the add-on is installed, navigate to:
`Apps` → `Event Driven Ansible Add-on For Splunk` → `Configuration` → Click **Add**

&emsp; a. Give the Webhook a name.\
&emsp; b. **Integration Type:** `Webhook`\
&emsp; c. **Environment:** Give the environment a name.\
&emsp; d. **Webhook Endpoint:** Use the **URL** created in [AAP Step 3 — Event Streams](#3-create-event-stream).\
&emsp; e. **Webhook Auth Type:** `API Key in Header`\
&emsp; f. **Authentication Token:** Use the Token Event Stream created in [AAP Step 2](#2-create-credential) (for example `12345678`).

### 2. Configure the ITSI Episode Action

Navigate to:
`Apps` → `IT Service Intelligence` → `Alerts and Episodes`

&emsp; a. Click on the Episode you want to configure with EDA.\
&emsp; b. Under **Actions**, select **Ansible Episode Action (ITSI)**.\
&emsp; c. **Integration Type:** `Webhook`\
&emsp; d. **Environment:** Choose the relevant environment created in the [Configure the Webhook Step 1c](#1-configure-the-webhook).

> **Tip:** Go to the AAP Rulebook Activation instance to view the EDA activation log.

---

## Scenario #2 — Execute Playbook

Follow the steps below to execute a playbook from the rulebook action.

### Ansible Automation Platform (AAP) Configurations

All steps below are performed on your AAP instance.

### 1. Create Project

Navigate to:
`Automation Execution` → `Projects` → `Create project`

&emsp; a. Give the project a name and fill in all the required fields.\
&emsp; b. **Organization:** `Default`\
&emsp; c. **Source control type:** `Git`\
&emsp; d. **Source control URL:**
```
https://github.com/ansible-collections/splunk.itsi.git
```
&emsp; e. **Source control branch/tag/commit:** `main`

### 2. Create Template

Navigate to:
`Automation Execution` → `Templates` → `Create template`

&emsp; a. Template name should be splunk_itsi_eda if you use the `run_job_template name: splunk_itsi_eda` from `splunk-itsi-rulebook.yml`\
&emsp; In case you give other name, change it also in splunk-itsi-rulebook.yml\
&emsp; Fill in all the required fields.\
&emsp; b. **Project:** Select the project created in [Step 1](#1-create-project-1).\
&emsp; c. **Playbook:** `extensions/eda/playbooks/process_event.yml`\
&emsp; d. In **Extra variables**, check the box — **Prompt on launch**.

### 3. Create Rulebook Activation

Navigate to:
`Automation Decisions` → `Rulebook Activations` → `Create rulebook activation`

&emsp; a. Use the same steps as in [Scenario #1](#scenario-1--webhook-event-stream) to create the rulebook activation.\
&emsp; b. **Rulebook:** Choose `splunk-itsi-rulebook.yml`.

### 4. Splunk ITSI Server

Use the same steps as in [Scenario #1 — Splunk ITSI Server Configurations](#splunk-itsi-server-configurations) to configure the Webhook.

> **Tip:** Go to AAP `Automation Execution` → `Jobs` to view the playbook execution as defined in the template ([Step 2](#2-create-template)).
