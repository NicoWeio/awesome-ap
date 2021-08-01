import github
import re
from rich import print

def getLastCommit(repo):
    branches = list(repo.get_branches())
    dates = [b.commit.commit.author.date for b in branches]
    return sorted(dates)[-1]

def parseVersuchNummer(dirname, dirs_to_versuche=None):
    if dirname in (dirs_to_versuche or []):
        return dirs_to_versuche[dirname]
    if not dirname:
        return None

    # Die Ultraschall-Versuche heißen auch US1 etc.
    # Der Einheitlichkeit halber wird aber ihre *Nummer*, also z.B. 901 verwendet.
    s = re.search(r'US[._\s]*(\d)(?!\d)', dirname, re.IGNORECASE)
    if s:
        return 900 + int(s.group(1))

    s = re.search(r'(?<!\d)[VD]?[._\s]*(\d{3})(?!\d)', dirname, re.IGNORECASE)
    if s:
        return int(s.group(1))

def getVersuchNummerAdvanced(dir, dirs_to_versuche, ref=None):
    print(f"{dir=}")
    basic_result = parseVersuchNummer(dir.name, dirs_to_versuche)
    if basic_result:
        # return basic_result
        pass
    try:
        main_tex_files = list(dir.rglob('main.tex'))
        print(f"{ main_tex_files=}")
        assert len(main_tex_files) == 1
        with open(main_tex_files[0], 'r') as f:
            main_tex_content = f.read()
        search_result = re.search(r'\\subject{(.*)}', main_tex_content)
        raw_num = search_result.group(1).strip() if search_result else None
        num = parseVersuchNummer(raw_num)
        if not num:
            print(f'cannot resolve "{raw_num}"')
        return num
    except AssertionError:
        pass

def printable_files(files):
    return ', '.join([f'[link={f.html_url}]{f.name}[/link]' for f in files])

def find_pdfs(base_dir, num, repo, ref=None):
    try:
        contents = repo.get_contents(base_dir, ref=ref)
    except github.UnknownObjectException as e: # file not found
        print(f'[yellow]Not found: {base_dir=}, {ref=}[/yellow]')
        return
    pdf_files_in_base = [c for c in contents if c.type == 'file' and c.name.endswith('.pdf')]
    RE_VALID_NAMES = rf'(abgabe|korrektur|main|protokoll|[VD]?[._\s]*{num})(.*)\.pdf'
    # RE_INVALID_NAMES = rf'(graph|plot)(.*)\.pdf'
    pdf_matches = [f for f in pdf_files_in_base if re.search(RE_VALID_NAMES, f.name, re.IGNORECASE)]
    print("pdf_files_in_base:", printable_files(pdf_files_in_base))
    print("pdf_matches:", printable_files(pdf_matches))
    if pdf_matches:
        return pdf_matches
    else:
        VALID_SUBDIR_NAMES = ['build', 'latex-template']
        subdirs = [c for c in contents if c.type == 'dir' and c.name in VALID_SUBDIR_NAMES]
        for subdir in subdirs:
            print("Recursing into", subdir.path)
            result = find_pdfs(subdir.path, num, repo, ref=ref)
            if result:
                return result

def import_repo(source, gh):
    import subprocess
    import os.path
    from pathlib import Path
    print("→ ", source['name'])
    gh_repo = gh.get_repo(source['name'])
    print(f"+++ [link={gh_repo.html_url}]{source['name']}[/link]: ")

    # TODO: https://stackoverflow.com/a/34396983/6371758
    # -c core.askPass=""
    cwd = source['name'].replace('/', '∕')
    cwd_path = Path(cwd)
    if not os.path.exists(cwd):
        print("Does not exist – cloning…")
        subprocess.call(["git", "clone", "--depth", "1", "https://github.com/" + source['name'], cwd])
    else:
        print("Exists – pulling…")
        subprocess.call(["git", "pull"], cwd=cwd)


    subdirs = source.get('subdirectory', '')
    if isinstance(subdirs, str):
        subdirs = [subdirs]
    dir_candidates = []
    for subdir in subdirs:
        dir_candidates.extend([f.relative_to(cwd_path) for f in cwd_path.iterdir() if f.is_dir()])
    print(f"{dir_candidates=}")

    versuche = dict()
    for dir in dir_candidates:
        num = getVersuchNummerAdvanced(cwd_path / dir, source.get('dirs_to_versuche'))
        if not num:
            continue
        elif num in versuche:
            versuche[num]['dirs'].append(dir)
        else:
            versuche.setdefault(num, {})['dirs'] = [dir]

    if 'pdfs' in source:
        if 'directory' in source['pdfs']:
            print(f"[green]PDFs in \"{source['pdfs']['directory']}\"[/green]")
            pdf_contents = repo.get_contents(source['pdfs']['directory'], ref=ref)
            pdf_candidates = [c for c in pdf_contents if c.type == 'file' and c.name.endswith('.pdf')]
            print("pdf_candidates:", printable_files(pdf_candidates))

            for pdf in pdf_candidates:
                num = parseVersuchNummer(pdf.name, source.get('dirs_to_versuche'))
                if not num:
                    continue
                elif num in versuche and 'pdfs' in versuche[num]:
                    versuche[num]['pdfs'].append(pdf)
                else:
                    versuche.setdefault(num, {})['pdfs'] = [pdf]

        elif source['pdfs'].get('in_source_dir'):
            print("[green]PDFs in source dir[/green]")
            for num, v in versuche.items():
                print("Checking", num)
                for dir in v['dirs']:
                    pdfs = find_pdfs(dir.path, num, repo, ref=ref)
                    if not pdfs:
                        continue
                    elif num in versuche and 'pdfs' in versuche[num]:
                        versuche[num]['pdfs'].extend(pdfs)
                    else:
                        versuche.setdefault(num, {})['pdfs'] = pdfs

    source['contributors'] = list(gh_repo.get_contributors())
    source['lastCommit'] = getLastCommit(gh_repo)
    source['repo'] = gh_repo
    source['versuche'] = versuche

    print(
        f'{len(versuche)} Versuche erkannt;',
        f'{sum(1 for v in versuche.values() if "dirs" in v)} Ordner,',
        f'{sum(1 for v in versuche.values() if "pdfs" in v)} PDFs',
        )
    return source
