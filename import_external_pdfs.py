import os
from pathlib import Path
import subprocess
from urllib.parse import quote

from console import *
from file import File
from repo import Repo


def add_aap_pdfs(repos, gh):
    console.rule('*** NicoWeio/awesome-ap-pdfs ***')
    aap_repo = Repo({'name': 'NicoWeio/awesome-ap-pdfs'}, gh)
    aap_repo.update_repo_mirror()
    aap_repo.branch = 'main'  # TODO unsauber; siehe auch import_repo.py

    for repo in repos:
        repo_dir = aap_repo.cwd_path / repo.full_name.replace('/', '∕')
        # überspringen, falls aweseome-ap-pdfs zu diesem Repo keine PDFs bereitstellt
        if not repo_dir.exists():
            continue

        versuche_dirs = [f for f in repo_dir.iterdir() if f.is_dir()]
        for versuch_dir in versuche_dirs:
            versuch = int(versuch_dir.stem)  # TODO: unsichere Annahme über die Ordnerstruktur von awesome-ap-pdfs
            paths = [Path(f) for f in versuch_dir.iterdir() if f.suffix == '.pdf']
            files = [File(path, aap_repo, is_user_generated=False) for path in paths]
            if versuch in repo.versuche:
                repo.versuche[versuch].setdefault('pdfs', []).extend(files)
            else:
                warn(f'Versuch {versuch} existiert nicht in {repo.full_name}, aber in awesome-ap-pdfs.')

    return repos
