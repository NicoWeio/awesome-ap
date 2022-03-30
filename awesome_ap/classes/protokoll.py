from .file import File
from .repo import Repo
from dataclasses import dataclass


@dataclass(order=True)
class Protokoll:
    dirs: list[File]
    pdfs: list[File]
    repo: Repo
    versuch: int

    def __repr__(self):
        return f'<Protokoll {self.repo.full_name} # {self.versuch}>'
