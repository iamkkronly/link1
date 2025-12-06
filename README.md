# Movie Scraper & Bypasser Bot

A Telegram bot that scrapes movie download links from various websites and bypasses common link shorteners and file hosts.

## Features

### Web Scraping
Extracts download links from:
*   **HDHub4u**
*   **SkyMoviesHD**
*   **4KHUB**
*   **Filmyfiy**
*   **Vegamovies**
*   **KatMovieHD**
*   **MyMP4Movies**
*   **HBLinks**

### Link Bypassing
Automatically resolves links from:
*   **GadgetsWeb**
*   **HubCloud**
*   **HubDrive**
*   **GoFile**
*   **HubCDN**
*   **HowBlogs**
*   **VPLink**

### Additional Features
*   **Search Engine**: Built-in movie search via `hdhub4u.rehab`.
*   **Poster Fetching**: Retrieves high-quality movie posters from IMDb, Google Images, or The Cat API (as a fallback).
*   **Smart Fallbacks**: If scraping or bypassing fails, the bot attempts alternative strategies.

## Requirements

*   Python 3.8+
*   `python-telegram-bot`
*   `requests`
*   `beautifulsoup4`
*   `lxml`

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Open `bot.py`.
2.  Locate the `TOKEN` variable at the top of the file:
    ```python
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    ```
3.  Replace the placeholder with your actual Telegram Bot Token obtained from BotFather.

## Usage

Run the bot:
```bash
python bot.py
```

### Commands

*   `/start` - Initialize the bot and view instructions.
*   `/p <movie name>` - Fetch and display the poster for a movie.

### Interactions

*   **Send a Link**: Simply paste a supported link (e.g., from HDHub4u, SkyMoviesHD, or a shortener like VPLink) into the chat. The bot will automatically detect the domain, scrape for download links, or bypass the shortener/host to give you the direct link.
*   **Send a Movie Name**: Type a movie name (e.g., "Avengers") to search. The bot will return a list of results with buttons. Click a button to scrape links for that movie.

## Disclaimer

This tool is for educational purposes only. The developers are not responsible for any misuse of this bot.
