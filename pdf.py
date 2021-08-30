from urllib.parse import quote
from path import CoolPath

class Pdf:
    def __init__(self, path, repo):
        assert isinstance(path, CoolPath)
        self.path = path
        self.repo = repo

        self.download_url = f'https://raw.githubusercontent.com/{repo.full_name}/{repo.branch}/{quote(str(path))}'
        self.name = self.path.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
