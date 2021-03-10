from datetime import datetime
import os
import urllib

def get_url(repo, type='pdfs'):
    base = f"https://github.com/{repo['name']}"
    if 'subdirectory' in repo:
        subdir = urllib.parse.quote(repo['subdirectory'])
        return f"{base}/tree/master/{subdir}"
    else:
        return base

def generate_md(repos_to_versuche, versuche_to_repos):
    os.makedirs('build/versuch', exist_ok=True)
    os.makedirs('build/repo', exist_ok=True)

    ## Versuch → Repos
    for versuch, repos in versuche_to_repos.items():
        with open(f'build/versuch/{versuch}.md', 'w') as g:
            repoNames = [r['name'].split('/')[0] for r in repos]
            out = f'# Versuch *{versuch}*\n\n'
            out += f'## Repos\n\n'
            out += 'Repo | Link\n'
            out += '--- | ---\n'
            for r in sorted(repos, key=lambda r: r['name'].lower()):
                name = r['name'].split('/')[0]
                out += f'{name} | [Übersicht](../repo/{name})\n'
            g.write(out)

    ## Repo → Versuche
    for repo in repos_to_versuche:
        owner = repo['name'].split('/')[0]
        # versuche = sorted([versuch for versuch, repos in versuche_to_repos.items() if repo in repos])
        versuche = sorted(repo['versuchNummern'])
        with open(f'build/repo/{owner}.md', 'w') as g:
            out = f'# Repo von *{owner}*\n\n'
            out += f'## [zum Repo auf GitHub]({get_url(repo)})\n\n'

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

        versuche = sorted(versuche_to_repos.keys())
        out += f'## Versuche\n\n'
        out += 'Versuch | Link | # Repos\n'
        out += '--- | --- | :---:\n'
        for v in versuche:
            repos = versuche_to_repos[v]
            out += f'{v} | [Übersicht](versuch/{v}) | {len(repos)}\n'
        out += '\n\n'

        out += f'## Repos\n\n'
        out += 'Repo | Link | Letzter Commit | # Versuche\n'
        out += '--- | --- | --- | :---:\n'
        for r in sorted(repos_to_versuche, key=lambda r: r['name'].lower()):
            name = r['name'].split('/')[0]
            lastCommit = r['lastCommit'].strftime('%d.%m.%Y %H:%M:%S')
            versuche = [versuch for versuch, repos in versuche_to_repos.items() if r in repos]
            out += f'{name} | [Übersicht](repo/{name}) | {lastCommit} | {len(versuche)}\n'
        out += '\n\n'

        out += '## Statistiken\n'
        out += f'- **{len(repos_to_versuche)}** Repos\n'
        out += f'- **{len(versuche_to_repos.keys())}** Versuche\n'
        out += f'- **{sum([len(repos) for versuch, repos in versuche_to_repos.items()])}** Protokolle\n'

        g.write(out)
