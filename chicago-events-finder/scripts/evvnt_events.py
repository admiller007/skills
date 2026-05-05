#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime


PUBLISHERS = {
    "chicago-reader": {
        "label": "CHICAGO READER",
        "publisher_id": "9072",
    },
    "your-chicago-guide": {
        "label": "YOUR CHICAGO GUIDE",
        "publisher_id": "7780",
    },
}
WHITESPACE_PATTERN = re.compile(r"\s+")
TAG_PATTERN = re.compile(r"<[^>]+>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and parse evvnt event feeds for supported Chicago publishers."
    )
    parser.add_argument(
        "publisher",
        choices=sorted(PUBLISHERS),
        help="Publisher slug.",
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
            "Parse a saved evvnt JSON file instead of fetching. "
            "Requires exactly one DATE."
        ),
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=25,
        help="Maximum pages to scan for evvnt pagination and fallback lookups.",
    )
    parser.add_argument(
        "--description-limit",
        type=int,
        default=120,
        help="Maximum description characters to print for Chicago Reader events.",
    )
    return parser.parse_args()


def normalize_date(raw_date: str) -> str:
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Invalid date {raw_date!r}; expected YYYY-MM-DD.") from exc


def clean_text(raw_text: str) -> str:
    without_tags = TAG_PATTERN.sub(" ", raw_text or "")
    return WHITESPACE_PATTERN.sub(" ", html.unescape(without_tags)).strip()


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "chicago-events-skill/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch {url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse JSON from {url}: {exc}") from exc


