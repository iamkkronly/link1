import argparse
import logging
import re
import cloudscraper
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GdflixScraper:
    def __init__(self, url):
        self.url = url
        self.session = cloudscraper.create_scraper()
        self.domain = urlparse(url).netloc

    def scrape_links(self):
        logger.info(f"Scraping URL: {self.url}")

        # Initial request to the gdflix URL
        try:
            response = self.session.get(self.url)
            if response.status_code != 200:
                logger.error(f"Failed to fetch {self.url}, status code: {response.status_code}")
                return []

            # Follow redirects if any
            final_url = response.url
            parsed_final_url = urlparse(final_url)
            base_url = f"{parsed_final_url.scheme}://{parsed_final_url.netloc}"
            logger.info(f"Final URL after redirects: {final_url}")

            soup = BeautifulSoup(response.content, 'lxml')

            # Look for the fkeys variable in the script
            scripts = soup.find_all('script')
            fkeys_json = None

            for script in scripts:
                if script.string and 'const fkeys = JSON.parse' in script.string:
                    match = re.search(r"const fkeys = JSON.parse\('([^']+)'\)", script.string)
                    if match:
                        fkeys_json = json.loads(match.group(1))
                        logger.info(f"Found {len(fkeys_json)} file keys.")
                        break

            if not fkeys_json:
                logger.error("Could not find file keys on the page.")
                return []

            download_links = []

            for index, file_key in enumerate(fkeys_json):
                logger.info(f"Processing key {index+1}/{len(fkeys_json)}: {file_key}")

                # Construct file page URL
                file_page_url = f"{base_url}/file/{file_key}"

                try:
                    # Visit file page to get the key
                    file_resp = self.session.get(file_page_url)
                    if file_resp.status_code != 200:
                        logger.error(f"Failed to fetch file page {file_page_url}, status: {file_resp.status_code}")
                        continue

                    file_soup = BeautifulSoup(file_resp.content, 'lxml')
                    file_scripts = file_soup.find_all('script')
                    file_api_key = None

                    for fscript in file_scripts:
                        if fscript.string and 'formData.append("key",' in fscript.string:
                            key_match = re.search(r'formData\.append\("key", "([^"]+)"\)', fscript.string)
                            if key_match:
                                file_api_key = key_match.group(1)
                                break

                    if not file_api_key:
                        logger.warning(f"Could not find API key on file page {file_page_url}")
                        continue

                    # Construct mfile URL for "instant" action
                    mfile_url = file_page_url.replace('/file/', '/mfile/')

                    data = {
                        "action": "instant",
                        "key": file_api_key,
                        "action_token": "",
                    }

                    parsed_file_url = urlparse(file_page_url)
                    headers = {
                        "x-token": parsed_file_url.hostname,
                        "Referer": file_page_url,
                        "Origin": f"{parsed_file_url.scheme}://{parsed_file_url.netloc}",
                        "X-Requested-With": "XMLHttpRequest",
                        "User-Agent": self.session.headers['User-Agent']
                    }

                    # POST to mfile URL
                    post_resp = self.session.post(mfile_url, data=data, headers=headers)
                    if post_resp.status_code == 200:
                        try:
                            json_resp = post_resp.json()
                            link = None
                            if 'url' in json_resp:
                                link = json_resp['url']
                            elif 'visit_url' in json_resp:
                                link = json_resp['visit_url']

                            if link:
                                logger.info(f"Found link: {link}")
                                download_links.append(link)
                            else:
                                logger.warning(f"No URL in response for key {file_key}: {json_resp}")
                        except ValueError:
                            logger.error(f"Invalid JSON response for key {file_key}")
                    else:
                        logger.error(f"Failed to generate link for key {file_key}, status: {post_resp.status_code}")

                except Exception as e:
                    logger.error(f"Error processing key {file_key}: {e}")

                # Respectful delay
                time.sleep(1)

            return download_links

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description="Scrape download links from gdflix.dev")
    parser.add_argument("url", help="The gdflix URL to scrape")
    args = parser.parse_args()

    scraper = GdflixScraper(args.url)
    links = scraper.scrape_links()

    if links:
        print("\nScraped Links:")
        for link in links:
            print(link)
    else:
        print("No links found.")

if __name__ == "__main__":
    main()
