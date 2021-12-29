from console import *
from parse_tex_author import parse_macro_author
from pylatexenc.latexwalker import *
from pylatexenc.macrospec import MacroSpec, MacroStandardArgsParser, LatexContextDb

# Der LatexWalker muss wissen, dass `\subject` genau ein Argument bekommt.
latex_context = get_default_latex_context_db()
macros = [
    MacroSpec('subject', args_parser=MacroStandardArgsParser(argspec='{')),
    MacroSpec('href', args_parser=MacroStandardArgsParser(argspec='{{')),
]
latex_context.add_context_category('foo', macros=macros)


def parse_rec(nodelist) -> dict:
    """
    Sucht rekursiv nach Makros von Interesse und gibt diese zurück.
    Es wird davon ausgegangen, dass jedes Makro nur einmal vorkommt; ansonsten wird nur das letzte zurückgegeben.
    """

    data = {}
    for node in nodelist:
        if node.isNodeType(LatexEnvironmentNode):
            data.update(parse_rec(node.nodelist))  # Rekursion ✨
        if node.isNodeType(LatexMacroNode):
            if node.macroname in PARSER_MAP:
                data.update({node.macroname: PARSER_MAP[node.macroname](node)})
    return data


def parse_macro_content(macro: LatexMacroNode):
    """Versucht, den Text-Inhalt eines Makros zu lesen."""
    try:
        parsed_macro_args = macro.nodeargd
        argnlist = parsed_macro_args.argnlist
        assert len(argnlist) == 1
        nodelist = argnlist[0].nodelist
        assert len(nodelist) == 1
        assert nodelist[0].isNodeType(LatexCharsNode)
        chars = nodelist[0].chars
        return chars
    except Exception as e:
        # info(f'Fehler beim Parsen eines `{macro.macroname}`-Makros: {e}', 'Inhalt:', macro.latex_verbatim())
        pass


# jedem Makro wird ein Parser zugeordnet:
PARSER_MAP = {
    'author': parse_macro_author,
    'subject': parse_macro_content,
    'title': parse_macro_content,
    # TODO: date, input
}


def parse(content: str) -> dict:
    # Falls kein Makro in content vorkommt, kann direkt {} zurückgegeben werden.
    # Das gibt eine enorme Zeitersparnis!
    if not any(f'\\{macro}' in content for macro in PARSER_MAP.keys()):
        return {}
    w = LatexWalker(content, latex_context=latex_context)
    nodelist, pos, len_ = w.get_latex_nodes(pos=0)
    return parse_rec(nodelist)
