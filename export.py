import yaml
from console import *


def generate_yaml(repos_to_versuche):
    data = list(map(serialize_repo, repos_to_versuche))

    with open('build/data.yml', 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
    debug('YAML file written successfully')


def serialize_repo(repo):
    return {a: getattr(repo, a) for a in ['branch', 'last_commit', 'full_name']} | \
        {
        'contributors': [{a: getattr(contributor, a) for a in ['html_url', 'login']} for contributor in repo.contributors],
        'protokolle': {versuch: serialize_protokoll(protokoll) for versuch, protokoll in repo.versuche.items()},
    }


def serialize_protokoll(protokoll):
    return {
        'dirs': sorted(map(str, protokoll.get('dirs', []))),
        'pdfs': sorted(str(pdf.path) for pdf in protokoll.get('pdfs', [])),
    }
