#!/usr/bin/python
DOCUMENTATION = """
---
module: eda_activations
short_description: Create activations in EDA Controller for a given project and decision environment
options:
  controller_url:
    description:
      - The URL of the EDA Controller.
    type: str
    required: true
  controller_user:
    description:
      - The username for authenticating with the EDA Controller.
    type: str
    required: true
  controller_password:
    description:
      - The password for authenticating with the EDA Controller.
    type: str
    required: true
  activations:
    description:
      - The list of activations to create.
      - Each activation requires the following parameters:
        - name: The name of the activation.
        - project_name: The name of the project associated with the activation.
        - rulebook: The name of the rulebook associated with the activation.
        - extra_vars: The extra variables for the activation.
        - restart_policy: The restart policy for the activation. Default: 'always'
        - enabled: Whether the activation should be enabled. Default: true
        - decision_env: The name of the decision environment.
        - controller_token: The name of the controller token
      - At least one activation must be provided.
    type: list
    required: true
    elements: dict
    options:
      name:
        description:
          - The name of the activation.
        type: str
        required: true
      project_name:
        description:
          - The name of the project associated with the activation.
        type: str
        required: true
      rulebook:
        description:
          - The name of the rulebook associated with the activation.
        type: str
        required: true
      extra_vars:
        description:
          - The extra variables for the activation.
          - Default: ''
        type: str
        default: ''
      restart_policy:
        description:
          - The restart policy for the activation.
          - Default: 'always'
        type: str
        default: 'always'
      enabled:
        description:
          - Whether the activation should be enabled.
          - Default: true
        type: bool
        default: true
      decision_env:
        description:
          - The name of the decision environment.
        type: str
        required: true
      controller_token:
        description:
          - The name of the Controller Token to use
        type: str
        required: true
"""

from ansible.module_utils.basic import AnsibleModule
import requests


def get_project_id(controller_url, controller_user, controller_password, project_name):
    url = f"{controller_url}/api/eda/v1/projects/?name={project_name.replace(' ', '+')}"
    response = requests.get(
        url, auth=(controller_user, controller_password), verify=False
    )
    if response.status_code in (200, 201):
        projects = response.json().get("results", [])
        if projects:
            return int(projects[0].get("id"))
    return None


def get_denv_id(controller_url, controller_user, controller_password, decision_env):
    url = f"{controller_url}/api/eda/v1/decision-environments/?name={decision_env.replace(' ', '+')}"
    response = requests.get(
        url, auth=(controller_user, controller_password), verify=False
    )
    if response.status_code in (200, 201):
        denvs = response.json().get("results", [])
        if denvs:
            return int(denvs[0].get("id"))
    return None

def get_token_id(controller_url, controller_user, controller_password, controller_token):
    url = f"{controller_url}/api/eda/v1/users/me/awx-tokens/"
    response = requests.get(
        url, auth=(controller_user, controller_password), verify=False
    )
    if response.status_code in (200, 201):
        awx_tokens = response.json().get("results", [])
        if awx_tokens:
            for token in awx_tokens:
              if token.get("name") == controller_token:
                return token.get("id")
    return None

def create_activations(module):
    # Extract input parameters from the module object
    controller_url = module.params["controller_url"]
    controller_user = module.params["controller_user"]
    controller_password = module.params["controller_password"]
    activations = module.params["activations"]

    response_list = []

    for activation in activations:
        project_name = activation.get("project_name")
        decision_env = activation.get("decision_env")
        controller_token = activation.get("controller_token")
        enabled = activation.get("enabled", True)
        restart_policy = activation.get("restart_policy", "always")
        activation_name = activation["name"]
        rulebook_name = activation["rulebook"]

        if not project_name:
            module.fail_json(msg="Project name is required for each activation.")
        if not decision_env:
            module.fail_json(
                msg="Decision environment is required for each activation."
            )
        if not controller_token:
            module.fail_json(msg="Controller token name is required for each activation.")

        project_id = get_project_id(
            controller_url, controller_user, controller_password, project_name
        )
        if project_id is None:
            module.fail_json(msg=f"Project '{project_name}' not found.")

        denv_id = get_denv_id(
            controller_url, controller_user, controller_password, decision_env
        )
        if denv_id is None:
            module.fail_json(msg=f"Decision environment '{decision_env}' not found.")

        awx_token_id = get_token_id(controller_url, controller_user, controller_password, controller_token)
        if not awx_token_id:
            module.fail_json(msg=f"Controller token '{controller_token}' not found for user: '{controller_user}'")

        rulebook_list = []

        # Retrieve rulebooks
        rulebook_url = f"{controller_url}/api/eda/v1/rulebooks/?project_id={project_id}"
        response = requests.get(
            rulebook_url, auth=(controller_user, controller_password), verify=False
        )
        if response.status_code in (200, 201):
            rulebooks = response.json().get("results", [])
            for rulebook in rulebooks:
                if rulebook["name"] == rulebook_name:
                    rulebook_list.append(int(rulebook["id"]))
                    break

        if not rulebook_list:
            module.fail_json(
                msg=f"Rulebook '{rulebook_name}' not found in project '{project_name}'."
            )

        # Create activations for given project
        activations_url = f"{controller_url}/api/eda/v1/activations/"
        headers = {"Content-Type": "application/json"}
        for rulebook_id in rulebook_list:
            body = {
                "name": activation_name,
                "project_id": project_id,
                "decision_environment_id": denv_id,
                "rulebook_id": rulebook_id,
                "restart_policy": restart_policy,
                "is_enabled": enabled,
                "awx_token_id": awx_token_id
            }
            if "extra_vars" in activation and activation["extra_vars"]:
                vars_url = f"{controller_url}/api/eda/v1/extra-vars/"
                extra_vars_body = {"extra_var": activation["extra_vars"]}
                response = requests.post(
                    vars_url,
                    auth=(controller_user, controller_password),
                    json=extra_vars_body,
                    headers=headers,
                    verify=False,
                    timeout=15,
                )
                if response.status_code in (200, 201):
                  body["extra_var_id"] = response.json().get("id")

            response = requests.post(
                activations_url,
                auth=(controller_user, controller_password),
                json=body,
                headers=headers,
                verify=False,
                timeout=15,
            )
            if response.status_code in (200, 201):
                response_list.append(response.json())
            elif response.status_code == 400 and "already exists" in ' '.join(response.json().get("name")):
                response_list.append(response.json())
            else:
                module.fail_json(
                    msg=f"Failed to create activation '{activation_name}' for project '{project_name}'. RESPONSE: {response.json()}"
                )

    module.exit_json(changed=True, activations=response_list)


def main():
    module_args = dict(
        controller_url=dict(type='str', required=True),
        controller_user=dict(type='str', required=True),
        controller_password=dict(type='str', required=True, no_log=True),
        activations=dict(
            type='list',
            required=True,
            elements='dict',
            options=dict(
                name=dict(type='str', required=True),
                project_name=dict(type='str', required=True),
                rulebook=dict(type='str', required=True),
                extra_vars=dict(type='str', default=''),
                restart_policy=dict(type='str', default='always'),
                enabled=dict(type='bool', default=True),
                decision_env=dict(type='str', required=True),
                controller_token=dict(type='str', required=True),
            ),
        ),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    try:
        create_activations(module)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
