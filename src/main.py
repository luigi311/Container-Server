import os
import json
import traceback
import argparse
import requests
import zipfile
import shutil
from difflib import get_close_matches
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv(override=True)

# Set default values for directories from environment variables or use provided defaults
DOCKER_COMPOSE_FOLDER = os.getenv("DOCKER_COMPOSE_FOLDER", ".")
TEMPLATES_FOLDER = os.getenv("TEMPLATES_FOLDER", "Docker_Compose")

# Function to load the application structure from a JSON file
def load_app_structure(directory):
    with open(os.path.join(directory, "app_list.json"), "r") as f:
        data = json.load(f)
    return data["apps"], data["authors"], data["folder_structure"]

# Function to handle app and author specific operations
def handle_app_author(app_directory, output_directory, args):
    apps, authors, structure = load_app_structure(app_directory)
    app_authors = []

    if args.app:
        matched_apps = [app for app in structure if args.app.lower() == app.lower()]
        if matched_apps:
            if len(matched_apps) > 1:
                print(f"Multiple apps found for {args.app}. There should only be a single match.")
                return

            app = matched_apps[0]
            if args.author:
                matched_authors = [
                    author
                    for author in structure[app]
                    if args.author.lower() == author.lower()
                ]
                if matched_authors:
                    if len(matched_authors) > 1:
                        print(f"Multiple authors found for {app} matching {args.author}. There should only be a single match.")
                        return

                    author = matched_authors[0]
                    print(f"Creating {app} with author {author}")
                    output_app_dir = os.path.join(output_directory, app)
                    source_file = os.path.join(app_directory, app, author, "docker-compose.yml")
                    target_file = os.path.join(output_app_dir, "docker-compose.yml")

                    # Create the application directory if it doesn't exist
                    os.makedirs(output_app_dir, exist_ok=True)
                    
                    # Rename the existing docker-compose.yml file if it exists
                    if os.path.exists(target_file):
                        os.rename(target_file, f"{target_file}.old")
                    
                    # Copy the template docker-compose.yml file to the target location
                    shutil.copyfile(source_file, target_file)
                else:
                    app_authors = structure[app]
                    print(f"Author {args.author} not found for app {args.app}")
                    suggest_matches(args.author, app_authors, "authors")
            else:
                app_authors = structure[app]
                print(f"App name {args.app} has the following authors:")
                print_list(app_authors)
                print("Specify an author with --author")
        else:
            suggest_matches(args.app, apps, "apps")

    elif args.author:
        author_apps = [
            app
            for app, authors in structure.items()
            if args.author.lower() in map(str.lower, authors)
        ]
        if author_apps:
            print(f"Author {args.author} has the following apps:")
            print_list(author_apps)
            print("Specify an app name with --app")
        else:
            suggest_matches(args.author, authors, "authors")

# Function to suggest matches for a given query
def suggest_matches(query, items, item_type):
    matches = get_close_matches(query, items, cutoff=0.5)
    if matches:
        print(f"Did you mean one of the following {item_type}?")
        print_list(matches)
    else:
        print(f"No close matches found for {query} in {item_type}.")

# Function to print a list of items
def print_list(items):
    for item in items:
        print(f"  {item}")

# Function to update the compose files by downloading the latest release and extracting it
def update_compose(directory):
    url = "https://github.com/luigi311/Container-Server-Templates/releases/download/latest/Docker_Compose.zip"
    response = requests.get(url)
    response.raise_for_status()

    zip_path = "Docker_Compose.zip"
    with open(zip_path, "wb") as f:
        f.write(response.content)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(directory)

    os.remove(zip_path)

# Function to parse command-line arguments
def arg_parser():
    parser = argparse.ArgumentParser(
        description="Create docker-compose.yml files from community docker compose files"
    )
    parser.add_argument("--app", help="App name to create docker-compose.yml file for")
    parser.add_argument("--list", action="store_true", help="List apps")
    parser.add_argument("--author", help="Author of the template")
    parser.add_argument("--update_compose", action="store_true", help="Update compose files")
    
    return parser.parse_args()

# Main function to handle the script execution
def main():
    try:
        args = arg_parser()

        # Update the compose files if the folder does not exist or if the update_compose flag is specified
        if not os.path.exists(TEMPLATES_FOLDER) or args.update_compose:
            update_compose(TEMPLATES_FOLDER)

        # Update containers if the update_containers flag is specified
        if args.update_containers:
            update_containers(args.container_system, DOCKER_COMPOSE_FOLDER)

        # Handle app and author arguments
        if args.app or args.author:
            handle_app_author(TEMPLATES_FOLDER, DOCKER_COMPOSE_FOLDER, args)
        elif args.list:
            apps, _, _ = load_app_structure(TEMPLATES_FOLDER)
            print("List of apps:")
            print_list(apps)

    except Exception as error:
        print(f"Error: {error}")
        print(traceback.format_exc())
    except KeyboardInterrupt:
        print("Exiting...")
        os._exit(0)

if __name__ == "__main__":
    main()
