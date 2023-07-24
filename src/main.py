import os, yaml, json, traceback, argparse

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


def update():
    # Get Unraid templates
    unraid = Unraid(
        repo_folder=os.getenv("UNRAID_REPO_FOLDER", "./Unraid_Repositories"),
        repositoryList=os.getenv("UNRAID_REPOSITORY_LIST", None),
        repositories=os.getenv("UNRAID_REPOSITORIES", None),
    )

    unraid.update_repos()
    unraid.update_templates()

    templates = unraid.templates

    save_templates(os.getenv("DOCKER_COMPOSE_FOLDER", "."), templates)

    return templates


def main():
    try:
        load_dotenv(override=True)

        parser = argparse.ArgumentParser(
            description="Create docker-compose.yml files from community templates"
        )
        parser.add_argument(
            "--update_templates",
            action="store_true",
            help="Update templates from repositoryList and repositories",
        )
        parser.add_argument(
            "--app_name", help="App name to create docker-compose.yml file for"
        )
        parser.add_argument("--author", help="Author of the template")
        args = parser.parse_args()

        templates = load_templates(os.getenv("DOCKER_COMPOSE_FOLDER", "."))
        if not templates:
            templates = update()

        if args.update_templates:
            templates = update()

        if args.app_name and args.author:
            found = False
            for app in templates.keys():
                if args.app_name.lower() == app.lower():
                    for author in templates[app]:
                        if args.author.lower() == author.lower():
                            found = True
                            print(f"Creating {app} with author {author}")
                            create_app(
                                folder=os.getenv("DOCKER_COMPOSE_FOLDER", "."),
                                app_name=app,
                                template=templates[app][author],
                            )

            if not found:
                print(
                    f"App name {args.app_name} with author {args.author} not found in templates"
                )

        elif args.app_name and not args.author:
            authors = []
            for app in templates.keys():
                if args.app_name.lower() == app.lower():
                    for author in templates[app]:
                        authors.append(author)

            if authors:
                print(f"App name {args.app_name} has the following authors:")
                for author in authors:
                    print(f"  {author}")
                print("Specify an author with --author")
            else:
                print(f"App name {args.app_name} not found in templates")

        elif not args.app_name and args.author:
            apps = []
            for app in templates:
                for author in templates[app]:
                    if args.author.lower() == author.lower():
                        apps.append(app)

            if apps:
                print(f"Author {args.author} has the following apps, specify one:")
                for app in apps:
                    print(f"  {app}")
                print("Specify an app name with --app_name")
            else:
                print(f"Author {args.author} not found in templates")

        else:
            print("List of avaliable apps:")
            for app in templates:
                print(f"  {app}")

            print("Specify an app name with --app_name")

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
