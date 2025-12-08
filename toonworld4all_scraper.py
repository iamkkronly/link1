import cloudscraper
from bs4 import BeautifulSoup
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_toonworld4all(url):
    """
    Scrapes download links from a toonworld4all.me URL.
    """
    scraper = cloudscraper.create_scraper()

    try:
        logger.info(f"Fetching URL: {url}")
        response = scraper.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        download_links = []

        # Strategy 1: Look for specific download containers if known (generic fallbacks for now)
        # Strategy 2: Look for all links and filter by keywords

        all_links = soup.find_all("a", href=True)

        for link in all_links:
            href = link['href']
            text = link.get_text(strip=True)

            # Common patterns for download links or redirect pages
            is_potential_link = False

            # Keywords often found in download buttons
            keywords = ["Download", "Watch Online", "G-Direct", "Mega", "Drive", "File", "Link"]

            if any(k.lower() in text.lower() for k in keywords):
                is_potential_link = True

            # Check for specific classes if we knew them, but we don't.
            # So rely on context.

            if is_potential_link:
                # Try to find quality info from previous headers or text
                quality_header = "Unknown Quality"
                header = link.find_previous(["h3", "h4", "h5", "h2", "strong", "b"])

                if header:
                    quality_header = header.get_text(strip=True)

                # Filter out internal navigation links if they accidentally matched
                if not href.startswith("#") and "javascript" not in href.lower():
                     # Simple dedup based on URL
                    if not any(d['url'] == href for d in download_links):
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
            url = input("Enter toonworld4all link: ")

    if not url:
        print("No URL provided.")
        return

    links = scrape_toonworld4all(url)

    if links:
        print(f"\nFound {len(links)} links:")
        for link in links:
            print(f"[{link['quality_header']}] {link['text']}: {link['url']}")
    else:
        print("No links found.")

if __name__ == "__main__":
    main()
