import github
from rich import print

def get_last_commit(repo):
    branches = list(repo.get_branches())
    dates = [b.commit.commit.author.date for b in branches]
    return sorted(dates)[-1]


class Repo:
    def __init__(self, data, gh):
        self.data = data
        self.name = data.get('name')
        self.pdfs = data.get('pdfs')

        self.login = self.name.split("/")[0]

        self.subdirs = self.data.get('subdirectory', '')
        if isinstance(self.subdirs, str):
            self.subdirs = [self.subdirs]

        print(f'Initializing {self.name}…')

        # try:
        #     gh_repo = gh.get_repo(self.name)
        # except github.UnknownObjectException:
        #     print(f"[yellow]Not found: {self.name}[/yellow]")
        #     raise
        self.contributors = [] # list(gh_repo.get_contributors())
        self.html_url = f'https://github.com/{self.name}' # gh_repo.html_url
        self.last_commit = None # get_last_commit(gh_repo)

    def __str__(self):
        return self.name
