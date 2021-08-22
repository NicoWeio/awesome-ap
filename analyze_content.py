import re
from console import *
import parse_tex


def parse_versuch_nummer(dirname, dirs_to_versuche=None):
    if dirs_to_versuche and dirname in dirs_to_versuche:
        return dirs_to_versuche[dirname]
    if not dirname:
        return None

    # Die Ultraschall-Versuche heißen auch US1 etc.
    # Der Einheitlichkeit halber wird aber ihre *Nummer*, also z.B. 901, verwendet.
    s = re.search(r'US[._\s\-0]*(\d)(?!\d)', dirname, re.IGNORECASE)
    if s:
        return 900 + int(s.group(1))

    matches = re.finditer(r'(?<!\d)[VD]?[._\s\-]*(\d{2,3})(?!\d)', dirname, re.IGNORECASE)
    matches = list(int(match.group(1)) for match in matches)
    if matches:
        if set(matches) == set([501, 502]):  # Doppelversuch
            return 501
        if len(matches) > 1:
            warn(f'multiple matches: {matches}, using the last one')
        return matches[-1]


def find_from_candidates(candidates, analyzer):
    # Analyse für jeden Kandidaten laufen lassen
    results = list(map(analyzer, candidates))
    # `None`-Werte entfernen
    results = [r for r in results if r is not None]
    # abbrechen, falls keine gültigen Werte verbleiben
    if not results:
        return None
    # den häufigsten Wert zurückgeben
    most_common = max(set(results), key=results.count)
    return most_common


def find_from_candidates_dict(candidates, analyzer, namer):
    # Analyse für jeden Kandidaten laufen lassen
    results = {namer(candidate): analyzer(candidate) for candidate in candidates}
    # `None`-Werte entfernen
    results = {k: v for k, v in results.items() if v is not None}
    result_values = list(results.values())
    # abbrechen, falls keine gültigen Werte verbleiben
    if not any(result_values):
        return None, []
    # den häufigsten Wert zurückgeben
    most_common = max(set(result_values), key=result_values.count)
    keys = [k for k, v in results.items() if v == most_common]
    return most_common, keys


def extract_versuch(file):
    try:
        with open(file, 'r') as f:
            content = f.read()
        data = parse_tex.parse(content)
        return parse_versuch_nummer(data.get('subject')) or parse_versuch_nummer(data.get('title'))
    except UnicodeDecodeError:
        pass
