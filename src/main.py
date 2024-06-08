import os, re, json, traceback, argparse, requests, zipfile, shutil

from dotenv import load_dotenv
from difflib import get_close_matches

load_dotenv(override=True)

DOCKER_COMPOSE_FOLDER = os.getenv("DOCKER_COMPOSE_FOLDER", ".")
TEMPLATES_FOLDER = os.getenv("TEMPLATES_FOLDER", "Docker_Compose")


def generate_apps_authors_structure(directory: str):
    with open(f"{directory}/app_list.json", "r") as f:
        app_list = json.load(f)

    apps = app_list["apps"]
    authors = app_list["authors"]
    structure = app_list["folder_structure"]

    return apps, authors, structure


def args_app_author(app_directory: str, output_directory, args):
    app_authors = []
    apps, authors, structure = generate_apps_authors_structure(app_directory)

    if args.app and args.author:
        found = False
        for app in structure.keys():
            if args.app.lower() == app.lower():
                for author in structure[app]:
                    if args.author.lower() == author.lower():
                        found = True
                        print(f"Creating {app} with author {author}")
                        docker_file_path = os.path.join(
                            output_directory, app, "docker-compose.yml"
                        )
                        source_file_path = os.path.join(
                            app_directory, app, author, "docker-compose.yml"
                        )

                        # Create application directory if it does not exist
                        if not os.path.exists(f"{output_directory}/{app}"):
                            os.makedirs(f"{output_directory}/{app}", exist_ok=True)

                        # Rename existing docker-compose.yml file to docker-compose.yml.old
                        if os.path.exists(docker_file_path):
                            if os.path.exists(f"{docker_file_path}.old"):
                                os.remove(f"{docker_file_path}.old")
                            os.rename(docker_file_path, f"{docker_file_path}.old")

                        # Copy the template docker-compose.yml file to the application directory
                        shutil.copyfile(source_file_path, docker_file_path)

                    else:
                        app_authors.append(author)

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
                print(f"App name {args.app} not found in docker compose folder")
                print(f"Did you mean one of the following apps?")
                print(get_close_matches(args.app, apps, cutoff=0.5))

    elif args.app and not args.author:
        for app in structure.keys():
            if args.app.lower() == app.lower():
                for author in structure[app]:
                    app_authors.append(author)

        if app_authors:
            print(f"App name {args.app} has the following authors:")
            for author in app_authors:
                print(f"  {author}")
            print("Specify an author with --author")
        else:
            print(f"App name {args.app} not found in docker compose folder")
            print(f"Did you mean one of the following apps?")
            print(get_close_matches(args.app, apps, cutoff=0.5))

    elif not args.app and args.author:
        author_apps = []

        for app in structure.keys():
            for author in structure[app]:
                if args.author.lower() == author.lower():
                    author_apps.append(app)

        if author_apps:
            print(f"Author {args.author} has the following apps:")
            for app in author_apps:
                print(f"  {app}")
            print("Specify an app name with --app")
        else:
            print(f"Author {args.author} not found in docker compose folder")
            print(f"Did you mean one of the following authors?")
            print(get_close_matches(args.author, authors, cutoff=0.5))


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


def update_compose(directory: str):
    # Download the latest release
    url = "https://github.com/luigi311/Container-Server-Templates/releases/download/latest/Docker_Compose.zip"
    response = requests.get(url)
    response.raise_for_status()

    # Save the zip file
    with open("Docker_Compose.zip", "wb") as f:
        f.write(response.content)

    # Unzip the file
    with zipfile.ZipFile("Docker_Compose.zip", "r") as zip_ref:
        zip_ref.extractall(directory)

    # Remove the zip file
    os.remove("Docker_Compose.zip")


def arg_parser():
    parser = argparse.ArgumentParser(
        description="Create docker-compose.yml files from community docker compose files"
    )
    parser.add_argument("--app", help="App name to create docker-compose.yml file for")
    parser.add_argument("--list", action="store_true", help="List apps")
    parser.add_argument("--author", help="Author of the template")
    parser.add_argument(
        "--update_compose", action="store_true", help="Update compose files"
    )
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
        args = arg_parser()

        # If the folder does not exist or if update_compose is specified, update the compose files
        if not os.path.exists(TEMPLATES_FOLDER) or args.update_compose:
            update_compose(TEMPLATES_FOLDER)

        if args.update_containers:
            update_containers(args.container_system, DOCKER_COMPOSE_FOLDER)

        if args.app or args.author:
            args_app_author(TEMPLATES_FOLDER, DOCKER_COMPOSE_FOLDER, args)
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
