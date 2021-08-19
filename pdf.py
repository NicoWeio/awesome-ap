from urllib.parse import quote

class Pdf:
    def __init__(self, path, repo):
        self.path = path
        self.repo = repo

        self.download_url = f'https://raw.githubusercontent.com/{repo.name}/{repo.branch}/{quote(str(path))}'
        self.name = self.path.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
