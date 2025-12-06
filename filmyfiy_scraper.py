import requests
from bs4 import BeautifulSoup
import re
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_soup(content):
    try:
        return BeautifulSoup(content, 'lxml')
    except:
        return BeautifulSoup(content, 'html.parser')

def scrape_filmyfiy(url):
    logger.info(f"Scraping Filmyfiy URL: {url}")
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = get_soup(response.content)

        # Find the intermediate download link
        # Look for "Download 480p 720p 1080p [HD]" or similar
        download_link = None

        # Strategy 1: Look for specific text
        for a in soup.find_all('a', href=True):
            text = a.get_text().strip()
            if "Download 480p 720p 1080p" in text:
                download_link = a['href']
                break

        # Strategy 2: If not found, look for any link to linkmake.in
        if not download_link:
            for a in soup.find_all('a', href=True):
                if "linkmake.in" in a['href']:
                    download_link = a['href']
                    break

        if not download_link:
            logger.error("Could not find the intermediate download link (linkmake.in) on the page.")
            return []

        logger.info(f"Found intermediate link: {download_link}")

        # Now scrape the intermediate page
        response = requests.get(download_link, headers=headers, timeout=15)
        response.raise_for_status()
        soup = get_soup(response.content)

        links = []
        # The links seem to be in simple <a> tags with text like "Download ... {quality}"
        # Based on view_text_website output:
        # Download 430mb {480p-HEVC}
        # Download 730mb {720p-HEVC}

        for a in soup.find_all('a', href=True):
            text = a.get_text().strip()
            href = a['href']

            # Filter for relevant download links
            # They seem to point to filesdl.site or similar, but the text is the key
            if "Download" in text and ("480p" in text or "720p" in text or "1080p" in text):
                links.append({'quality': text, 'link': href})

        return links

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter Filmyfiy URL: ")

    results = scrape_filmyfiy(url)

    if results:
        print("\nFound Links:")
        for res in results:
            print(f"{res['quality']} -> {res['link']}")
    else:
        print("\nNo links found.")
