# CodeAlpha_Web-scraping

A Python web scraper built with **BeautifulSoup + Requests** that extracts
structured data (title, price, availability, star rating) from
[books.toscrape.com](https://books.toscrape.com) — a public scraping
practice sandbox.

## Setup
```bash
pip install -r requirements.txt
```

## Usage
```bash
python scraper.py --pages 5
```

Scrapes 5 pages (~100 books) and saves results as `books.json` and `books.csv`.

## Features
- Extracts title, price, availability, star rating, and links
- Auto-follows pagination across multiple pages
- Outputs clean JSON and CSV datasets

## Tech Stack
Python, BeautifulSoup4, Requests
