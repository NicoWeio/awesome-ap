class RepoConfig:
    subdirs: list[str]

    def __init__(self, data):
        # SOLL-Branch
        self.branch = data.get('branch')
        # manuelle Zuordnung von Versuchen zu Ordnern; so können auch Ordner ignoriert werden
        self.dirs_to_versuche = data.get('dirs_to_versuche')
        # Optionen zum Parsing; so kann z.B. das Erkennen aus Ordnernamen deaktiviert werden
        self.parsing = data.get('parsing', {})

        self.pdfs = data.get('pdfs')
        if self.pdfs:
            directories = self.pdfs.get('directory', [])
            if isinstance(directories, str):
                directories = [directories]
            self.pdfs['directories'] = directories

        # Ordner, in denen nach Protokollen gesucht werden soll; kann auch '.' sein
        self.subdirs = data.get('subdirectory', ['.'])
        if isinstance(self.subdirs, str):
            self.subdirs = [self.subdirs]
