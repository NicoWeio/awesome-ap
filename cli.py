import click
import github
from dotenv import load_dotenv
import os
import yaml

from console import *
from import_repo import import_repo
from repo import Repo
from export import serialize_repo

load_dotenv()

# funktioniert auch ohne Token
TOKEN = os.getenv('GITHUB_TOKEN') or os.getenv('INPUT_GITHUB_TOKEN')
gh = github.Github(TOKEN)

with open("sources.yaml", 'r') as stream:
    repos = yaml.safe_load(stream)


@click.command()
@click.option('--repo', '-r', required=False, help='Name of the repo to import: <owner>/<repo>')
def main(repo_name):
    if repo_name:
        repo_name = repo_name.replace('∕', '/')
    repos_to_import = (r for r in repos if r['name'] == repo_name) if repo_name else repos
    if not repos_to_import:
        error(f'Could not find repo {repo_name}')
        return

    for repo_to_import in repos_to_import:
        # Exceptions werden hier bewusst nicht gefangen. Für den Moment ist das CLI nur ein Tool zum Debuggen.
        imported_repo = import_repo(Repo(repo_to_import, gh))
        debug(serialize_repo(imported_repo))

    console.print("Done! 🎉", style='bold')


if __name__ == '__main__':
    main()
