# Event Driven Automation Collection - kubealex.eda

This collection was born with the idea to group some plugins and resources that can be helpful in extending the Event Driven Automation collection.

## Roles

The following roles are included in the collection

| Name                                   | Description                                  |
| -------------------------------------- | -------------------------------------------- |
| kubealex.eda.role_eda_controller_setup | Configure Projects, DE, Rulebook Activations |

### Usage

```yaml
---
- name: Sample EDA Controller Setup
  hosts: localhost
  gather_facts: false

  roles:

  - role: role_eda_controller_setup
    vars:
      eda_controller_url: "https://your-eda-controller-api.com"
      eda_controller_user: "your_eda_user"
      eda_controller_password: "your_eda_password"
      eda_projects: - name: "EDA Demo Project"
      git_url: "https://github.com/kubealex/event-driven-automation"
      description: "Demo project to show EDA in action"
      eda_decision_env: - name: "kubealex-eda"
      image_url: "quay.io/kubealex/eda-decision-env"
      eda_activations: - name: "eda-alertmanager"
      rulebook: "eda-rulebook-alertmanager.yml"
      project_name: EDA Demo Project
      decision_env: Automation Hub Default Decision Environment
```

## Plugins

The following plugins are included in the collection

| Name              | Description                        |
| ----------------- | ---------------------------------- |
| kubealex.eda.mqtt | Configure MQTT listener for events |

### Usage

A sample rulebook using _kubealex.eda.mqtt_ plugin is shown below

```yaml
---
- name: Hello Events
  hosts: all
  sources:
    - kubealex.eda.mqtt:
        host: localhost
        port: 1883
        topic: anomaly-data-out
  rules:
    - name: Debug connection
      condition: event.sensor_location is defined
      action:
        debug:
```
