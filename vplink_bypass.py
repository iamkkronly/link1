import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_soup(content):
    """Helper to parse HTML with fallback."""
    try:
        return BeautifulSoup(content, 'lxml')
    except:
        return BeautifulSoup(content, 'html.parser')

def bypass_vplink(url):
    """
    Bypasses vplink.in and similar shorteners.
    Handles Meta Refresh, Window Location, Forms, and 'Next' buttons.
    """
    logger.info(f"Bypassing VPLink: {url}")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
        "Connection": "keep-alive",
    }

    session = requests.Session()
    session.headers.update(headers)

    current_url = url
    max_steps = 15 # Covers the 6-8 page requirement + buffer
    step = 0

    # Common destination domains to stop at
    final_domains = [
        'hubcloud', 'hubdrive', 'hubcdn', 'gofile.io',
        'drive.google', 'mega.nz', 'pixeldrain', 'mediafire'
    ]

    while step < max_steps:
        step += 1
        try:
            logger.info(f"Step {step}: Visiting {current_url}")

            # Initial GET
            response = session.get(current_url, allow_redirects=True, timeout=20)

            # Handle potential VPN/Proxy block page
            if "VPN Detected" in response.text or "Turn off VPN" in response.text:
                logger.warning("VPN/Proxy detected by the site. This script may fail if not run from a residential IP.")
                # We can't really bypass this programmatically without a proxy, but we continue in case it's a false positive

            current_url = response.url # Update URL if redirected by requests
            logger.info(f"  Current URL: {current_url}")

            # Check if we reached a final destination
            domain = urlparse(current_url).netloc
            if any(x in domain for x in final_domains):
                logger.info(f"  Final destination reached: {current_url}")
                return current_url

            # If we are redirected to a completely different domain that isn't vplink, it might be the end or an ad
            # But vplink usually redirects to other vplink-like pages.

            soup = get_soup(response.content)

            # --- Strategy 1: Meta Refresh ---
            meta = soup.find("meta", attrs={"http-equiv": re.compile("refresh", re.I)})
            if meta:
                content = meta.get("content", "")
                if "url=" in content.lower():
                    next_url = content.split("url=")[-1].strip()
                    # Remove quotes if present
                    next_url = next_url.strip("'\"")
                    current_url = urljoin(current_url, next_url)
                    logger.info(f"  Found Meta Refresh to {current_url}")
                    time.sleep(2) # Wait a bit for "refresh"
                    continue

            # --- Strategy 2: JavaScript Redirects ---
            scripts = soup.find_all('script')
            js_found = False
            for script in scripts:
                if script.string:
                    # window.location = "..."
                    match = re.search(r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']', script.string)
                    if not match:
                        # location.replace("...")
                        match = re.search(r'location\.replace\s*\(\s*["\']([^"\']+)["\']\s*\)', script.string)
                    if not match:
                         # setTimeout(function() { window.location = "..." }, ...)
                         match = re.search(r'setTimeout\s*\(\s*function\s*\(\)\s*\{\s*window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']', script.string)

                    if match:
                        next_url = match.group(1)
                        current_url = urljoin(current_url, next_url)
                        logger.info(f"  Found JS Redirect to {current_url}")
                        js_found = True
                        break
            if js_found:
                time.sleep(3) # Wait for JS timer
                continue

            # --- Strategy 3: Forms ---
            # Many link shorteners use a form to POST data to the next step
            # Look for forms that look like "continue" or "go"
            forms = soup.find_all('form')
            valid_form = None

            for form in forms:
                action = form.get('action', '')
                f_id = form.get('id', '').lower()
                f_class = " ".join(form.get('class', [])).lower()

                # Heuristics for a valid form
                if "landing" in f_id or "submission" in f_id or "go-link" in f_id or "getlink" in action:
                    valid_form = form
                    break

                # Check for buttons inside
                btn = form.find('button', type='submit') or form.find('input', type='submit')
                if btn:
                    btn_text = ""
                    if btn.name == 'input': btn_text = btn.get('value', '').lower()
                    else: btn_text = btn.get_text().strip().lower()

                    if any(x in btn_text for x in ['continue', 'next', 'get link', 'verify', 'go']):
                        valid_form = form
                        break

            if valid_form:
                action = valid_form.get('action')
                if action:
                    next_url = urljoin(current_url, action)
                    data = {}
                    for input_tag in valid_form.find_all('input'):
                        name = input_tag.get('name')
                        value = input_tag.get('value', '')
                        if name:
                            data[name] = value

                    logger.info(f"  Submitting form to {next_url}")
                    # Respect method
                    method = valid_form.get('method', 'post').lower()
                    if method == 'get':
                        resp = session.get(next_url, params=data, allow_redirects=True, timeout=20)
                    else:
                        resp = session.post(next_url, data=data, allow_redirects=True, timeout=20)

                    current_url = resp.url
                    time.sleep(2)
                    continue

            # --- Strategy 4: "Next" / "Continue" / "Get Link" Buttons (Anchors) ---
            # This is critical for the "click next page" requirement
            next_link = None

            # Specific ID/Class check
            special_buttons = soup.select('a#getlink, a.get-link, a#continue, a.continue, a#btn-main')
            if special_buttons:
                next_link = special_buttons[0]['href']

            if not next_link:
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    text = a.get_text().strip().lower()

                    # Filter out nav links or common unrelated links
                    if href.startswith('#') or 'facebook' in href or 'twitter' in href or 'telegram' in href:
                        continue

                    if any(x in text for x in ['click here to continue', 'next page', 'get link', 'continue', 'verify', 'click to scan']):
                        next_link = href
                        logger.info(f"  Found link text '{text}'")
                        break

                    # Sometimes the link is an image button
                    img = a.find('img')
                    if img:
                        alt = img.get('alt', '').lower()
                        src = img.get('src', '').lower()
                        if 'continue' in alt or 'next' in alt or 'getlink' in src:
                            next_link = href
                            break

            if next_link:
                current_url = urljoin(current_url, next_link)
                logger.info(f"  Following link to {current_url}")
                time.sleep(3) # Wait between clicks
                continue

            # --- End of strategies ---
            logger.warning("  No obvious next step found. Dumping page text preview:")
            logger.warning(soup.get_text()[:500].strip().replace('\n', ' '))
            break

        except Exception as e:
            logger.error(f"Error on step {step}: {e}")
            break

    return current_url

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Enter vplink URL: ")
    if url:
        final = bypass_vplink(url)
        print(f"\nFinal Result: {final}")
