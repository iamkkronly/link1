import logging
import time
from playwright.sync_api import sync_playwright

def scrape_oxxfile(url):
    logging.info(f"Scraping OxxFile URL: {url}")
    links = []

    with sync_playwright() as p:
        try:
            # Use stealth arguments to avoid detection
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certifcate-errors",
                    "--ignore-certifcate-errors-spki-list",
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1,
            )

            # Mask webdriver property
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page = context.new_page()

            page.goto(url)
            page.wait_for_timeout(5000)

            # --- GDToT ---
            gdtot_btn = page.locator("button:has-text('Generate GDToT Link')")
            if gdtot_btn.count() > 0:
                max_retries = 3
                for i in range(max_retries):
                    # Check for "fetch failed" error which appears as text
                    if "fetch failed" in page.content():
                        logging.warning("GDToT fetch failed detected. Reloading page...")
                        page.reload()
                        page.wait_for_timeout(5000)
                        gdtot_btn = page.locator("button:has-text('Generate GDToT Link')") # re-locate

                    if gdtot_btn.count() == 0: break

                    logging.info(f"Clicking GDToT button (Attempt {i+1})...")

                    try:
                        with context.expect_page(timeout=10000) as new_page_info:
                            try:
                                gdtot_btn.click()
                            except Exception as e:
                                logging.warning(f"Click failed: {e}")
                                # If click fails, maybe continue to next attempt

                        new_page = new_page_info.value
                        new_page.wait_for_load_state()
                        url_found = new_page.url
                        logging.info(f"Opened: {url_found}")

                        if "alibaba" in url_found or "google" in url_found:
                            logging.info("Ad detected. Closing and retrying...")
                            new_page.close()
                            page.wait_for_timeout(2000)
                            continue # Try clicking again

                        if url_found and url_found != "about:blank":
                            links.append({'text': "GDToT", 'link': url_found})
                            new_page.close()
                            break # Success
                        new_page.close()
                    except Exception as e:
                        logging.warning(f"No new page opened or timeout in attempt {i+1}: {e}")
                        page.wait_for_timeout(2000)
                        continue

            # --- FilePress ---
            filepress_btn = page.locator("button:has-text('Filepress Download')")
            if filepress_btn.count() > 0:
                max_retries = 3
                for i in range(max_retries):
                    logging.info(f"Clicking FilePress button (Attempt {i+1})...")

                    try:
                        with context.expect_page(timeout=10000) as new_page_info:
                            try:
                                filepress_btn.click()
                            except Exception as e:
                                logging.warning(f"Click failed: {e}")

                        new_page = new_page_info.value
                        new_page.wait_for_load_state()
                        url_found = new_page.url
                        logging.info(f"Opened: {url_found}")

                        if "alibaba" in url_found or "google" in url_found:
                             logging.info("Ad detected. Closing and retrying...")
                             new_page.close()
                             page.wait_for_timeout(2000)
                             continue

                        if url_found and url_found != "about:blank":
                            links.append({'text': "FilePress", 'link': url_found})
                            new_page.close()
                            break
                        new_page.close()
                    except Exception as e:
                        logging.warning(f"No new page opened or timeout in attempt {i+1}: {e}")
                        page.wait_for_timeout(2000)
                        continue

            browser.close()

        except Exception as e:
            logging.error(f"OxxFile Scrape Error: {e}")

    return links

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Testing with the URL provided
    found_links = scrape_oxxfile("https://new7.oxxfile.info/s/RKHx64eGzp/")
    print(found_links)
