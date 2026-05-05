#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import urllib.error
import urllib.request


USER_AGENT = "chicago-events-skill/1.0"
DEFAULT_WEEKEND_URL = (
    "https://www.timeout.com/chicago/things-to-do/best-things-to-do-this-weekend-in-chicago"
)
ARTICLE_PATTERN = re.compile(
    r'<article[^>]*class="tile [^"]*"[^>]*>.*?'
    r'<a href="([^"]+)"[^>]*data-testid="tile-link_testID"[^>]*>\s*'
    r'<h3[^>]*data-testid="tile-title_testID"[^>]*>(.*?)</h3>.*?'
    r'<section[^>]*data-testid="tags_testID"[^>]*>(.*?)</section>',
    re.DOTALL,
)
TIME_PATTERN = re.compile(r"<time[^>]*>(.*?)</time>", re.DOTALL)
TAG_TEXT_PATTERN = re.compile(r'<span[^>]*class="[^"]*_text_[^"]*"[^>]*>(.*?)</span>', re.DOTALL)
STRIP_TAGS_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and parse Time Out Chicago editorial guide pages."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_WEEKEND_URL,
        help="Time Out Chicago guide URL to fetch. Defaults to the weekend guide.",
    )
    parser.add_argument(
        "--input-file",
        help="Parse a saved Time Out Chicago HTML file instead of fetching.",
    )
    return parser.parse_args()


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch {url}: {exc}") from exc


def clean_text(raw_html: str) -> str:
    without_tags = STRIP_TAGS_PATTERN.sub(" ", raw_html)
    text = WHITESPACE_PATTERN.sub(" ", html.unescape(without_tags)).strip()
    return re.sub(r"^\d+\.\s*", "", text)


def parse_items(page_html: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for href, raw_title, raw_tags in ARTICLE_PATTERN.findall(page_html):
        title = clean_text(raw_title)
        if not title:
            continue

        url = href if href.startswith("http") else f"https://www.timeout.com{href}"
        if url in seen_urls:
            continue
        seen_urls.add(url)

        tags = [clean_text(tag) for tag in TAG_TEXT_PATTERN.findall(raw_tags)]
        time_match = TIME_PATTERN.search(raw_tags)
        time_text = clean_text(time_match.group(1)) if time_match else ""

        items.append(
            {
                "title": title,
                "url": url,
                "category": ", ".join(tag for tag in tags if tag and tag != title),
                "time": time_text,
            }
        )

    return items


def print_items(source_url: str, items: list[dict[str, str]]) -> None:
    print(f"TIME OUT CHICAGO — {len(items)} items:")
    print(f"Source page: {source_url}")
    print()
    for item in items:
        print(f"• {item['title']}")
        meta = " | ".join(part for part in [item["category"], item["time"]] if part)
        if meta:
            print(f"  {meta}")
        print(f"  {item['url']}")
    print()


def main() -> None:
    args = parse_args()

    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as handle:
            page_html = handle.read()
        source_url = args.url or "(input file)"
    else:
        source_url = args.url
        page_html = fetch_html(source_url)

    print_items(source_url, parse_items(page_html))


if __name__ == "__main__":
    main()
