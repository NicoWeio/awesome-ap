import os
from rich.console import Console
from rich.progress import track as _track

GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS', 'False').lower() == 'true'


def should_force_terminal():
    return True if any(os.getenv(key) for key in ['GITHUB_ACTIONS', 'FORCE_COLOR', 'PY_COLORS']) else None


console = Console(force_terminal=True, width=80 * 2) if should_force_terminal() else Console()


def makeLogFn(style):
    def logFn(*args, **kwargs):
        return console.print(*args, **kwargs, style=style)
    return logFn


debug = makeLogFn('bright_black')
info = makeLogFn('green')
warn = makeLogFn('yellow')
error = makeLogFn('red bold')


def track_wrapper(iterable, **kwargs):
    kwargs.setdefault('transient', True)
    kwargs.setdefault('console', console)
    return _track(iterable, **kwargs)


# GitHub Actions rendert die Progress-Bars nicht richtig, daher werden sie dort deaktiviert.
track = (lambda iterable, **kwargs: iterable) if GITHUB_ACTIONS else track_wrapper
