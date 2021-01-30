from github import Github
import json
from dotenv import load_dotenv
import os
import re

load_dotenv()

# funktioniert auch ohne Token
gh = Github(os.getenv('GITHUB_ACCESS_TOKEN'))

with open('sources.json') as f:
  sources = json.load(f)

data = dict()

def getDirsOfInterest(contents):
    # TODO auf einzelne PDFs erweitern
    # TODO various strategies for subdirs etc.
    return [dir for dir in contents if getVersuchNummer(dir.name) and dir.type == 'dir']

def getVersuchNummer(dirname):
    s = re.search(r'V[._]?(\d{3})', dirname)
    return int(s.group(1)) if s else None

def getFilesRec(path):
    list = []
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            list.append(file_content)
    return list

for source in sources:
    print('+++', source['name'])
    repo = gh.get_repo(source['name'])
    contents = repo.get_contents(source.get('subdirectory', ''))
    dirsOfInterest = getDirsOfInterest(contents)

    versuchNummern = [getVersuchNummer(d.name) for d in dirsOfInterest]
    versuchNummern = [i for i in versuchNummern if i] # nicht erkannte Versuchs-Nummern entfernen
    print("Hat Versuche:", versuchNummern)
