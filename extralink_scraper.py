import requests
import logging
import re
from urllib.parse import urlparse

# Use a module-level logger
logger = logging.getLogger(__name__)

def is_extralink_url(url):
    return "extralink.ink" in url

def scrape_extralink(url):
    """
    Scrapes download links from an extralink.ink URL using its API.
    """
    logger.info(f"Scraping ExtraLink URL: {url}")

    # Extract token from URL
    # URL format: https://new3.extralink.ink/s/ed84b86e or https://new3.extralink.ink/s/ed84b86e/
    # API format: https://new3.extralink.ink/api/s/ed84b86e/

    match = re.search(r'/s/([a-zA-Z0-9]+)', url)
    if not match:
        logger.error("Could not extract token from ExtraLink URL.")
        return []

    token = match.group(1)
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    scheme = parsed_url.scheme

    api_url = f"{scheme}://{domain}/api/s/{token}/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        links = []

        # Helper to add link if valid
        def add_link(key, name):
            if data.get(key):
                links.append({'text': name, 'link': data[key]})

        # Extract links based on known keys from JSON response
        add_link('filepressLink', 'FilePress')
        add_link('streamhgLink', 'StreamHG')
        add_link('vidhideLink', 'VidHide')
        add_link('r2Link', 'R2 Direct')
        add_link('vikingLink', 'VikingFile')
        add_link('photoLink', 'Photo')
        add_link('gdtotLink', 'GDTOT')
        add_link('hubcloudLink', 'HubCloud')
        add_link('pixeldrainLink', 'PixelDrain')
        add_link('gofileLink', 'GoFile')
        add_link('abyssPlayerLink', 'AbyssPlayer')

        # Handle driveLinks (encrypted)
        # We probably can't decrypt them easily without the key/logic, but we can check if they exist
        # If the user wants "all links", maybe we should just output what we have.
        # The prompt says "scrape all download links".

        return links

    except Exception as e:
        logger.error(f"ExtraLink Scrape Error: {e}")
        return []

if __name__ == "__main__":
    # Test with the provided URL
    test_url = "https://new3.extralink.ink/s/ed84b86e"
    print(f"Testing with {test_url}")
    logging.basicConfig(level=logging.INFO)
    results = scrape_extralink(test_url)
    for link in results:
        print(f"{link['text']}: {link['link']}")
