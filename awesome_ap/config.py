from dotenv import load_dotenv
import os
from pathlib import Path
import yaml

load_dotenv()


DEV = os.getenv('DEV', 'False').lower() == 'true'

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN') or os.getenv('INPUT_GITHUB_TOKEN')

REPOS_BASE_PATH = Path(os.getenv('REPOS_BASE_PATH')).absolute()
# Dass dieser Pfad existiert, wird in main.py sichergestellt.

with open('config.yaml') as stream:
    CONFIG = yaml.safe_load(stream)
