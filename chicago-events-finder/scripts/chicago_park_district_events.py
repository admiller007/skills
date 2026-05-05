#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime


BASE_URL = "https://www.chicagoparkdistrict.com"
USER_AGENT = "chicago-events-skill/1.0"
MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
ROW_PATTERN = re.compile(
    r'<div class="views-row">\s*<div class="node--type-event node--view-mode-card">(.*?)</div>\s*</div>',
    re.DOTALL,
)
DATE_PATTERN = re.compile(r'<div class="event--date[^"]*">\s*([A-Za-z]{3})\s*</br>\s*(\d+)', re.DOTALL)
TITLE_PATTERN = re.compile(
    r'<h3 class="event--title">\s*<a href="([^"]+)"[^>]*>(.*?)</a>\s*</h3>',
    re.DOTALL,
)
LOCATION_PATTERN = re.compile(
    r'<div class="field-with-icon event--location">.*?<a [^>]*>(.*?)</a>',
    re.DOTALL,
)
TIME_PATTERN = re.compile(
    r'<div class="field-with-icon event--duration">\s*(.*?)\s*</div>',
    re.DOTALL,
)
DATE_TIME_DETAIL_PATTERN = re.compile(
    r'<div class="field event--date-time">.*?<div class="field__item">\s*(.*?)\s*</div>',
    re.DOTALL,
)
PARK_NAME_PATTERN = re.compile(
    r'<div class="field__label">Location</div>.*?<a href="[^"]+"><span[^>]*>(.*?)</span>',
    re.DOTALL,
)
ADDRESS_PATTERN = re.compile(
    r'class="address"[^>]*>\s*(.*?)\s*</div>',
    re.DOTALL,
)
FEE_PATTERN = re.compile(
    r'<div class="field__label">Event Fee</div>\s*<div[^>]*class="field__item">(.*?)</div>',
    re.DOTALL,
)
AGE_PATTERN = re.compile(
    r'<div class="field__label">Age Range</div>\s*<div class="field__item">(.*?)</div>',
    re.DOTALL,
)
CATEGORY_PATTERN = re.compile(
    r'<div class="field__label">Categories:</div>\s*(.*?)\s*</div>',
    re.DOTALL,
)
DESCRIPTION_PATTERN = re.compile(
    r'<div class="event--description">.*?<div class="clearfix text-formatted [^"]* field__item">(.*?)</div>',
    re.DOTALL,
)
TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and parse Chicago Park District events for one or more dates."
    )
    parser.add_argument(
        "dates",
        metavar="DATE",
        nargs="+",
        help="Target date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--input-file",
        help="Parse a saved Park District list HTML file instead of fetching. Requires exactly one DATE.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Maximum list pages to scan before stopping.",
    )
    parser.add_argument(
        "--skip-details",
        action="store_true",
        help="Skip per-event detail fetches.",
    )
    parser.add_argument(
        "--description-limit",
        type=int,
        default=160,
        help="Maximum description characters to print per event.",
    )
    return parser.parse_args()


def normalize_date(raw_date: str) -> str:
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Invalid date {raw_date!r}; expected YYYY-MM-DD.") from exc


def collapse_text(raw_html: str) -> str:
    without_tags = TAG_PATTERN.sub(" ", raw_html or "")
    return WHITESPACE_PATTERN.sub(" ", html.unescape(without_tags)).strip()


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch {url}: {exc}") from exc


def list_page_url(date: str, page: int) -> str:
    query = {"field_date_value": date}
    if page:
        query["page"] = page
    return f"{BASE_URL}/events?{urllib.parse.urlencode(query)}"


def parse_row_date(month_text: str, day_text: str, target_year: int) -> str:
    month_number = MONTHS.get(month_text.lower())
    if month_number is None:
        raise ValueError(f"Unknown month abbreviation: {month_text!r}")
    return datetime(target_year, month_number, int(day_text)).strftime("%Y-%m-%d")


