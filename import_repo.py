from datetime import datetime
from dotenv import load_dotenv
import github
import re
import subprocess
import os.path
from pathlib import Path

from console import *
from pdf import Pdf
from analyze_content import parse_versuch_nummer, find_from_candidates_dict, extract_versuch

load_dotenv()
REPOS_BASE_PATH = Path(os.getenv('REPOS_BASE_PATH'))
REPOS_BASE_PATH.mkdir(exist_ok=True)


def get_versuch_nummer_from_content(dir):
    main_tex_files = set(dir.glob('*.tex')) | set(dir.rglob('main.tex'))
    if len(main_tex_files) > 10:
        warn(f'Skipping detection of {dir} – too many ({len(main_tex_files)}) candidates')
        return None, []
    return find_from_candidates_dict(main_tex_files, extract_versuch, lambda file: str(file))


def get_versuch_nummer_advanced(dir, dirs_to_versuche):

    dir_result, dir_keys = get_versuch_nummer_from_content(dir)

    results = [  # absteigend nach Priorität sortiert ↓
        dirs_to_versuche.get(dir.name) if dirs_to_versuche else None,  # explizit angegeben
        dir_result,  # Datei-Inhalte
        parse_versuch_nummer(dir.name),  # Dateipfad
    ]

    valid_results = [result for result in results if result]
    valid_results_unique = set(valid_results)

    if valid_results:
        chosen_result = valid_results[0]
        if len(valid_results_unique) > 1:
            warn(f'ambiguous results: {valid_results}; using {chosen_result}')
            warn(f'{dir_result} was found in {dir_keys}')
        return chosen_result
    else:
        debug(f'Cannot resolve (at all): {dir}')


def printable_files(files):
    # return ', '.join([f'[link={f.html_url}]{f.name}[/link]' for f in files])
    return ', '.join([f'{f.name}' for f in files])


def find_pdfs(base_dir, num):
    try:
        pdf_files_in_base = base_dir.glob('*.pdf')
    except github.UnknownObjectException as e: # file not found
        # print(f'[yellow]Not found: {base_dir=}, {ref=}[/yellow]')
        return
    RE_VALID_NAMES = rf'(abgabe|korrektur|main|protokoll|[VD]?[._\s\-]*{num})(.*)\.pdf'
    # RE_INVALID_NAMES = rf'(graph|plot)(.*)\.pdf'
    pdf_matches = [f for f in pdf_files_in_base if re.search(RE_VALID_NAMES, f.name, re.IGNORECASE)]
    # debug("pdf_files_in_base:", printable_files(pdf_files_in_base))
    # debug("pdf_matches:", printable_files(pdf_matches))
    if pdf_matches:
        return pdf_matches
    else:
        VALID_SUBDIR_NAMES = ['build', 'latex-template']
        subdirs = [c for c in base_dir.iterdir() if c.is_dir() and c.name in VALID_SUBDIR_NAMES]
        for subdir in subdirs:
            # debug("Recursing into", subdir)
            result = find_pdfs(subdir, num)
            if result:
                return result

def import_repo(source, gh, refresh=True):
    console.print()
    console.rule(source.full_name)
    cwd_path = REPOS_BASE_PATH / source.full_name.replace('/', '∕')

    def run_command(command, cwd=cwd_path):
        console.print(f'$ {" ".join(map(str, command))}', style='blue')
        subprocess.run(command, cwd=cwd) # raises subprocess.CalledProcessError ✓

    if not cwd_path.exists():
        debug("Does not exist – cloning…")
        # lege einen „shallow clone“ an, um Speicherplatz zu sparen
        run_command(["git", "clone"] + (["--branch", source.branch] if source.branch else []) + ["--depth", "1", "https://github.com/" + source.full_name, cwd_path], cwd=None)
        # ↓ https://stackoverflow.com/a/34396983/6371758
        # run_command(["git", "-c", 'core.askPass=""', "clone", "--depth", "1", "https://github.com/" + source.full_name, cwd_path])
    elif not refresh:
        debug("Exists – NOT pulling, because refresh=False was passed")
    else:
        debug("Exists – pulling…")
        run_command(["git", "pull"])
        if source.branch:
            # TODO: Viele edge cases wegen des Cachings!
            run_command(["git", "remote", "set-branches", "origin", source.branch])
            run_command(["git", "fetch"])
            run_command(["git", "switch", "-f", source.branch])

    source.last_commit = datetime.utcfromtimestamp(int(subprocess.check_output(["git", "log", "-1", "--format=%at"], cwd=cwd_path)))

    # Unsauber: Ursprünglich ist `branch` nur angegeben, wenn es sich nicht um den default branch handelt.
    # Hiermit stellen wir sicher, dass `branch` immer korrekt gesetzt ist, weil wir ihn zwingend benötigen.
    source.branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=cwd_path).decode().strip()

    dir_candidates = []
    for subdir in source.subdirs:
        dir_candidates.extend([f.relative_to(cwd_path) for f in (cwd_path / subdir).iterdir() if f.is_dir()])

    versuche = dict()
    for dir in dir_candidates:
        num = get_versuch_nummer_advanced(cwd_path / dir, source.dirs_to_versuche)
        if not num:
            continue
        elif num in versuche:
            versuche[num]['dirs'].append(dir)
        else:
            versuche.setdefault(num, {})['dirs'] = [dir]

    if source.pdfs:
        if 'directory' in source.pdfs:
            info(f"PDFs in \"{source.pdfs['directory']}\"")
            pdf_candidate_files = (cwd_path / source.pdfs['directory']).rglob('*.pdf')
            pdf_candidates = list(Pdf(path.relative_to(cwd_path), source) for path in pdf_candidate_files)
            debug(f"{pdf_candidates=}")

            for pdf in pdf_candidates:
                num = parse_versuch_nummer(pdf.name, source.dirs_to_versuche)
                if not num:
                    continue
                elif num in versuche and 'pdfs' in versuche[num]:
                    versuche[num]['pdfs'].append(pdf)
                else:
                    versuche.setdefault(num, {})['pdfs'] = [pdf]

        elif source.pdfs.get('in_source_dir'):
            info("PDFs in source dir")
            for num, v in versuche.items():
                for dir in v['dirs']:
                    pdfs = find_pdfs(cwd_path / dir, num)
                    pdfs = list(Pdf(path.relative_to(cwd_path), source) for path in pdfs) if pdfs else None
                    if not pdfs:
                        continue
                    elif num in versuche and 'pdfs' in versuche[num]:
                        versuche[num]['pdfs'].extend(pdfs)
                    else:
                        versuche.setdefault(num, {})['pdfs'] = pdfs


    source.versuche = versuche
    source.num_dirs = sum(1 for v in versuche.values() if 'dirs' in v)
    source.num_pdfs = sum(1 for v in versuche.values() if 'pdfs' in v)
    source.num_pdfs_total = sum(len(v['pdfs']) for v in versuche.values() if 'pdfs' in v)

    info('Erkannte Versuche:', sorted(list(versuche.keys())))
    info(
        f'{len(source.versuche)} Versuche erkannt;',
        f'{source.num_dirs} Ordner,',
        f'{source.num_pdfs} Versuche mit PDFs,',
        f'{source.num_pdfs_total} PDFs insgesamt',
        )

    return source
