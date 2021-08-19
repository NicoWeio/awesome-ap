import github
from rich import print


def get_last_commit(repo):
    branches = list(repo.get_branches())
    dates = [b.commit.commit.author.date for b in branches]
    return sorted(dates)[-1]


class Repo:
    def __init__(self, data, gh):
        self.branch = data.get('branch')
        self.dirs_to_versuche = data.get('dirs_to_versuche')
        self.name = data.get('name')
        self.pdfs = data.get('pdfs')

        self.login = self.name.split('/')[0]

        self.subdirs = data.get('subdirectory', '')
        if isinstance(self.subdirs, str):
            self.subdirs = [self.subdirs]

        self.contributors = []  # list(gh_repo.get_contributors())
        # TODO: missing branch ↓
        self.html_url = f'https://github.com/{self.name}'  # gh_repo.html_url

    def __str__(self):
        return self.name
