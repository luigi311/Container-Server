import os
from dotenv import load_dotenv

from src.unraid_templates import Unraid


def main():
    load_dotenv(override=True)

    # Get Unraid templates
    unraid = Unraid(
        repo_file=os.getenv("REPO_FILE", "repos.csv"),
        template_file=os.getenv("TEMPLATE_FILE", "templates.json"),
        repositoryList=os.getenv("UNRAID_REPOSITORY_LIST", None),
        repositories=os.getenv("UNRAID_REPOSITORIES", None),
    )
