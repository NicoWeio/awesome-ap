from pathlib import Path

from radon.raw import analyze
from radon.metrics import mi_visit
from radon.complexity import cc_visit
from radon.cli.tools import iter_filenames

from .code.comments import analyze as custom_analyze

from dataclasses import dataclass


@dataclass
class Result:
    """Holds the result of a single file's analysis."""
    # radon ↓
    lloc: int
    sloc: int
    comments: int
    single_comments: int
    # custom ↓
    comments_of_interest: int


def analyze_dirs(dirs: list[Path]):
    # TODO: Take a look at the Harvester approach – maybe it's better?

    # ipynb files are excluded from the analysis
    files_to_analyze = [f for f in iter_filenames(dirs) if f.endswith('.py')]

    return {filename: analyze_file(filename) for filename in files_to_analyze}


def analyze_file(path: str) -> Result | None:
    source = Path(path).read_text()
    try:
        # https://radon.readthedocs.io/en/latest/intro.html#raw-metrics
        # NOTE: cc_visit and mi_visit could be used in the future
        radon_raw = analyze(source)
        custom_raw = custom_analyze(source)

        return Result(
            # radon ↓
            lloc=radon_raw.lloc,
            sloc=radon_raw.sloc,
            comments=radon_raw.comments,
            single_comments=radon_raw.single_comments,
            # custom ↓
            comments_of_interest=custom_raw['validCommentCount'],
        )

    except SyntaxError:
        # warn(f'Caught a SyntaxError while analyzing {path}')
        return None
