import github
from console import *


class Repo:
    def __init__(self, data, gh):
        self.branch = data.get('branch')
        self.dirs_to_versuche = data.get('dirs_to_versuche')
        self.ignore_dirs = data.get('ignore_dirs', [])
        self.full_name = data.get('name')
        self.pdfs = data.get('pdfs')

        self.login, self.name = self.full_name.split('/')

        self.subdirs = data.get('subdirectory', '')  # TODO !?
        if isinstance(self.subdirs, str):
            self.subdirs = [self.subdirs]

        try:
            gh_repo = gh.get_repo(self.full_name)
            self.contributors = list(gh_repo.get_contributors())
            self.html_url = gh_repo.html_url
        except github.UnknownObjectException:
            error(f"Not found: {self}")
            raise

        # Platzhalter für Testläufe ohne GitHub-API:
        # self.contributors = []
        # self.html_url = "https://google.com/"

    def __str__(self):
        return self.full_name
