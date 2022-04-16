from ...config import CONFIG


def isSingleComment(line):
    if not line:
        return False
    return line.lstrip().startswith('#')


def isNonSingleComment(line):
    return all([
        '#' in line,
        ('"' not in line.rsplit('#', 1)[-1]),
        ("'" not in line.rsplit('#', 1)[-1]),
        not isSingleComment(line),
    ])


def isComment(line):
    return isSingleComment(line) or isNonSingleComment(line)


def printContent(content, validComments):
    """Render the content with the valid comments highlighted"""
    def renderBool(b):
        return '✓' if b else '⨯'

    for i, line in enumerate(content):
        isValidComment = any(c['startLine'] <= i <= c['endLine'] for c in validComments)
        print(f'{i:3}|{renderBool(isComment(line))}|{renderBool(isValidComment)}| {line}')


# if a comment is longer, it is considered invalid
maxCommentLineCount = CONFIG \
    .get('code_analysis', {}) \
    .get('max_comment_line_count', 3)


def analyze(rawcontent):
    # NOTE: This also discards consecutive non-single comments
    # ■ Extrahieren der Kommentare:
    content = rawcontent.splitlines()[1:]
    currentCommentLineCount = 0
    validComments = []
    for lineIndex in range(len(content)):
        line = content[lineIndex]
        if isComment(line):
            currentCommentLineCount += 1
        else:
            if 0 < currentCommentLineCount <= maxCommentLineCount:
                startLine = lineIndex - currentCommentLineCount
                endLine = lineIndex - 1
                validComments.append({
                    'content': '\n'.join(content[startLine: endLine + 1]),
                    'startLine': startLine,
                    'endLine': endLine,
                })
            currentCommentLineCount = 0

    # ■ Berechnung der Metriken:
    return {
        'validCommentCount': len(validComments),
    }
