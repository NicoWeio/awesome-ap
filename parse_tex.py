from pylatexenc.latexwalker import *
from pylatexenc.macrospec import MacroSpec, MacroStandardArgsParser, LatexContextDb
from rich import print

# Der LatexWalker muss wissen, dass `\subject` genau ein Argument bekommt.
latex_context = get_default_latex_context_db()
macros = [MacroSpec('subject', args_parser=MacroStandardArgsParser(argspec='{'))]
latex_context.add_context_category('foo', macros=macros)


def parse(content):
    w = LatexWalker(content, latex_context=latex_context)
    nodelist, pos, len_ = w.get_latex_nodes(pos=0)
    return parse_rec(nodelist)


def parse_rec(nodelist):
    data = {}
    for node in nodelist:
        if node.isNodeType(LatexEnvironmentNode):
            data.update(parse_rec(node.nodelist))
        if node.isNodeType(LatexMacroNode):
            if node.macroname in ['date', 'input', 'subject', 'title']:
                data.update({node.macroname: parse_macro_content(node)})
    return data


def parse_macro_content(macro):
    try:
        parsed_macro_args = macro.nodeargd
        argnlist = parsed_macro_args.argnlist
        assert len(argnlist) == 1
        nodelist = argnlist[0].nodelist
        assert len(nodelist) == 1
        assert nodelist[0].isNodeType(LatexCharsNode)
        chars = nodelist[0].chars
        return chars
    except:
        pass
