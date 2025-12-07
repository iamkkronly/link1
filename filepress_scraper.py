import cloudscraper
from bs4 import BeautifulSoup
import sys
import re
from urllib.parse import urljoin

def scrape_filepress(url):
    print(f"Scraping FilePress: {url}")
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    links = []

    # Strategy 1: Find links with "Download" text
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        href = a['href']

        # Handle relative URLs
        if not href.startswith(('http://', 'https://')):
            href = urljoin(url, href)

        # Filter junk
        if href == url or href.startswith('javascript:'):
            continue

        text_lower = text.lower()

        # Keywords indicating download/quality
        if any(kw in text_lower for kw in ['download', '480p', '720p', '1080p', '2160p', '4k', 'get link']):
             links.append({'text': text, 'link': href})

        # Check for known file hosts if the text is generic
        elif any(host in href for host in ['drive.google.com', 'mega.nz', 'gofile.io', '1fichier.com', 'pixeldrain.com']):
             links.append({'text': text or "File Host", 'link': href})

    # Strategy 2: If no explicit download links, maybe look for buttons
    if not links:
        for btn in soup.find_all(class_=re.compile(r'btn|button|download', re.I)):
            if btn.name == 'a' and btn.get('href'):
                href = btn['href']
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(url, href)
                links.append({'text': btn.get_text(strip=True) or "Download", 'link': href})

    return links

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        # Default for testing if run without args
        target_url = input("Enter FilePress URL: ")

    if target_url:
        results = scrape_filepress(target_url)
        if results:
            print(f"Found {len(results)} links:")
            for r in results:
                print(f"{r['text']}: {r['link']}")
        else:
            print("No links found.")
