import github
from dotenv import load_dotenv
import os
from rich import print, progress
import yaml

load_dotenv()
# funktioniert auch ohne Token
TOKEN = os.getenv('GITHUB_TOKEN') or os.getenv('INPUT_GITHUB_TOKEN')
gh = github.Github(TOKEN)

with open('sources.yaml', 'r') as stream:
    sources = yaml.safe_load(stream)

with open('specials/discover/config.yaml', 'r') as stream:
    config = yaml.safe_load(stream)


def unique_repos(repos):
    seen = set()
    return [seen.add(obj.full_name) or obj for obj in repos if obj.full_name not in seen]


def unique_users(users):
    seen = set()
    return [seen.add(obj.name) or obj for obj in users if obj.name not in seen]

def match_repo(repo):
    matches = [
        any(match in repo.name.lower() for match in ['ap', 'fp', 'praktikum', 'protokolle']),
        repo.full_name not in config.get('ignore', []),
    ]
    return all(matches)

source_repos = [source['name'] for source in sources]
usernames = [repo.split('/')[0] for repo in source_repos]

users = {username: gh.get_user(username) for username in progress.track(usernames, description='Getting known users…')}

for username, user in progress.track(users.copy().items(), description='Finding users…'):
    print(f"{user=}")
    for follower in list(user.get_followers()):
        print(f"{follower=}")
        users.update({follower.login: follower})
    for followee in list(user.get_following()):
        print(f"{followee=}")
        users.update({followee.login: followee})

print(f"{users=}")
print('–' * 10)

all_new_candidates = []
for user in progress.track(users.values(), description='Discovering repos…'):
    print(f'→ {user.login}:')
    repos = unique_repos(list(user.get_repos()) + list(user.get_starred()))
    # repo_candidates = [repo for repo in repos if ]
    repo_candidates = list(filter(match_repo, repos))
    new_candidates = [repo for repo in repo_candidates if not repo.full_name in source_repos]
    if new_candidates:
        print('[green]' + '\n'.join(candidate.full_name for candidate in new_candidates) + '[/green]')
        all_new_candidates.extend(new_candidates)
    else:
        print(f'{len(repos)} repo(s); {len(repo_candidates)} candidate(s); {len(new_candidates)} new')

all_new_candidates_out = sorted(set([repo.full_name for repo in all_new_candidates]), key=str.casefold)

with open('specials/discover/results.yaml', 'w') as outfile:
    yaml.dump(all_new_candidates_out, outfile, default_flow_style=False)
