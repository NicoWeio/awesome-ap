import subprocess

from console import *


def get_command_runner(default_cwd):
    def run_command(command, **kwargs):
        kwargs.setdefault('cwd', default_cwd)
        if kwargs.get('shell'):
            console.print(f'$ {command}', style='blue')
        else:
            console.print(f'$ {" ".join(map(str, command))}', style='blue')
        if kwargs.get('capture_output'):
            console.print('→ output not shown', style='blue')
        return subprocess.run(command, **kwargs)  # raises subprocess.CalledProcessError ✓
    return run_command
