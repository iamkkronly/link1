import requests
from bs4 import BeautifulSoup
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_moviesmod(url):
    """
    Scrapes download links from a moviesmod.kids URL.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        download_links = []

        all_links = soup.find_all("a", href=True)

        for link in all_links:
            href = link['href']
            text = link.get_text(strip=True)

            if "links.modpro.blog" in href:
                # Based on inspection, the structure is typically:
                # <h3>Download ... 480p ...</h3>
                # <p><a ...>Download Links</a></p>
                # So we look for the closest preceding header (h3, h4, h5, or h2)

                quality_header = "Unknown Quality"
                header = link.find_previous(["h3", "h4", "h5", "h2"])

                if header:
                    quality_header = header.get_text(strip=True)

                # Clean up the header text to be more concise if needed,
                # but providing the full header is informative.

                download_links.append({
                    "text": text,
                    "url": href,
                    "quality_header": quality_header
                })

        return download_links

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return []

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Check if input is piped
        if not sys.stdin.isatty():
            url = sys.stdin.read().strip()
        else:
            url = input("Enter moviesmod link: ")

    if not url:
        print("No URL provided.")
        return

    links = scrape_moviesmod(url)

    if links:
        print(f"\nFound {len(links)} links:")
        for link in links:
            # We print the Quality Header found above the link
            print(f"{link['quality_header']}\n{link['url']}\n")
    else:
        print("No links found.")

if __name__ == "__main__":
    main()
