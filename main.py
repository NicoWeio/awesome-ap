from github import Github
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import re

load_dotenv()

# funktioniert auch ohne Token
gh = Github(os.getenv('GITHUB_ACCESS_TOKEN'))

with open('sources.json') as f:
  sources = json.load(f)

data = dict()

def getDirsOfInterest(contents):
    # TODO auf einzelne PDFs erweitern
    # TODO various strategies for subdirs etc.
    return [dir for dir in contents if getVersuchNummer(dir.name) and dir.type == 'dir']

def getLastCommit(repo):
    branches = list(repo.get_branches())
    dates = [b.commit.commit.author.date for b in branches]
    return sorted(dates)[-1]

def getVersuchNummer(dirname):
    s = re.search(r'[VD][._]?(\d{3})', dirname, re.IGNORECASE)
    return int(s.group(1)) if s else None

def getFilesRec(path):
    list = []
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            list.append(file_content)
    return list

### Laden der Daten:

for source in sources:
    print('+++', source['name'])
    repo = gh.get_repo(source['name'])
    contents = repo.get_contents(source.get('subdirectory', ''))
    dirsOfInterest = getDirsOfInterest(contents)

    source['lastCommit'] = getLastCommit(repo)
    source['contributors'] = list(repo.get_contributors())

    versuchNummern = [getVersuchNummer(d.name) for d in dirsOfInterest]
    versuchNummern = [i for i in versuchNummern if i] # nicht erkannte Versuchs-Nummern entfernen
    print("Hat Versuche:", versuchNummern)

    for num in versuchNummern:
        data.setdefault(num, []).append(source)

### Generieren der statischen Website-Inhalte:

os.makedirs('build/versuch', exist_ok=True)
os.makedirs('build/repo', exist_ok=True)

## Versuch → Repos
for versuch, repos in data.items():
    with open(f'build/versuch/{versuch}.md', 'w') as g:
        repoNames = [r['name'].split('/')[0] for r in repos]
        print(repoNames)
        # out = json.dumps({'title': versuch, 'repos': repoNames}, indent=4)
        out = f'# Versuch *{versuch}*\n\n'
        out += f'## Repos\n\n'
        out += 'Repo | Link\n'
        out += '--- | ---\n'
        for r in sorted(repos, key=lambda r: r['name']):
            name = r['name'].split('/')[0]
            out += f'{name} | [Übersicht](../repo/{name})\n'
        g.write(out)

## Repo → Versuche
for repo in sources:
    owner = repo['name'].split('/')[0]
    versuche = sorted([int(versuch) for versuch, repos in data.items() if repo in repos])
    repo_url = repo['url']
    with open(f'build/repo/{owner}.md', 'w') as g:
        # out = json.dumps({'title': owner, 'versuche': versuche, 'github': repo['url']}, indent=4)
        out = f'# Repo von *{owner}*\n\n'
        out += f'## [zum Repo auf GitHub]({repo_url})\n\n'

        lastCommit = repo['lastCommit'].strftime('%d.%m.%Y %H:%M:%S')
        out += f'Letzter Commit: {lastCommit}\n\n'

        if len(repo['contributors']) > 1:
            contributors = "\n".join([f'- [{c.login}]({c.html_url})' for c in repo['contributors']])
            out += '## Autoren\n' + contributors + '\n\n'

        out += f'## Versuche\n\n'
        out += 'Versuch | Link\n'
        out += '--- | ---\n'
        for v in versuche:
            out += f'{v} | [Übersicht](../versuch/{v})\n'
        g.write(out)

## Startseite
with open(f'build/index.md', 'w') as g:
    out = '# Startseite\n\n'
    now = datetime.today().strftime('%d.%m.%Y %H:%M:%S')
    out += f'Zuletzt aktualisiert: {now}\n'
    out += f'\n\n'

    versuche = sorted([int(v) for v in data.keys()])
    out += f'## Versuche\n\n'
    out += 'Versuch | Link\n'
    out += '--- | ---\n'
    for v in versuche:
        out += f'{v} | [Übersicht](versuch/{v})\n'
    out += '\n\n'

    out += f'## Repos\n\n'
    out += 'Repo | Link | Letzter Commit\n'
    out += '--- | --- | ---\n'
    for r in sorted(sources, key=lambda r: r['name']):
        name = r['name'].split('/')[0]
        lastCommit = r['lastCommit'].strftime('%d.%m.%Y %H:%M:%S')
        out += f'{name} | [Übersicht](repo/{name}) | {lastCommit}\n'
    out += '\n\n'

    out += '## Statistiken\n'
    out += f'- **{len(data.keys())}** Versuche\n'
    out += f'- **{sum([len(repos) for versuch, repos in data.items()])}** Protokolle\n'

    g.write(out)
