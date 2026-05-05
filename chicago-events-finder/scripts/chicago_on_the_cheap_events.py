#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import urllib.error
import urllib.request
from datetime import datetime


EVENT_PATTERN = re.compile(
    r'<div[^>]*class="[^"]*lotc-v2 row event[^"]*"[^>]*>.*?'
    r'<h3[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>\s*</h3>\s*'
    r'<p[^>]*class="[^"]*meta[^"]*"[^>]*>(.*?)</p>.*?</div>\s*</div>',
    re.DOTALL,
)
TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and parse Chicago on the Cheap event listings."
    )
    parser.add_argument(
        "dates",
        metavar="DATE",
        nargs="+",
        help="Target date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--input-file",
        help=(
            "Parse a saved Chicago on the Cheap HTML file instead of fetching. "
            "Requires exactly one DATE."
        ),
    )
    parser.add_argument(
        "--details-limit",
        type=int,
        default=160,
        help="Maximum number of detail characters to print per event.",
    )
    return parser.parse_args()


def normalize_date(raw_date: str) -> str:
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Invalid date {raw_date!r}; expected YYYY-MM-DD.") from exc


def fetch_html(date: str) -> str:
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%m-%d-%Y")
    url = f"https://chicagoonthecheap.com/events/view-date/{formatted_date}/"
    request = urllib.request.Request(url, headers={"User-Agent": "chicago-events-skill/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch {url}: {exc}") from exc


def collapse_text(raw_html: str) -> str:
    without_tags = TAG_PATTERN.sub(" ", raw_html)
    return WHITESPACE_PATTERN.sub(" ", html.unescape(without_tags)).strip()


def parse_events(page_html: str) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for url, title, details in EVENT_PATTERN.findall(page_html):
        clean_title = html.unescape(title).strip()
        if not clean_title or url in seen_urls:
            continue

        seen_urls.add(url)
        events.append(
            {
                "title": clean_title,
                "url": url,
                "details": collapse_text(details),
            }
        )

    return events


def print_events(
    date: str, events: list[dict[str, str]], details_limit: int, multiple_dates: bool
) -> None:
    if multiple_dates:
        print(f"=== {date} ===")
        print()

    print(f"CHICAGO ON THE CHEAP — {len(events)} events on {date}:")
    print()
    for event in events:
        print(f"• {event['title']}")
        if event["details"]:
            print(f"  {event['details'][:details_limit]}")
        print(f"  {event['url']}")
        print()


def main() -> None:
    args = parse_args()
    dates = [normalize_date(raw_date) for raw_date in args.dates]

    if args.input_file and len(dates) != 1:
        raise SystemExit("--input-file supports exactly one DATE.")

    multiple_dates = len(dates) > 1
    for date in dates:
        if args.input_file:
            with open(args.input_file, "r", encoding="utf-8") as handle:
                page_html = handle.read()
        else:
            page_html = fetch_html(date)

        print_events(date, parse_events(page_html), args.details_limit, multiple_dates)


if __name__ == "__main__":
    main()
