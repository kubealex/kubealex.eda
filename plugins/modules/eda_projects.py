#!/usr/bin/python
DOCUMENTATION = """
---
module: eda_project
short_description: Manage projects in EDA Controller
version_added: '1.0'
author: Your Name
description:
  - This module allows you to create/update projects in EDA Controller.
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
  project_name:
    description:
      - The name of the project in EDA Controller.
    required: true
  project_description:
    description:
      - The description of the project in EDA Controller.
    required: false
    default: ''
  project_git_url:
    description:
      - The Git URL of the project in EDA Controller.
    required: false
    default: ''
"""

from ansible.module_utils.basic import AnsibleModule
import requests


def get_project_id(controller_url, controller_user, controller_password, project_name):
    url = f"{controller_url}/api/eda/v1/projects/?name={project_name.replace(' ', '+')}"
    response = requests.get(url, auth=(controller_user, controller_password), verify=False)
    if response.status_code in (200, 201):
        project_id = response.json().get('results', [{}])[0].get('id')
        return int(project_id) if project_id else None


def create_project(module):
    # Extract input parameters from the module object
    controller_url = module.params['controller_url']
    controller_user = module.params['controller_user']
    controller_password = module.params['controller_password']
    project_name = module.params['project_name']
    project_description = module.params['project_description']
    project_git_url = module.params['project_git_url']

    # Check if the project already exists
    url = f"{controller_url}/api/eda/v1/projects/?name={project_name.replace(' ', '+')}"
    response = requests.get(url, auth=(controller_user, controller_password), verify=False)
    if response.status_code in (200, 201):
        project_exists = len(response.json().get('results', [])) > 0
        method = 'PATCH' if project_exists else 'POST'
        project_id = response.json().get('results', [{}])[0].get('id') if project_exists else None

        # Create or update the project
        url = f"{controller_url}/api/eda/v1/projects/{str(project_id) + '/' if project_id else ''}"
        body = {
            'name': project_name,
            'description': project_description,
            'url': project_git_url
        }
        response = requests.request(
            method,
            url,
            auth=(controller_user, controller_password),
            json=body,
            verify=False
        )

        if response.status_code in (200, 201):
            project_id = response.json().get('id')
            module.exit_json(changed=True, project_id=project_id)
        else:
            module.fail_json(msg=f"Failed to create/update project '{project_name}': {response.text}")
    else:
        module.fail_json(msg=f"Failed to check project '{project_name}': {response.text}")


def main():
    module_args = dict(
        controller_url=dict(type='str', required=True),
        controller_user=dict(type='str', required=True),
        controller_password=dict(type='str', required=True, no_log=True),
        project_name=dict(type='str', required=True),
        project_description=dict(type='str', required=False, default=''),
        project_git_url=dict(type='str', required=False, default=''),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    try:
        create_project(module)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
