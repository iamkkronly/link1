import logging
import time
import sys
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright
    from playwright_stealth.stealth import Stealth
except ImportError:
    logger.error("Playwright or playwright-stealth not installed. Please install them.")
    sys.exit(1)

def scrape_filepress(url):
    """
    Scrapes download links from a FilePress URL using Playwright with stealth settings
    to bypass Cloudflare/Turnstile.
    """
    logger.info(f"Scraping FilePress: {url}")
    results = []

    with sync_playwright() as p:
        stealth = Stealth()
        # Launch browser with stealth args
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )

        # Create context with realistic user agent
        context = browser.new_context(
             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )

        # Apply stealth to the context
        stealth.apply_stealth_sync(context)

        page = context.new_page()

        try:
            # Navigate to URL
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)

            # --- Cloudflare / Turnstile Handling ---
            if "Just a moment..." in page.title() or "Verifying you are human" in page.content():
                logger.info("Cloudflare challenge detected. Attempting to solve...")

                start_time = time.time()
                # Try for up to 40 seconds to pass the challenge
                while time.time() - start_time < 40:
                    # Check all frames for Turnstile widget
                    frames = page.frames
                    clicked_something = False

                    for frame in frames:
                        if "challenges.cloudflare.com" in frame.url:
                             try:
                                 # 1. Try clicking the checkbox directly
                                 checkbox = frame.locator("input[type='checkbox']")
                                 if checkbox.count() > 0:
                                     logger.info("Found Turnstile checkbox, clicking...")
                                     checkbox.locator("..").click(force=True)
                                     clicked_something = True
                                     break

                                 # 2. Fallback: Click the body of the challenge frame
                                 # This often triggers the verification if it's just 'verify'
                                 logger.info("Clicking Turnstile frame body...")
                                 frame.click("body", force=True)
                                 clicked_something = True
                             except Exception:
                                 pass

                    if clicked_something:
                        page.wait_for_timeout(3000)
                    else:
                        page.wait_for_timeout(1000)

                    # Check if we passed
                    if "Just a moment..." not in page.title():
                        logger.info("Challenge solved (page title changed).")
                        break
                else:
                    logger.warning("Timed out trying to solve Cloudflare challenge.")

            # Wait for content to stabilize
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass

            logger.info(f"Final Page Title: {page.title()}")

            if "Just a moment..." in page.title():
                 logger.error("Failed to bypass Cloudflare.")
                 return []

            # --- Link Extraction ---

            # 1. Look for anchor tags with hrefs
            elements = page.locator("a[href]").all()
            for el in elements:
                try:
                    text = el.inner_text().strip()
                    href = el.get_attribute("href")

                    if not href or href.startswith("javascript") or href == "#" or href == "/":
                        continue

                    text_lower = text.lower()
                    href_lower = href.lower()

                    is_valid = False

                    # Keyword matching
                    download_keywords = ["download", "480p", "720p", "1080p", "2160p", "4k", "get link"]
                    if any(k in text_lower for k in download_keywords):
                        is_valid = True

                    # File host matching
                    host_keywords = ["drive.google.com", "mega.nz", "gofile.io", "1fichier.com", "pixeldrain.com", "mediafire.com"]
                    if any(h in href_lower for h in host_keywords):
                        is_valid = True

                    if is_valid:
                        # Avoid duplicates
                        if not any(r['link'] == href for r in results):
                            results.append({"text": text or "Download Link", "link": href})

                except Exception:
                    pass

            # 2. If no links found via keywords, dump all valid external links
            if not results:
                 logger.info("No explicit download links found via keywords. Dumping all external links...")
                 for el in page.locator("a[href]").all():
                     try:
                         href = el.get_attribute("href")
                         text = el.inner_text().strip()
                         if href and href.startswith("http") and url not in href:
                             if not any(r['link'] == href for r in results):
                                 results.append({"text": text or "Link", "link": href})
                     except:
                         pass

            # 3. Handle 'button' tags that might be download buttons (rare for direct links but possible)
            if not results:
                 for btn in page.locator("button, .btn, .button").all():
                      try:
                          text = btn.inner_text().strip()
                          if "download" in text.lower():
                              # Sometimes buttons use onclick. We might not get a link easily without clicking.
                              # But user asked to "scrape links", not "click and follow".
                              pass
                      except:
                          pass

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            browser.close()

    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        # Default for testing
        target_url = input("Enter FilePress URL: ")
        if not target_url:
            print("No URL provided.")
            sys.exit(1)

    links = scrape_filepress(target_url)

    if links:
        print(f"Found {len(links)} links:")
        for link in links:
            print(f"{link['text']}: {link['link']}")
    else:
        print("No links found.")
