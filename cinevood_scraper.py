import cloudscraper
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

def scrape_cinevood(url):
    logger.info(f"Scraping Cinevood URL: {url}")

    # Cloudscraper handles Cloudflare
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

    try:
        response = scraper.get(url, timeout=15)

        # Check for Cloudflare or other protections
        if response.status_code in [403, 503]:
            logger.error(f"Access denied (Status: {response.status_code}). Site might be protected by Cloudflare.")
            print("Tip: If you are seeing 403/503 errors, the Cloudflare protection might be too strong for the current solver.")
            return []

        response.raise_for_status()
        soup = get_soup(response.content)

        links = []

        # Generic scraping logic based on common patterns
        # Look for <a> tags with quality info or "Download" text

        for a in soup.find_all('a', href=True):
            text = a.get_text().strip()
            href = a['href']

            # Skip empty or internal anchors
            if not href or href.startswith('#'):
                continue

            text_lower = text.lower()

            # Keywords indicating a download link
            quality_keywords = ['480p', '720p', '1080p', '2160p', '4k']
            download_keywords = ['download', 'links', 'gdrive', 'mega', 'file']

            is_download = False

            # Check for quality info
            if any(q in text_lower for q in quality_keywords):
                is_download = True
            # Check for explicit download text
            elif any(k in text_lower for k in download_keywords):
                # Filter out navigation links if possible (heuristic)
                if len(text) < 50:
                    is_download = True

            if is_download:
                links.append({'text': text, 'link': href})

        # If we found links, categorize them
        categorized_links = {
            '480p': [],
            '720p': [],
            '1080p': [],
            'Other': []
        }

        for item in links:
            q_found = False
            for q in ['480p', '720p', '1080p']:
                if q in item['text'].lower():
                    categorized_links[q].append(item)
                    q_found = True

            if not q_found:
                categorized_links['Other'].append(item)

        return categorized_links

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return {}

if __name__ == "__main__":
    print("Cinevood Scraper")
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter Cinevood Movie URL: ")

    results = scrape_cinevood(url)

    if results:
        found_any = False
        for quality in ['480p', '720p', '1080p']:
            if results[quality]:
                found_any = True
                print(f"\n--- {quality} Links ---")
                for res in results[quality]:
                    print(f"[{res['text']}] -> {res['link']}")

        if results['Other']:
            found_any = True
            print("\n--- Other Links ---")
            for res in results['Other']:
                print(f"[{res['text']}] -> {res['link']}")

        if not found_any:
             print("\nNo specific quality links found.")
    else:
        print("\nNo links found or error occurred.")
