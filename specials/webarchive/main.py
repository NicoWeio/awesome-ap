import requests
import tenacity
import yaml
from rich.console import Console

console = Console()

with console.status("Loading data…"):
    with open('build/data.yml') as f:
        data = yaml.safe_load(f)


def check_archived(url):
    """Check whether the url is archived in the Wayback Machine."""
    r = requests.get('https://archive.org/wayback/available', params={'url': url})
    r.raise_for_status()
    # archived_snapshots is an empty object if the url is not archived
    return r.json().get('archived_snapshots', {}).get('closest', {}).get('available', False)


def check_url(url):
    """Check whether the url is available using a HEAD request."""
    r = requests.head(url)
    return r.status_code == 200


@tenacity.retry(
    # Handle "429 Client Error: TOO MANY REQUESTS"
    stop=tenacity.stop_after_delay(60*2),
    wait=tenacity.wait_exponential(multiplier=1, min=5, max=60),
    retry=tenacity.retry_if_exception(lambda e: isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 429),
    before_sleep=lambda retry_state: print(f"⌛ Retrying in {retry_state.next_action.sleep} seconds…"),
    reraise=True,
)
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
    if not data:
        print("The data file appears to be empty.")
        return

    for repo in data:
        console.rule(repo['full_name'])

        # landing page
        handle_url(f"https://github.com/{repo['full_name']}")

        # PDFs
        for protokoll in repo['protokolle'].values():
            for pdf_path in protokoll['pdfs']:
                handle_url(f"https://raw.githubusercontent.com/{repo['full_name']}/{repo['branch']}/{pdf_path}")

        # contributors
        for contributor in repo['contributors']:
            handle_url(contributor['html_url'])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\nAborted.")
