#!/usr/bin/python
DOCUMENTATION = """
---
module: eda_project
short_description: Manage EDA projects in the EDA Controller
description:
  - This module allows you to create or update projects in the EDA Controller.
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
  project_name:
    description:
      - Name of the project.
    type: str
    required: true
  project_description:
    description:
      - Description of the project (optional).
    type: str
    required: false
    default: ""
  project_git_url:
    description:
      - Git URL of the project (optional).
    type: str
    required: false
    default: ""
  project_credential:
    description:
      - Name of the credential to associate with the project (optional).
    type: str
    required: false
    default: ""
notes:
  - If the project already exists, it will be updated with the provided information.
  - The module uses the EDA Controller API to manage the projects.
  - The module does not support check mode.
requirements:
  - requests module
"""

from ansible.module_utils.basic import AnsibleModule
import requests


def get_project_credential_id(controller_url, controller_user, controller_password, project_credential):
    if not project_credential:
        return None

    url = f"{controller_url}/api/eda/v1/credentials/?name={project_credential}"
    response = requests.get(url, auth=(controller_user, controller_password), verify=False)
    if response.status_code in (200, 201):
        credential_id = response.json().get('results', [{}])[0].get('id')
        return int(credential_id) if credential_id else None


def create_project(module):
    # Extract input parameters from the module object
    controller_url = module.params['controller_url']
    controller_user = module.params['controller_user']
    controller_password = module.params['controller_password']
    project_name = module.params['project_name']
    project_description = module.params['project_description']
    project_git_url = module.params['project_git_url']
    project_credential = module.params['project_credential']

    # Retrieve project_credential_id
    project_credential_id = get_project_credential_id(controller_url, controller_user, controller_password, project_credential)

    # Check if the project already exists
    url = f"{controller_url}/api/eda/v1/projects/?name={project_name.replace(' ', '+')}"
    response = requests.get(url, auth=(controller_user, controller_password), verify=False)
    if response.status_code in (200, 201):
        project_exists = len(response.json().get('results', [])) > 0
        method = 'PATCH' if project_exists else 'POST'
        project_id = response.json().get('results', [{}])[0].get('id') if project_exists else None

        # Create or update the project
        url = f"{controller_url}/api/eda/v1/projects/{project_id + '/' if project_id else ''}"
        body = {
            'name': project_name,
            'description': project_description,
            'url': project_git_url,
        }
        if project_credential_id:
            body['credential_id'] = project_credential_id

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
        project_credential=dict(type='str', required=False, default='')
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
