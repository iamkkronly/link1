import re
import requests
from bs4 import BeautifulSoup
import logging
import cloudscraper
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_animeflix_links(url):
    scraper = cloudscraper.create_scraper()
    try:
        logger.info(f"Fetching AnimeFlix URL: {url}")
        response = scraper.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        links = []

        # Find "Gdrive + Mirrors" links
        gdrive_links = soup.find_all('a', string=re.compile(r'Gdrive \+ Mirrors'))

        if not gdrive_links:
            logger.warning("No 'Gdrive + Mirrors' links found.")
            return []

        for link in gdrive_links:
            archive_url = link.get('href')
            if not archive_url:
                continue

            # Extract quality info from the previous text node if possible
            # The structure is often: Text Node (Quality) -> Link
            quality_text = "Unknown Quality"
            prev = link.previous_sibling
            if prev and isinstance(prev, str):
                quality_text = prev.strip()
            elif link.find_previous('p'):
                quality_text = link.find_previous('p').get_text(strip=True)

            # Clean up quality text
            # E.g., "1080p 10bit [1.96 GB]"
            # If it's too long, just truncate or use a generic name
            if len(quality_text) > 50:
                 quality_text = "Download"

            logger.info(f"Fetching archive: {archive_url}")
            try:
                arch_resp = scraper.get(archive_url)
                arch_resp.raise_for_status()
                arch_soup = BeautifulSoup(arch_resp.text, 'lxml')

                # Find getlink URLs
                getlinks = arch_soup.find_all('a', href=re.compile(r'/getlink/'))

                for gl in getlinks:
                    gl_url = gl.get('href')
                    gl_text = gl.get_text(strip=True)
                    if not gl_text:
                        gl_text = "Episode"

                    if gl_url.startswith('/'):
                        gl_url = 'https://episodes.animeflix.pm' + gl_url

                    logger.info(f"Processing getlink: {gl_url}")

                    # Follow redirect to driveseed
                    ds_resp = scraper.get(gl_url, allow_redirects=True)

                    if 'driveseed.org' in ds_resp.url:
                        final_links = process_driveseed(ds_resp, scraper)
                        for fl in final_links:
                            # Combine quality info with episode info if relevant
                            # E.g. "1080p 10bit [1.96 GB] - Episode 1"
                            full_text = f"{quality_text} - {gl_text}"
                            links.append({'text': full_text, 'link': fl})

            except Exception as e:
                logger.error(f"Error processing archive {archive_url}: {e}")

        return links

    except Exception as e:
        logger.error(f"Error scraping animeflix: {e}")
        return []

def process_driveseed(response, scraper):
    soup = BeautifulSoup(response.text, 'lxml')
    links = []

    # Check for JS redirect
    file_id = None
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            match = re.search(r'window\.location\.replace\("(/file/[^"]+)"\)', script.string)
            if match:
                file_path = match.group(1)
                file_url = 'https://driveseed.org' + file_path
                logger.info(f"Followed JS redirect to: {file_url}")
                try:
                    response = scraper.get(file_url)
                    soup = BeautifulSoup(response.text, 'lxml')
                    file_id = file_path.split('/')[-1]
                except:
                    pass
                break

    if not file_id:
        if '/file/' in response.url:
             file_id = response.url.split('/')[-1]

    if not file_id:
        return []

    # 1. Instant Download
    instant_dl = soup.find('a', string=re.compile('Instant Download'))
    if instant_dl:
        links.append(instant_dl['href'])

    # 2. Mirrors (Workers)
    wfile_url = f"https://driveseed.org/wfile/{file_id}"

    for type_val in [1, 2]:
        try:
            wfile_resp = scraper.get(f"{wfile_url}?type={type_val}")
            wsoup = BeautifulSoup(wfile_resp.text, 'lxml')

            dls = wsoup.find_all('a', string=re.compile('Download'))
            for dl in dls:
                href = dl.get('href')
                if href and 'workers.dev' in href:
                    links.append(href)
        except Exception as e:
            logger.error(f"Error fetching wfile type {type_val}: {e}")

    return links

if __name__ == "__main__":
    url = input("Enter AnimeFlix URL: ")
    if url:
        print(get_animeflix_links(url))
