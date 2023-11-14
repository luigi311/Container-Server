import os, yaml, json, traceback, argparse

from dotenv import load_dotenv
from difflib import get_close_matches

from src.unraid_templates import Unraid

def template_json_to_list(variables_json: json) -> list:
    output_list = []
    for container_variable in variables_json:
        output_list.append(f"{variables_json[container_variable]['Default']}:{container_variable}")

    return output_list


def template_json_to_dict(variables_json: json) -> dict:
    output_dict = {}
    for variable in variables_json:
        output_dict[variable] = variables_json[variable]["Default"]

    return output_dict


def create_app_docker_compose(folder: str, app_name: str, template: json):
    docker_compose_config = {
        "version": "3",
        "services": {
            app_name: {
                "image": template["image"],
                "network_mode": template["network_mode"],
                "ports": template_json_to_list(template["ports"]) if template["ports"] else [],
                "environment": template_json_to_dict(template["environment"]) if template["environment"] else {},
                "volumes": template_json_to_list(template["volumes"]) if template["volumes"] else [],
                "devices": template_json_to_list(template["devices"]) if template["devices"] else [],
            }
        },
    }

    docker_compose_yaml = yaml.dump(docker_compose_config, sort_keys=False)
    if not os.path.exists(f"{folder}/{app_name}"):
        os.makedirs(f"{folder}/{app_name}", exist_ok=True)

    docker_file_path = f"{folder}/{app_name}/docker-compose.yml"
    if os.path.exists(docker_file_path):
        print(f"docker-compose.yml file already exists at {docker_file_path}")
        print("Moving current file to docker-compose.yml.old")

        if os.path.exists(f"{docker_file_path}.old"):
            os.remove(f"{docker_file_path}.old")

        os.rename(docker_file_path, f"{docker_file_path}.old")

    with open(docker_file_path, "w") as f:
        f.write(docker_compose_yaml)

    print(f"Created {docker_file_path}")


def create_app_args(templates: json, args):
    app_authors = []
    apps, authors = generate_apps_authors(templates)

    if args.app and args.author:
        found = False
        for app in templates.keys():
            if args.app.lower() == app.lower():
                for author in templates[app]:
                    app_authors.append(author)
                    if args.author.lower() == author.lower():
                        found = True
                        print(f"Creating {app} with author {author}")
                        create_app_docker_compose(
                            folder=os.getenv("DOCKER_COMPOSE_FOLDER", "."),
                            app_name=app,
                            template=templates[app][author],
                        )

        if not found:
            if app_authors:
                print(f"Author {args.author} not found for app {args.app}")
                print(f"Did you mean one of the following authors?")
                close_matches = get_close_matches(args.author, app_authors, cutoff=0.5)
                if close_matches:
                    for match in close_matches:
                        print(f"  {match}")
                else:
                    for author in app_authors:
                        print(f"  {author}")
            else:
                print(f"App name {args.app} not found in templates")
                print(f"Did you mean one of the following apps?")
                print(get_close_matches(args.app, apps, cutoff=0.5))

    elif args.app and not args.author:
        for app in templates.keys():
            if args.app.lower() == app.lower():
                for author in templates[app]:
                    app_authors.append(author)

        if app_authors:
            print(f"App name {args.app} has the following authors:")
            for author in app_authors:
                print(f"  {author}")
            print("Specify an author with --author")
        else:
            print(f"App name {args.app} not found in templates")
            print(f"Did you mean one of the following apps?")
            print(get_close_matches(args.app, apps, cutoff=0.5))

    elif not args.app and args.author:
        author_apps = []

        for app in templates:
            for author in templates[app]:
                if args.author.lower() == author.lower():
                    author_apps.append(app)

        if author_apps:
            print(f"Author {args.author} has the following apps:")
            for app in author_apps:
                print(f"  {app}")
            print("Specify an app name with --app")
        else:
            print(f"Author {args.author} not found in templates")
            print(f"Did you mean one of the following authors?")
            print(get_close_matches(args.author, authors, cutoff=0.5))


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


def update_templates():
    # Get Unraid templates
    unraid = Unraid(
        repo_folder=os.getenv("UNRAID_REPO_FOLDER", "./Unraid_Repositories"),
        repositoryList=os.getenv(
            "UNRAID_REPOSITORY_LIST",
            "https://raw.githubusercontent.com/Squidly271/AppFeed/master/repositoryList.json",
        ),
        repositories=os.getenv("UNRAID_REPOSITORIES", None),
    )

    unraid.update_repos()
    unraid.update_templates()

    templates = unraid.templates

    save_templates(os.getenv("DOCKER_COMPOSE_FOLDER", "."), templates)

    return templates


def generate_apps_authors(templates: json):
    apps = []
    authors = []

    for app in templates.keys():
        apps.append(app)
        for author in templates[app].keys():
            authors.append(author)

    # Remove duplicates
    apps = list(dict.fromkeys(apps))
    authors = list(dict.fromkeys(authors))

    return apps, authors


def update_containers(container_system: str, directory: str):
    from python_on_whales import DockerClient

    for folder in os.listdir(directory):
        if os.path.isdir(f"{directory}/{folder}"):
            if folder not in ["Unraid_Repositories", ".git", ".github", "src", ".venv"]:
                compose_file = f"{directory}/{folder}/docker-compose.yml"
                print(f"Updating {folder}")
                if os.path.exists(compose_file):
                    if container_system == "docker":
                        client = DockerClient(compose_files=[compose_file])
                        client.compose.pull()
                        client.compose.up(
                            detach=True,
                            remove_orphans=True,
                        )
                    else:
                        raise Exception("Invalid container system")


def arg_parser():
    parser = argparse.ArgumentParser(
        description="Create docker-compose.yml files from community templates"
    )
    parser.add_argument(
        "--update_templates",
        action="store_true",
        help="Update templates from repositoryList and repositories",
    )
    parser.add_argument("--app", help="App name to create docker-compose.yml file for")
    parser.add_argument("--list", action="store_true", help="List apps")
    parser.add_argument("--author", help="Author of the template")
    parser.add_argument(
        "--update_containers", action="store_true", help="Update containers"
    )
    parser.add_argument(
        "--container_system",
        help="Container system to use",
        default="docker",
        choices=["docker"],
    )
    args = parser.parse_args()

    return args


def main():
    try:
        load_dotenv(override=True)

        args = arg_parser()

        templates = load_templates(os.getenv("DOCKER_COMPOSE_FOLDER", "."))
        updated = False
        if not templates:
            updated = True
            templates = update_templates()

        if args.update_templates:
            # Do not update templates if they were just updated
            if not updated:
                templates = update_templates()

        if args.update_containers:
            update_containers(
                args.container_system, os.getenv("DOCKER_COMPOSE_FOLDER", ".")
            )

        if args.app or args.author:
            create_app_args(templates, args)
        elif args.list:
            print("List of apps:")
            for app in templates.keys():
                print(f"  {app}")

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
