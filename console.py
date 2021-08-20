import os
from rich.console import Console


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
