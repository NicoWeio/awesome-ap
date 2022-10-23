import yaml

from ..console import *


def generate_yaml(repos_to_versuche):
    data = list(map(serialize_repo, repos_to_versuche))

    with open('build/data.yml', 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
    debug('YAML file written successfully')


def serialize_repo(repo):
    return {a: getattr(repo, a) for a in ['branch', 'last_commit', 'full_name']} | \
        {
        'authors': sorted(repo.authors),
        'contributors': [
            {a: getattr(contributor, a) for a in ['html_url', 'login']}
            for contributor in sorted(repo.contributors, key=lambda c: c.login)
        ],
        'protokolle': {protokoll.versuch: serialize_protokoll(protokoll) for protokoll in repo.protokolle},
    }


def serialize_protokoll(protokoll):
    return {
        'code_analysis': protokoll.code_analysis,
        'dirs': sorted(str(dir.relative_path) for dir in protokoll.dirs),
        'pdfs': sorted(str(pdf.relative_path) for pdf in protokoll.pdfs if pdf.is_user_generated),
    }
