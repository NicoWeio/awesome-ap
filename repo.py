from config import REPOS_BASE_PATH
from console import *
from datetime import datetime
import github
from misc import get_command_runner
from pathlib import Path
from repo_config import RepoConfig
from subprocess import CalledProcessError


class Repo:
    def __init__(self, data, gh):
        # Die Konfiguration aus der YAML-Datei wird in eine RepoConfig-Instanz ausgelagert.
        self.config = RepoConfig(data)
        # voller Name des Repos in der Form <login>/<name>
        self.full_name = data.get('name')
        # Login des Besitzers und Name des Repos
        self.login, self.name = self.full_name.split('/')
        # Pfad zum Repo im lokalen Cache; muss hier noch nicht existieren
        self.cwd_path = REPOS_BASE_PATH / self.full_name.replace('/', '∕')

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

    def __repr__(self):
        return f'<Repo "{self.full_name}">'

    def update_repo_mirror(self, refresh=True):
        run_command = get_command_runner(self.cwd_path)

        if not self.cwd_path.exists():
            debug("Does not exist – cloning…")
            # lege einen „shallow clone“ an, um Speicherplatz zu sparen
            run_command(["git", "clone"] + (["--branch", self.config.branch] if self.config.branch else []) +
                        ["--depth", "1", "https://github.com/" + self.full_name, self.cwd_path], cwd=None)
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

            if self.config.branch:
                # TODO: Viele edge cases wegen des Cachings!
                run_command(["git", "remote", "set-branches", "origin", self.config.branch])
                run_command(["git", "fetch"])
                run_command(["git", "switch", "-f", self.config.branch])

        # self.branch gibt den Ist-Branch an, self.config.branch den Soll-Branch
        self.branch = run_command(['git', 'branch', '--show-current'],
                                  capture_output=True, silent=True, text=True).stdout.strip()

        last_commit_timestamp = int(run_command(
            ["git", "log", "-1", "--format=%at"],
            capture_output=True, silent=True).stdout)
        self.last_commit = datetime.utcfromtimestamp(last_commit_timestamp)
