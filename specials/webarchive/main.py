from rich.console import Console
import requests
import yaml

console = Console()

with console.status("Loading data…"):
    with open('build/data.yml') as f:
        data = yaml.safe_load(f)


def check_archived(url):
    """Check whether the url is archived in the Wayback Machine."""
    r = requests.get('https://archive.org/wayback/available', params={'url': url})
    return r.json().get('archived_snapshots', {}).get('closest', {}).get('available', False)


def check_url(url):
    """Check whether the url is available using a HEAD request."""
    r = requests.head(url)
    return r.status_code == 200


def archive_url(url):
    """Archive the url in the Wayback Machine."""
    r = requests.get(f'https://web.archive.org/save/{url}')
    r.raise_for_status()
    return r


def handle_url(url):
    """Check for archival and availability and archive if possible/necessary."""
    print(f'→ "{url}"')
    with console.status("Checking archival status…"):
        is_archived = check_archived(url)

    if is_archived:
        print("⏭️ Already archived")
        return

    with console.status("Checking availability…"):
        is_available = check_url(url)

    if not is_available:
        print("❌ Not available")
        return

    try:
        with console.status("Archiving…"):
            result = archive_url(url)
        print("✅ Archived")
    except requests.exceptions.HTTPError as e:
        print("⚠️", e)


def main():
    for repo in data:
        console.rule(repo['full_name'])

        # landing page
        handle_url(f"https://github.com/{repo['full_name']}")

        # PDFs
        for protokoll in repo['protokolle'].values():
            for pdfPath in protokoll['pdfs']:
                handle_url(f"https://raw.githubusercontent.com/{repo['full_name']}/{repo['branch']}/{pdfPath}")

        # contributors
        for contributor in repo['contributors']:
            handle_url(contributor['html_url'])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\nAborted.")
