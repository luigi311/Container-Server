import json, requests, os
import git

import xml.etree.ElementTree as ET

exclude_xmls = ["ca_profile.xml"]
exclude_dirs = [".git", ".github", "issues", "depricated", ".history", ".idea"]


def get_repositoryList(repositoryList: str):
    # Request repositoryList.json from url and parse it into a dictionary
    repositoryListJson = json.loads(requests.get(repositoryList).text)

    repositories = []
    for repository in repositoryListJson:
        repositories.append(repository["url"])

    return repositories


def parse_template(template: str, user: str, file_name: str):
    try:
        # Parse template and return variables
        variables = {}
        root = ET.fromstring(template)

        # Get template name
        name = root.findtext("Name")
        variables[name] = {}
        variables[name][user] = {}

        # Get template repository
        variables[name][user]["repository"] = root.findtext("Repository")

        if not variables[name][user]["repository"]:
            return

        # Get template description
        variables[name][user]["description"] = root.findtext("Overview")

        # Get template network type
        variables[name][user]["networkType"] = root.findtext("Network")

        variables[name][user]["variables"] = {}
        variables[name][user]["ports"] = []
        variables[name][user]["volumes"] = []
        variables[name][user]["labels"] = {}
        variables[name][user]["devices"] = []

        # Iterate though all the Config tags and create a dictionary of the Configs and their values using the Config's Name tag as the key
        # with the value being a dictionary of the Config's attributes
        for config in root.findall("Config"):
            if config.attrib["Type"].lower() == "variable":
                variables[name][user]["variables"][
                    config.attrib["Target"].strip()
                ] = config.attrib["Default"].strip()
            elif config.attrib["Type"].lower() == "port":
                variables[name][user]["ports"].append(
                    f"{config.attrib['Default'].strip()}:{config.attrib['Target'].strip()}"
                )
            elif config.attrib["Type"].lower() == "path":
                variables[name][user]["volumes"].append(
                    f"{config.attrib['Default'].strip()}:{config.attrib['Target'].strip()}"
                )
            elif config.attrib["Type"].lower() == "label":
                variables[name][user]["labels"][
                    config.attrib["Target"].strip()
                ] = config.attrib["Default"].strip()
            elif config.attrib["Type"].lower() == "device":
                variables[name][user]["devices"].append(
                    f"{config.attrib['Default'].strip()}:{config.attrib['Default'].strip()}"
                )

        return variables

    except Exception as error:
        print(f"Failed to parse template {file_name}: {error}")
        return


def get_xmls_from_dir(directory: str):
    xmls = []
    # Iterate through directory and subdirectories and add all xml files to xmls
    # excluding files named exclude_xmls and directories containing anything in exclude_dirs
    for file in os.listdir(directory):
        if os.path.isdir(f"{directory}/{file}"):
            # if directory contains anything in exclude_dirs ignoring case, skip it
            if any(exclude_dir.lower() in file.lower() for exclude_dir in exclude_dirs):
                continue
            xmls.extend(get_xmls_from_dir(f"{directory}/{file}"))
        elif file.endswith(".xml"):
            if file in exclude_xmls:
                continue
            xmls.append(f"{directory}/{file}")

    return xmls


# Parse Unraid templates and return variables for use in container creation
class Unraid:
    def __init__(
        self,
        repo_folder: str = "./Unraid_Repositories",
        repositoryList: str = None,
        repositories: list = None,
    ):
        self.repo_folder = repo_folder
        self.repo_file = f"{repo_folder}/unraid_repos.csv"
        self.template_file = f"{repo_folder}/unraid_templates.json"
        self.repositoryList = repositoryList
        self.repositories = repositories

        self.load_repos()
        self.load_templates()

    def save_repos(self):
        if not os.path.exists(self.repo_folder):
            os.makedirs(self.repo_folder, exist_ok=True)

        # Save repos to repos.csv
        with open(self.repo_file, "w") as f:
            for repo in self.repos:
                f.write(f"{repo}\n")

    def load_repos(self):
        self.repos = []
        if os.path.exists(self.repo_file):
            with open(self.repo_file, "r") as f:
                for line in f:
                    self.repos.append(line.strip())

    def update_repos(self):
        self.repos = []
        if self.repositoryList:
            self.repos.extend(get_repositoryList(self.repositoryList))

        if self.repositories:
            if type(self.repositories) == str:
                repositories = self.repositories.split(",")

            if type(repositories) == list:
                for repository in repositories:
                    self.repos.append(repository)

        self.save_repos()

    def save_templates(self):
        if not os.path.exists(self.repo_folder):
            os.makedirs(self.repo_folder, exist_ok=True)

        # Save templates to templates.json
        with open(self.template_file, "w") as f:
            json.dump(self.templates, f, indent=4, sort_keys=True)

    def load_templates(self):
        if os.path.exists(self.template_file):
            print(f"Loading templates from {self.template_file}")
            with open(self.template_file, "r") as f:
                self.templates = json.load(f)
        else:
            self.templates = {}

    def update_templates(self):
        self.templates = {}
        xmls = {}
        for repo in self.repos:
            # Cloning the repository if it doesn't exist
            try:
                user, name = repo.split("/")[3:5]
                repo_path = f"{self.repo_folder}/{user}/{name}"

                if os.path.exists(repo_path):
                    print(f"Updating {user}/{name}")
                    git.Repo(repo_path).remotes.origin.pull()
                else:
                    # Create directory if it doesn't exist
                    os.makedirs(repo_path, exist_ok=True)

                    print(f"Cloning {user}/{name}")
                    git.Repo.clone_from(repo, repo_path)

                if user not in xmls:
                    xmls[user] = []

                xmls[user].extend(get_xmls_from_dir(repo_path))
            except:
                print(f"Failed to clone {repo}")
                continue

        for user in xmls:
            for xml in xmls[user]:
                try:
                    with open(xml, "r") as f:
                        template_str = f.read()

                    template = parse_template(template_str, user, xml)
                    if template:
                        self.templates.update(template)

                except Exception as error:
                    continue

        self.save_templates()
