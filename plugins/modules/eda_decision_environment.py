#!/usr/bin/python
DOCUMENTATION = """
---
module: eda_decision_envs
short_description: Create or update EDA decision environments.
description:
  - This module allows you to create or update EDA (Event-Driven Architecture) decision environments in a controller.
version_added: "2.12"
options:
  controller_url:
    description:
      - The URL of the EDA controller where the decision environments will be created or updated.
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
  decision_envs:
    description:
      - A list of decision environments to create or update in the EDA controller.
    type: list
    required: true
    elements: dict
    options:
      name:
        description:
          - The name of the decision environment.
        type: str
        required: true
      image_url:
        description:
          - The image URL of the decision environment.
        type: str
        required: false
notes:
  - To create or update EDA decision environments, provide the necessary information through the 'decision_envs' list argument. Each decision environment should be a dictionary with the following subarguments:
    - 'name' (mandatory): The name of the decision environment.
    - 'image_url' (optional): The image URL of the decision environment.
  - The module will check if a decision environment already exists based on the 'name' provided. If the decision environment exists, it will be updated; otherwise, a new decision environment will be created.
  - The 'image_url' field is optional and can be used to specify the image URL associated with the decision environment.
requirements:
  - The 'requests' Python module must be installed on the Ansible control node.

"""

from ansible.module_utils.basic import AnsibleModule
import requests


def get_decision_environment_id(
    controller_url, controller_user, controller_password, decision_environment_name
):
    url = f"{controller_url}/api/eda/v1/decision-environments/?name={decision_environment_name.replace(' ', '+')}"
    response = requests.get(
        url, auth=(controller_user, controller_password), verify=False
    )
    if response.status_code in (200, 201):
        count = response.json().get("count", 0)
        if count > 0:
            denv_id = response.json().get("results", [{}])[0].get("id")
            return int(denv_id) if denv_id else None
    return None


def create_decision_environments(module):
    # Extract input parameters from the module object
    controller_url = module.params["controller_url"]
    controller_user = module.params["controller_user"]
    controller_password = module.params["controller_password"]
    decision_envs = module.params["decision_envs"]

    response_list = []

    for decision_env in decision_envs:
        name = decision_env["name"]
        image_url = decision_env.get("image_url", "")

        # Check if the decision environment already exists
        denv_id = get_decision_environment_id(
            controller_url, controller_user, controller_password, name
        )

        # Prepare request body
        body = {"name": name, "image_url": image_url}

        # Create or update the decision environment
        url = f"{controller_url}/api/eda/v1/decision-environments/"
        if denv_id:
            url += f"{denv_id}/"

        response = requests.request(
            method="PATCH" if denv_id else "POST",
            url=url,
            auth=(controller_user, controller_password),
            json=body,
            verify=False,
        )

        if response.status_code in (200, 201):
            response_list.append(response.json())
        else:
            module.fail_json(
                msg=f"Failed to create or update decision environment '{name}': {response.text}"
            )

        # Debug message to display response content
        module.debug(f"Response Content: {response.content}")

    module.exit_json(changed=True, decision_environments=response_list)


def main():
    module_args = dict(
        controller_url=dict(type="str", required=True),
        controller_user=dict(type="str", required=True),
        controller_password=dict(type="str", required=True, no_log=True),
        decision_envs=dict(type="list", required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    try:
        create_decision_environments(module)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
