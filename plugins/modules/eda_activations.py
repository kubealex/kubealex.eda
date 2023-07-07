#!/usr/bin/python
DOCUMENTATION = """
---
module: eda_activations
short_description: Manage EDA activations in the EDA Controller
description:
  - This module allows you to create activations in the EDA Controller.
version_added: "2.12"
options:
  controller_url:
    description:
      - Base URL of the EDA Controller API.
    type: str
    required: true
  controller_user:
    description:
      - Username for basic authentication with the EDA Controller API.
    type: str
    required: true
  controller_password:
    description:
      - Password for basic authentication with the EDA Controller API.
    type: str
    required: true
    no_log: true
  activations:
    description:
      - List of activation objects to create in the EDA Controller.
    type: list
    required: true
    elements: dict
    suboptions:
      name:
        description:
          - Name of the activation.
        type: str
        required: true
      restart_policy:
        description:
          - Restart policy for the activation (default: always).
        type: str
        required: false
        default: always
      enabled:
        description:
          - Whether the activation is enabled (default: true).
        type: bool
        required: false
        default: true
      decision_env:
        description:
          - ID of the decision environment to associate with the activation.
        type: int
        required: true
      project_id:
        description:
          - ID of the project for the activation.
        type: int
        required: true
      rulebook_id:
        description:
          - ID of the rulebook to associate with the activation.
        type: int
        required: true
      extra_var_id:
        description:
          - ID of the extra variable to associate with the activation.
        type: int
        required: false
requirements:
  - requests module

"""

from ansible.module_utils.basic import AnsibleModule
import requests


def get_decision_environment_id(controller_url, controller_user, controller_password, decision_env):
    # Build the URL for retrieving the decision environment ID
    url = f"{controller_url}/api/eda/v1/decision-environments/?name={decision_env}"
    response = requests.get(url, auth=(controller_user, controller_password), verify=False)

    if response.status_code in (200, 201):
        results = response.json().get('results', [])
        if results:
            return results[0].get('id')
        else:
            raise Exception(f"Decision environment '{decision_env}' not found.")
    else:
        raise Exception(f"Failed to retrieve decision environment '{decision_env}': {response.text}")


def create_activation(module, decision_env_id):
    # Extract input parameters from the module object
    controller_url = module.params['controller_url']
    controller_user = module.params['controller_user']
    controller_password = module.params['controller_password']
    activations = module.params['activations']

    # Create activations
    for activation in activations:
        # Extract activation parameters
        name = activation.get('name')
        restart_policy = activation.get('restart_policy', 'always')
        enabled = activation.get('enabled', True)
        decision_env = activation.get('decision_env')
        project_id = activation.get('project_id')
        rulebook_id = activation.get('rulebook_id')
        extra_var_id = activation.get('extra_var_id')

        # Retrieve decision environment ID
        decision_env_id = get_decision_environment_id(controller_url, controller_user, controller_password, decision_env)

        # Build the request body
        body = {
            'restart_policy': restart_policy,
            'is_enabled': enabled,
            'name': name,
            'project_id': project_id,
            'decision_environment_id': decision_env_id,
            'rulebook_id': rulebook_id,
            'extra_var_id': extra_var_id
        }

        # Send the request to create the activation
        url = f"{controller_url}/api/eda/v1/activations/"
        response = requests.post(url, auth=(controller_user, controller_password), json=body, verify=False)

        if response.status_code in (200, 201):
            module.exit_json(changed=True, activation_id=response.json().get('id'))
        else:
            module.fail_json(msg=f"Failed to create activation '{name}': {response.text}")


def main():
    module_args = dict(
        controller_url=dict(type='str', required=True),
        controller_user=dict(type='str', required=True),
        controller_password=dict(type='str', required=True, no_log=True),
        activations=dict(type='list', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    try:
        create_activation(module)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
