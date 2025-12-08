import re
import time
from playwright.sync_api import sync_playwright

class GPLinksScraper:
    def __init__(self):
        pass

    def scrape(self, url):
        print(f"Scraping: {url}")

        # Max attempts for the whole scraping process
        max_attempts = 5

        for attempt in range(1, max_attempts + 1):
            print(f"\n--- Attempt {attempt}/{max_attempts} ---")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1280, 'height': 800}
                )
                context.set_default_timeout(90000)
                page = context.new_page()

                try:
                    # 1. Initial Navigation
                    print(f"Navigating to {url}")
                    page.goto(url)
                    page.wait_for_load_state('domcontentloaded')
                    print(f"Landed on: {page.url}")

                    # Check for error immediately
                    if "gplinks" in page.url and "error" in page.url:
                        if "not_enough_time" in page.url:
                            print("Error: Not Enough Time. Waiting 20s...")
                            time.sleep(20)
                        else:
                            print(f"Error page detected: {page.url}")

                    # Loop through steps
                    max_steps = 7
                    for step in range(1, max_steps + 1):
                        print(f"--- Step {step} ---")

                        if "gplinks.co" in page.url and "pid=" in page.url:
                             print("Reached final gplinks page.")
                             break

                        # Wait for timer (15s + buffer)
                        print("Waiting for 16s (timer)...")
                        time.sleep(16)

                        # Check VerifyBtn
                        verify_exists = page.evaluate("!!document.getElementById('VerifyBtn')")
                        if verify_exists:
                            print("Verify button exists. Force showing and clicking...")
                            page.evaluate("document.getElementById('VerifyBtn').style.display = 'block';")
                            page.evaluate("document.getElementById('VerifyBtn').style.visibility = 'visible';")
                            page.evaluate("document.getElementById('VerifyBtn').click()")
                            time.sleep(3)
                        else:
                            print("Verify button not found.")

                        # Check NextBtn
                        next_exists = page.evaluate("!!document.getElementById('NextBtn')")
                        if next_exists:
                            print("Next button exists. Force showing and clicking...")
                            page.evaluate("document.getElementById('GoNewxtDiv').style.display = 'block';")
                            page.evaluate("document.getElementById('NextBtn').style.display = 'block';")
                            page.evaluate("document.getElementById('NextBtn').style.visibility = 'visible';")

                            # Wait for navigation
                            try:
                                current_url = page.url
                                with page.expect_navigation(timeout=60000):
                                    page.evaluate("document.getElementById('NextBtn').click()")
                                print(f"Navigated to: {page.url}")
                                page.wait_for_load_state('domcontentloaded')
                            except:
                                print("Navigation timeout/failed on NextBtn.")
                                if page.url != current_url:
                                    print(f"URL changed to: {page.url}")
                                else:
                                    # Stuck?
                                    break
                        else:
                            print("Next button not found.")
                            # Check if we are on final page
                            if "gplinks" in page.url:
                                break

                    # Final Page
                    if "gplinks" in page.url:
                        print("Processing final page...")
                        time.sleep(5)

                        # Submit form #go-link
                        try:
                            print("Submitting form #go-link...")
                            page.evaluate("document.getElementById('go-link').classList.remove('hidden');")

                            try:
                                with page.expect_navigation(timeout=60000):
                                     page.evaluate("document.getElementById('go-link').submit()")

                                print(f"Navigated to: {page.url}")

                                # Check if success
                                if "gplinks" not in page.url and "error" not in page.url:
                                    return page.url

                            except Exception as e:
                                print(f"Form submission navigation failed: {e}")

                        except Exception as e:
                            print(f"Form submission error: {e}")

                    # Fallback Extraction
                    print("Attempting fallback link extraction...")
                    content = page.content()

                    # Find all http links
                    candidates = re.findall(r'href=["\'](http[^"\']+)["\']', content)

                    # Filter candidates
                    valid_candidates = []
                    for link in candidates:
                        # Exclude common junk
                        if any(x in link for x in ["gplinks", "google", "facebook", "twitter", "whatsapp", "telegram", "blogger", "javascript", "#", "wp-includes", "wp-content", "w.org"]):
                            continue
                        # Exclude spam keywords
                        if any(x in link for x in ["porno", "sex", "ads", "click", "play", "game", "bet", "casino"]):
                            continue

                        valid_candidates.append(link)

                    if valid_candidates:
                        # Prefer longest link? or first?
                        # Usually the file hosting link is unique.
                        print(f"Found candidate links: {valid_candidates}")
                        return valid_candidates[0]

                    print("No valid link found.")

                except Exception as e:
                    print(f"Attempt failed: {e}")

                finally:
                    browser.close()

            # Wait before retry
            print("Retrying in 5 seconds...")
            time.sleep(5)

        return None

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Enter GPLinks URL: ")
    if url:
        scraper = GPLinksScraper()
        res = scraper.scrape(url)
        print(f"\nFinal Destination: {res}")
