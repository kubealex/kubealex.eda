#!/usr/bin/python
DOCUMENTATION = """
---
module: eda_projects
short_description: Create or update EDA projects.
description:
  - This module allows you to create or update EDA (Event-Driven Architecture) projects in a controller.
version_added: "2.12"
options:
  controller_url:
    description:
      - The URL of the EDA controller where the projects will be created or updated.
    type: str
    required: true
  controller_user:
    description:
      - The username for authenticating with the EDA controller.
    type: str
    required: true
  controller_password:
    description:
      - The password for authenticating with the EDA controller.
    type: str
    required: true
    no_log: true
  projects:
    description:
      - A list of projects to create or update in the EDA controller.
    type: list
    required: true
    elements: dict
    options:
      name:
        description:
          - The name of the project.
        type: str
        required: true
      description:
        description:
          - The description of the project (optional).
        type: str
        required: false
      git_url:
        description:
          - The Git URL of the project.
        type: str
        required: true
      credential:
        description:
          - The name of the credential to associate with the project (optional).
        type: str
        required: false
notes:
  - To create or update EDA projects, provide the necessary information through the 'projects' list argument. Each project should be a dictionary with the following subarguments:
    - 'name' (mandatory): The name of the project.
    - 'description' (optional): The description of the project.
    - 'git_url' (mandatory): The Git URL of the project.
    - 'credential' (optional): The name of the credential to associate with the project.
  - The 'description' field is optional and will not be included in the payload if it is not defined.
  - The module will check if a project already exists based on the 'name' provided. If the project exists, it will be updated; otherwise, a new project will be created.
  - The 'credential' field is optional and allows associating a credential with the project for authentication purposes.
requirements:
  - The 'requests' Python module must be installed on the Ansible control node.

"""

from ansible.module_utils.basic import AnsibleModule
import requests


def get_project_credential_id(
    controller_url, controller_user, controller_password, project_credential
):
    if not project_credential:
        return None

    url = f"{controller_url}/api/eda/v1/credentials/?name={project_credential}"
    response = requests.get(
        url, auth=(controller_user, controller_password), verify=False
    )
    if response.status_code in (200, 201):
        credential_id = response.json().get("results", [{}])[0].get("id")
        return int(credential_id) if credential_id else None


def create_project(module):
    # Extract input parameters from the module object
    controller_url = module.params["controller_url"]
    controller_user = module.params["controller_user"]
    controller_password = module.params["controller_password"]
    projects = module.params["projects"]

    response_list = []

    for project in projects:
        project_name = project["name"]
        project_description = project.get("description")
        project_git_url = project["git_url"]
        project_credential = project.get("credential")

        # Retrieve project_credential_id
        project_credential_id = get_project_credential_id(
            controller_url, controller_user, controller_password, project_credential
        )

        # Check if the project already exists
        url = f"{controller_url}/api/eda/v1/projects/?name={project_name.replace(' ', '+')}"
        response = requests.get(
            url, auth=(controller_user, controller_password), verify=False
        )
        if response.status_code in (200, 201):
            project_exists = len(response.json().get("results", [])) > 0
            method = "PATCH" if project_exists else "POST"
            project_id = (
                response.json().get("results", [{}])[0].get("id")
                if project_exists
                else None
            )

            # Create or update the project
            url = f"{controller_url}/api/eda/v1/projects/{str(project_id) + '/' if project_id else ''}"
            body = {
                "name": project_name,
                "url": project_git_url,
            }
            if project_description:
                body["description"] = project_description
            if project_credential_id:
                body["credential_id"] = project_credential_id

            response = requests.request(
                method,
                url,
                auth=(controller_user, controller_password),
                json=body,
                verify=False,
            )

            if response.status_code in (200, 201):
                project_id = response.json().get("id")
                response_list.append({"project_id": project_id})
            else:
                module.fail_json(
                    msg=f"Failed to create/update project '{project_name}': {response.text}"
                )
        else:
            module.fail_json(
                msg=f"Failed to check project '{project_name}': {response.text}"
            )

    module.exit_json(changed=True, projects=response_list)


def main():
    module_args = dict(
        controller_url=dict(type="str", required=True),
        controller_user=dict(type="str", required=True),
        controller_password=dict(type="str", required=True, no_log=True),
        projects=dict(
            type="list",
            required=True,
            elements="dict",
            options=dict(
                name=dict(type="str", required=True),
                description=dict(type="str", required=False),
                git_url=dict(type="str", required=True),
                credential=dict(type="str", required=False),
            ),
        ),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    try:
        create_project(module)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
