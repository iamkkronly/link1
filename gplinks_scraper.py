import cloudscraper
import requests
from bs4 import BeautifulSoup
import base64
import time
import re
import random
from urllib.parse import urlparse, parse_qs, unquote, urljoin

class GPLinksScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','mobile': False})
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://gplinks.co/',
        })

    def decode_base64(self, s):
        try:
            return base64.b64decode(s + '=' * (-len(s) % 4)).decode('utf-8')
        except:
            return None

    def scrape(self, url):
        print(f"Scraping: {url}")

        attempt = 0
        max_attempts = 10

        while attempt < max_attempts:
            attempt += 1
            print(f"\n--- Attempt {attempt} ---")

            try:
                self.scraper.cookies.clear()

                resp = self.scraper.get(url, allow_redirects=True)
                landing_url = resp.url

                if "get2.in" in landing_url:
                    query = urlparse(landing_url).query
                    if query:
                        landing_url = unquote(query)
                        resp = self.scraper.get(landing_url, allow_redirects=True)
                        landing_url = resp.url

                print(f"Landing URL: {landing_url}")

                parsed = urlparse(landing_url)
                qs = parse_qs(parsed.query)

                lid = qs.get('lid', [None])[0]
                pid = qs.get('pid', [None])[0]
                vid = qs.get('vid', [None])[0]
                pages_b64 = qs.get('pages', [None])[0]

                if not (lid and pid and vid):
                    print("Could not extract parameters from URL.")
                    return None

                decoded_lid = self.decode_base64(lid)
                decoded_pid = self.decode_base64(pid)
                decoded_pages = self.decode_base64(pages_b64)

                try:
                    pages_num = int(decoded_pages)
                except:
                    pages_num = 3

                print(f"LID: {decoded_lid}, PID: {decoded_pid}, VID: {vid}, Pages: {pages_num}")

                domain = parsed.netloc
                final_target = f"https://gplinks.co/{decoded_lid}/?pid={decoded_pid}&vid={vid}"

                if not self.scraper.cookies.get('lid'):
                    self.scraper.cookies.set('lid', decoded_lid, domain=domain)
                if not self.scraper.cookies.get('pid'):
                    self.scraper.cookies.set('pid', decoded_pid, domain=domain)
                if not self.scraper.cookies.get('vid'):
                    self.scraper.cookies.set('vid', vid, domain=domain)
                if not self.scraper.cookies.get('pages'):
                    self.scraper.cookies.set('pages', str(pages_num), domain=domain)

                self.scraper.cookies.set('step_count', '0', domain=domain)

                current_url = landing_url
                time.sleep(2)

                for step in range(pages_num + 1):
                    self.scraper.cookies.set('step_count', str(step), domain=domain)
                    print(f"Processing Step {step}/{pages_num}")

                    post_url = landing_url

                    if step >= pages_num:
                        next_target = final_target
                    else:
                        next_target = landing_url

                    # Increasing wait time slightly more aggressively
                    sleep_time = 18 + (attempt * 3)
                    print(f"  Waiting {sleep_time}s...")
                    time.sleep(sleep_time)

                    data = {
                        'visitor_id': vid,
                        'next_target': next_target,
                        'ad_impressions': str(step * 5),
                        'step_id': '',
                        'form_name': 'ads-track-data'
                    }

                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Referer': landing_url,
                        'Origin': f"{parsed.scheme}://{parsed.netloc}",
                        'User-Agent': self.scraper.headers['User-Agent'],
                        'X-Requested-With': 'XMLHttpRequest'
                    }

                    print(f"  Posting to {post_url}")
                    resp = self.scraper.post(post_url, data=data, headers=headers, allow_redirects=True)
                    current_url = resp.url

                    if "gplinks.co" in current_url or "gplinks.com" in current_url:
                        if "error" in current_url:
                             print(f"  Got error: {current_url}")
                             if "not_enough_time" in current_url:
                                 break
                             return current_url

                        soup2 = BeautifulSoup(resp.content, 'lxml')
                        meta = soup2.find("meta", attrs={"http-equiv": re.compile("refresh", re.I)})
                        if meta:
                            content = meta.get("content", "")
                            if "url=" in content.lower():
                                 current_url = content.split("url=")[-1].strip()
                                 print(f"  Final Meta Refresh to: {current_url}")
                                 resp = self.scraper.get(current_url, allow_redirects=True)
                                 current_url = resp.url

                        if "gplinks.co" in current_url:
                            print("  Reached gplinks.co final page. Looking for link...")
                            # Short sleep for page load
                            time.sleep(5)

                            soup3 = BeautifulSoup(resp.content, 'lxml')
                            links = soup3.find_all('a', href=True)
                            final_link = None
                            for a in links:
                                txt = a.get_text().strip().lower()
                                if any(x in txt for x in ["get link", "open link", "go to link", "submit"]):
                                    final_link = a['href']
                                    print(f"  Found final link anchor: {final_link}")
                                    break

                            if not final_link:
                                for a in links:
                                    href = a['href']
                                    if "gplinks.co" not in href and "facebook" not in href and "javascript" not in href and "#" not in href:
                                         final_link = href
                                         print(f"  Found candidate link: {final_link}")
                                         break

                            if final_link:
                                print(f"  Visiting final link: {final_link}")
                                time.sleep(3)
                                resp = self.scraper.get(final_link, allow_redirects=True)
                                print(f"  Final Destination Reached: {resp.url}")
                                return resp.url

                            print("  Could not find final link on the page.")
                            return current_url

                        return current_url

            except Exception as e:
                print(f"Error scraping gplinks: {e}")

        return None

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Enter GPLinks URL: ")
    if url:
        scraper = GPLinksScraper()
        res = scraper.scrape(url)
        print(f"\nFinal Destination: {res}")
