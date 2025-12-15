import cloudscraper
from bs4 import BeautifulSoup
import sys
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://1cinevood.fyi"

def get_soup(content):
    try:
        return BeautifulSoup(content, 'lxml')
    except Exception:
        return BeautifulSoup(content, 'html.parser')

def search_movies(movie_name):
    """
    Searches for a movie on 1cinevood.fyi and returns a list of results.
    """
    search_url = f"{BASE_URL}/?s={movie_name}"
    logger.info(f"Searching for: {movie_name} at {search_url}")

    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(search_url)
        response.raise_for_status()
        soup = get_soup(response.content)

        results = []
        articles = soup.find_all('article')

        for article in articles:
            link_tag = article.find('a', href=True)
            if link_tag:
                title = link_tag.get('title') or link_tag.get_text().strip()
                url = link_tag['href']
                if title and url:
                    results.append({'title': title, 'url': url})

        return results

    except Exception as e:
        logger.error(f"Error searching for movie: {e}")
        return []

def get_download_links(url):
    """
    Scrapes download links from a specific movie page.
    """
    logger.info(f"Scraping URL: {url}")
    scraper = cloudscraper.create_scraper()

    try:
        response = scraper.get(url)
        response.raise_for_status()
        soup = get_soup(response.content)

        links_data = []
        content_div = soup.find('div', class_='post-single-content')

        if not content_div:
            logger.warning("Could not find post content div.")
            return []

        current_quality = "Unknown Quality"

        # Helper to process a link tag
        def process_link(link, quality):
            href = link['href']
            text = link.get_text().strip()
            if not text:
                text = link.get('title', '').strip()
            if not text:
                text = "Download Link"

            # Filter
            invalid_patterns = [
                '/1080p/', '/720p/', '/480p/', '/tg', 'facebook.com',
                'twitter.com', 'whatsapp://', 'telegram.me/share',
                'pinterest.com', 'wa.me', 'mailto:', '/how-to-download', '/tgfile'
            ]
            if any(p in href for p in invalid_patterns):
                return

            links_data.append({
                'quality': quality,
                'text': text,
                'link': href
            })

        for elem in content_div.children:
            if not elem.name:
                continue

            if elem.name in ['h5', 'h6']:
                text = elem.get_text().strip()
                if text: current_quality = text

            elif elem.name == 'a' and elem.has_attr('href'):
                process_link(elem, current_quality)

            elif elem.name in ['p', 'div']:
                for link in elem.find_all('a', href=True):
                    process_link(link, current_quality)

        return links_data

    except Exception as e:
        logger.error(f"Error scraping movie page: {e}")
        return []

def main():
    if len(sys.argv) > 1:
        # Check if the argument is a URL or a movie name
        arg = sys.argv[1]
        if arg.startswith("http://") or arg.startswith("https://"):
             # Direct URL scraping
            url = arg
            print(f"Scraping URL: {url}")
            links = get_download_links(url)
            if links:
                print("\n--- Download Links ---\n")
                # Group by quality for display
                grouped_links = {}
                for item in links:
                    q = item['quality']
                    if q not in grouped_links:
                        grouped_links[q] = []
                    grouped_links[q].append(item)

                for q, items in grouped_links.items():
                    print(f"Quality: {q}")
                    for item in items:
                        print(f"  [{item['text']}] -> {item['link']}")
                    print("")
            else:
                print("No download links found on the page.")
            return
        else:
            movie_name = " ".join(sys.argv[1:])
    else:
        # Interactive mode
        user_input = input("Enter movie name or URL: ").strip()
        if user_input.startswith("http://") or user_input.startswith("https://"):
            url = user_input
            print(f"Scraping URL: {url}")
            links = get_download_links(url)
            # ... (display logic duplicated, can be refactored) ...
            if links:
                print("\n--- Download Links ---\n")
                grouped_links = {}
                for item in links:
                    q = item['quality']
                    if q not in grouped_links:
                        grouped_links[q] = []
                    grouped_links[q].append(item)

                for q, items in grouped_links.items():
                    print(f"Quality: {q}")
                    for item in items:
                        print(f"  [{item['text']}] -> {item['link']}")
                    print("")
            else:
                print("No download links found on the page.")
            return
        else:
            movie_name = user_input

    if not movie_name:
        print("Please provide a movie name or URL.")
        return

    print(f"\nSearching for '{movie_name}'...")
    results = search_movies(movie_name)

    if not results:
        print("No results found.")
        return

    print(f"\nFound {len(results)} results:")
    for i, res in enumerate(results):
        print(f"{i + 1}. {res['title']}")

    choice = 0
    if len(results) > 1:
        while True:
            try:
                choice_str = input("\nEnter the number of the movie to scrape (or 0 to exit): ")
                choice = int(choice_str)
                if choice == 0:
                    return
                if 1 <= choice <= len(results):
                    choice -= 1 # 0-indexed
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    selected_movie = results[choice]
    print(f"\nScraping links for: {selected_movie['title']}")
    print(f"URL: {selected_movie['url']}")

    links = get_download_links(selected_movie['url'])

    if links:
        print("\n--- Download Links ---\n")
        # Group by quality for display
        grouped_links = {}
        for item in links:
            q = item['quality']
            if q not in grouped_links:
                grouped_links[q] = []
            grouped_links[q].append(item)

        for q, items in grouped_links.items():
            print(f"Quality: {q}")
            for item in items:
                print(f"  [{item['text']}] -> {item['link']}")
            print("")
    else:
        print("No download links found on the page.")

if __name__ == "__main__":
    main()
