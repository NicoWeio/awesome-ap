from dotenv import load_dotenv
import os
from rich import print, progress
import requests
import yaml
load_dotenv()
TOKEN = os.getenv('GITHUB_TOKEN') or os.getenv('INPUT_GITHUB_TOKEN')
headers = {"Authorization": 'Bearer ' + TOKEN}


def run_query(query):  # A simple function to use requests.post to make the API call. Note the json= section.
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        response = request.json()
        if errors := response.get('errors'):
            raise Exception(f"GraphQL reported error(s): {' +++ '.join(e.get('message', e) for e in errors)}")
        return response
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


def query_repos_for_user(user):
    query = """
    {
        user(login:"<<<USER>>>") {
            followers(first: 100) {
                nodes {
                    ...dings
                }
            }
            following(first: 10) {
                nodes {
                    ...dings
                }
            }
        }
    }
    fragment dings on User {
        login
        repositories(isFork: false, first: 100) {
            nodes {
                isEmpty
                nameWithOwner
                stargazerCount
            }
        }
    }
    """.replace('<<<USER>>>', user)
    try:
        result = run_query(query)
        followers = result['data']['user']['followers']['nodes']
        following = result['data']['user']['following']['nodes']
        all_users = followers + following
        all_repos = [repo for user in all_users for repo in user['repositories']['nodes']]
        print(f"{user}: {len(followers)} followers, {len(following)} following → {len(all_repos)} repos")
        return all_repos
    except Exception as e:
        print(f'An error occured while querying {user}:', e)
        return []


def query_rate_limit():
    query = """
    {
        rateLimit {
            limit
            remaining
            resetAt
        }
    }
    """
    result = run_query(query)
    return result['data']['rateLimit']


with open('sources.yaml', 'r') as stream:
    sources = yaml.safe_load(stream)

with open('specials/discover/config.yaml', 'r') as stream:
    config = yaml.safe_load(stream)

repos_from_sources = [source['name'] for source in sources]
users_from_sources = sorted(set([source['name'].split('/')[0] for source in sources]), key=str.casefold)

print(f"Rate limit before: {query_rate_limit()}")

repos = [repo for user in progress.track(users_from_sources, description='Querying users…')
         for repo in query_repos_for_user(user)]

print(f"Rate limit after: {query_rate_limit()}")


def match_repo(repo):
    matches = [
        # nicht ignoriert?
        repo['nameWithOwner'] not in config.get('ignore', []),
        # nicht leer?
        not repo['isEmpty'],
        # nicht bereits vorhanden?
        not repo['nameWithOwner'] in repos_from_sources,
        # Schlüsselwort im Namen?
        any(match in repo['nameWithOwner'].split('/')[1].lower() for match in ['ap', 'fp', 'praktikum', 'protokolle']),
    ]
    return all(matches)


all_candidates = list(filter(match_repo, repos))
all_candidates_out = sorted(set([repo['nameWithOwner'] for repo in all_candidates]), key=str.casefold)

with open('specials/discover/results.yaml', 'w') as outfile:
    yaml.dump(all_candidates_out, outfile, default_flow_style=False)

print("Done! 🎉")
print(f"{len(all_candidates_out)} repo candidates found")
