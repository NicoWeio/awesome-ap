from datetime import datetime
from dotenv import load_dotenv
import github
import re
from rich import print
import subprocess
import os.path
from pathlib import Path

from pdf import Pdf
from analyze_content import parse_versuch_nummer, find_from_candidates, extract_title, extract_versuch

load_dotenv()
REPOS_BASE_PATH = Path(os.getenv('REPOS_BASE_PATH'))
REPOS_BASE_PATH.mkdir(exist_ok=True)

def get_versuch_nummer_advanced(dir, dirs_to_versuche):
    ##TEST
    # main_tex_files = list(dir.rglob('main.tex'))
    # title = find_from_candidates(main_tex_files, extract_title)
    # print(f"{title=}")
    ##TEST

    basic_result = parse_versuch_nummer(dir.name, dirs_to_versuche)
    if basic_result:
        return basic_result
    main_tex_files = list(dir.rglob('main.tex'))
    num = find_from_candidates(main_tex_files, extract_versuch)
    if main_tex_files and not num:
        print(f'cannot resolve versuch using {main_tex_files}')
    return num

def printable_files(files):
    # return ', '.join([f'[link={f.html_url}]{f.name}[/link]' for f in files])
    return ', '.join([f'{f.name}' for f in files])

def find_pdfs(base_dir, num):
    # print(f"{base_dir=}")
    try:
        pdf_files_in_base = base_dir.glob('*.pdf')
    except github.UnknownObjectException as e: # file not found
        # print(f'[yellow]Not found: {base_dir=}, {ref=}[/yellow]')
        return
    RE_VALID_NAMES = rf'(abgabe|korrektur|main|protokoll|[VD]?[._\s]*{num})(.*)\.pdf'
    # RE_INVALID_NAMES = rf'(graph|plot)(.*)\.pdf'
    pdf_matches = [f for f in pdf_files_in_base if re.search(RE_VALID_NAMES, f.name, re.IGNORECASE)]
    # print("pdf_files_in_base:", printable_files(pdf_files_in_base))
    # print("pdf_matches:", printable_files(pdf_matches))
    if pdf_matches:
        return pdf_matches
    else:
        VALID_SUBDIR_NAMES = ['build', 'latex-template']
        subdirs = [c for c in base_dir.iterdir() if c.is_dir() and c.name in VALID_SUBDIR_NAMES]
        for subdir in subdirs:
            # print("Recursing into", subdir)
            result = find_pdfs(subdir, num)
            if result:
                return result

def import_repo(source, gh, refresh=True):
    print(f"→ [link={source.html_url}]{source.name}[/link]")
    cwd_path = REPOS_BASE_PATH / source.name.replace('/', '∕')

    def run_command(command, cwd=cwd_path):
        print(f'[blue]$ {" ".join(map(str, command))}[/blue]')
        subprocess.run(command, cwd=cwd) # raises subprocess.CalledProcessError ✓

    if not cwd_path.exists():
        print("Does not exist – cloning…")
        # lege einen „shallow clone“ an, um Speicherplatz zu sparen
        run_command(["git", "clone"] + (["--branch", source.branch] if source.branch else []) + ["--depth", "1", "https://github.com/" + source.name, cwd_path], cwd=None)
        # ↓ https://stackoverflow.com/a/34396983/6371758
        # run_command(["git", "-c", 'core.askPass=""', "clone", "--depth", "1", "https://github.com/" + source.name, cwd_path])
    elif not refresh:
        print("Exists – NOT pulling, because refresh=False was passed")
    else:
        print("Exists – pulling…")
        run_command(["git", "pull"])
        if source.branch:
            # TODO: Viele edge cases wegen des Cachings!
            # Z.B wird nicht zurückgewechselt, wenn zuvor ein branch angegeben war und jetzt nicht mehr…
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
            print(f"[green]PDFs in \"{source.pdfs['directory']}\"[/green]")
            pdf_candidate_files = (cwd_path / source.pdfs['directory']).rglob('*.pdf')
            pdf_candidates = list(Pdf(path.relative_to(cwd_path), source) for path in pdf_candidate_files)
            print(f"{pdf_candidates=}")

            for pdf in pdf_candidates:
                num = parse_versuch_nummer(pdf.name, source.dirs_to_versuche)
                if not num:
                    continue
                elif num in versuche and 'pdfs' in versuche[num]:
                    versuche[num]['pdfs'].append(pdf)
                else:
                    versuche.setdefault(num, {})['pdfs'] = [pdf]

        elif source.pdfs.get('in_source_dir'):
            print("[green]PDFs in source dir[/green]")
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

    print('Erkannte Versuche:', sorted(list(versuche.keys())))
    print(
        f'{len(source.versuche)} Versuche erkannt;',
        f'{source.num_dirs} Ordner,',
        f'{source.num_pdfs} Versuche mit PDFs,',
        f'{source.num_pdfs_total} PDFs insgesamt',
        )

    return source
