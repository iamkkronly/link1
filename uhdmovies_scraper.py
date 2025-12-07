import cloudscraper
from bs4 import BeautifulSoup
import re
import sys

def scrape_uhdmovies(url):
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    content_div = soup.find('div', class_='entry-content')
    if not content_div:
        print("Could not find entry-content div.")
        return []

    download_links = []

    # Strategy: Find all download buttons directly
    # Then for each button, find its parent paragraph, and then look backwards for the title.

    # Search for any element with class starting with 'maxbutton' that is an 'a' tag
    buttons = content_div.find_all('a', class_=lambda c: c and 'maxbutton' in c)

    for button in buttons:
        link = button.get('href')
        if not link:
            continue

        # Find the title
        # The button is usually deep inside: p > span > span > a
        # So we need to traverse up to find the container p, then look at previous siblings

        # Traverse up to find the closest 'p' tag or div that acts as a container
        container = button.find_parent('p')
        if not container:
             container = button.find_parent('div')

        title = "Unknown Quality"
        if container:
            # Look at previous siblings of this container
            # We want to find the nearest previous 'p' that contains strong/bold text

            # Get all previous siblings
            prev_siblings = container.find_previous_siblings()

            for sibling in prev_siblings:
                if sibling.name == 'p':
                    # Check if it has strong text
                    if sibling.find('strong') or sibling.find('b'):
                        text = sibling.get_text(" ", strip=True)
                        # Avoid matching "Download" headings if possible, though sometimes they are the title
                        # Heuristic: titles are usually long or contain year/resolution
                        if text and len(text) > 5:
                            title = text
                            break
                elif sibling.name == 'div' and 'mks_separator' in sibling.get('class', []):
                    # Separator usually comes *before* the title, so if we hit it, keep looking?
                    # Actually, structure is: Separator -> Title -> Button
                    # So when we look backwards from Button: Title -> Separator
                    # So if we hit Title first, we are good.
                    pass
                elif sibling.name == 'h2' or sibling.name == 'h3':
                     # Sometimes title is in h2/h3
                    text = sibling.get_text(" ", strip=True)
                    if text:
                        title = text
                        break

        download_links.append({
            'title': title,
            'link': link
        })

    return download_links

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # url = "https://uhdmovies.stream/download-american-outlaws-2001-dual-audio-hindi-english-1080p-x264-remux-blu-ray-esubs/"
        print("Please provide a UHDMovies URL as an argument.")
        sys.exit(1)

    links = scrape_uhdmovies(url)
    if links:
        print(f"Found {len(links)} links:")
        for link in links:
            print(f"Title: {link['title']}")
            print(f"Link: {link['link']}")
            print("-" * 20)
    else:
        print("No links found.")
