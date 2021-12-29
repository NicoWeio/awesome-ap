import github
from dotenv import load_dotenv
import os
import yaml

from console import *
from generate import generate_md
from import_repo import import_repo
import transpose
from repo import Repo
from export import generate_yaml
from import_external_pdfs import add_aap_pdfs

load_dotenv()
DEV = os.getenv('DEV', 'False').lower() == 'true'

# funktioniert auch ohne Token
TOKEN = os.getenv('GITHUB_TOKEN') or os.getenv('INPUT_GITHUB_TOKEN')
gh = github.Github(TOKEN)

with open("sources.yaml", 'r') as stream:
    repos = yaml.safe_load(stream)

# ■ Laden der Daten:
repos_to_versuche = []
for repo in repos:
    try:
        repos_to_versuche.append(import_repo(Repo(repo, gh)))
    except github.UnknownObjectException:
        pass
    except KeyboardInterrupt:
        warn("\n"*5 + "KeyboardInterrupt – exiting early…")
        break
    except Exception as e:
        error(f'Could not import {repo["name"]}')
        # So ist anhand des Status in GitHub Actions direkt ersichtlich, ob es ein Problem gab.
        raise

# ■ Einbinden der „awesome-ap-pdfs“:
repos_to_versuche = add_aap_pdfs(repos_to_versuche, gh)

versuche_to_repos = transpose.versuche_to_repos(repos_to_versuche)

# ■ Generieren der statischen Website-Inhalte:
if not DEV:  # damit nicht bei jedem Testdurchlauf >100 Dateien geschrieben werden
    generate_md(repos_to_versuche, versuche_to_repos)

# ■ Generieren einer (in erster Linie) maschinenlesbaren Datenbank:
generate_yaml(repos_to_versuche)


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


console.print("Done! 🎉", style='blink bold')
info(stats())
