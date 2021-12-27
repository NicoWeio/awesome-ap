from datetime import datetime
import os
import pytablewriter
from urllib.parse import quote
from console import *

def fmt_repo(repo):
    return f'[{repo.full_name}](../repo/{repo.full_name})'

def fmt_dirs(repo, dirs):
    if not dirs:
        return '–'
    return '<br/>'.join(fmt_content(repo, dir) for dir in sorted(dirs, key=lambda dir: dir.name.lower()))

def fmt_pdfs(repo, pdfs):
    if not pdfs:
        return '–'
    return '<br/>'.join(fmt_pdf(pdf) for pdf in sorted(pdfs, key=lambda pdf: pdf.name.lower()))

def fmt_pdf(pdf):
    return f"[{pdf.name}](https://docs.google.com/viewer?url={pdf.download_url})" + (r' \*' if getattr(pdf, 'is_user_generated', True) is False else '')

def fmt_content(repo, c):
    from pathlib import Path
    assert isinstance(c, Path)
    html_url = content_url(repo, c)
    return f"[{c.name}]({html_url})" if c else '–'

def content_url(repo, path):
    return f'{repo.html_url}/tree/{repo.branch}/{quote(str(path))}'

def generate_md(repos_to_versuche, versuche_to_repos):
    os.makedirs('build/versuch', exist_ok=True)
    os.makedirs('build/repo', exist_ok=True)
    writer = pytablewriter.MarkdownTableWriter()

    ## Versuch → Repos
    for versuch, repos in versuche_to_repos.items():
        with open(f'build/versuch/{versuch}.md', 'w') as g:
            out = f'# Versuch *{versuch}*\n\n'
            out += f'## Repos\n\n'

            writer.headers = ['Repo', 'Ordner', 'PDFs']
            writer.value_matrix = []
            for repo in sorted(repos, key=lambda r: r.full_name.lower()):
                versuch_data = repo.versuche[versuch]
                writer.value_matrix.append((
                    fmt_repo(repo),
                    fmt_dirs(repo, versuch_data.get('dirs')),
                    fmt_pdfs(repo, versuch_data.get('pdfs'))
                 ))
            out += writer.dumps()
            g.write(out)

    ## Repo → Versuche
    for repo in repos_to_versuche:
        os.makedirs(f'build/repo/{repo.login}', exist_ok=True)
        with open(f'build/repo/{repo.login}/{repo.name}.md', 'w') as g:
            out = f'# [{repo.full_name}]({repo.html_url})\n\n'

            lastCommit = repo.last_commit.strftime('%d.%m.%Y %H:%M:%S')
            out += f'Letzter Commit: {lastCommit}\n\n'

            if len(repo.contributors) > 1:
                contributors = "\n".join([f'- [{c.login}]({c.html_url})' for c in repo.contributors])
                out += '## Autoren\n' + contributors + '\n\n'

            out += f'## Versuche\n\n'
            writer.headers = ['Versuch', 'Ordner', 'PDFs']
            writer.value_matrix = []
            for num in sorted(repo.versuche):
                v = repo.versuche[num]
                writer.value_matrix.append((
                    f'[{num}](../../versuch/{num})',
                    fmt_dirs(repo, v.get('dirs')),
                    fmt_pdfs(repo, v.get('pdfs'))
                ))
            out += writer.dumps()

            g.write(out)

    ## Startseite
    with open(f'build/index.md', 'w') as g:
        out = '# Startseite\n\n'
        # now = datetime.today().strftime('%d.%m.%Y %H:%M:%S')
        # out += f'Zuletzt aktualisiert: {now}\n'
        # out += f'\n\n'

        out += '[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/L4L25K04F)\n\n'
        out += '<script src="https://liberapay.com/NicoWeio/widgets/button.js"></script><noscript><a href="https://liberapay.com/NicoWeio/donate"><img alt="Spenden mittels Liberapay" src="https://liberapay.com/assets/widgets/donate.svg"></a></noscript>\n\n'

        out += f'## Versuche\n\n'
        writer.headers = ['Versuch', '', '# Repos']
        writer.value_matrix = [(v, f'[Übersicht](versuch/{v})', len(versuche_to_repos[v])) for v in sorted(versuche_to_repos.keys())]
        out += writer.dumps()
        out += '\n\n'

        out += f'## Repos\n\n'
        writer.headers = ['Repo', '', 'Letzter Commit', '# Protokolle', '# Protokolle mit PDFs']
        writer.value_matrix = []
        for repo in sorted(repos_to_versuche, key=lambda r: r.full_name.lower()):
            writer.value_matrix.append((
                f'[{repo.full_name}]({repo.html_url})',
                f'[Übersicht](repo/{repo.full_name})',
                f'{repo.last_commit.strftime("%d.%m.%Y %H:%M:%S")}',
                f'{len(repo.versuche)}',
                f'{sum(1 for versuch in repo.versuche.values() if "pdfs" in versuch)}'))
        out += writer.dumps()
        out += '\n\n'

        out += '## Statistiken\n'
        out += f'- **{len(repos_to_versuche)}** Repos\n'
        out += f'- **{len(versuche_to_repos.keys())}** Versuche\n'
        out += f'- **{sum([len(repos) for versuch, repos in versuche_to_repos.items()])}** Protokolle\n'
        out += f'- **{sum(repo.num_pdfs for repo in repos_to_versuche)}** Protokolle mit PDFs\n'
        out += f'- **{sum(0 if getattr(pdf, "is_user_generated", True) else 1 for repo in repos_to_versuche for versuch in repo.versuche.values() for pdf in versuch.get("pdfs", []))}** PDFs von _awesome-ap-pdfs_\n'
        out += f'- **{sum(repo.num_pdfs_total for repo in repos_to_versuche)}** PDFs insgesamt\n'
        out += '\n'

        # Die "Zuletzt aktualisiert"-Zeit wird dynamisch geladen, um im gh-pages-Branch leere Commits zu vermeiden.
        with open('static/last_modified.html') as f:
            out += f.read()

        g.write(out)

        debug('MD files written successfully')
