import re
import requests
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_watchadsontape(url):
    logger.info(f"Scraping WatchAdsOnTape URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # Look for the robot link script
        # Pattern: document.getElementById('norobotlink').innerHTML = ...

        match = re.search(r"document\.getElementById\('norobotlink'\)\.innerHTML\s*=\s*'//([^']+)'\s*\+\s*\('([^']+)'\)\.substring\((\d+)\)\.substring\((\d+)\)", response.text)

        if match:
            domain_part = match.group(1) # watchadsontape.com/
            token_string = match.group(2) # xcdget_video...
            sub1 = int(match.group(3))
            sub2 = int(match.group(4))

            # Apply substrings
            # JS: ('string').substring(sub1).substring(sub2)
            # Python: string[sub1:][sub2:]

            final_path = token_string[sub1:][sub2:]

            final_link = f"https://{domain_part}{final_path}"
            return [{"text": "Download Link", "link": final_link}]

        # Fallback if pattern is slightly different (e.g. only one substring)
        match = re.search(r"document\.getElementById\('norobotlink'\)\.innerHTML\s*=\s*'//([^']+)'\s*\+\s*\('([^']+)'\)\.substring\((\d+)\);", response.text)
        if match:
            domain_part = match.group(1)
            token_string = match.group(2)
            sub1 = int(match.group(3))

            final_path = token_string[sub1:]
            final_link = f"https://{domain_part}{final_path}"
            return [{"text": "Download Link", "link": final_link}]

        logger.error("Could not find download link pattern in WatchAdsOnTape page.")
        return []

    except Exception as e:
        logger.error(f"WatchAdsOnTape Scrape Error: {e}")
        return []

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter WatchAdsOnTape link: ")

    if not url:
        print("No URL provided.")
        return

    links = scrape_watchadsontape(url)
    if links:
        for link in links:
            print(f"{link['text']}: {link['link']}")
    else:
        print("No links found.")

if __name__ == "__main__":
    main()
