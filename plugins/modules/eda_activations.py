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
"""

from ansible.module_utils.basic import AnsibleModule
import requests


def get_project_id(controller_url, controller_user, controller_password, project_name):
    url = f"{controller_url}/api/eda/v1/projects/?name={project_name.replace(' ', '+')}"
    response = requests.get(url, auth=(controller_user, controller_password), verify=False)
    if response.status_code in (200, 201):
        projects = response.json().get('results', [])
        if projects:
            return int(projects[0].get('id'))
    return None


def get_denv_id(controller_url, controller_user, controller_password, decision_env):
    url = f"{controller_url}/api/eda/v1/decision-environments/?name={decision_env.replace(' ', '+')}"
    response = requests.get(url, auth=(controller_user, controller_password), verify=False)
    if response.status_code in (200, 201):
        denvs = response.json().get('results', [])
        if denvs:
            return int(denvs[0].get('id'))
    return None


def create_activations(module):
    # Extract input parameters from the module object
    controller_url = module.params['controller_url']
    controller_user = module.params['controller_user']
    controller_password = module.params['controller_password']
    activations = module.params['activations']

    response_list = []

    for activation in activations:
        project_name = activation.get('project_name')
        decision_env = activation.get('decision_env')
        enabled = activation.get('enabled', True)
        restart_policy = activation.get('restart_policy', 'always')
        activation_name = activation['name']
        rulebook_name = activation['rulebook']

        if not project_name:
            module.fail_json(msg="Project name is required for each activation.")
        if not decision_env:
            module.fail_json(msg="Decision environment is required for each activation.")

        project_id = get_project_id(controller_url, controller_user, controller_password, project_name)
        if project_id is None:
            module.fail_json(msg=f"Project '{project_name}' not found.")

        denv_id = get_denv_id(controller_url, controller_user, controller_password, decision_env)
        if denv_id is None:
            module.fail_json(msg=f"Decision environment '{decision_env}' not found.")

        rulebook_list = []
        extra_vars_list = []

        # Retrieve rulebooks
        url = f"{controller_url}/api/eda/v1/rulebooks/?project_id={project_id}"
        response = requests.get(url, auth=(controller_user, controller_password), verify=False)
        if response.status_code in (200, 201):
            rulebooks = response.json().get('results', [])
            for rulebook in rulebooks:
                if rulebook['name'] == rulebook_name:
                    rulebook_list.append({'name': activation_name, 'id': int(rulebook['id'])})
                    break

        # Create extra vars for activations
        if 'extra_vars' in activation and activation['extra_vars']:
            url = f"{controller_url}/api/eda/v1/extra-vars/"
            body = {"extra_var": activation['extra_vars']}
            response = requests.post(url, auth=(controller_user, controller_password),
                                     json=body, verify=False)
            if response.status_code in (200, 201):
                extra_vars_list.append({'name': activation_name, 'var_id': int(response.json().get('id'))})

        # Join rulebook_list and extra_vars_list
        activations_list = []
        for rulebook in rulebook_list:
            activation = {
                'name': rulebook['name'],
                'project_id': project_id,
                'decision_environment_id': denv_id,
                'rulebook_id': rulebook['id'],
                'restart_policy': restart_policy,
                'is_enabled': enabled
            }
            for extra_vars in extra_vars_list:
                if extra_vars['name'] == rulebook['name']:
                    activation['extra_var_id'] = extra_vars['var_id']
                    break
            activations_list.append(activation)

        # Create activations for given project
        url = f"{controller_url}/api/eda/v1/activations/"
        for activation in activations_list:
            body = {
                'restart_policy': activation['restart_policy'],
                'is_enabled': activation['is_enabled'],
                'name': activation['name'],
                'project_id': activation['project_id'],
                'decision_environment_id': activation['decision_environment_id'],
                'rulebook_id': activation['rulebook_id'],
            }
            if 'extra_var_id' in activation:
                body['extra_var_id'] = activation['extra_var_id']
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, auth=(controller_user, controller_password),
                                     json=body, headers=headers, verify=False)
            if response.status_code in (200, 201):
                response_list.append(response.json())

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
