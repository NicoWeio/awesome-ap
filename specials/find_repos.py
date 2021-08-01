import github
from dotenv import load_dotenv
import os
from rich import print
import yaml

load_dotenv()
# funktioniert auch ohne Token
TOKEN = os.getenv('GITHUB_TOKEN') or os.getenv('INPUT_GITHUB_TOKEN')
gh = github.Github(TOKEN)

with open('sources.yaml', 'r') as stream:
    sources = yaml.safe_load(stream)

source_repos = [source['name'] for source in sources]
usernames = [repo.split('/')[0] for repo in source_repos]

for username in usernames:
    print(f'→ {username}:')
    repos = list(gh.get_user(username).get_repos())
    repo_candidates = [repo for repo in repos if any(match in repo.name.lower() for match in ['ap', 'fp', 'praktikum'])]
    new_candidates = [repo for repo in repo_candidates if not repo.full_name in source_repos]
    if new_candidates:
        print('[green]' + '\n'.join(candidate.full_name for candidate in new_candidates) + '[/green]')
    else:
        print(f'{len(repos)} repo(s); {len(repo_candidates)} candidate(s)')