def parse_list_events(page_html: str, target_year: int) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for block in ROW_PATTERN.findall(page_html):
        date_match = DATE_PATTERN.search(block)
        title_match = TITLE_PATTERN.search(block)
        location_match = LOCATION_PATTERN.search(block)
        time_match = TIME_PATTERN.search(block)

        if not date_match or not title_match:
            continue

        href, title = title_match.groups()
        url = href if href.startswith("http") else f"{BASE_URL}{href}"
        if url in seen_urls:
            continue

        seen_urls.add(url)
        events.append(
            {
                "date": parse_row_date(date_match.group(1), date_match.group(2), target_year),
                "title": collapse_text(title),
                "url": url,
                "address": collapse_text(location_match.group(1)) if location_match else "",
                "time": collapse_text(time_match.group(1)) if time_match else "",
            }
        )

    return events


def parse_detail_fields(page_html: str) -> dict[str, str]:
    date_time = collapse_text(match.group(1)) if (match := DATE_TIME_DETAIL_PATTERN.search(page_html)) else ""
    park_name = collapse_text(match.group(1)) if (match := PARK_NAME_PATTERN.search(page_html)) else ""
    address = collapse_text(match.group(1)) if (match := ADDRESS_PATTERN.search(page_html)) else ""
    fee = collapse_text(match.group(1)) if (match := FEE_PATTERN.search(page_html)) else ""
    age_range = collapse_text(match.group(1)) if (match := AGE_PATTERN.search(page_html)) else ""
    categories = collapse_text(match.group(1)) if (match := CATEGORY_PATTERN.search(page_html)) else ""
    description = collapse_text(match.group(1)) if (match := DESCRIPTION_PATTERN.search(page_html)) else ""
    return {
        "date_time": date_time,
        "park_name": park_name,
        "address": address,
        "fee": fee,
        "age_range": age_range,
        "categories": categories,
        "description": description,
    }


def fetch_events_for_dates(
    dates: list[str],
    max_pages: int,
    *,
    skip_details: bool,
) -> dict[str, list[dict[str, str]]]:
    target_year = datetime.strptime(dates[0], "%Y-%m-%d").year
    grouped = {date: [] for date in dates}
    for date in dates:
        added_urls: set[str] = set()
        for page in range(max_pages):
            page_html = fetch_html(list_page_url(date, page))
            page_events = parse_list_events(page_html, target_year)
            if not page_events:
                break

            date_matches = [event for event in page_events if event["date"] == date]
            if not date_matches:
                break

            for event in date_matches:
                if event["url"] in added_urls:
                    continue

                full_event = dict(event)
                if not skip_details:
                    detail_html = fetch_html(event["url"])
                    full_event.update(parse_detail_fields(detail_html))
                grouped[date].append(full_event)
                added_urls.add(event["url"])

    return grouped


def print_events(
    date: str,
    events: list[dict[str, str]],
    description_limit: int,
    multiple_dates: bool,
) -> None:
    if multiple_dates:
        print(f"=== {date} ===")
        print()

    print(f"CHICAGO PARK DISTRICT - {len(events)} events on {date}:")
    print()
    for event in events:
        print(f"• {event['title']}")
        if event.get("park_name"):
            print(f"  Park: {event['park_name']}")
        if event.get("date_time"):
            print(f"  {event['date_time']}")
        elif event.get("time"):
            print(f"  Time: {event['time']}")
        if event.get("address"):
            print(f"  {event['address']}")
        if event.get("fee"):
            print(f"  Fee: {event['fee']}")
        if event.get("age_range"):
            print(f"  Ages: {event['age_range']}")
        if event.get("categories"):
            print(f"  Category: {event['categories']}")
        if event.get("description"):
            print(f"  {event['description'][:description_limit]}")
        print(f"  {event['url']}")
        print()


def main() -> None:
    args = parse_args()
    dates = [normalize_date(raw_date) for raw_date in args.dates]

    if args.input_file and len(dates) != 1:
        raise SystemExit("--input-file supports exactly one DATE.")

    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as handle:
            page_html = handle.read()
        target_year = datetime.strptime(dates[0], "%Y-%m-%d").year
        grouped = {date: [] for date in dates}
        for event in parse_list_events(page_html, target_year):
            if event["date"] in grouped:
                grouped[event["date"]].append(event)
    else:
        grouped = fetch_events_for_dates(
            dates,
            args.max_pages,
            skip_details=args.skip_details,
        )

    multiple_dates = len(dates) > 1
    for date in dates:
        print_events(date, grouped[date], args.description_limit, multiple_dates)


if __name__ == "__main__":
    main()
