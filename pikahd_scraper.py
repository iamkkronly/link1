import requests
from bs4 import BeautifulSoup
import argparse
import sys
import re

def scrape_pikahd_links(url):
    print(f"Scraping {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

    soup = BeautifulSoup(response.text, 'lxml')

    # Based on the observed structure, download links seem to be under specific text or buttons.
    # In the example:
    # [132]720p 10bit Links [740MB] -> https://links.kmhd.net/file/Suzu_3cdc5c77
    # [133]1080p 10bit Links [1.6GB] -> https://links.kmhd.net/file/Suzu_37e55a80

    # We should look for links that look like download links.
    # The text suggests they are often wrapped in 'p' tags with strong text or just 'a' tags.
    # A common pattern in these sites is links pointing to 'links.kmhd.net', 'hubcloud', etc.

    download_links = []

    # Strategy 1: Find all links and filter by interesting domains or keywords in text
    all_links = soup.find_all('a', href=True)

    for a in all_links:
        href = a['href']
        text = a.get_text(strip=True)

        # Check if it's a potential download link
        # Common domains often seen in these sites (expanding based on memory/experience with similar sites)
        if "links.kmhd.net" in href or "hubcloud" in href or "drive" in href or "mega.nz" in href:
             download_links.append((text, href))
        elif "Download" in text or "Links" in text:
             # Sometimes the link itself might be internal redirect or shortened
             if href.startswith("http"):
                 # Avoid nav links
                 if "category" not in href and "wp-json" not in href and "feed" not in href:
                    download_links.append((text, href))

    # Remove duplicates while preserving order
    unique_links = []
    seen = set()
    for text, href in download_links:
        if href not in seen:
            unique_links.append((text, href))
            seen.add(href)

    return unique_links

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter Pikahd URL: ")

    if not url:
        print("No URL provided.")
        return

    links = scrape_pikahd_links(url)

    if links:
        print(f"\nFound {len(links)} links:")
        for text, href in links:
            # Clean up text for better display
            clean_text = text.replace('\n', ' ').strip()
            if not clean_text:
                clean_text = "Download Link"
            print(f"{clean_text}: {href}")
    else:
        print("No download links found.")

if __name__ == "__main__":
    main()
