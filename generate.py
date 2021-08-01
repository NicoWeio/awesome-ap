from datetime import datetime
import os
import pytablewriter
import urllib

def fmt_repo(repo):
    owner = repo["name"].split("/")[0]
    return f'[{owner}](../repo/{owner})'

def fmt_dirs(dirs):
    if not dirs:
        return '–'
    return '<br/>'.join(fmt_content(dir) for dir in dirs)

def fmt_pdfs(pdfs):
    if not pdfs:
        return '–'
    return '<br/>'.join(fmt_pdf(pdf) for pdf in pdfs)

def fmt_pdf(pdf):
    return f"[{pdf.name}](https://docs.google.com/viewer?url={pdf.download_url})" if pdf else '–'

def fmt_content(c):
    from pathlib import Path
    assert isinstance(c, Path)
    html_url = content_url("CHR", "PRAKT", c)
    return f"[{c.name}]({html_url})" if c else '–'

def content_url(username, repo_name, path):
    return f"https://github.com/{username}/{repo_name}/tree/master/{path}"

def generate_md(repos_to_versuche, versuche_to_repos):
    os.makedirs('build/versuch', exist_ok=True)
    os.makedirs('build/repo', exist_ok=True)
    writer = pytablewriter.MarkdownTableWriter()

    ## Versuch → Repos
    for versuch, repos in versuche_to_repos.items():
        with open(f'build/versuch/{versuch}.md', 'w') as g:
            out = f'# Versuch *{versuch}*\n\n'
            out += f'## Repos\n\n'

            writer.headers = ['Repo von', 'Ordner', 'PDFs']
            writer.value_matrix = []
            for r in repos:
                versuch_data = r['versuche'][versuch]
                writer.value_matrix.append((
                    fmt_repo(r),
                    fmt_dirs(versuch_data.get('dirs')),
                    fmt_pdfs(versuch_data.get('pdfs'))
                 ))
            out += writer.dumps()
            g.write(out)

    ## Repo → Versuche
    for repo in repos_to_versuche:
        owner = repo['name'].split('/')[0]
        with open(f'build/repo/{owner}.md', 'w') as g:
            out = f'# Repo von *{owner}*\n\n'
            out += f'## [zum Repo auf GitHub]({repo["repo"].html_url})\n\n'

            lastCommit = repo['lastCommit'].strftime('%d.%m.%Y %H:%M:%S')
            out += f'Letzter Commit: {lastCommit}\n\n'

            if len(repo['contributors']) > 1:
                contributors = "\n".join([f'- [{c.login}]({c.html_url})' for c in repo['contributors']])
                out += '## Autoren\n' + contributors + '\n\n'

            out += f'## Versuche\n\n'
            writer.headers = ['Versuch', 'Ordner', 'PDFs']
            writer.value_matrix = []
            for num in sorted(repo['versuche']):
                v = repo['versuche'][num]
                writer.value_matrix.append((
                    f'[{num}](../versuch/{num})',
                    fmt_dirs(v.get('dirs')),
                    fmt_pdfs(v.get('pdfs'))
                ))
            out += writer.dumps()

            g.write(out)

    ## Startseite
    with open(f'build/index.md', 'w') as g:
        out = '# Startseite\n\n'
        # now = datetime.today().strftime('%d.%m.%Y %H:%M:%S')
        # out += f'Zuletzt aktualisiert: {now}\n'
        # out += f'\n\n'

        out += f'## Versuche\n\n'
        writer.headers = ['Versuch', '', 'Repos']
        writer.value_matrix = [(v, f'[Übersicht](versuch/{v})', len(versuche_to_repos[v])) for v in sorted(versuche_to_repos.keys())]
        out += writer.dumps()
        out += '\n\n'

        out += f'## Repos\n\n'
        writer.headers = ['Repo von', '', 'Letzter Commit', '# Versuche']
        writer.value_matrix = []
        for r in sorted(repos_to_versuche, key=lambda r: r['name'].lower()):
            name = r['name'].split('/')[0]
            lastCommit = r['lastCommit'].strftime('%d.%m.%Y %H:%M:%S')
            versuche = [versuch for versuch, repos in versuche_to_repos.items() if r in repos]
            writer.value_matrix.append((
                f'[{name}]({r["repo"].html_url})',
                f'[Übersicht](repo/{name})',
                f'{lastCommit}',
                f'{len(versuche)}'))
        out += writer.dumps()
        out += '\n\n'

        out += '## Statistiken\n'
        out += f'- **{len(repos_to_versuche)}** Repos\n'
        out += f'- **{len(versuche_to_repos.keys())}** Versuche\n'
        out += f'- **{sum([len(repos) for versuch, repos in versuche_to_repos.items()])}** Protokolle\n'

        g.write(out)
