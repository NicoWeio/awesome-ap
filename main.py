import github
import os
import yaml

from config import DEV, GITHUB_TOKEN, REPOS_BASE_PATH
from console import *
from find_common_files import find_common_files
from generate import generate_md
from import_repo import import_repo
import transpose
from repo import Repo
from export import generate_yaml
from import_external_pdfs import add_aap_pdfs

# funktioniert auch ohne Token
gh = github.Github(GITHUB_TOKEN)

with open("config.yaml", 'r') as stream:
    config = yaml.safe_load(stream)

with open("sources.yaml", 'r') as stream:
    repos = yaml.safe_load(stream)

REPOS_BASE_PATH.mkdir(exist_ok=True)

# ■ Laden der Daten:
repos_to_versuche = []
for repo in repos:
    try:
        console.print()
        console.rule(repo['name'])
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
console.rule('*** NicoWeio/awesome-ap-pdfs ***')
repos_to_versuche = add_aap_pdfs(repos_to_versuche, gh)

console.rule('*** Analyse ***')

# transponiere [{repo: {versuche: [versuch]}}] zu {versuch: [repo]}
versuche_to_repos = transpose.versuche_to_repos(repos_to_versuche)

# ■ Finden gemeinsamer Dateien:
versuche_to_common_files = find_common_files(versuche_to_repos, config.get('common_files', {}))
info("gemeinsame Dateien:", versuche_to_common_files)

# ■ Einbinden der manuell kuratierten Informationen zu den Versuchen:
with open("versuche.yaml", 'r') as stream:
    versuche = yaml.safe_load(stream)

console.rule('*** Export ***')

# ■ Generieren der statischen Website-Inhalte:
generate_md(repos_to_versuche, versuche_to_repos, versuche, versuche_to_common_files, dry_run=DEV)

# ■ Generieren einer (in erster Linie) maschinenlesbaren Datenbank:
generate_yaml(repos_to_versuche)


def stats():
    out = ""
    out += f'- {len(repos_to_versuche)} Repos\n'
    out += f'- {len(versuche_to_repos.keys())} Versuche\n'
    out += f'- {sum([len(repos) for versuch, repos in versuche_to_repos.items()])} Protokolle\n'
    out += f'- {sum(repo.num_pdfs for repo in repos_to_versuche)} Protokolle mit PDFs\n'
    out += f'- {sum(repo.num_pdfs_total for repo in repos_to_versuche)} PDFs insgesamt\n'
    return out


console.print("Done! 🎉", style='blink bold')
console.rule('*** Statistiken ***')
info(stats())
