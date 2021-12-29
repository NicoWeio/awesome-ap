from urllib.parse import quote
from dotenv import load_dotenv
import os
import subprocess

from console import *
from path import CoolPath
from repo import Repo


class AapPdf:  # TODO: erben?
    """repräsentiert ein PDF aus dem „awesome-ap-pdfs“-Projekt"""

    def __init__(self, path):
        assert isinstance(path, CoolPath)
        self.download_url = f'https://raw.githubusercontent.com/NicoWeio/awesome-ap-pdfs/main/{quote(str(path))}'
        self.name = path.name
        self.is_user_generated = False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


def add_aap_pdfs(repos, gh):
    console.rule('*** NicoWeio/awesome-ap-pdfs ***')
    aap_repo = Repo({'name': 'NicoWeio/awesome-ap-pdfs'}, gh)
    aap_repo.update_repo_mirror()

    for repo in repos:
        repo_dir = aap_repo.cwd_path / repo.full_name.replace('/', '∕')
        # überspringen, falls aweseome-ap-pdfs zu diesem Repo keine PDFs bereitstellt
        if not repo_dir.exists():
            continue

        versuche_dirs = [f for f in repo_dir.iterdir() if f.is_dir()]
        for versuch_dir in versuche_dirs:
            versuch = int(versuch_dir.stem)  # TODO: unsichere Annahme über die Ordnerstruktur von awesome-ap-pdfs
            filelist = [CoolPath(f, cwd=aap_repo.cwd_path) for f in versuch_dir.iterdir() if f.name.endswith('.pdf')]
            if versuch in repo.versuche:
                repo.versuche[versuch].setdefault('pdfs', []).extend(map(AapPdf, filelist))
            else:
                warn(f'Versuch {versuch} existiert nicht in {repo.full_name}, aber in awesome-ap-pdfs.')

    return repos
