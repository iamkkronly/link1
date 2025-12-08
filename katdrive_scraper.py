import cloudscraper
from bs4 import BeautifulSoup
import sys
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def scrape_katdrive(url):
    scraper = cloudscraper.create_scraper()
    links = []

    try:
        logger.info(f"Scraping URL: {url}")
        response = scraper.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # Extract Filename
        filename_tag = soup.find('h4', class_='text-primary')
        if filename_tag:
            filename = filename_tag.get_text(strip=True)
            logger.info(f"Filename: {filename}")
        else:
            filename = "Unknown Filename"
            logger.warning("Could not find filename.")

        # Extract ID from URL or page
        match = re.search(r'/file/(\d+)', url)
        if match:
            file_id = match.group(1)
        else:
            id_div = soup.find('div', id='down-id')
            if id_div:
                file_id = id_div.get_text(strip=True)
            else:
                logger.error("Could not find file ID.")
                return []

        # 1. Try Direct Download
        ajax_url = "https://katdrive.eu/ajax.php?ajax=direct-download"
        data = {'id': file_id}
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': url,
            'Origin': 'https://katdrive.eu'
        }

        logger.info("Attempting to generate direct download link...")
        try:
            ajax_response = scraper.post(ajax_url, data=data, headers=headers)
            ajax_response.raise_for_status()
            json_data = ajax_response.json()

            # Check for success (code can be int 200 or str '200')
            code = json_data.get('code')
            if str(code) == '200':
                dl_link = json_data.get('file')
                logger.info(f"Found Direct Link: {dl_link}")
                links.append({"type": "Direct Download", "link": dl_link})
            else:
                msg = json_data.get('file', 'Unknown Error')
                logger.warning(f"Direct download failed: {msg}")
        except Exception as e:
            logger.error(f"Error during AJAX request: {e}")

        # 2. Extract Embed/Stream Link
        embed_div = soup.find('div', id='embed')
        if embed_div:
            iframe = embed_div.find('iframe')
            if iframe and iframe.get('src'):
                stream_link = iframe['src']
                logger.info(f"Found Stream Link: {stream_link}")
                links.append({"type": "Stream/Embed", "link": stream_link})
        else:
             # Fallback: construct it if not found in DOM (less reliable but possible)
             stream_link = f"https://katdrive.eu/stream/{file_id}"
             links.append({"type": "Stream/Embed (Constructed)", "link": stream_link})

        return links

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter the KatDrive URL: ")

    if url:
        results = scrape_katdrive(url)
        if results:
            print("\n--- Scraped Links ---")
            for item in results:
                print(f"{item['type']}: {item['link']}")
        else:
            print("No links found.")
