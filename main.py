from github import Github
import json
import os

gh = Github()

with open('sources.json') as f:
  sources = json.load(f)

data = dict()

def getDirsOfInterest(contents):
    # TODO various strategies for subdirs etc.
    return [dir for dir in contents if dir.path.startswith('V') and dir.type == 'dir']

def getVersuchNummer(dirname):
    print('-', dirname)
    try:
        if dirname.startswith('V.'):
            num = dirname.split('.')[1].strip()
            assert len(num) == 3
            return int(num)
        if dirname.startswith('V_'):
            num = dirname.split('_')[1].strip()
            assert len(num) == 3
            return int(num)
        elif dirname.startswith('V'):
            assert len(dirname) == 4
            return int(dirname[1:])
    except:
        pass

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
    print(source['name'])
    repo = gh.get_repo(source['name'])
    contents = repo.get_contents(source.get('subdirectory', ''))
    dirsOfInterest = getDirsOfInterest(contents)

    versuchNummern = [getVersuchNummer(d.name) for d in dirsOfInterest]
    versuchNummern = [i for i in versuchNummern if i] # nicht erkannte Versuchs-Nummern entfernen
    print("Hat Versuche:", versuchNummern)
