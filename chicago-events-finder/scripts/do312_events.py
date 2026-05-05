#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import urllib.parse
import urllib.error
import urllib.request
from datetime import datetime


USER_AGENT = "chicago-events-skill/1.0"
TITLE_PATTERN = re.compile(
    r'<a href="([^"]+)"[^>]*class="[^"]*ds-listing-event-title[^"]*"[^>]*>'
    r".*?<span[^>]*class=\"[^\"]*ds-listing-event-title-text[^\"]*\"[^>]*>([^<]+)</span>",
    re.DOTALL,
)
DETAIL_TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.DOTALL)
CITY_VENUE_PATTERN = re.compile(r"\s+in\s+(.+?)\s+at\s+(.+?)\s*$")
NEXT_PAGE_PATTERN = re.compile(
    r'<a href="([^"]+)"[^>]*class="[^"]*ds-next-page[^"]*"[^>]*rel="next"',
    re.DOTALL,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and parse Do312 event listings for one or more dates."
    )
    parser.add_argument(
        "dates",
        metavar="DATE",
        nargs="+",
        help="Target date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--input-file",
        help="Parse a saved Do312 HTML file instead of fetching. Requires exactly one DATE.",
    )
    parser.add_argument(
        "--skip-city-check",
        action="store_true",
        help="Skip per-event detail-page verification and return raw listing matches.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Maximum number of paginated listing pages to scan per date.",
    )
    return parser.parse_args()


def normalize_date(raw_date: str) -> str:
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Invalid date {raw_date!r}; expected YYYY-MM-DD.") from exc


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch {url}: {exc}") from exc


def build_page_url(date: str, page: int) -> str:
    base_url = f"https://do312.com/events/{date.replace('-', '/')}"
    if page <= 1:
        return base_url
    return f"{base_url}?{urllib.parse.urlencode({'page': page})}"


def parse_events(page_html: str) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for href, title in TITLE_PATTERN.findall(page_html):
        clean_title = html.unescape(title).strip()
        if not clean_title:
            continue

        url = href if href.startswith("http") else f"https://do312.com{href}"
        if url in seen_urls:
            continue

        seen_urls.add(url)
        events.append({"title": clean_title, "url": url})

    return events


def has_next_page(page_html: str) -> bool:
    return NEXT_PAGE_PATTERN.search(page_html) is not None


def fetch_events(date: str, max_pages: int) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for page in range(1, max_pages + 1):
        page_html = fetch_html(build_page_url(date, page))
        page_events = parse_events(page_html)
        new_events = 0

        for event in page_events:
            if event["url"] in seen_urls:
                continue
            seen_urls.add(event["url"])
            events.append(event)
            new_events += 1

        if not page_events or new_events == 0 or not has_next_page(page_html):
            break

    return events


def fetch_detail_metadata(url: str) -> tuple[str, str] | None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            page_html = response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError:
        return None

    match = DETAIL_TITLE_PATTERN.search(page_html)
    if not match:
        return None

    title_text = html.unescape(match.group(1)).strip()
    city_match = CITY_VENUE_PATTERN.search(title_text)
    if not city_match:
        return None

    city, venue = city_match.groups()
    return city.strip(), venue.strip()


def filter_to_chicago(events: list[dict[str, str]]) -> list[dict[str, str]]:
    filtered: list[dict[str, str]] = []
    seen_titles: set[tuple[str, str]] = set()

    for event in events:
        metadata = fetch_detail_metadata(event["url"])
        if not metadata:
            continue

        city, venue = metadata
        if city != "Chicago":
            continue

        dedupe_key = (event["title"].casefold(), venue.casefold())
        if dedupe_key in seen_titles:
            continue

        seen_titles.add(dedupe_key)
        filtered.append({"title": event["title"], "url": event["url"], "venue": venue})

    return filtered


def print_events(date: str, events: list[dict[str, str]], multiple_dates: bool) -> None:
    if multiple_dates:
        print(f"=== {date} ===")
        print()

    print(f"DO312 — {len(events)} events on {date}:")
    print()
    for event in events:
        print(f"• {event['title']}")
        if event.get("venue"):
            print(f"  Venue: {event['venue']}")
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
            events = parse_events(page_html)
        else:
            events = fetch_events(date, args.max_pages)

        if not args.input_file and not args.skip_city_check:
            events = filter_to_chicago(events)

        print_events(date, events, multiple_dates)


if __name__ == "__main__":
    main()
