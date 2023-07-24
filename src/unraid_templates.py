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
                variables[name][user]["variables"][config.attrib["Target"].strip()] = config.attrib["Default"].strip()
            elif config.attrib["Type"].lower() == "port":
                variables[name][user]["ports"].append(f"{config.attrib['Default'].strip()}:{[config.attrib['Target']]}")
            elif config.attrib["Type"].lower() == "path":
                variables[name][user]["volumes"].append(f"{config.attrib['Default'].strip()}:{[config.attrib['Target']]}")
            elif config.attrib["Type"].lower() == "label":
                variables[name][user]["labels"][config.attrib["Target"].strip()] = config.attrib["Default"].strip()
            elif config.attrib["Type"].lower() == "device":
                variables[name][user]["devices"].append(config.attrib["Default"].strip())

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
        repo_file: str = "repos.csv",
        template_file: str = "templates.json",
        repositoryList: str = None,
        repositories=None,
    ):
        self.load_repos(repo_file)
        if not self.repos:
            self.update_repos(repositoryList, repositories)
            self.save_repos(repo_file)

        self.load_templates(template_file)
        print(f"Loaded {len(self.templates)} templates")
        if not self.templates:
            self.get_repo_templates()
            self.save_templates(template_file)

    def save_repos(self, repo_file: str):
        # Save repos to repos.csv
        with open(repo_file, "w") as f:
            for repo in self.repos:
                f.write(f"{repo}\n")

    def load_repos(self, repo_file: str):
        self.repos = []
        if os.path.exists(repo_file):
            with open(repo_file, "r") as f:
                for line in f:
                    self.repos.append(line.strip())

    def save_templates(self, template_file: str):
        # Save templates to templates.json
        with open(template_file, "w") as f:
            json.dump(self.templates, f, indent=4, sort_keys=True)

    def load_templates(self, template_file: str):
        if os.path.exists(template_file):
            print(f"Loading templates from {template_file}")
            with open(template_file, "r") as f:
                self.templates = json.load(f)
        else:
            self.templates = {}

    def update_repos(self, repositoryList: str = None, repositories=None):
        print(
            f"Updating repos from repositoryList: {repositoryList} and repositories: {repositories}"
        )
        self.repos = []
        if repositoryList:
            self.repos.extend(get_repositoryList(repositoryList))

        if repositories:
            if type(repositories) == str:
                repositories = repositories.split(",")

            if type(repositories) == list:
                for repository in repositories:
                    self.repos.append(repository)

    def get_repo_templates(self):
        self.templates = {}
        xmls = {}
        for repo in self.repos:
            # Cloning the repository if it doesn't exist
            try:
                user, name = repo.split("/")[-2:]
                # Check if repo exists and pull if it does, otherwise clone it
                if os.path.exists(f"repos/{user}/{name}"):
                    print(f"Updating {user}/{name}")
                    #git.Repo(f"repos/{user}/{name}").remotes.origin.pull()

                else:
                    # Create directory if it doesn't exist
                    if not os.path.exists(f"repos/{user}"):
                        os.makedirs(f"repos/{user}")

                    #print(f"Cloning {user}/{name}")
                    #git.Repo.clone_from(repo, f"repos/{user}/{name}")
                if user not in xmls:
                    xmls[user] = []

                xmls[user].extend(get_xmls_from_dir(f"repos/{user}/{name}"))
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
