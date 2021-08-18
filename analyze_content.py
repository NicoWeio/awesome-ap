import re


def parse_versuch_nummer(dirname, dirs_to_versuche=None):
    if dirs_to_versuche and dirname in dirs_to_versuche:
        return dirs_to_versuche[dirname]
    if not dirname:
        return None

    # Die Ultraschall-Versuche heißen auch US1 etc.
    # Der Einheitlichkeit halber wird aber ihre *Nummer*, also z.B. 901, verwendet.
    s = re.search(r'US[._\-\s]*(\d)(?!\d)', dirname, re.IGNORECASE)
    if s:
        return 900 + int(s.group(1))

    s = re.search(r'(?<!\d)[VD]?[._\-\s]*(\d{3})(?!\d)', dirname, re.IGNORECASE)
    if s:
        return int(s.group(1))


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


def extract_versuch(file):
    with open(file, 'r') as f:
        content = f.read()
    search_result = re.search(r'\\subject{(.*)}', content)
    raw_num = search_result.group(1).strip() if search_result else None
    return parse_versuch_nummer(raw_num)

def extract_title(file):
    with open(file, 'r') as f:
        content = f.read()
        search_result = re.search(r'\\title{(.*)}', content)
        title = search_result.group(1).strip() if search_result else None
        return title
