#!/usr/bin/python
DOCUMENTATION = """
---
module: eda_credentials
short_description: Create or update credentials in EDA Controller.
description:
  - This module allows creating or updating credentials in EDA Controller. It supports various credential types
    such as GitHub Personal Access Token, GitLab Personal Access Token, and Container registry.
    The module uses the EDA Controller API to interact with the credentials.

options:
  controller_url:
    description:
      - The URL of the EDA Controller.
    type: str
    required: true

  controller_user:
    description:
      - The username for authentication with the EDA Controller.
    type: str
    required: true

  controller_password:
    description:
      - The password for authentication with the EDA Controller.
    type: str
    required: true
    no_log: true

  credentials:
    description:
      - A list of credentials to create or update.
    type: list
    required: true
    elements: dict
    suboptions:
      name:
        description:
          - The name of the credential.
        type: str
        required: true

      description:
        description:
          - The description of the credential.
        type: str
        required: false

      username:
        description:
          - The username associated with the credential.
        type: str
        required: true

      secret:
        description:
          - The secret/password associated with the credential.
        type: str
        required: true
        no_log: true

      credential_type:
        description:
          - The type of the credential.
        type: str
        required: true
        choices:
          - "GitHub Personal Access Token"
          - "GitLab Personal Access Token"
          - "Container registry"

notes:
  - The module retrieves the list of existing credentials by making API requests to the EDA Controller.
  - If a credential with the specified name already exists, it will be updated with the provided information.
    Otherwise, a new credential will be created.
  - The module uses basic authentication to authenticate with the EDA Controller.

requirements:
  - The requests module must be installed on the Ansible control node.

"""
from ansible.module_utils.basic import AnsibleModule
import requests


def check_credential_exists(controller_url, controller_user, controller_password, name):
    url = f"{controller_url}/api/eda/v1/credentials/?name={name}"
    response = requests.get(
        url, auth=(controller_user, controller_password), verify=False
    )
    if response.status_code in (200, 201):
        count = response.json().get("count", 0)
        if count > 0:
            credential_id = response.json().get("results", [{}])[0].get("id")
            return int(credential_id) if credential_id else None
    return None


def create_or_update_credentials(module):
    # Extract input parameters from the module object
    controller_url = module.params["controller_url"]
    controller_user = module.params["controller_user"]
    controller_password = module.params["controller_password"]
    credentials = module.params["credentials"]

    response_list = []

    for credential in credentials:
        name = credential["name"]
        description = credential.get("description")
        username = credential["username"]
        secret = credential["secret"]
        credential_type = credential["credential_type"]

        # Check if credential exists
        credential_id = check_credential_exists(
            controller_url, controller_user, controller_password, name
        )

        # Prepare request body
        body = {
            "name": name,
            "credential_type": credential_type,
            "username": username,
            "secret": secret,
        }
        if description:
            body["description"] = description

        # Create or update credential
        url = f"{controller_url}/api/eda/v1/credentials/"
        if credential_id:
            url += f"{credential_id}/"
            response = requests.patch(
                url,
                auth=(controller_user, controller_password),
                json=body,
                verify=False,
            )
        else:
            response = requests.post(
                url,
                auth=(controller_user, controller_password),
                json=body,
                verify=False,
            )

        if response.status_code in (200, 201):
            response_list.append(response.json())
        else:
            module.fail_json(msg=f"Failed to create or update credential: {name}")

        # Debug message to display response content
        module.debug(f"Response Content: {response.content}")

    module.exit_json(changed=True, credentials=response_list)


def main():
    module_args = dict(
        controller_url=dict(type="str", required=True),
        controller_user=dict(type="str", required=True),
        controller_password=dict(type="str", required=True, no_log=True),
        credentials=dict(
            type="list",
            required=True,
            elements="dict",
            options=dict(
                description=dict(type="str", required=False),
                name=dict(type="str", required=True),
                username=dict(type="str", required=True),
                secret=dict(type="str", required=True, no_log=True),
                credential_type=dict(
                    type="str",
                    required=True,
                    choices=[
                        "GitHub Personal Access Token",
                        "GitLab Personal Access Token",
                        "Container Registry",
                    ],
                ),
            ),
        ),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    try:
        create_or_update_credentials(module)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
