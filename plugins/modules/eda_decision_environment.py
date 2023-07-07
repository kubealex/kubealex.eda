#!/usr/bin/python
DOCUMENTATION = """
---
module: eda_decision_environment
short_description: Manage decision environments in EDA Controller
version_added: '1.0'
author: Your Name
description:
  - This module allows you to create/update decision environments in EDA Controller.
options:
  controller_url:
    description:
      - The URL of the EDA Controller API.
    required: true
  controller_user:
    description:
      - The username for authentication with the EDA Controller API.
    required: true
  controller_password:
    description:
      - The password for authentication with the EDA Controller API.
    required: true
    no_log: true
  decision_environment_name:
    description:
      - The name of the decision environment in EDA Controller.
    required: true
  decision_environment_image_url:
    description:
      - The image URL of the decision environment in EDA Controller.
    required: false
    default: ''
"""

from ansible.module_utils.basic import AnsibleModule
import requests


def get_decision_environment_id(controller_url, controller_user, controller_password, decision_environment_name):
    url = f"{controller_url}/api/eda/v1/decision-environments/?name={decision_environment_name.replace(' ', '+')}"
    response = requests.get(url, auth=(controller_user, controller_password), verify=False)
    if response.status_code in (200, 201):
        denv_id = response.json().get('results', [{}])[0].get('id')
        return int(denv_id) if denv_id else None


def create_decision_environment(module):
    # Extract input parameters from the module object
    controller_url = module.params['controller_url']
    controller_user = module.params['controller_user']
    controller_password = module.params['controller_password']
    decision_environment_name = module.params['decision_environment_name']
    decision_environment_image_url = module.params['decision_environment_image_url']

    # Check if the decision environment already exists
    url = f"{controller_url}/api/eda/v1/decision-environments/?name={decision_environment_name.replace(' ', '+')}"
    response = requests.get(url, auth=(controller_user, controller_password), verify=False)
    if response.status_code in (200, 201):
        denv_exists = len(response.json().get('results', [])) > 0
        method = 'PATCH' if denv_exists else 'POST'
        denv_id = response.json().get('results', [{}])[0].get('id') if denv_exists else None

        # Create or update the decision environment
        url = f"{controller_url}/api/eda/v1/decision-environments/{str(denv_id) + '/' if denv_id else ''}"
        body = {
            'name': decision_environment_name,
            'image_url': decision_environment_image_url
        }
        response = requests.request(
            method,
            url,
            auth=(controller_user, controller_password),
            json=body,
            verify=False
        )

        if response.status_code in (200, 201):
            denv_id = response.json().get('id')
            module.exit_json(changed=True, denv_id=denv_id)
        else:
            module.fail_json(msg=f"Failed to create/update decision environment '{decision_environment_name}': {response.text}")
    else:
        module.fail_json(msg=f"Failed to check decision environment '{decision_environment_name}': {response.text}")


def main():
    module_args = dict(
        controller_url=dict(type='str', required=True),
        controller_user=dict(type='str', required=True),
        controller_password=dict(type='str', required=True, no_log=True),
        decision_environment_name=dict(type='str', required=True),
        decision_environment_image_url=dict(type='str', required=False, default=''),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    try:
        create_decision_environment(module)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()