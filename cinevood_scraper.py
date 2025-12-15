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

        # Strategy 1: Look for <h6> headers followed by <p> containing links
        # This structure was observed in the provided example
        content_div = soup.find('div', class_='post-single-content')

        if content_div:
            # Find all h6 and p tags in order
            elements = content_div.find_all(['h6', 'p'])
            current_quality = "Unknown Quality"

            for elem in elements:
                if elem.name == 'h6':
                    # Clean up quality text
                    text = elem.get_text().strip()
                    if text:
                        current_quality = text
                elif elem.name == 'p':
                    # Look for links in this paragraph
                    # We are looking for download links which often have specific classes or text
                    # In the example, they have classes like 'maxbutton-hubcloud', 'maxbutton-oxxfile'

                    found_links = elem.find_all('a', href=True)
                    for link in found_links:
                        href = link['href']
                        text = link.get_text().strip()

                        # STRICT FILTER: Only keep OxxFile links
                        if "oxxfile" in href.lower() or "oxxfile" in text.lower() or "oxx file" in text.lower():
                             # If the text is empty, try to get it from title attribute
                             if not text:
                                 text = link.get('title', '').strip()

                             if not text:
                                 text = "Download Link"

                             links.append({
                                 'quality': current_quality,
                                 'text': text,
                                 'link': href
                             })

        # Strategy 2: Fallback if Strategy 1 found nothing (different template?)
        if not links:
            logger.info("Strategy 1 found no links. Trying generic fallback.")
            # ... existing generic logic could go here or a variation ...
            # For now, let's just do a broad search for maxbuttons if above failed
            for a in soup.find_all('a', class_='maxbutton', href=True):
                 text = a.get_text().strip() or a.get('title', '').strip() or "Download"
                 href = a['href']

                 # STRICT FILTER for fallback too
                 if "oxxfile" in href.lower() or "oxxfile" in text.lower() or "oxx file" in text.lower():
                     links.append({
                         'quality': "Unknown (Fallback)",
                         'text': text,
                         'link': href
                     })

        return links

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("Please provide a Cinevood URL as an argument.")
        print("Usage: python3 cinevood_scraper.py <url>")
        sys.exit(1)

    results = scrape_cinevood(url)

    if results:
        print(f"\nFound {len(results)} links:\n")
        # Group by quality for better display
        grouped = {}
        for item in results:
            q = item['quality']
            if q not in grouped:
                grouped[q] = []
            grouped[q].append(item)

        for q, items in grouped.items():
            print(f"--- {q} ---")
            for item in items:
                print(f"[{item['text']}] -> {item['link']}")
            print("")
    else:
        print("\nNo links found.")
