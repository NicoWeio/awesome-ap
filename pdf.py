class Pdf:
    def __init__(self, path, repo):
        self.path = path
        self.repo = repo

        self.download_url = str(path)  # TODO
        self.name = self.path.name
