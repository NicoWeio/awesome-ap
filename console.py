from rich.console import Console
console = Console()


def makeLogFn(style):
    def logFn(*args, **kwargs):
        return console.print(*args, **kwargs, style=style)
    return logFn


debug = makeLogFn('bright_black')
info = makeLogFn('green')
warn = makeLogFn('yellow')
error = makeLogFn('red bold')
