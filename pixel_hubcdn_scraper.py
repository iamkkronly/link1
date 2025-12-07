import requests
from bs4 import BeautifulSoup
import logging
import argparse

# Configure logging for standalone use, but don't override if imported
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def scrape_pixel_hubcdn(url):
    """
    Scrapes download links from pixel.hubcdn.fans URLs.
    Returns a list of dictionaries with 'text' and 'link' keys.
    """
    logging.info(f"Scraping Pixel HubCDN URL: {url}")
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # Use lxml if available, fallback to html.parser
        try:
            soup = BeautifulSoup(response.content, 'lxml')
        except Exception:
            soup = BeautifulSoup(response.content, 'html.parser')

        links = []

        # Method 1: Check for the specific #vd element (primary download button)
        vd_link = soup.find('a', id='vd')
        if vd_link and vd_link.get('href'):
            href = vd_link['href']
            # Clean up the link if necessary
            links.append({'text': "Download Here", 'link': href})

        # Method 2: Check for other download buttons (e.g. .btn-success, .btn-primary)
        # This handles potential variations or multiple links
        for btn in soup.find_all('a', class_=lambda c: c and ('btn-success' in c or 'btn-primary' in c or 'btn-brand' in c)):
            text = btn.get_text(strip=True)
            href = btn.get('href')

            # Filter valid download links
            if href and "download" in text.lower():
                # Avoid duplicates
                if not any(l['link'] == href for l in links):
                     links.append({'text': text, 'link': href})

        logging.info(f"Found {len(links)} links on Pixel HubCDN page.")
        return links

    except Exception as e:
        logging.error(f"Pixel HubCDN Scrape Error: {e}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape pixel.hubcdn.fans links")
    parser.add_argument("url", help="The URL to scrape")
    args = parser.parse_args()

    results = scrape_pixel_hubcdn(args.url)
    if results:
        print(f"Found {len(results)} links:")
        for r in results:
            print(f"- {r['text']}: {r['link']}")
    else:
        print("No links found.")
