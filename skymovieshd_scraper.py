import requests
from bs4 import BeautifulSoup
import sys
import urllib.parse
import time

# Use a session to persist parameters/headers if needed
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
})

BASE_URL = "https://skymovieshd.mba"

def search_movies(movie_name):
    """Searches for a movie and returns a list of (title, url) tuples."""
    print(f"Searching for '{movie_name}'...")
    search_url = f"{BASE_URL}/search.php?search={urllib.parse.quote(movie_name)}&cat=All"
    try:
        response = session.get(search_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error searching for movie: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    results = []

    # Based on the HTML provided: <div class='L' align='left'><b><a href='/movie/...'>...</a></b></div>
    # There are also other links in div.L, so we need to filter carefully.
    # The movie links start with /movie/

    for div in soup.find_all('div', class_='L'):
        a_tag = div.find('a')
        if a_tag and a_tag.get('href', '').startswith('/movie/'):
            title = a_tag.get_text(strip=True)
            link = a_tag['href']
            if not link.startswith('http'):
                link = BASE_URL + link
            results.append((title, link))

    return results

def scrape_download_links(movie_url):
    """Scrapes download links from a specific movie page."""
    print(f"Scraping links from: {movie_url}")
    try:
        response = session.get(movie_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching movie page: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    download_links = []

    # Based on the HTML provided:
    # <div class='Bolly'>
    # <a href='https://howblogs.xyz/464088'>Google Drive Direct Links</a><br/>
    # ...
    # </div>

    bolly_div = soup.find('div', class_='Bolly')
    if bolly_div:
        for a_tag in bolly_div.find_all('a'):
            href = a_tag.get('href')
            text = a_tag.get_text(strip=True)
            if href:
                download_links.append((text, href))

    return download_links

def main():
    if len(sys.argv) > 1:
        movie_name = " ".join(sys.argv[1:])
    else:
        movie_name = input("Enter movie name: ")

    if not movie_name:
        print("Please provide a movie name.")
        return

    results = search_movies(movie_name)

    if not results:
        print("No movies found.")
        return

    print(f"Found {len(results)} movies.")

    all_links = []

    for title, link in results:
        print(f"\nProcessing: {title}")
        links = scrape_download_links(link)
        if links:
            for link_text, download_link in links:
                print(f"  - {link_text}: {download_link}")
                all_links.append(f"{title} | {link_text}: {download_link}")
        else:
            print("  No download links found.")

        # Be polite to the server
        time.sleep(1)

    print("\n" + "="*50)
    print("Summary of all scraped links:")
    for item in all_links:
        print(item)

if __name__ == "__main__":
    main()
