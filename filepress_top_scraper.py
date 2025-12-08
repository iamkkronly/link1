import logging
import time
import sys
import random
from urllib.parse import urlparse, urlunparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth
except ImportError:
    logger.error("Playwright or playwright-stealth not installed. Please install them.")
    sys.exit(1)

def scrape_filepress_top(url):
    """
    Scrapes download links from a filepress.top URL using Playwright.
    """

    # Optional: Rewrite URL if known bad domain, but try original first or standard replacement
    parsed = urlparse(url)
    if "filepress.top" in parsed.netloc:
        new_netloc = "filepress.cloud" # Standard domain
        url = urlunparse((parsed.scheme, new_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        logger.info(f"Rewrote URL to: {url}")

    logger.info(f"Scraping FilePress: {url}")
    results = []

    with sync_playwright() as p:
        stealth = Stealth()
        # Note: Set headless=False if running locally and encountering issues with Cloudflare
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )

        context = browser.new_context(
             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        stealth.apply_stealth_sync(context)
        page = context.new_page()

        try:
            # Navigate
            logger.info("Navigating to URL...")
            try:
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                 logger.warning(f"Goto warning: {e}")

            page.wait_for_timeout(5000)

            # Cloudflare Bypass Loop
            start_time = time.time()
            success_detected = False

            while time.time() - start_time < 60:
                if page.is_closed():
                    break

                try:
                    title = page.title()
                    content = page.content()
                except Exception:
                    time.sleep(1)
                    continue

                # Check for success message
                if "Verification successful" in content or "challenge-success-text" in content:
                    if not success_detected:
                        logger.info("Verification successful detected. Waiting for redirect...")
                        success_detected = True

                    page.wait_for_timeout(2000)
                    if "Just a moment..." not in page.title():
                        logger.info("Redirect confirmed (title changed).")
                        break
                    continue

                if "Just a moment..." not in title and "Verifying you are human" not in content and "challenges.cloudflare.com" not in content:
                    logger.info("Cloudflare challenge passed or not present.")
                    break

                if not success_detected:
                    logger.info("Cloudflare detected. Attempting to solve...")

                    # Check frames
                    frames = page.frames
                    clicked = False
                    for frame in frames:
                        try:
                            if "challenges.cloudflare.com" in frame.url:
                                # Try checkbox
                                cb = frame.locator("input[type='checkbox']")
                                if cb.count() > 0:
                                     logger.info("Found checkbox. Clicking...")
                                     cb.locator("..").click(force=True)
                                     clicked = True
                                     page.wait_for_timeout(2000)
                                     break

                                # Wrapper
                                wrapper = frame.locator(".ctp-checkbox-container, .mark")
                                if wrapper.count() > 0:
                                    logger.info("Found checkbox wrapper. Clicking...")
                                    wrapper.first.click(force=True)
                                    clicked = True
                                    page.wait_for_timeout(2000)
                                    break

                                # Fallback: Click center of frame
                                logger.info("Clicking frame body center...")
                                try:
                                    box = frame.bounding_box("body")
                                    if box:
                                        x = box['x'] + box['width'] / 2
                                        y = box['y'] + box['height'] / 2
                                        page.mouse.move(x, y)
                                        page.mouse.down()
                                        page.wait_for_timeout(100)
                                        page.mouse.up()
                                        clicked = True
                                except:
                                    frame.click("body", force=True)
                                    clicked = True

                                page.wait_for_timeout(2000)
                        except Exception as e:
                            pass

                    if not clicked:
                         try:
                             # Main frame fallback
                             page.mouse.move(random.randint(100, 300), random.randint(100, 300))
                             page.click("body", force=True)
                             page.wait_for_timeout(1000)
                         except:
                             pass

            # Wait for final load
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass

            # Function to extract links from current page
            def extract_links():
                found_links = []
                anchors = page.locator("a").all()
                for a in anchors:
                    try:
                        href = a.get_attribute("href")
                        text = a.inner_text().strip()
                        if not href: continue
                        if href.startswith("javascript") or href == "#": continue

                        is_candidate = False

                        # Keywords
                        if any(k in text.lower() for k in ["download", "get link", "480p", "720p", "1080p"]):
                            is_candidate = True

                        # Hosts
                        host_keywords = ["drive.google.com", "mega.nz", "mediafire.com", "gofile.io", "pixeldrain.com"]
                        if any(k in href.lower() for k in host_keywords):
                            is_candidate = True

                        # Fallback for external
                        if href.startswith("http") and "filepress" not in href and "cloudflare.com" not in href:
                             if "facebook" in href or "twitter" in href or "telegram" in href:
                                 pass
                             else:
                                 is_candidate = True

                        if is_candidate:
                            found_links.append({"text": text or "Link", "link": href})

                    except Exception:
                        pass
                return found_links

            # 1. Extract links from initial page
            results = extract_links()

            # 2. If no links, look for "Continue" or "Download" buttons and click them
            if not results:
                 logger.info("No direct links found. checking for buttons to click...")
                 btns = page.locator("button, input[type='submit'], .btn, a.btn").all()
                 clicked_button = False
                 for btn in btns:
                     try:
                         if not btn.is_visible(): continue

                         txt = btn.inner_text().lower() if hasattr(btn, 'inner_text') else ""
                         val = btn.get_attribute("value").lower() if btn.get_attribute("value") else ""

                         if "download" in txt or "continue" in txt or "download" in val or "get link" in txt:
                             logger.info(f"Clicking button: {txt or val}")
                             # We need to handle navigation
                             with page.expect_navigation(timeout=10000):
                                 btn.click()
                             clicked_button = True
                             break
                     except Exception as e:
                         # Navigation might timeout if it's just a DOM change
                         logger.debug(f"Button click error/timeout: {e}")
                         clicked_button = True # Assume we clicked something
                         break

                 if clicked_button:
                     page.wait_for_timeout(3000)
                     try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                     except: pass

                     # Extract links again from new page
                     logger.info("Extracting links from second page...")
                     results = extract_links()

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            browser.close()

    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = input("Enter FilePress URL: ")

    if not target_url:
        print("No URL provided.")
        sys.exit(1)

    links = scrape_filepress_top(target_url)

    print(f"\nFound {len(links)} links:")
    for link in links:
        print(f"{link['text']}: {link['link']}")
