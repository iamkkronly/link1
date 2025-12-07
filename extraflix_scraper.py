import cloudscraper
from bs4 import BeautifulSoup
import sys

def get_download_links(url):
    """
    Scrapes download links from an ExtraFlix URL.
    Returns a list of strings formatted as "Quality: Link".
    """
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url)
        response.raise_for_status()
    except Exception as e:
        return [f"Error fetching URL: {e}"]

    soup = BeautifulSoup(response.content, 'html.parser')
    results = []

    # Identify links pointing to extralink.ink (the file host/shortener used)
    # The pattern seen is new3.extralink.ink, but we'll search for extralink.ink generally
    links_found = soup.find_all('a', href=lambda href: href and 'extralink.ink' in href)

    for a in links_found:
        link = a['href']
        quality = "Unknown Quality"

        # Heuristic: The quality text is usually in the preceding sibling element of the parent paragraph
        # Structure seen:
        # <p>Quality Text</p>
        # <p><a href="...">Link</a></p>
        try:
            parent = a.find_parent()
            if parent:
                prev_sibling = parent.find_previous_sibling()
                if prev_sibling:
                    text = prev_sibling.get_text(strip=True)
                    if text:
                        quality = text
        except Exception:
            pass

        results.append(f"{quality} : {link}")

    return results

if __name__ == "__main__":
    print("ExtraFlix Link Scraper")
    print("----------------------")

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter ExtraFlix URL: ").strip()

    if not url:
        print("No URL provided.")
        sys.exit(1)

    print(f"\nProcessing: {url}...\n")
    links = get_download_links(url)

    if links:
        print(f"Found {len(links)} links:\n")
        for link_info in links:
            print(link_info)
    else:
        print("No links found or an error occurred.")
