from analyze_content import find_from_candidates
from config import REPOS_BASE_PATH
from console import *
from file import File
from misc import get_command_runner, md5sum, most
import os
from pathlib import Path


def find_common_files(versuche_to_repos, config):
    run_command = get_command_runner(REPOS_BASE_PATH)

    versuche_to_files = {}

    for versuch, repos in track(sorted(versuche_to_repos.items()), description='Suche gemeinsame Dateien…'):
        if len(repos) <= 1:
            continue

        # Wird hier wegen der repo-Liste definiert. Verbesserungswürdig.
        def repo_from_path(path: Path):
            repo_name = path.relative_to(REPOS_BASE_PATH).parts[0].replace('∕', '/')
            return next(repo for repo in repos if repo.full_name == repo_name)

        # die zu `versuch` gehörenden Ordner sämtlicher Repos
        dirs = [dir.path for repo in repos for dir in repo.versuche[versuch].get('dirs', [])]

        # suche nach Duplikaten
        fdupes_result = run_command(['fdupes', '--noempty', '--quiet', '--recurse', *dirs],
                                    capture_output=True, silent=True, text=True)

        if stderr := fdupes_result.stderr.strip():
            raise Exception(f'Fehler beim Aufruf von fdupes:\n{stderr}')

        fdupes_output = fdupes_result.stdout.strip()

        # überspringen, falls keine Duplikate gefunden wurden
        if not fdupes_output:
            continue

        # Jeder Block entspricht einer Datei (also einem Hash).
        blocks = fdupes_output.split('\n\n')
        # Jeder Block enthält eine Liste von Dateien mit identischem Inhalt.
        # Zuerst werden diese als Pfade eingelesen…
        blocks = [[Path(path) for path in block.split('\n')] for block in blocks]
        # …dann zu `File`s umgewandelt.
        blocks = [[File(path, repo_from_path(path)) for path in block] for block in blocks]
        # Offensichtlich müssen alle Blöcke mehrere Dateipfade enthalten, sonst wären es ja keine Duplikate.
        assert all(len(paths) > 1 for paths in blocks)

        def count_block_repos(block: list[Path]):
            """Zählt, wie viele Repos den zum Block gehörigen Dateiinhalt haben."""
            repo_names = [file.repo.full_name for file in block]
            return len(set(repo_names))

        # Innerhalb eines Repos kann ein Dateiinhalt so oft vorkommen, wie sie will, das interessiert uns aber nicht.
        # Darum wird hier geprüft, ob der Dateiinhalt in (mindestens 3) verschiedenen Repos vorkommt.
        blocks = [block for block in blocks if count_block_repos(block) >= 3]

        # Einige Dateien/Blöcke, die in vielen Repos vorkommen, interessieren uns nicht weiter…
        def is_filename_ignored(filename):
            return filename in config.get('ignore', {}).get('filename', []) or \
                any(filename.endswith(suffix) for suffix in config.get('ignore', {}).get('suffix', []))

        # Hier sind wir großzügig und verwerfen Blöcke nur, wenn über 50% der Dateipfade ignoriert sind.
        # So wird verhindert, dass eine Datei fälschlicherweise verworfen wird, weil sie wenige falsch benannt haben.
        blocks = [block for block in blocks if not most(is_filename_ignored(file.name) for file in block)]

        # Neben ignorierten Dateinamen gibt es aber auch ignorierte DateiINHALTE.
        # Wir prüfen, ob ein Repräsentant des Blocks mit einer der Prüfsummen übereinstimmt.
        def is_block_ignored(block):
            return md5sum(block[0].path) in config.get('ignore', {}).get('md5sum', [])

        blocks = [block for block in blocks if not is_block_ignored(block)]

        # Zuletzt wird für jeden Block ein Repräsentant ausgewählt: Der häufigste Dateiname gewinnt.
        def choose_file_from_block(block):
            top_filename = find_from_candidates(block, lambda file: file.name, return_single=True)
            return next(file for file in block if file.name == top_filename)

        chosen_files = [choose_file_from_block(block) for block in blocks]

        if chosen_files:
            versuche_to_files[versuch] = chosen_files

    return versuche_to_files
