from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from .repo import Repo


@dataclass(frozen=True, order=True)
class File:
    path: Path
    repo: Repo
    is_user_generated: bool = True  # für awesome-ap-pdfs

    @property
    def name(self):
        return self.path.name

    @property
    def relative_path(self):
        """Gibt den Pfad relativ zum Wurzelordner des Repos zurück."""
        return self.path.relative_to(self.repo.cwd_path)

    @property
    def download_url(self):
        return f'https://raw.githubusercontent.com/{self.repo.full_name}/{self.repo.branch}/{quote(str(self.relative_path))}'

    @property
    def view_url(self):
        if self.path.is_dir():
            return f'{self.repo.html_url}/tree/{self.repo.branch}/{quote(str(self.relative_path))}'
        else:
            if self.path.suffix == '.pdf':
                return f'https://docs.google.com/viewer?url={self.download_url}'
            else:
                return self.download_url

    def __repr__(self):
        return f'<File "{self.name}">'
