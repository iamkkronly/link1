import logging
import time
import re
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

class MediaCMScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def scrape(self, url):
        self.logger.info(f"MediaCM Scraper: Processing {url}")

        # Ensure URL is valid
        if not url.startswith("http"):
            url = "https://" + url

        links = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox"
                    ]
                )

                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800}
                )

                # Apply stealth
                stealth = Stealth()
                stealth.apply_stealth_sync(context)

                page = context.new_page()

                try:
                    self.logger.info(f"Navigating to {url}...")
                    page.goto(url, timeout=60000)

                    # Wait for potential Cloudflare challenge
                    self.logger.info("Waiting for page load / challenge...")
                    page.wait_for_load_state("networkidle", timeout=30000)

                    # Check if we are stuck on Cloudflare
                    title = page.title()
                    if "Just a moment" in title or "Cloudflare" in title:
                        self.logger.info("Cloudflare challenge detected. Waiting/Attempting bypass...")
                        time.sleep(10)

                        # Handle Turnstile iframe if present
                        for frame in page.frames:
                            if "challenges.cloudflare.com" in frame.url:
                                self.logger.info("Found Cloudflare frame. Attempting to click...")
                                try:
                                    # Try generic click on body or checkbox
                                    frame.click("body", timeout=2000)
                                    checkbox = frame.query_selector("input[type='checkbox']")
                                    if checkbox:
                                        checkbox.click(force=True)
                                except Exception:
                                    pass

                        time.sleep(5)
                        title = page.title()
                        self.logger.info(f"Title after wait: {title}")

                    # Dump content to find links
                    content = page.content()

                    # Strategy 1: Find 'download' links
                    # Strategy 2: Find known file host links (mediafire, mega, etc)
                    # Strategy 3: Just return all external links if it looks like a landing page

                    found_elements = page.query_selector_all("a")
                    self.logger.info(f"Found {len(found_elements)} anchor tags.")

                    unique_links = set()

                    for element in found_elements:
                        href = element.get_attribute("href")
                        text = element.inner_text().strip()

                        if not href or href.startswith("#") or href.startswith("javascript"):
                            continue

                        # Normalize URL
                        full_url = urljoin(page.url, href)

                        # Filter out common junk
                        if any(x in full_url for x in ["facebook.com", "twitter.com", "whatsapp", "telegram", "google.com/search", "policy", "terms", "contact"]):
                            continue

                        # Heuristics for "Download" links
                        is_download = False
                        if "download" in text.lower() or "get link" in text.lower():
                            is_download = True
                        elif any(host in full_url for host in ["mediafire.com", "mega.nz", "drive.google.com", "gofile.io", "pixeldrain.com", "1fichier.com"]):
                            is_download = True
                        elif "file" in full_url.split("/")[-1]: # e.g. /file/ID/name
                             is_download = True

                        if is_download and full_url not in unique_links:
                             links.append({'text': text or "Download", 'link': full_url})
                             unique_links.add(full_url)

                    if not links:
                        # Fallback: if redirected to mediafire, scrape mediafire specific button
                        if "mediafire.com" in page.url:
                            self.logger.info("Redirected to MediaFire. Scraping download button...")
                            download_btn = page.query_selector("a#downloadButton")
                            if download_btn:
                                href = download_btn.get_attribute("href")
                                links.append({'text': "MediaFire Download", 'link': href})

                except Exception as e:
                    self.logger.error(f"Error during page interaction: {e}")
                finally:
                    browser.close()

        except Exception as e:
            self.logger.error(f"Playwright error: {e}")

        return links

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Enter Media.cm URL: ")
    if url:
        scraper = MediaCMScraper()
        results = scraper.scrape(url)
        print("\n--- Results ---")
        for res in results:
            print(f"{res['text']}: {res['link']}")
