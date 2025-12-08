# Scraper Bot

A powerful Telegram bot designed to scrape and bypass download links from various movie and file hosting sites. It supports Cloudflare bypass using Playwright and integrates with sites like FilePress, HubCloud, HubDrive, and more.

## Features

- **Link Bypassing & Scraping:**
  - FilePress (with Cloudflare Turnstile bypass)
  - HubCloud, HubDrive, HubCDN
  - GPLinks
  - SkyMoviesHD, Cinevood, MoviesMod
  - VegaMovies, KatMovieHD, 4kHDHub
  - And many others (see `bot.py` for full list).
- **Search:** Built-in search for movies on supported sites.
- **Posters:** Fetch movie posters via `/p` command.
- **Uptime:** Includes a Flask server to keep the bot alive on services like Render.

## Deployment on Render

This bot is configured to be easily deployed on [Render](https://render.com). Since it uses Playwright, it requires a specific build command to install the necessary browsers.

### Option 1: Blueprints (Recommended)

1.  Fork this repository.
2.  Create a new **Blueprint Instance** on Render.
3.  Connect your forked repository.
4.  Render will automatically detect the `render.yaml` file.
5.  **Important:** You must provide the `TOKEN` environment variable in the Render dashboard during setup or afterwards.

### Option 2: Manual Web Service

1.  Create a new **Web Service** on Render.
2.  Connect your repository.
3.  **Settings:**
    *   **Runtime:** Python 3
    *   **Build Command:** `./render_build.sh`
    *   **Start Command:** `python bot.py`
4.  **Environment Variables:**
    *   Key: `TOKEN`
    *   Value: `YOUR_TELEGRAM_BOT_TOKEN`

**Note:** The `./render_build.sh` script is essential as it installs the Chromium browser required by Playwright to bypass Cloudflare.

## Local Development

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

4.  **Configure Token:**
    *   Open `bot.py` and set the `TOKEN` variable, or better yet, use environment variables.

5.  **Run the bot:**
    ```bash
    python bot.py
    ```

## Requirements

*   Python 3.8+
*   `playwright`
*   `playwright-stealth`
*   `cloudscraper`
*   `python-telegram-bot`
*   `flask` (for uptime)
