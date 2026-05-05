#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import urllib.error
import urllib.request
from datetime import datetime


USER_AGENT = "chicago-events-skill/1.0"
ARTICLE_PATTERN = re.compile(
    r'<h2[^>]*class="[^"]*module-title[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>',
    re.DOTALL,
)
STRIP_TAGS_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")
MONTH_NAMES = {
    1: "january",
    2: "february",
    3: "march",
    4: "april",
    5: "may",
    6: "june",
    7: "july",
    8: "august",
    9: "september",
    10: "october",
    11: "november",
    12: "december",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and parse Secret Chicago editorial roundup articles."
    )
    parser.add_argument(
        "date",
        nargs="?",
        help="Target date in YYYY-MM-DD format. Used to build the monthly roundup URL.",
    )
    parser.add_argument(
        "--url",
        help="Fetch a specific Secret Chicago editorial page instead of building the monthly roundup URL.",
    )
    parser.add_argument(
        "--input-file",
        help="Parse a saved Secret Chicago HTML file instead of fetching.",
    )
    return parser.parse_args()


def normalize_date(raw_date: str) -> datetime:
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Invalid date {raw_date!r}; expected YYYY-MM-DD.") from exc


def build_monthly_roundup_url(target_date: datetime) -> str:
    month = MONTH_NAMES[target_date.month]
    return f"https://secretchicago.com/things-to-do-in-chicago-{month}-{target_date.year}/"


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch {url}: {exc}") from exc


def clean_text(raw_html: str) -> str:
    without_tags = STRIP_TAGS_PATTERN.sub(" ", raw_html)
    return WHITESPACE_PATTERN.sub(" ", html.unescape(without_tags)).strip()


def parse_roundup_items(page_html: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for url, raw_title in ARTICLE_PATTERN.findall(page_html):
        title = clean_text(raw_title)
        if not title or url in seen_urls:
            continue
        seen_urls.add(url)
        items.append({"title": title, "url": url})

    return items


def print_items(label: str, source_url: str, items: list[dict[str, str]]) -> None:
    print(f"SECRET CHICAGO — {len(items)} items from {label}:")
    print(f"Source page: {source_url}")
    print()
    for item in items:
        print(f"• {item['title']}")
        print(f"  {item['url']}")
    print()


def main() -> None:
    args = parse_args()
    if not args.url and not args.input_file and not args.date:
        raise SystemExit("Provide DATE, --url, or --input-file.")

    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as handle:
            page_html = handle.read()
        source_url = args.url or "(input file)"
        label = "input file"
    else:
        source_url = args.url or build_monthly_roundup_url(normalize_date(args.date))
        page_html = fetch_html(source_url)
        label = "editorial roundup"

    print_items(label, source_url, parse_roundup_items(page_html))


if __name__ == "__main__":
    main()
