import github
from console import *
from dotenv import load_dotenv
from misc import get_command_runner
from pathlib import Path
from subprocess import CalledProcessError

load_dotenv()
REPOS_BASE_PATH = Path(os.getenv('REPOS_BASE_PATH'))
REPOS_BASE_PATH.mkdir(exist_ok=True)


class Repo:
    def __init__(self, data, gh):
        self.branch = data.get('branch')
        self.dirs_to_versuche = data.get('dirs_to_versuche')
        self.ignore_dirs = data.get('ignore_dirs', [])
        self.parsing = data.get('parsing', {})
        self.full_name = data.get('name')

        self.login, self.name = self.full_name.split('/')

        self.pdfs = data.get('pdfs')
        if self.pdfs:
            directories = self.pdfs.get('directory', [])
            if isinstance(directories, str):
                directories = [directories]
            self.pdfs['directories'] = directories

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

    def update_repo_mirror(self, refresh=True):
        cwd_path = REPOS_BASE_PATH / self.full_name.replace('/', '∕')
        self.cwd_path = cwd_path
        run_command = get_command_runner(cwd_path)

        if not cwd_path.exists():
            debug("Does not exist – cloning…")
            # lege einen „shallow clone“ an, um Speicherplatz zu sparen
            run_command(["git", "clone"] + (["--branch", self.branch] if self.branch else []) +
                        ["--depth", "1", "https://github.com/" + self.full_name, cwd_path], cwd=None)
            # ↓ https://stackoverflow.com/a/34396983/6371758
            # run_command(["git", "-c", 'core.askPass=""', "clone", "--depth", "1", "https://github.com/" + self.full_name, cwd_path])
        elif not refresh:
            debug("Exists – NOT pulling, because refresh=False was passed")
        else:
            debug("Exists – pulling…")
            try:
                run_command(["git", "pull"])
            except CalledProcessError as e:
                warn("Pull failed. Maybe there are merge conflicts? Trying to reset…")
                run_command(["git", "fetch"])
                run_command(["git", "reset", "--hard", "origin/HEAD"])
            except Exception as e:
                error("Still failed:", e)
                raise

            if self.branch:
                # TODO: Viele edge cases wegen des Cachings!
                run_command(["git", "remote", "set-branches", "origin", self.branch])
                run_command(["git", "fetch"])
                run_command(["git", "switch", "-f", self.branch])
