import github
from dotenv import load_dotenv
import os
import yaml

from generate import generate_md
from import_repo import import_repo
import transpose

load_dotenv()

# funktioniert auch ohne Token
TOKEN = os.getenv('GITHUB_TOKEN') or os.getenv('INPUT_GITHUB_TOKEN')
gh = github.Github(TOKEN)

with open("sources.yaml", 'r') as stream:
    sources = yaml.safe_load(stream)

### Laden der Daten:
repos_to_versuche = []
for source in sources:
    try:
        repos_to_versuche.append(import_repo(source, gh))
    except github.RateLimitExceededException:
        print("Rate limit exceeded!")
        exit(1)

versuche_to_repos = transpose.versuche_to_repos(repos_to_versuche)

### Generieren der statischen Website-Inhalte:
generate_md(repos_to_versuche, versuche_to_repos)
