import os, yaml, json, traceback

from dotenv import load_dotenv
from python_on_whales import DockerClient

from src.unraid_templates import Unraid


def create_app_docker_compose(
    folder: str,
    app_name: str,
    image: str,
    ports: list,
    volumes: list,
    variables: dict,
    devices: list,
):
    docker_compose_config = {
        "version": "3",
        "services": {
            app_name: {
                "image": image,
                "ports": ports,
                "volumes": volumes,
                "environment": variables,
                "devices": devices,
            }
        },
    }

    docker_compose_yaml = yaml.dump(docker_compose_config, sort_keys=False)
    if not os.path.exists(f"{folder}/{app_name}"):
        os.makedirs(f"{folder}/{app_name}", exist_ok=True)

    with open(f"{folder}/{app_name}/docker-compose.yml", "w") as f:
        f.write(docker_compose_yaml)


def create_app(folder: str, app_name: str, template: json):
    create_app_docker_compose(
        folder=folder,
        app_name=app_name,
        image=template["repository"],
        ports=template["ports"],
        volumes=template["volumes"],
        variables=template["variables"],
        devices=template["devices"],
    )


def load_templates(folder: str):
    templates = {}

    # Load folder/templates.json
    if os.path.exists(f"{folder}/templates.json"):
        with open(f"{folder}/templates.json", "r") as f:
            templates = json.load(f)

    return templates


def save_templates(folder: str, templates: dict):
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    # Save templates to templates.json
    with open(f"{folder}/templates.json", "w") as f:
        json.dump(templates, f, indent=4, sort_keys=True)


def main():
    try:
        load_dotenv(override=True)

        templates = load_templates(os.getenv("DOCKER_COMPOSE_FOLDER", "."))
        if not templates:
            # Get Unraid templates
            unraid = Unraid(
                repo_folder=os.getenv("UNRAID_REPO_FOLDER", "./Unraid_Repositories"),
                repositoryList=os.getenv("UNRAID_REPOSITORY_LIST", None),
                repositories=os.getenv("UNRAID_REPOSITORIES", None),
            )

            templates = unraid.templates

            save_templates(os.getenv("DOCKER_COMPOSE_FOLDER", "."), templates)

        # Create docker-compose.yml file for JellyPlex-Watched
        create_app(
            folder=os.getenv("DOCKER_COMPOSE_FOLDER", "."),
            app_name="JellyPlex-Watched",
            template=unraid.templates["jellyplex-watched"]["luigi311"],
        )

    except Exception as error:
        if isinstance(error, list):
            for message in error:
                print(message)
        else:
            print(error)

        print(traceback.format_exc())

    except KeyboardInterrupt:
        print("Exiting...")
        os._exit(0)
