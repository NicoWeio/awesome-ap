def versuche_to_repos(sources):
    versuche = dict()
    for source in sources:
        for num in source['versuchNummern']:
            versuche.setdefault(num, []).append(source)
    return versuche
