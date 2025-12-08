import cloudscraper
from bs4 import BeautifulSoup
import urllib.parse
import sys

def scrape_gd_kmhd(url):
    print(f"Scraping GD KMHD URL: {url}")
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = []

    # Helper to add link
    def add_link(text, link):
        if link and link not in [l['link'] for l in links]:
            # Resolve relative URLs
            link = urllib.parse.urljoin(url, link)
            links.append({'text': text, 'link': link})

    # Iterate over all <a> tags
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(" ", strip=True) # Use space separator
        text_lower = text.lower()

        # Skip invalid links
        if not href or href.startswith(('javascript', '#')):
            continue

        # Skip Login/Contact links
        if "login" in text_lower:
            continue

        if any(x in text_lower for x in ['about us', 'privacy', 'terms', 'dmca', 'join telegram']):
            continue

        # Check for specific buttons
        if "instant dl" in text_lower:
            add_link(text, href)
        elif "cloud download" in text_lower:
            add_link(text, href)
        elif "fast cloud" in text_lower or "zipdisk" in text_lower:
            add_link(text, href)
        elif "pixeldrain" in text_lower:
            add_link(text, href)
        elif "telegram file" in text_lower:
            add_link(text, href)
        elif "gofile" in text_lower:
            add_link(text, href)
        # Fallback for any other download link
        elif "download" in text_lower or "dl" in text_lower or "file" in text_lower:
            # Avoid the header "File Information"
            if "information" in text_lower:
                continue
            add_link(text, href)

    return links

if __name__ == "__main__":
    if len(sys.argv) > 1:
        start_url = sys.argv[1]
        results = scrape_gd_kmhd(start_url)
        if results:
            print(f"\nFound {len(results)} links:")
            for item in results:
                print(f"[{item['text']}] {item['link']}")
        else:
            print("No links found.")
    else:
        # Prompt user for input if no arg provided
        start_url = input("Enter GD KMHD URL: ").strip()
        if start_url:
            results = scrape_gd_kmhd(start_url)
            if results:
                print(f"\nFound {len(results)} links:")
                for item in results:
                    print(f"[{item['text']}] {item['link']}")
            else:
                print("No links found.")
