import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..', '..'))
# ---
from awesome_ap.config import GITHUB_TOKEN, REPOS_BASE_PATH
from awesome_ap.console import *
from awesome_ap.misc import get_command_runner
from pathlib import Path
import click
import github
import yaml



BUNDLES_BASE_PATH = REPOS_BASE_PATH / '0_BUNDLES'
BUNDLES_BASE_PATH.mkdir(exist_ok=True)

# funktioniert auch ohne Token
gh = github.Github(GITHUB_TOKEN)

with open("sources.yaml", 'r') as stream:
    repos = yaml.safe_load(stream)


def is_repo_available(full_name):
    try:
        gh_repo = gh.get_repo(full_name)
        return True
    except github.UnknownObjectException:
        return False


def archive_repo(repo):
    cwd_path = REPOS_BASE_PATH / repo['name'].replace('/', '∕')

    if not cwd_path.exists():
        error(f"Local clone of {repo['name']} not found. Skipping…")
        return

    run_command = get_command_runner(cwd_path)
    bundle_path = BUNDLES_BASE_PATH / f"{repo['name'].replace('/', '∕')}.bundle"

    if bundle_path.exists():
        warning(f"Bundle for {repo['name']} already exists. Skipping…")
        return

    run_command(['git', 'bundle', 'create', str(bundle_path.absolute()), '--all'])


@click.command()
@click.option('--only-notfound/--all', help='Whether to only archive repos that are not found online', is_flag=True, default=True)
def main(only_notfound):
    for repo_source in track(repos):
        if (not only_notfound or not is_repo_available(repo_source['name'])):
            archive_repo(repo_source)


if __name__ == '__main__':
    main()
