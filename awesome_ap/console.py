import logging
import os

from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.progress import (BarColumn, MofNCompleteColumn, Progress,
                           SpinnerColumn, TimeRemainingColumn)
from rich.progress import track as _track

GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS', 'False').lower() == 'true'


def should_force_terminal():
    return True if any(os.getenv(key) for key in ['GITHUB_ACTIONS', 'FORCE_COLOR', 'PY_COLORS']) else None


console = Console(force_terminal=True, width=80 * 2) if should_force_terminal() else Console()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()],
)
# logging.getLogger('urllib3').setLevel(logging.WARNING)

_job_progress = Progress(
    "{task.description}",
    SpinnerColumn(),
    BarColumn(),
    MofNCompleteColumn(),
    TimeRemainingColumn(),
)


def track(iterable, description="Working...", total=None):
    """
    An alternative to rich.progress.track that allows multiple progress bars to be displayed at once.
    """
    try:
        total = total or len(iterable)
    except TypeError:
        total = None

    my_job = _job_progress.add_task(description, total=total)
    for i in iterable:
        yield i
        _job_progress.update(my_job, advance=1)
    _job_progress.remove_task(my_job)


track_context = Live(_job_progress, refresh_per_second=10)


def status(message):
    """
    A context manager that displays a status message while the context is active.
    """
    class Status:
        def __enter__(self):
            self.job = _job_progress.add_task(description=message, total=0)

        def __exit__(self, exc_type, exc_val, exc_tb):
            _job_progress.remove_task(self.job)

    return Status()


# === ↑ new code | old code ↓ ===


def makeLogFn(fn):
    def logFn(*args, **kwargs):
        one_str = ' '.join(str(arg) for arg in args)
        return fn(one_str, **kwargs)
    return logFn


debug = makeLogFn(logging.debug)
info = makeLogFn(logging.info)
warn = makeLogFn(logging.warning)
error = makeLogFn(logging.error)


def track_wrapper(iterable, **kwargs):
    kwargs.setdefault('transient', True)
    kwargs.setdefault('console', console)
    return _track(iterable, **kwargs)


# GitHub Actions rendert die Progress-Bars nicht richtig, daher werden sie dort deaktiviert.
track = (lambda iterable, **kwargs: iterable) if GITHUB_ACTIONS else track_wrapper
