from ..analyze.analyze_content import analyze_file, parse_versuch_nummer, find_from_candidates
from ..config import REPOS_BASE_PATH
from ..console import *
from ..classes.file import File
from ..classes.path import CoolPath
from ..classes.protokoll import Protokoll
from ..misc import get_command_runner
import github
import re
import subprocess


def is_dir_ignored(dir, dirs_to_versuche):
    return (dirs_to_versuche or {}).get(dir.name, None) is False


def analyze_dir(dir):
    tex_files = set(dir.full_path.glob('*.tex')) | set(dir.full_path.rglob('main.tex'))
    if len(tex_files) > 10:
        warn(f'Skipping analysis of files in "{dir}" – too many ({len(tex_files)}) candidates')
        return {}
    return analyze_tex_files(tex_files)


def analyze_tex_files(tex_files):
    analysis_list = list(map(analyze_file, tex_files))
    ATTRS = ['date_durchfuehrung', 'versuch_name', 'versuch_nummer']
    return {attr: find_from_candidates(analysis_list, lambda a: a.get(attr), return_single=True) for attr in ATTRS}


def get_authors_from_content(dir):
    # TODO: Alle TeX-Dateien zu durchsuchen ist ineffizient, aber gut genug.
    # Mit der aktuellen Implementierung werden zudem viele Dateien doppelt gelesen, einmal pro dir, einmal hier.
    # Das ließe sich z.B. mit einem „Merker-Dict“ vermeiden.
    main_tex_files = set(dir.rglob('*.tex'))
    result = find_from_candidates(
        track(main_tex_files, description='Extracting authors…'),
        lambda file: analyze_file(file).get('authors', None),
        flatten=True, full_return=True, n=2, n_strict=False)
    if result['excluded']:
        info(f'Einige Autoren wurden ausgelassen: {result["excluded"]}')
    return result['most_common'] or set()


def get_versuch_nummer_advanced(dir, dirs_to_versuche, parsing_options, dir_result):
    if is_dir_ignored(dir, dirs_to_versuche):
        info(f'"{dir}" is ignored')
        return None

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
            # TODO: wieder implementieren? ↓
            # warn(f'{dir_result} was found in {dir_keys}')
        return chosen_result
    else:
        debug(f'Cannot resolve (at all): "{dir}"')


def find_pdfs(base_dir, num):
    pdf_files_in_base = base_dir.glob('*.pdf')
    RE_VALID_NAMES = rf'(abgabe|korrektur|main|protokoll|[VD]?[._\s\-]*{num})(.*)\.pdf'
    # RE_INVALID_NAMES = rf'(graph|plot)(.*)\.pdf'
    pdf_matches = [f for f in pdf_files_in_base if re.search(RE_VALID_NAMES, f.name, re.IGNORECASE)]
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


def import_repo(source, refresh=True):
    source.update_repo_mirror(refresh=refresh)

    run_command = get_command_runner(source.cwd_path)

    dir_candidates = []
    explicit_subdirs = list(source.cwd_path / subdir for subdir in source.config.subdirs)
    for subdir in explicit_subdirs:
        dir_candidates.extend([CoolPath(f, cwd=source.cwd_path)
                              for f in subdir.iterdir() if f.is_dir() and not f.name.startswith('.')])

    protokolle_map = dict()  # {versuch_num: protokoll}

    for dir in dir_candidates:
        if dir in explicit_subdirs:
            info(f'skipping explicit subdir "{dir}"')
            continue

        analysis = analyze_dir(dir)

        num = get_versuch_nummer_advanced(dir, source.config.dirs_to_versuche,
                                          source.config.parsing, analysis.get('versuch_nummer'))
        if not num:
            continue
        else:
            f = File(dir.full_path, source)
            if num in protokolle_map:
                protokolle_map[num].dirs.append(f)
            else:
                protokolle_map[num] = Protokoll(dirs=[f], pdfs=[], repo=source, versuch=num)

    if source.config.pdfs:
        for pdf_dir in source.config.pdfs['directories']:
            info(f"PDFs in \"{pdf_dir}\"")
            pdf_candidate_files = (source.cwd_path / pdf_dir).rglob('*.pdf')
            pdf_candidates = [File(path, source) for path in pdf_candidate_files]
            debug(f"{pdf_candidates=}")

            for pdf in pdf_candidates:
                num = parse_versuch_nummer(pdf.name, source.config.dirs_to_versuche)
                if not num:
                    continue
                else:
                    if num in protokolle_map:
                        protokolle_map[num].pdfs.append(pdf)
                    else:
                        protokolle_map[num] = Protokoll(dirs=[], pdfs=[pdf], repo=source, versuch=num)

        if source.config.pdfs.get('in_source_dir'):
            info("PDFs in source dir")
            for num, p in protokolle_map.items():
                for dir in p.dirs:
                    pdfs = find_pdfs(dir.path, num)
                    pdfs = [File(path, source) for path in pdfs] if pdfs else None
                    if not pdfs:
                        continue
                    else:
                        if num in protokolle_map:
                            protokolle_map[num].pdfs.extend(pdfs)
                        else:
                            protokolle_map[num] = Protokoll(dirs=[], pdfs=pdfs, repo=source, versuch=num)

    source.authors = get_authors_from_content(source.cwd_path)

    source.protokolle = protokolle_map.values()

    # run code analysis (cached property)
    for protokoll in track(source.protokolle, description='Analyzing code…'):
        protokoll.code_analysis

    source.num_dirs = sum(1 for p in source.protokolle if p.dirs)
    source.num_pdfs = sum(1 for p in source.protokolle if p.pdfs)
    source.num_pdfs_total = sum(len(p.pdfs) for p in source.protokolle if p.pdfs)

    info('Erkannte Versuche:', sorted(protokolle_map.keys()))
    info('Erkannte Autoren:', source.authors)
    info(
        f'{len(protokolle_map)} Versuche erkannt;',
        f'{source.num_dirs} Ordner,',
        f'{source.num_pdfs} Versuche mit PDFs,',
        f'{source.num_pdfs_total} PDFs insgesamt',
    )

    return source
