import github
from rich import print


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

        try:
            gh_repo = gh.get_repo(self.name)
            self.contributors = list(gh_repo.get_contributors())
            self.html_url = gh_repo.html_url
        except github.UnknownObjectException:
            print(f"[yellow]Not found: {self.name}[/yellow]")
            raise

    def __str__(self):
        return self.name
