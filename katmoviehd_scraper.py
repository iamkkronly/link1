import requests
from bs4 import BeautifulSoup
import sys
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_soup(content):
    try:
        return BeautifulSoup(content, 'lxml')
    except:
        return BeautifulSoup(content, 'html.parser')

def scrape_katmoviehd(url):
    logger.info(f"Scraping KatMovieHD URL: {url}")
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = get_soup(response.content)

        links = []

        # Strategy: Look for <a> tags containing quality keywords in their text
        # Filter out links that are likely categories or tags

        for a in soup.find_all('a', href=True):
            text = a.get_text().strip()
            href = a['href']

            # Skip if href is just a fragment or relative root
            if not href or href.startswith('#') or href == '/':
                continue

            # Skip tag and category links
            if '/tag/' in href or '/category/' in href:
                continue

            # Skip self link if it matches the current url (ignoring protocol/www difference mostly handled by simple check)
            if href.rstrip('/') == url.rstrip('/'):
                continue

            # Check if text contains quality indicators
            if re.search(r'(480p|720p|1080p|2160p|4k)', text, re.IGNORECASE):
                 # Additional check: usually download links are on specific domains like links.kmhd.net
                 # or the text explicitly says "Links" or "Download"
                 # or it is enclosed in an element that suggests it's a download button/link

                 # The valid links seen were: https://links.kmhd.net/file/...
                 # And text: "480p Links [326MB]", "720p Links [1GB]"

                 # If we see "Links" in text, it's a strong signal.
                 if "links" in text.lower() or "download" in text.lower():
                     links.append({'quality': text, 'link': href})
                 elif "links.kmhd.net" in href:
                     links.append({'quality': text, 'link': href})

        return links

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter KatMovieHD URL: ")

    results = scrape_katmoviehd(url)

    if results:
        print("\nFound Links:")
        for res in results:
            print(f"{res['quality']} -> {res['link']}")
    else:
        print("\nNo links found.")
