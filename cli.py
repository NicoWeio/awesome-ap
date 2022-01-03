from awesome_ap.classes.repo import Repo
from awesome_ap.config import GITHUB_TOKEN
from awesome_ap.console import *
from awesome_ap.exporting.export import serialize_repo
from awesome_ap.importing.import_repo import import_repo
import click
import github
import os
import yaml

# funktioniert auch ohne Token
gh = github.Github(GITHUB_TOKEN)

with open("sources.yaml", 'r') as stream:
    repos = yaml.safe_load(stream)


@click.command()
@click.option('--repo', '-r', 'repo_name', required=False, help='Name of the repo to import: <owner>/<repo>')
def main(repo_name):
    if repo_name:
        repo_name = repo_name.replace('∕', '/')
        repos_to_import = [r for r in repos if r['name'] == repo_name]
        if not repos_to_import:
            error(f'Could not find repo {repo_name}')
            return
    else:
        repos_to_import = repos

    for repo_to_import in repos_to_import:
        # Exceptions werden hier bewusst nicht gefangen. Für den Moment ist das CLI nur ein Tool zum Debuggen.
        imported_repo = import_repo(Repo(repo_to_import, gh))
        debug(serialize_repo(imported_repo))

    console.print("Done! 🎉", style='bold')


if __name__ == '__main__':
    main()
