import requests
from bs4 import BeautifulSoup
import sys
import argparse

# Import the existing KMHD scraper function
try:
    from kmhd_scraper import scrape_kmhd_links
except ImportError:
    # If we can't import the function, we can't resolve the final links.
    # We should probably exit or define a dummy function that warns the user.
    print("Error: Could not import 'scrape_kmhd_links' from 'kmhd_scraper.py'.")
    print("Ensure 'kmhd_scraper.py' is in the same directory.")
    sys.exit(1)

def scrape_katdrama(url):
    """
    Scrapes download links from a katdrama.net movie/show page.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'lxml')

    # katdrama.net usually lists links to links.kmhd.net
    # Structure: <a href="https://links.kmhd.net/file/...">Quality info</a>

    download_links = []

    # Find all links starting with https://links.kmhd.net
    # We look for 'file' or 'play' in the URL, though usually download links are 'file'

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if "links.kmhd.net" in href:
            # Check if it is a download link (usually contains /file/ or just links.kmhd.net)
            # Sometimes play links are also there. We want download links.
            # Based on inspection: https://links.kmhd.net/file/Sure_1a44947c

            link_text = a_tag.get_text(strip=True)

            # Context: The quality is often in the link text or nearby.
            # If the link text is empty, check parent or previous siblings.
            # But simpler is to just collect the URL and resolve it.

            if "/file/" in href:
                 download_links.append({
                     'url': href,
                     'text': link_text
                 })

    results = {}

    print(f"Found {len(download_links)} intermediate links.")

    for item in download_links:
        kmhd_url = item['url']
        label = item['text'] or "Unknown Quality"
        print(f"Processing: {label} -> {kmhd_url}")

        try:
            # Use the existing scraper to resolve final links
            final_links = scrape_kmhd_links(kmhd_url)
            if final_links:
                results[kmhd_url] = {
                    'label': label,
                    'links': final_links
                }
            else:
                 print(f"  No links found for {kmhd_url}")
        except Exception as e:
            print(f"  Error processing {kmhd_url}: {e}")

    return results

def main():
    parser = argparse.ArgumentParser(description="Scrape download links from KatDrama.net")
    parser.add_argument("url", help="The KatDrama.net movie/show URL")
    args = parser.parse_args()

    scraped_data = scrape_katdrama(args.url)

    if scraped_data:
        print("\n--- All Scraped Links ---\n")
        for kmhd_url, data in scraped_data.items():
            print(f"Quality/Label: {data['label']}")
            print(f"Source: {kmhd_url}")
            for link in data['links']:
                print(f"  - {link}")
            print("-" * 30)
    else:
        print("No download links found.")

if __name__ == "__main__":
    main()
