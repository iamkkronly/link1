import cloudscraper
from bs4 import BeautifulSoup
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_vikingfile(url):
    """
    Scrapes download links from a VikingFile URL using Cloudscraper.
    """
    logger.info(f"Scraping VikingFile: {url}")

    # Initialize cloudscraper with browser emulation
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )

    try:
        response = scraper.get(url)
        response.raise_for_status()

        try:
            soup = BeautifulSoup(response.content, 'lxml')
        except Exception:
            soup = BeautifulSoup(response.content, 'html.parser')

        links = []

        # Extract Filename and Size if available
        filename_elem = soup.find(id='filename')
        size_elem = soup.find(id='size')

        if filename_elem:
            logger.info(f"Filename: {filename_elem.get_text(strip=True)}")
        if size_elem:
            logger.info(f"Size: {size_elem.get_text(strip=True)}")

        # Look for the download link
        # Note: VikingFile uses Turnstile and WASM/JS to generate the link.
        # Cloudscraper cannot execute this, so we look for any exposed links.

        download_link = soup.find('a', id='download-link')
        if download_link and download_link.get('href') and download_link['href'] != '#':
             links.append({'text': download_link.get_text(strip=True) or "Download Link", 'link': download_link['href']})

        # Look for other potential download links
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)

            if not href or href.startswith('#') or href.startswith('javascript'):
                continue

            # Filter for likely download buttons
            if "download" in text.lower():
                 # Avoid the Usenet ad link usually present
                 if "fast-download" in href and "usenet" in text.lower():
                     continue

                 # Add the link
                 if not any(l['link'] == href for l in links):
                     links.append({'text': text, 'link': href})

        # Fallback: if no download links found, just return the page URL as a reference
        # or indicate that the link is protected.
        if not links:
             logger.warning("No direct download links found (likely protected by Turnstile).")

        return links

    except Exception as e:
        logger.error(f"VikingFile Scrape Error: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = input("Enter VikingFile URL: ")

    if target_url:
        results = scrape_vikingfile(target_url)
        print(f"Found {len(results)} links:")
        for res in results:
            print(f"{res['text']}: {res['link']}")
    else:
        print("No URL provided.")
