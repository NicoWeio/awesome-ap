from console import *
from pylatexenc.latexwalker import *
from pylatexenc.macrospec import MacroSpec, MacroStandardArgsParser, LatexContextDb
import re

# Der LatexWalker muss wissen, dass `\subject` genau ein Argument bekommt.
latex_context = get_default_latex_context_db()
macros = [MacroSpec('subject', args_parser=MacroStandardArgsParser(argspec='{'))]
# macros += [MacroSpec('author', args_parser=MacroStandardArgsParser(argspec='{'))]
macros += [MacroSpec('href', args_parser=MacroStandardArgsParser(argspec='{{'))]
latex_context.add_context_category('foo', macros=macros)


def parse_href(node):
    """Extrahiert (href, name) aus einem `\href`-Makro."""
    argnlist = node.nodeargd.argnlist
    assert len(argnlist[0].nodelist) == 1

    href_node = argnlist[0].nodelist[0]
    assert href_node.isNodeType(LatexCharsNode)
    name_node = argnlist[1].nodelist[0]
    assert name_node.isNodeType(LatexCharsNode)

    return href_node.chars, name_node.chars


def is_node_interesting(node):
    if node.isNodeType(LatexMacroNode):
        if node.macroname in ['and', r'\\']:
            return False
        if node.macroname == 'href':
            # Enthält das href-Makro nur eine E-Mail-Adresse?
            href, name = parse_href(node)
            return not '@' in href
    if node.isNodeType(LatexCommentNode):
        return False
    return True  # TODO: Bleibt hier überhaupt etwas Interessantes übrig?


def extract_names(name_candidate: str) -> list[str]:
    if not name_candidate:
        return []

    EXCLUSION_LIST = ['AUTOR', '@']
    if any((e in name_candidate) for e in EXCLUSION_LIST):
        return []

    # Ein name_candidate kann mehrere Namen enthalten. Diese werden hier aufgeteilt.
    raw_names = re.split(r'\b(?:and|und)\b', name_candidate)
    # entferne Leerzeichen, Newlines und leere Namen
    names = [name.strip() for name in raw_names if name.strip()]
    return names


def parse_macro_author(macro):
    r"""Extrahiert die Autoren-Namen aus einem `\author`-Makro."""
    try:
        # die Nodes in z.B. `\authors{…}`
        nodes = macro.nodeargd.argnlist[0].nodelist
        # filtere nach Nodes von Interesse
        nodes = list(filter(is_node_interesting, nodes))
        # extrahiere Namens-Kandidaten aus Zeichenketten-Nodes
        name_candidates = [node.chars for node in nodes if node.isNodeType(LatexCharsNode)]
        # extrahiere Namen aus Kandidaten; ein Kandidat kann mehrere Namen enthalten
        extracted_names = [extract_names(nc) for nc in name_candidates]
        # flatten und in ein Set umwandeln
        names = {name for names in extracted_names for name in names}
        return names
    except Exception as e:
        debug("Could not parse content of macro `author`:", e)
        pass
