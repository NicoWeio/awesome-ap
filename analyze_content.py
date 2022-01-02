from collections import Counter
from console import *
import parse_tex
import re


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
            warn(f'multiple matches in "{dirname}": {matches}, using the last one')
        return matches[-1]


def find_from_candidates(candidates, analyzer, flatten=False, full_return=False, n=1, n_strict=True, return_single=False):
    """
    Analysiert eine Liste von Kandidaten und gibt die Resultate abhängig von ihrer Häufigkeit zurück.
    :param candidates: Liste von Kandidaten, z.B. Dateipfaden
    :param n_strict: Wenn False, können auch >n Kandidaten zurückgegeben werden, wenn sie ebenso häufig vorkommen wie der n-te.
    """

    # Analyse für jeden Kandidaten laufen lassen
    results = list(map(analyzer, candidates))
    if flatten:
        results = [item for sublist in results if sublist for item in sublist]

    # `None`-Werte entfernen
    results = [r for r in results if r is not None]

    # Häufigkeiten der einzelnen Resultate bestimmen
    # Die Einträge werden sortiert, um konsistente Ergebnisse von `counter.most_common(n)` zu garantieren, wenn n_strict == True ist.
    counter = Counter(sorted(results))

    def lax_most_common():
        last_count = float('inf')
        i = 0
        for item, count in counter.most_common():
            if i >= n and count < last_count:
                break
            yield (item, count)
            i += 1
            last_count = count

    # die `n` häufigsten Werte:
    most_common = set(item for item, count in (counter.most_common(n) if n_strict else lax_most_common()))

    if full_return:
        return {
            'all': results,
            'counter': counter,
            'excluded': set(results) - most_common,
            'most_common': most_common,
        }
    else:
        if return_single:
            assert n == 1
            # den/einen häufigsten Wert zurückgeben, sofern überhaupt einer existiert
            # Auch hier wird zuerst sortiert, um konsistente Ergebnisse zu gewährleisten.
            return next(iter(sorted(most_common)), None)
        else:
            return most_common


def analyze_file(file):
    try:
        with open(file, 'r') as f:
            content = f.read()
        data = parse_tex.parse(content)

        return {
            'authors': data.get('author'),  # sic: Das Node heißt author, nicht authors.
            # 'date_durchfuehrung': data.get('date'),  # TODO: Noch fehlt ein richtiger Parser dafür.
            # 'versuch_name': …, # TODO: siehe anderen Branch
            'versuch_nummer': parse_versuch_nummer(data.get('subject')) or parse_versuch_nummer(data.get('title')),
        }
    except UnicodeDecodeError:
        return {}
