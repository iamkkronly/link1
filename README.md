# Scraper Bot

A powerful Telegram bot designed to scrape and bypass download links from various movie and file hosting sites. It supports Cloudflare bypass using **Playwright** and integrates with sites like FilePress, HubCloud, HubDrive, and more.

## Features

- **Link Bypassing & Scraping:**
  - **GPLinks** (using Playwright for robust bypassing)
  - **VPLink** (handling multiple redirects and form submissions)
  - **FilePress** (with Cloudflare Turnstile bypass)
  - **OxxFile**, **MediaCM**
  - **HubCloud, HubDrive, HubCDN**
  - **SkyMoviesHD, Cinevood, MoviesMod**
  - **VegaMovies, KatMovieHD, 4kHDHub**
  - And many others.
- **Search:** Built-in search for movies on supported sites (Hdhub4u, SkyMoviesHD, Cinevood).
- **Posters:** Fetch movie posters via `/p` command (IMDb, Google Images fallback).
- **Uptime:** Includes a Flask server to keep the bot alive on services like Render.

---

## Deployment on Render (Recommended)

This bot is configured to be easily deployed on [Render](https://render.com). Since it uses Playwright, it requires a specific build environment to install the necessary browsers.

### Prerequisites
- A GitHub account.
- A Render account.
- A Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather)).

### Option 1: Blueprints (Fastest)

1.  **Fork** this repository to your GitHub account.
2.  Log in to Render and click **"New +"**.
3.  Select **"Blueprint Instance"**.
4.  Connect your forked repository.
5.  Render will automatically detect the `render.yaml` file.
6.  **Important:** You will be prompted to enter your **Environment Variables**.
    - `TOKEN`: Paste your Telegram Bot Token here.
7.  Click **Apply**. Render will deploy the bot.

### Option 2: Manual Web Service

1.  **Fork** this repository.
2.  Create a new **Web Service** on Render.
3.  Connect your repository.
4.  **Settings:**
    *   **Name:** `scraper-bot` (or any name you like)
    *   **Runtime:** `Python 3`
    *   **Build Command:** `./render_build.sh`
    *   **Start Command:** `python bot.py`
5.  **Environment Variables:**
    *   Scroll down to "Environment Variables".
    *   Add Key: `TOKEN`
    *   Value: `YOUR_TELEGRAM_BOT_TOKEN`
6.  Click **Create Web Service**.

### Why `./render_build.sh`?
The `./render_build.sh` script is crucial. It does the following:
1.  Upgrades `pip`.
2.  Installs python dependencies from `requirements.txt`.
3.  Installs **Playwright** browsers (`chromium`).

Without this, features like **GPLinks**, **OxxFile**, and **MediaCM** bypass will fail because they rely on a headless browser to execute JavaScript and pass Cloudflare checks.

---

## Local Development / VPS

If you want to run this on your own machine or a VPS:

1.  **Clone the repo:**
    ```bash
    git clone <repo-url>
    cd <repo-folder>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright browsers:**
    ```bash
    playwright install chromium
    ```
    *Note: You might need to run `playwright install-deps` on some Linux distributions.*

4.  **Configure Token:**
    *   Set the `TOKEN` environment variable, or edit `bot.py` (not recommended for public repos).

5.  **Run the bot:**
    ```bash
    python bot.py
    ```

## Troubleshooting

-   **Playwright Errors:** If you see "Playwright not installed" or browser errors, ensure the build command was run correctly. On Render, checking the logs will usually show if `playwright install` succeeded.
-   **VPLink/GPLinks Failures:** These sites change their logic frequently. If a bypass stops working, the specific scraper script (`gplinks_scraper.py` or `vplink_bypass.py`) might need updating.
-   **Cloudflare Blocks:** Some sites (like VegaMovies) aggressively block bot IPs (including Render's). The bot handles some of these, but 403 errors are sometimes unavoidable without premium proxies.

## Credits

-   **Playwright** for the browser automation engine.
-   **Cloudscraper** for handling basic Cloudflare challenges.
