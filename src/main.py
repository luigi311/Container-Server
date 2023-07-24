import os, yaml, json
import traceback
from dotenv import load_dotenv

from src.unraid_templates import Unraid

def create_app_docker_compose(app_name: str, image: str, ports: list, volumes: list, variables: dict):
    docker_compose_config = {
        "version": "3",
        "services": {
            app_name: {
                "image": image,
                "ports": ports,
                "volumes": volumes,
                "environment": variables if variables else None,
            }
        }
    }

    docker_compose_yaml = yaml.dump(docker_compose_config, sort_keys=False)

    if not os.path.exists(app_name):
        os.mkdir(app_name)

    with open(f"{app_name}/docker-compose.yml", "w") as f:
        f.write(docker_compose_yaml)

def create_app(app_name: str, template: json):
    create_app_docker_compose(
        app_name=app_name,
        image=template["repository"],
        ports=template["ports"],
        volumes=template["volumes"],
        variables=template["variables"]
    )


def main():
    try:
        load_dotenv(override=True)

        # Get Unraid templates
        unraid = Unraid(
            repo_file=os.getenv("REPO_FILE", "repos.csv"),
            template_file=os.getenv("TEMPLATE_FILE", "templates.json"),
            repositoryList=os.getenv("UNRAID_REPOSITORY_LIST", None),
            repositories=os.getenv("UNRAID_REPOSITORIES", None),
        )

        # Create docker-compose.yml file for JellyPlex-Watched
        create_app(
            app_name="JellyPlex-Watched",
            template=unraid.templates["jellyplex-watched"]["luigi311"]
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