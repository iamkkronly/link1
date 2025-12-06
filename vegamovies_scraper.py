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

def scrape_vegamovies(url):
    logger.info(f"Scraping Vegamovies URL: {url}")
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=15)

        # Check for Cloudflare or other protections
        if response.status_code in [403, 503]:
            logger.error(f"Access denied (Status: {response.status_code}). Site might be protected by Cloudflare.")
            print("Tip: If you are seeing 403/503 errors, you might need a Cloudflare solver like 'cloudscraper' or 'cfscrape'.")
            return []

        response.raise_for_status()
        soup = get_soup(response.content)

        links = []

        # Vegamovies often organizes links in sections.
        # We will look for <a> tags that contain quality info or "Download" text.

        # General strategy: Find all links
        for a in soup.find_all('a', href=True):
            text = a.get_text().strip()
            href = a['href']

            # Filter for likely download links
            # Valid indicators: "Download", "480p", "720p", "1080p", "GDrive", "Mega", "V-Cloud"

            text_lower = text.lower()
            if any(q in text_lower for q in ['480p', '720p', '1080p']):
                # It has quality info, likely a download link
                links.append({'quality': text, 'link': href})
            elif "download" in text_lower and ("link" in text_lower or "server" in text_lower):
                 links.append({'quality': text, 'link': href})
            elif "g-direct" in text_lower or "v-cloud" in text_lower:
                 links.append({'quality': text, 'link': href})

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
                if q in item['quality'].lower():
                    categorized_links[q].append(item)
                    q_found = True

            if not q_found:
                categorized_links['Other'].append(item)

        return categorized_links

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return {}

if __name__ == "__main__":
    print("Vegamovies Scraper")
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter Vegamovies Movie URL: ")

    results = scrape_vegamovies(url)

    if results:
        found_any = False
        for quality in ['480p', '720p', '1080p']:
            if results[quality]:
                found_any = True
                print(f"\n--- {quality} Links ---")
                for res in results[quality]:
                    print(f"[{res['quality']}] -> {res['link']}")

        if results['Other']:
            found_any = True
            print("\n--- Other Links ---")
            for res in results['Other']:
                print(f"[{res['quality']}] -> {res['link']}")

        if not found_any:
             print("\nNo specific quality links found.")
    else:
        print("\nNo links found or error occurred.")
