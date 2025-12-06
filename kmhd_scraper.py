import cloudscraper
from bs4 import BeautifulSoup
import urllib.parse
import re
import sys

def scrape_kmhd_links(url):
    scraper = cloudscraper.create_scraper()

    # 1. Initial Request
    try:
        response = scraper.get(url)
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return []

    final_html = response.text
    base_url = response.url

    # 2. Check for Lock and Unlock if necessary
    if "locked" in base_url:
        print("Page is locked. Attempting to unlock...")
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')
        if form:
            action = form.get('action')
            # The action is usually relative to the current locked page
            post_url = urllib.parse.urljoin(base_url, action)

            headers = {
                'Referer': base_url,
                'Origin': 'https://links.kmhd.net',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            # Extract form inputs if any (usually empty for this site but good practice)
            data = {}
            for input_tag in form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    data[name] = value

            post_response = scraper.post(post_url, data=data, headers=headers)

            if post_response.status_code == 200:
                print("Unlock POST successful.")
                final_html = post_response.text
                # If redirected, we might need to handle it, but usually .text contains the destination content if cloudscraper follows redirects.
                # However, previous debug showed it followed redirect back to file page.
            else:
                print(f"Unlock failed with status {post_response.status_code}")
                return []
        else:
            print("Locked page but no form found.")
            return []

    # 3. Extract Data from SvelteKit Script
    # The data is inside <script>__sveltekit_....resolve(...)</script>
    # or sometimes embedded in the HTML if SSR.
    # Based on previous dump, it's in a script at the end.

    links = []

    # We need to find `upload_links` and `links` configuration.
    # Since the JS object is not valid JSON, we'll use regex.

    # Regex to extract the "upload_links" block
    # upload_links:{key:"value", key:"value", ...}
    upload_links_match = re.search(r'upload_links\s*:\s*{([^}]+)}', final_html)

    # Regex to extract the "links" configuration block
    # links:{key:{...link:"url"...}, ...}
    # This one is nested, so it's harder to capture with a single regex for the whole block if we don't know the depth.
    # But we can look for `key:{...link:"..."` pattern.

    if upload_links_match:
        upload_links_str = upload_links_match.group(1)
        # Parse content: key:"value"
        # e.g. ffast_res:"zunyyivp1x0x"
        res_ids = re.findall(r'([a-zA-Z0-9_]+)\s*:\s*"([^"]+)"', upload_links_str)

        # Now find the base URLs for these keys in the global text or a specific block
        # Pattern: key:{...link:"https://..."...}
        # We can iterate over the found keys and search for their config

        for key, value in res_ids:
            if value == "None" or value == "null":
                continue

            # Search for the link base for this key
            # Pattern example: hubdrive_res:{...,link:"https://hubcloud.ink/drive/",...}
            # We look for `key:{` then followed by `link:"(url)"`
            link_config_pattern = re.compile(rf'{key}\s*:\s*{{[^}}]*link\s*:\s*"([^"]+)"')
            link_config_match = link_config_pattern.search(final_html)

            if link_config_match:
                base_link = link_config_match.group(1)
                full_link = base_link + value
                links.append(full_link)
            else:
                # Fallback or specific handling if pattern differs
                # Some might simply be `link:"..."` if strict match fails
                pass

    return links

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Default for testing
        url = "https://links.kmhd.net/file/Suzu_3cdc5c77"

    print(f"Scraping {url}...")
    results = scrape_kmhd_links(url)
    print("\nFound Links:")
    for link in results:
        print(link)
