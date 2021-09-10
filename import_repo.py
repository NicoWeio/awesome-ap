from datetime import datetime
from dotenv import load_dotenv
import github
import re
import subprocess
import os.path
from pathlib import Path

from console import *
from path import CoolPath
from pdf import Pdf
from analyze_content import parse_versuch_nummer, find_from_candidates_dict, extract_versuch
from misc import get_command_runner

load_dotenv()
REPOS_BASE_PATH = Path(os.getenv('REPOS_BASE_PATH'))
REPOS_BASE_PATH.mkdir(exist_ok=True)


def is_dir_ignored(dir, dirs_to_versuche):
    return (dirs_to_versuche or {}).get(dir.name, None) is False


def get_versuch_nummer_from_content(dir):
    main_tex_files = set(dir.full_path.glob('*.tex')) | set(dir.full_path.rglob('main.tex'))
    if len(main_tex_files) > 10:
        warn(f'Skipping detection of "{dir}" – too many ({len(main_tex_files)}) candidates')
        return None, []
    return find_from_candidates_dict(main_tex_files, extract_versuch, lambda file: str(file))


def get_versuch_nummer_advanced(dir, dirs_to_versuche, parsing_options):
    if is_dir_ignored(dir, dirs_to_versuche):
        info(f'"{dir}" is ignored')
        return None

    dir_result, dir_keys = get_versuch_nummer_from_content(dir)

    results = [  # absteigend nach Priorität sortiert ↓
        (dirs_to_versuche or {}).get(dir.name),  # explizit angegeben
        dir_result if parsing_options.get('contents', True) else None,  # Datei-Inhalte
        parse_versuch_nummer(dir.name) if parsing_options.get('dirname', True) else None,  # Dateipfad
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
        debug(f'Cannot resolve (at all): "{dir}"')


def printable_files(files):
    # return ', '.join([f'[link={f.html_url}]{f.name}[/link]' for f in files])
    return ', '.join([f'{f.name}' for f in files])


def find_pdfs(base_dir, num):
    pdf_files_in_base = base_dir.glob('*.pdf')
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

    source.update_repo_mirror()

    run_command = get_command_runner(cwd_path)

    source.last_commit = datetime.utcfromtimestamp(int(run_command(["git", "log", "-1", "--format=%at"], capture_output=True).stdout))

    # Unsauber: Ursprünglich ist `branch` nur angegeben, wenn es sich nicht um den default branch handelt.
    # Hiermit stellen wir sicher, dass `branch` immer korrekt gesetzt ist, weil wir ihn zwingend benötigen.
    source.branch = run_command(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()

    dir_candidates = []
    explicit_subdirs = list(cwd_path / subdir for subdir in source.subdirs)
    for subdir in explicit_subdirs:
        dir_candidates.extend([CoolPath(f, cwd=cwd_path) for f in subdir.iterdir() if f.is_dir()])

    versuche = dict()
    for dir in dir_candidates:
        if dir in explicit_subdirs:
            info(f'skipping explicit subdir "{dir}"')
            continue
        num = get_versuch_nummer_advanced(dir, source.dirs_to_versuche, source.parsing)
        if not num:
            continue
        elif num in versuche:
            versuche[num]['dirs'].append(dir)
        else:
            versuche.setdefault(num, {})['dirs'] = [dir]

    if source.pdfs:
        for pdf_dir in source.pdfs['directories']:
            info(f"PDFs in \"{pdf_dir}\"")
            pdf_candidate_files = (cwd_path / pdf_dir).rglob('*.pdf')
            pdf_candidates = list(Pdf(CoolPath(path, cwd=cwd_path), source) for path in pdf_candidate_files)
            debug(f"{pdf_candidates=}")

            for pdf in pdf_candidates:
                num = parse_versuch_nummer(pdf.name, source.dirs_to_versuche)
                if not num:
                    continue
                elif num in versuche and 'pdfs' in versuche[num]:
                    versuche[num]['pdfs'].append(pdf)
                else:
                    versuche.setdefault(num, {})['pdfs'] = [pdf]

        if source.pdfs.get('in_source_dir'):
            info("PDFs in source dir")
            for num, v in versuche.items():
                for dir in v.get('dirs', []):
                    pdfs = find_pdfs(dir.full_path, num)
                    pdfs = list(Pdf(CoolPath(path, cwd=cwd_path), source) for path in pdfs) if pdfs else None
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
