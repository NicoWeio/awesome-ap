import os
from pathlib import Path

import pytablewriter

from ..classes.file import File
from ..console import *


def fmt_repo(repo):
    return f'[{repo.full_name}](../repo/{repo.full_name})'


def fmt_files(files):
    if not files:
        return '–'
    return '<br/>'.join(fmt_file(file) for file in sorted(files, key=lambda f: (f.name.lower(), str(f.path).lower())))


def fmt_file(f: File):
    return f"[{f.name}]({f.view_url})" + (r' \*' if not f.is_user_generated else '')


def generate_md(repos_to_versuche, versuche_to_repos, versuche_data, versuche_to_common_files, dry_run=False):
    os.makedirs('build/versuch', exist_ok=True)
    os.makedirs('build/repo', exist_ok=True)
    writer = pytablewriter.MarkdownTableWriter()

    # ■ Versuch → Repos
    for versuch, repos in versuche_to_repos.items():
        versuch_data = versuche_data.get(versuch, {})
        if name := versuch_data.get('name'):
            out = f'# Versuch *{versuch}*: {name}\n\n'
        else:
            out = f'# Versuch *{versuch}*\n\n'

        if notes := versuch_data.get('notes'):
            out += '## Anmerkungen\n' + notes + '\n\n'

        if common_files := versuche_to_common_files.get(versuch):
            common_files_out = '\n'.join(
                f'- [{f.name}]({f.view_url})'
                for f in sorted(common_files, key=lambda f: (f.name.lower(), str(f.path).lower()))
            )
            out += '## Gemeinsame Dateien\n' + common_files_out + '\n\n'

        out += f'## Repos\n\n'

        writer.headers = ['Repo', 'Ordner', 'PDFs']
        writer.value_matrix = [(
            fmt_repo(repo),
            fmt_files(repo.protokolle_map[versuch].dirs),
            fmt_files(repo.protokolle_map[versuch].pdfs),
        ) for repo in sorted(repos, key=lambda r: r.full_name.lower())]
        out += writer.dumps()

        if not dry_run:
            Path(f'build/versuch/{versuch}.md').write_text(out)

    # ■ Repo → Versuche
    for repo in repos_to_versuche:
        os.makedirs(f'build/repo/{repo.login}', exist_ok=True)
        out = f'# [{repo.full_name}]({repo.html_url})\n\n'

        lastCommit = repo.last_commit.strftime('%d.%m.%Y %H:%M:%S')
        out += f'Letzter Commit: {lastCommit}\n\n'

        if repo.authors:
            authors_out = "\n".join(
                f'- {a}'
                for a in sorted(repo.authors, key=lambda a: a.rsplit(' ', 1)[-1].lower())
            )
            out += '## Autoren (Klarnamen)\n' + authors_out + '\n\n'

        if repo.contributors:
            contributors_out = "\n".join(
                f'- [{c.login}]({c.html_url})'
                for c in sorted(repo.contributors, key=lambda c: c.login.lower())
            )
            out += '## Autoren (GitHub)\n' + contributors_out + '\n\n'

        out += f'## Versuche\n\n'
        writer.headers = ['Versuch', 'Ordner', 'PDFs']
        writer.value_matrix = [(
            f'[{num}](../../versuch/{num})',
            fmt_files(v.dirs),
            fmt_files(v.pdfs),
        ) for num, v in sorted(repo.protokolle_map.items())]
        out += writer.dumps()

        if not dry_run:
            Path(f'build/repo/{repo.login}/{repo.name}.md').write_text(out)

    # ■ Startseite
    out = '# Startseite\n\n'

    out += '[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/L4L25K04F)\n\n'
    out += '<script src="https://liberapay.com/NicoWeio/widgets/button.js"></script><noscript><a href="https://liberapay.com/NicoWeio/donate"><img alt="Spenden mittels Liberapay" src="https://liberapay.com/assets/widgets/donate.svg"></a></noscript>\n\n'

    out += f'## Versuche\n\n'
    writer.headers = ['Nr.', 'Name', '', '# Repos']
    writer.value_matrix = [(
        v,
        versuche_data.get(v, {}).get('name') or '–',
        f'[Übersicht](versuch/{v})',
        len(versuche_to_repos[v]),
    ) for v in sorted(versuche_to_repos.keys())]
    out += writer.dumps()
    out += '\n\n'

    out += f'## Repos\n\n'
    writer.headers = ['Repo', '', 'Letzter Commit', '# Protokolle', '# Protokolle mit PDFs']
    writer.value_matrix = [(
        f'[{repo.full_name}]({repo.html_url})',
        f'[Übersicht](repo/{repo.full_name})',
        f'{repo.last_commit.strftime("%d.%m.%Y %H:%M:%S")}',
        f'{len(repo.versuche)}',
        f'{sum(1 for protokoll in repo.protokolle if protokoll.pdfs)}',
    ) for repo in sorted(repos_to_versuche, key=lambda r: r.full_name.lower())]
    out += writer.dumps()
    out += '\n\n'

    out += '## Statistiken\n'
    out += f'- **{len(repos_to_versuche)}** Repos\n'
    out += f'- **{len(versuche_to_repos.keys())}** Versuche\n'
    out += f'- **{sum([len(repos) for versuch, repos in versuche_to_repos.items()])}** Protokolle\n'
    out += f'- **{sum(repo.num_pdfs for repo in repos_to_versuche)}** Protokolle mit PDFs\n'
    out += f'- **{sum((0 if pdf.is_user_generated else 1) for repo in repos_to_versuche for protokoll in repo.protokolle for pdf in protokoll.pdfs)}** PDFs von _awesome-ap-pdfs_\n'
    out += f'- **{sum(repo.num_pdfs_total for repo in repos_to_versuche)}** PDFs insgesamt\n'
    out += '\n'

    # Die "Zuletzt aktualisiert"-Zeit wird dynamisch geladen, um im gh-pages-Branch leere Commits zu vermeiden.
    out += (Path(__file__).parent / 'static' / 'last_modified.html').read_text()

    if not dry_run:
        Path(f'build/index.md').write_text(out)

    if not dry_run:
        debug('MD files written successfully')
