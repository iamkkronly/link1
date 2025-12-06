import requests
from bs4 import BeautifulSoup
import argparse

def get_soup(content):
    """Helper to parse HTML with fallback."""
    try:
        return BeautifulSoup(content, 'lxml')
    except Exception as e:
        return BeautifulSoup(content, 'html.parser')

def scrape_1tamilmv(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"Fetching URL: {url} ...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return

    soup = get_soup(response.content)

    title = soup.title.string if soup.title else "Unknown Title"
    print(f"\nPage Title: {title}\n")

    # Find Magnet Links
    print("--- Magnet Links ---")
    magnet_links = []
    for a_tag in soup.find_all('a', href=True):
        if a_tag['href'].startswith('magnet:'):
            magnet_links.append(a_tag['href'])
            print(f"{a_tag['href']}")
            print("-" * 20)

    if not magnet_links:
        print("No magnet links found.")

    print("\n--- Torrent Files ---")
    torrent_files = []
    for a_tag in soup.find_all('a', href=True):
        if a_tag.get('data-fileext') == 'torrent' or a_tag['href'].endswith('.torrent'):
            # Ensure full URL
            link = a_tag['href']
            # Some sites use relative URLs, though 1tamilmv usually uses absolute URLs for attachments.
            # No harm in leaving it as is since requests.get handles absolute URLs fine,
            # and if relative we'd need base URL but typically scraping href gives what's in attribute.
            torrent_files.append(link)
            print(f"{link}")
            print("-" * 20)

    if not torrent_files:
        print("No torrent file links found.")

    print(f"\nFound {len(magnet_links)} magnet links and {len(torrent_files)} torrent files.")

def main():
    parser = argparse.ArgumentParser(description="Scrape download links from 1tamilmv topic page.")
    parser.add_argument("url", nargs='?', help="The URL of the 1tamilmv topic page")
    args = parser.parse_args()

    url = args.url
    if not url:
        print("Please enter the 1tamilmv link:")
        url = input().strip()

    if not url:
        print("No URL provided. Exiting.")
        return

    scrape_1tamilmv(url)

if __name__ == "__main__":
    main()
