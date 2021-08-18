import github
from dotenv import load_dotenv
import os
import yaml

from generate import generate_md
from import_repo import import_repo
import transpose
from repo import Repo

load_dotenv()

# funktioniert auch ohne Token
TOKEN = os.getenv('GITHUB_TOKEN') or os.getenv('INPUT_GITHUB_TOKEN')
gh = github.Github(TOKEN)

with open("sources.yaml", 'r') as stream:
    repos = yaml.safe_load(stream)
    repos = list(Repo(repo, gh) for repo in repos)

### Laden der Daten:
repos_to_versuche = []
for repo in repos:
    try:
        repos_to_versuche.append(import_repo(repo, gh))
    except:
        print(f'Could not import {repo}')
        raise #TODO: error-handling

versuche_to_repos = transpose.versuche_to_repos(repos_to_versuche)

### Generieren der statischen Website-Inhalte:
# generate_md(repos_to_versuche, versuche_to_repos)

def stats():
    out = ""
    out += '-'*10 + '\n'
    out += '## Statistiken\n'
    out += f'- {len(repos_to_versuche)} Repos\n'
    out += f'- {len(versuche_to_repos.keys())} Versuche\n'
    out += f'- {sum([len(repos) for versuch, repos in versuche_to_repos.items()])} Protokolle\n'
    out += f'- {sum(repo.num_pdfs for repo in repos_to_versuche)} Protokolle mit PDFs\n'
    out += f'- {sum(repo.num_pdfs_total for repo in repos_to_versuche)} PDFs insgesamt\n'
    return out

print("Done! 🎉")
print(stats())