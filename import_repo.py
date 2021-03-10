import re

def getDirsOfInterest(contents):
    return [dir for dir in contents if getVersuchNummer(dir.name) and dir.type == 'dir']

def getLastCommit(repo):
    branches = list(repo.get_branches())
    dates = [b.commit.commit.author.date for b in branches]
    return sorted(dates)[-1]

def getVersuchNummer(dirname):
    s = re.search(r'[VD]?[._]?(\d{3})', dirname, re.IGNORECASE)
    return int(s.group(1)) if s else None

def import_repo(source, gh):
    # TODO: nicht mutaten, sondern neues Objekt erstellen
    print(f"+++ {source['name']}: ", end='')
    repo = gh.get_repo(source['name'])
    contents = repo.get_contents(source.get('subdirectory', ''))
    dirsOfInterest = getDirsOfInterest(contents)

    versuchNummern = set([getVersuchNummer(d.name) for d in dirsOfInterest])
    versuchNummern.discard(None)

    source['contributors'] = list(repo.get_contributors())
    source['lastCommit'] = getLastCommit(repo)
    source['versuchNummern'] = versuchNummern

    print(f'{len(versuchNummern)} Versuche erkannt')

    return source
