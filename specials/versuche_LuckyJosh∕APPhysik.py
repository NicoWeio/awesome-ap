import github
from dotenv import load_dotenv
import os
import re


def getVersuchNummer(string):
    s = re.search(r'V(\d{3})', string, re.IGNORECASE)
    if s:
        return int(s.group(1))


def analyze(path):
    try:
        main_tex_content = repo.get_contents(path).decoded_content.decode()
        search_result = re.search(r'\\newcommand{\\VNr}{(.*)}', main_tex_content)
        if not search_result:
            return False
        raw_num = search_result.group(1).strip() if search_result else None
        num = getVersuchNummer(raw_num)
        if num:
            print(f'"{versuch_dir.path}": {num}')
            return True  # ein paar API-Calls sparen
        else:
            # print(f'cannot resolve "{raw_num}" from "{path}"')
            return False
    except github.UnknownObjectException:  # file not found
        # print(f'not found: {path}')
        return False


load_dotenv()

# funktioniert auch ohne Token
TOKEN = os.getenv('GITHUB_TOKEN') or os.getenv('INPUT_GITHUB_TOKEN')
gh = github.Github(TOKEN)

repo = gh.get_repo('LuckyJosh/APPhysik')
versuche_dirs = [f for f in repo.get_contents('') if f.type == 'dir']
for versuch_dir in versuche_dirs:
    for relpath in ['Protokoll.tex', 'LaTeX/Preambel.tex', 'Latex/VersuchOrga.tex', 'Latex/VersuchsOrga.tex', 'Latex/VersuchDaten.tex']:
        if analyze(versuch_dir.path + '/' + relpath):
            pass  # ein paar API-Calls sparen
