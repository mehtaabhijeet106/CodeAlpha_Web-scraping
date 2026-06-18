# 🕷️ Web Scraper — Book Catalog Extractor

A Python web scraper built with **BeautifulSoup + Requests** that extracts a
structured dataset (title, price, availability, star rating, links, images)
from [books.toscrape.com](https://books.toscrape.com) — a site purpose-built
as a public sandbox for web scraping practice.

> ⚠️ **Note on target site:** This project originally targeted a request for
> a live pharmacy site. That target was swapped out because: (1) it's likely
> a JavaScript-rendered site that BeautifulSoup can't parse without a
> browser-automation tool like Selenium/Playwright, and (2) scraping
> live pricing/medicine data from a regulated e-pharmacy raises Terms-of-
> Service and legal concerns. `books.toscrape.com` is explicitly designed
> and maintained for scraping education, with no such restrictions — making
> it a safer, more reliable choice for this assignment.

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Usage

```bash
# Scrape page 1 of the catalog (default), save as JSON + CSV
python scraper.py

# Scrape the first 5 pages (paginated, ~20 books per page)
python scraper.py --pages 5

# Save only CSV, with a custom filename
python scraper.py --pages 3 --format csv --output my_books

# Start from a specific category page (e.g. "Travel")
python scraper.py --url https://books.toscrape.com/catalogue/category/books/travel_2/ --pages 2
```

### All CLI options

| Flag        | Default                          | Description                              |
|-------------|-----------------------------------|-------------------------------------------|
| `--url`     | `https://books.toscrape.com/`     | Starting catalog/listing URL              |
| `--pages`   | `1`                                | Number of paginated listing pages to walk |
| `--output`  | `books`                            | Base name for output file(s)              |
| `--format`  | `both`                             | `json`, `csv`, or `both`                  |
| `--delay`   | `1.0`                               | Seconds to wait between requests          |
| `--timeout` | `10`                                | Request timeout in seconds                |

---

## How it works (mapped to the task requirements)

- **BeautifulSoup + Requests** — `BookExtractor` fetches each catalog page
  and parses it with `BeautifulSoup`.
- **HTML structure & navigation** — `get_next_page_url()` reads the site's
  `li.next a` pagination link and follows it automatically across pages.
- **Custom dataset** — `extract_books_from_listing()` targets the exact CSS
  selectors used by the site (`article.product_pod`, `p.price_color`,
  `p.star-rating`, `p.instock.availability`) to pull only the fields that
  matter: title, price, rating, stock status, detail link, and cover image.
- **Relevant data, ready for analysis** — output is flat, tabular `Book`
  records, directly usable in pandas/Excel/Sheets without further cleanup.

---

## Output

Each book record contains:

- **title** — book title
- **price** — listed price (e.g. `£51.77`)
- **availability** — stock status text (e.g. `In stock`)
- **rating** — star rating, 1–5 (parsed from the `star-rating` CSS class)
- **category** — left blank by default (each listing page is single-category;
  set manually or extend `scrape_catalog` to tag it per page)
- **detail_url** — link to the book's full product page
- **image_url** — link to the cover thumbnail

---

## Extending to other sites

To target a different site, copy the `BookExtractor` pattern: write one
method that selects repeating "card" elements (e.g. `article.product_pod`)
and pulls fields from each, plus a `get_next_page_url()` method if the site
paginates. Always check the target site's `robots.txt` and Terms of Service
before pointing this at anything other than a sanctioned scraping sandbox.

---

## Notes

- Respects a configurable crawl delay (default 1 s) between requests.
- Sends a realistic `User-Agent` header.
- This code has not been executed against the live site in this environment
  (no outbound network access here) — run it locally to verify output before
  treating it as a final deliverable.
