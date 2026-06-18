"""
Web Scraper using BeautifulSoup + Requests
Target: https://books.toscrape.com (public scraping sandbox)

Usage:
    python scraper.py --url https://books.toscrape.com/ --pages 5
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import argparse
import time
import logging
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, asdict, field
from typing import Optional

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class ScrapedPage:
    url: str
    title: str
    headings: list[str]
    paragraphs: list[str]
    links: list[str]
    images: list[str]
    metadata: dict


@dataclass
class Book:
    """Structured record for a single book on books.toscrape.com"""
    title: str
    price: str
    availability: str
    rating: int            # 1-5 stars
    category: str
    detail_url: str
    image_url: str


# ── Core scraper ──────────────────────────────────────────────────────────────
class WebScraper:
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    def __init__(
        self,
        delay: float = 1.0,
        timeout: int = 10,
        headers: Optional[dict] = None,
    ):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(headers or self.DEFAULT_HEADERS)

    # ── Fetch ─────────────────────────────────────────────────────────────────
    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        try:
            log.info(f"Fetching: {url}")
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            time.sleep(self.delay)          # polite crawl delay
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:
            log.error(f"Failed to fetch {url}: {e}")
            return None

    # ── Parse ─────────────────────────────────────────────────────────────────
    def parse(self, url: str, soup: BeautifulSoup) -> ScrapedPage:
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        title = soup.title.get_text(strip=True) if soup.title else ""

        headings = [
            h.get_text(strip=True)
            for h in soup.find_all(["h1", "h2", "h3"])
            if h.get_text(strip=True)
        ]

        paragraphs = [
            p.get_text(strip=True)
            for p in soup.find_all("p")
            if p.get_text(strip=True)
        ]

        links = list({
            urljoin(base, a["href"])
            for a in soup.find_all("a", href=True)
        })

        images = list({
            urljoin(base, img.get("src", ""))
            for img in soup.find_all("img", src=True)
        })

        metadata = {
            tag.get("name", tag.get("property", "")): tag.get("content", "")
            for tag in soup.find_all("meta")
            if tag.get("content") and (tag.get("name") or tag.get("property"))
        }

        return ScrapedPage(
            url=url,
            title=title,
            headings=headings,
            paragraphs=paragraphs,
            links=links,
            images=images,
            metadata=metadata,
        )

    # ── Scrape (single URL) ───────────────────────────────────────────────────
    def scrape(self, url: str) -> Optional[ScrapedPage]:
        soup = self.fetch(url)
        if soup is None:
            return None
        return self.parse(url, soup)


# ── Custom extractor (override to target specific data) ───────────────────────
class CustomExtractor(WebScraper):
    """
    Subclass this to add site-specific extraction logic.
    Example below pulls article data from a news-style page.
    """

    def parse(self, url: str, soup: BeautifulSoup) -> ScrapedPage:
        page = super().parse(url, soup)

        # ── Add your custom selectors here ──────────────────────────────────
        # e.g. article_body = soup.select_one("div.article-body")
        # e.g. price        = soup.select_one("span.price")
        # page.metadata["custom_field"] = article_body.get_text() if article_body else ""

        return page


# ── Book extractor: targets https://books.toscrape.com structure ─────────────
RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BookExtractor(WebScraper):
    """
    Extracts structured book data (title, price, rating, availability,
    category) from books.toscrape.com — a public sandbox built for
    scraping practice.
    """

    def extract_books_from_listing(self, url: str, soup: BeautifulSoup) -> list[Book]:
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        books = []

        for pod in soup.select("article.product_pod"):
            title_tag = pod.select_one("h3 a")
            title = title_tag.get("title", "").strip() if title_tag else ""
            detail_url = urljoin(url, title_tag["href"]) if title_tag else ""

            price_tag = pod.select_one("p.price_color")
            price = price_tag.get_text(strip=True) if price_tag else ""

            avail_tag = pod.select_one("p.instock.availability")
            availability = avail_tag.get_text(strip=True) if avail_tag else ""

            rating_tag = pod.select_one("p.star-rating")
            rating = 0
            if rating_tag:
                for cls in rating_tag.get("class", []):
                    if cls in RATING_WORDS:
                        rating = RATING_WORDS[cls]
                        break

            img_tag = pod.select_one("img")
            image_url = urljoin(base, img_tag["src"]) if img_tag else ""

            books.append(Book(
                title=title,
                price=price,
                availability=availability,
                rating=rating,
                category="",          # filled in by caller (listing pages are per-category)
                detail_url=detail_url,
                image_url=image_url,
            ))

        return books

    def get_next_page_url(self, current_url: str, soup: BeautifulSoup) -> Optional[str]:
        next_link = soup.select_one("li.next a")
        if next_link and next_link.get("href"):
            return urljoin(current_url, next_link["href"])
        return None

    def scrape_catalog(self, start_url: str, max_pages: int = 1) -> list[Book]:
        """Scrape books across N paginated listing pages, in page order."""
        all_books: list[Book] = []
        url = start_url
        page_count = 0

        while url and page_count < max_pages:
            soup = self.fetch(url)
            if soup is None:
                break

            page_books = self.extract_books_from_listing(url, soup)
            all_books.extend(page_books)
            page_count += 1
            log.info(f"Page {page_count}: extracted {len(page_books)} books")

            url = self.get_next_page_url(url, soup)

        return all_books


# ── Output helpers ────────────────────────────────────────────────────────────
def save_json(data: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(d) for d in data], f, indent=2, ensure_ascii=False)
    log.info(f"Saved JSON → {path}")


def save_csv(data: list, path: str):
    if not data:
        return
    rows = [asdict(d) for d in data]
    # Flatten lists/dicts to strings for CSV
    for row in rows:
        for k, v in row.items():
            if isinstance(v, list):
                row[k] = " | ".join(v)
            elif isinstance(v, dict):
                row[k] = json.dumps(v)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    log.info(f"Saved CSV  → {path}")


# ── CLI ───────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Scrape structured book data from books.toscrape.com"
    )
    p.add_argument(
        "--url",
        default="https://books.toscrape.com/",
        help="Catalog/listing URL to start from (default: books.toscrape.com home)",
    )
    p.add_argument("--pages", type=int, default=1, help="Number of listing pages to scrape (pagination)")
    p.add_argument("--output", default="books", help="Output file base name (no extension)")
    p.add_argument("--format", choices=["json", "csv", "both"], default="both")
    p.add_argument("--delay", type=float, default=1.0, help="Delay between requests (s)")
    p.add_argument("--timeout", type=int, default=10, help="Request timeout (s)")
    return p


def main():
    args = build_parser().parse_args()

    scraper = BookExtractor(delay=args.delay, timeout=args.timeout)
    books = scraper.scrape_catalog(args.url, max_pages=args.pages)

    if not books:
        log.error("No books extracted. Check the URL or site structure.")
        return

    # Pretty-print summary
    print(f"\n{'-'*50}")
    print(f"  Total books scraped : {len(books)}")
    print(f"  Sample record       :")
    print(f"    Title       : {books[0].title}")
    print(f"    Price       : {books[0].price}")
    print(f"    Availability: {books[0].availability}")
    print(f"    Rating      : {books[0].rating} / 5")
    print(f"{'-'*50}\n")

    if args.format in ("json", "both"):
        save_json(books, f"{args.output}.json")
    if args.format in ("csv", "both"):
        save_csv(books, f"{args.output}.csv")


if __name__ == "__main__":
    main()
