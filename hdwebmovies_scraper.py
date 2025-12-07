import cloudscraper
from bs4 import BeautifulSoup
import re
import argparse

def scrape_hdwebmovies(url):
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        links_found = []

        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True)
            href = a['href']

            # Primary check: "DOWNLOAD" + Quality (e.g. 480p, 720p, etc.)
            # Exclude /tag/ and /category/ and current page anchors
            if "/tag/" in href or "/category/" in href or href.strip() == "#":
                continue

            # Case 1: Standard "DOWNLOAD <Quality>"
            if "download" in text.lower() and re.search(r'\d{3,4}p', text, re.IGNORECASE):
                 links_found.append({"text": text, "link": href})

            # Case 2: "Download Now" pointing to external shortener/host (e.g. hwmlinks.store)
            elif "download now" in text.lower():
                links_found.append({"text": text, "link": href})

            # Case 3: Known file hosts or magnet links
            elif any(x in href for x in ['magnet:', 'drive.google.com', 'mega.nz', 'pixeldra', 'tmbcloud.pro', 'hwmlinks']):
                # Avoid duplicates if already added by text match
                if not any(l['link'] == href for l in links_found):
                    links_found.append({"text": text or "Link", "link": href})

        return links_found

    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape HDWebMovies links")
    parser.add_argument("url", help="HDWebMovies movie URL")
    args = parser.parse_args()

    links = scrape_hdwebmovies(args.url)
    if isinstance(links, list):
        if not links:
            print("No links found.")
        for l in links:
            print(f"{l['text']}: {l['link']}")
    else:
        print(links)
