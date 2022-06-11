from .console import console
import hashlib
import subprocess


def get_command_runner(default_cwd):
    def run_command(command, silent=False, **kwargs):
        print = console.print if not silent else lambda *args, **kwargs: None
        kwargs.setdefault('cwd', default_cwd)
        kwargs.setdefault('check', True)
        if kwargs.get('shell'):
            print(f'$ {command}', style='blue')
        else:
            print(f'$ {" ".join(map(str, command))}', style='blue')
        if kwargs.get('capture_output'):
            print('→ output not shown', style='blue')
        return subprocess.run(command, **kwargs)  # raises subprocess.CalledProcessError ✓
    return run_command


def most(iterable):
    """Abwandlung von `all()`, bei der nur die Hälfte aller Elemente truthy sein muss."""
    elements = list(iterable)
    count = sum(1 if bool(x) else 0 for x in elements)
    return count / len(elements) >= 0.5


def lax_most_common(counter, n=1):
    last_count = float('inf')
    i = 0
    for item, count in counter.most_common():
        if i >= n and count < last_count:
            break
        yield (item, count)
        i += 1
        last_count = count


def md5sum(path):
    """
    One-Liner zum Berechnen von md5-Prüfsummen.
    md5sum aus den GNU Coreutils liefert die gleichen Ergebnisse.
    """
    return hashlib.md5(path.read_bytes()).hexdigest()