def dedupe_events(events: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    for event in events:
        venue = event.get("venue") or {}
        venue_name = venue.get("name", "") if isinstance(venue, dict) else ""
        key = (
            clean_text(event.get("title") or ""),
            (event.get("start_date") or "")[:10],
            clean_text(venue_name),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)

    return deduped


def build_page_signature(events: list[dict]) -> tuple[str, str, str, str]:
    first = events[0]
    last = events[-1]
    return (
        (first.get("start_date") or "")[:10],
        clean_text(first.get("title") or ""),
        (last.get("start_date") or "")[:10],
        clean_text(last.get("title") or ""),
    )


def scan_paged_events(publisher_id: str, max_pages: int) -> tuple[list[dict], list[str]]:
    all_events: list[dict] = []
    seen_signatures: set[tuple[str, str, str, str]] = set()
    seen_dates: list[str] = []

    for page in range(1, max_pages + 1):
        query = urllib.parse.urlencode(
            {
                "publisher_id": publisher_id,
                "limit": 30,
                "page": page,
            }
        )
        url = f"https://discovery.evvnt.com/api/events?{query}"
        data = fetch_json(url)
        events = data.get("events", [])
        if not events:
            break

        signature = build_page_signature(events)
        if signature in seen_signatures:
            break
        seen_signatures.add(signature)

        all_events.extend(events)
        seen_dates.extend((event.get("start_date") or "")[:10] for event in events if event.get("start_date"))

    return dedupe_events(all_events), sorted(set(seen_dates))


def fetch_reader_events(target_dates: list[str], max_pages: int) -> tuple[list[dict], list[str]]:
    del target_dates
    return scan_paged_events(PUBLISHERS["chicago-reader"]["publisher_id"], max_pages)


def fetch_ycg_events(target_dates: list[str], max_pages: int) -> tuple[list[dict], list[str]]:
    query = urllib.parse.urlencode(
        {
            "publisher_id": PUBLISHERS["your-chicago-guide"]["publisher_id"],
            "from": min(target_dates),
            "to": max(target_dates),
            "limit": 30,
        }
    )
    url = f"https://discovery.evvnt.com/api/events?{query}"
    data = fetch_json(url)
    events = dedupe_events(data.get("events", []))
    seen_dates = sorted(
        {
            (event.get("start_date") or "")[:10]
            for event in events
            if event.get("start_date")
        }
    )

    requested_dates = set(target_dates)
    if any((event.get("start_date") or "")[:10] in requested_dates for event in events):
        return events, seen_dates

    fallback_events, fallback_dates = scan_paged_events(
        PUBLISHERS["your-chicago-guide"]["publisher_id"], max_pages
    )
    return fallback_events, fallback_dates


def filter_events(events: list[dict], target_dates: set[str]) -> dict[str, list[dict]]:
    grouped = {date: [] for date in sorted(target_dates)}
    for event in events:
        start_date = (event.get("start_date") or "")[:10]
        if start_date in grouped:
            grouped[start_date].append(event)
    return grouped


def build_availability_note(
    label: str, date: str, events: list[dict], seen_dates: list[str]
) -> str | None:
    if events or not seen_dates:
        return None

    earliest = min(seen_dates)
    latest = max(seen_dates)
    if date < earliest:
        return (
            f"{label} upstream no longer serves {date}; earliest date seen in the scan "
            f"was {earliest}."
        )
    if date > latest:
        return (
            f"{label} scan only reached through {latest}; rerun with a higher --max-pages "
            f"value for {date}."
        )
    return f"{label} did not return {date} in the scanned pages."


def print_reader_events(
    label: str,
    date: str,
    events: list[dict],
    description_limit: int,
    multiple_dates: bool,
    note: str | None = None,
) -> None:
    if multiple_dates:
        print(f"=== {date} ===")
        print()

    print(f"{label} — {len(events)} events on {date}:")
    if note:
        print(f"WARNING: {note}")
    print()
    for event in events:
        title = clean_text(event.get("title") or "?")
        venue = event.get("venue") or {}
        venue_name = clean_text(venue.get("name") or "") if isinstance(venue, dict) else ""
        url = event.get("url") or ""
        description = clean_text(event.get("description") or "")

        print(f"• {title}")
        if venue_name:
            print(f"  Venue: {venue_name}")
        if url:
            print(f"  {url}")
        if description:
            print(f"  {description[:description_limit]}")
        print()


def print_ycg_events(
    label: str, date: str, events: list[dict], multiple_dates: bool, note: str | None = None
) -> None:
    if multiple_dates:
        print(f"=== {date} ===")
        print()

    print(f"{label} — {len(events)} events on {date}:")
    if note:
        print(f"WARNING: {note}")
    print()
    for event in events:
        title = clean_text(event.get("title") or "?")
        start = event.get("start_date") or ""
        venue = event.get("venue") or {}
        venue_name = clean_text(venue.get("name") or "") if isinstance(venue, dict) else ""
        url = event.get("url") or ""

        print(f"• {title}")
        print(f"  {start} | {venue_name}")
        if url:
            print(f"  {url}")
        print()


def main() -> None:
    args = parse_args()
    publisher = PUBLISHERS[args.publisher]
    dates = [normalize_date(raw_date) for raw_date in args.dates]

    if args.input_file and len(dates) != 1:
        raise SystemExit("--input-file supports exactly one DATE.")

    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        events = payload.get("events", [])
        seen_dates = sorted(
            {
                (event.get("start_date") or "")[:10]
                for event in events
                if event.get("start_date")
            }
        )
    elif args.publisher == "chicago-reader":
        events, seen_dates = fetch_reader_events(dates, args.max_pages)
    else:
        events, seen_dates = fetch_ycg_events(dates, args.max_pages)

    grouped = filter_events(events, set(dates))
    multiple_dates = len(dates) > 1
    for date in dates:
        note = build_availability_note(publisher["label"], date, grouped[date], seen_dates)
        if args.publisher == "chicago-reader":
            print_reader_events(
                publisher["label"],
                date,
                grouped[date],
                args.description_limit,
                multiple_dates,
                note,
            )
        else:
            print_ycg_events(publisher["label"], date, grouped[date], multiple_dates, note)


if __name__ == "__main__":
    main()
