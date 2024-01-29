import json


def template_json_to_list(variables_json: json) -> list:
    output_list = []
    for container_variable in variables_json:
        output_list.append(
            f"{variables_json[container_variable]['Default']}:{container_variable}"
        )

    return output_list


def template_json_to_dict(variables_json: json) -> dict:
    output_dict = {}
    for variable in variables_json:
        output_dict[variable] = variables_json[variable]["Default"]

    return output_dict
