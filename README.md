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

## Modules

The following modules are included in the collection

| Name                                  | Description                                       |
| ------------------------------------- | ------------------------------------------------- |
| kubealex.eda.eda_activations          | Configure activations in EDA Controller           |
| kubealex.eda.eda_credentials          | Configure credentials in EDA Controller           |
| kubealex.eda.eda_decision_environment | Configure decision_environments in EDA Controller |
| kubealex.eda.eda_projects             | Configure projects in EDA Controller              |

### Usage

A sample playbook to create items using the modules is shown below:

```yaml
---
- name: Example Playbook
  hosts: localhost
  tasks:
    - name: Create EDA Activations
      kubealex.eda.eda_activations:
        controller_url: "https://example-controller.com"
        controller_user: "admin"
        controller_password: "admin123"
        activations:
          - name: Activation 1
            project_name: Project 1
            rulebook: Rulebook 1
            extra_vars: {}
            restart_policy: always
            enabled: true
            decision_env: Decision Environment 1
          - name: Activation 2
            project_name: Project 2
            rulebook: Rulebook 2
            extra_vars: {}
            restart_policy: always
            enabled: true
            decision_env: Decision Environment 2

    - name: Create EDA Decision Environments
      kubealex.eda.eda_decision_envs:
        controller_url: "https://example-controller.com"
        controller_user: "admin"
        controller_password: "admin123"
        decision_envs:
          - name: Decision Environment 1
            image_url: "http://example.com/decision_env1"
          - name: Decision Environment 2
            image_url: "http://example.com/decision_env2"

    - name: Create EDA Credentials
      kubealex.eda.eda_credentials:
        controller_url: "https://example-controller.com"
        controller_user: "admin"
        controller_password: "admin123"
        credentials:
          - name: Credential 1
            description: "Credential 1 description"
            username: "user1"
            secret: "secret1"
            credential_type: "GitHub Personal Access Token"
          - name: Credential 2
            description: "Credential 2 description"
            username: "user2"
            secret: "secret2"
            credential_type: "GitLab Personal Access Token"

    - name: Create EDA Projects
      kubealex.eda.eda_projects:
        controller_url: "https://example-controller.com"
        controller_user: "admin"
        controller_password: "admin123"
        projects:
          - project_name: Project 1
            project_description: "Project 1 description"
            project_git_url: "http://example.com/project1"
            project_credential: "Credential 1"
          - project_name: Project 2
            project_description: "Project 2 description"
            project_git_url: "http://example.com/project2"
            project_credential: "Credential 2"
```

```

```
