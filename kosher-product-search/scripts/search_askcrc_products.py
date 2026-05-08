#!/usr/bin/env python3
"""Search ASKcRc public consumer product guidance."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any


BASE_URL = "https://www.askcrc.org"
SEARCH_BASE = f"{BASE_URL}/results/basic/year-round"
TOTAL_RE = re.compile(r"(\d+)\s+Results?\s+for:", re.I)
STATUS_RE = re.compile(r"<strong>\s*Status:\s*</strong>\s*([^<]+)", re.I)
TITLE_RE = re.compile(r"<h2>(.*?)</h2>", re.I | re.S)
PARA_RE = re.compile(r"<p>\s*(.*?)\s*</p>", re.I | re.S)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    value = re.sub(r"<[^>]+>", " ", str(value))
    return " ".join(html.unescape(value).split())


def norm(value: Any) -> str:
    return clean_text(value).casefold()


def search_term(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc.endswith("askcrc.org"):
        parts = [part for part in parsed.path.split("/") if part]
        if "year-round" in parts:
            index = parts.index("year-round")
            if len(parts) > index + 1:
                return urllib.parse.unquote(parts[index + 1])
        return ""
    return value


def search_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc.endswith("askcrc.org"):
        return value
    return f"{SEARCH_BASE}/{urllib.parse.quote(value.strip(), safe='')}"


class ASKcRcResultsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_item = False
        self.href = ""
        self.current: list[str] = []
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value or "" for name, value in attrs}
        href = attributes.get("href", "")
        if tag == "a" and href.startswith("/item/"):
            self.in_item = True
            self.href = href
            self.current = []

    def handle_data(self, data: str) -> None:
        if self.in_item:
            text = clean_text(data)
            if text:
                self.current.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_item:
            title = clean_text(" ".join(self.current))
            parts = [part for part in self.href.split("/") if part]
            category = urllib.parse.unquote(parts[1]) if len(parts) > 1 else ""
            record_id = parts[2] if len(parts) > 2 else ""
            self.rows.append(
                {
                    "product": title,
                    "category": category,
                    "record_id": record_id,
                    "detail_url": urllib.parse.urljoin(BASE_URL, self.href),
                    "source_url": BASE_URL,
                }
            )
            self.in_item = False
            self.href = ""
            self.current = []


def fetch_url(url: str, timeout: float) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "user-agent": "Codex ASKcRc Product Search/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def parse_results(html_text: str) -> tuple[int | None, list[dict[str, str]]]:
    total: int | None = None
    match = TOTAL_RE.search(html_text)
    if match:
        total = int(match.group(1))
    parser = ASKcRcResultsParser()
    parser.feed(html_text)
    return total, parser.rows


def parse_detail(html_text: str) -> dict[str, str]:
    title = clean_text(TITLE_RE.search(html_text).group(1)) if TITLE_RE.search(html_text) else ""
    status = clean_text(STATUS_RE.search(html_text).group(1)) if STATUS_RE.search(html_text) else ""
    notes = []
    for match in PARA_RE.finditer(html_text):
        text = clean_text(match.group(1))
        text = text.split(chr(169))[0]
        text = re.sub(r"\s*Copyright.*", "", text).strip()
        if text and not text.lower().startswith("copyright"):
            notes.append(text)
    return {
        "detail_product": title,
        "status": status,
        "notes": " ".join(note for note in notes if "Status:" not in note),
    }


def enrich_details(rows: list[dict[str, str]], timeout: float) -> None:
    for row in rows:
        try:
            details = parse_detail(fetch_url(row["detail_url"], timeout))
        except urllib.error.URLError as exc:
            row["detail_error"] = str(exc)
            continue
        row.update({key: value for key, value in details.items() if value})


def row_text(row: dict[str, str]) -> str:
    return " ".join(row.values())


def matches_filters(row: dict[str, str], args: argparse.Namespace) -> bool:
    query = search_term(args.query)
    if args.exact and norm(query) not in norm(row.get("product")):
        return False
    if args.category and norm(args.category) not in norm(row.get("category")):
        return False
    if args.status and norm(args.status) not in norm(row.get("status")):
        return False
    if args.contains and norm(args.contains) not in norm(row_text(row)):
        return False
    return True


def collect_results(args: argparse.Namespace) -> tuple[str, int | None, list[dict[str, str]]]:
    url = search_url(args.query)
    total, rows = parse_results(fetch_url(url, args.timeout))
    filtered = [row for row in rows if matches_filters(row, args)]
    if args.limit:
        filtered = filtered[: args.limit]
    if not args.no_details:
        enrich_details(filtered, args.timeout)
        filtered = [row for row in filtered if matches_filters(row, args)]
    return url, total, filtered


def print_text(url: str, total: int | None, rows: list[dict[str, str]], args: argparse.Namespace) -> None:
    print(f"Query: {search_term(args.query)}")
    if total is not None:
        print(f"ASKcRc total matches: {total}")
    print(f"Displayed matches after local filters: {len(rows)}")
    print("Scope note: ASKcRc provides cRc consumer guidance and recommended-item lists; it is not always a direct certification record.")
    print()

    for index, row in enumerate(rows, start=1):
        print(f"{index}. {row.get('product', '')}")
        print(f"   Category: {row.get('category', '')}")
        if row.get("status"):
            print(f"   Status: {row.get('status')}")
        if row.get("notes"):
            print(f"   Notes: {row.get('notes')}")
        print(f"   cRc record ID: {row.get('record_id', '')}")
        print(f"   Detail URL: {row.get('detail_url', '')}")
        print(f"   Search URL: {url}")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search ASKcRc public product guidance.")
    parser.add_argument("query", help="Product keyword or ASKcRc result URL to search.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum rows to display after local filters. Default: 10. Use 0 for all.")
    parser.add_argument("--exact", action="store_true", help="Require the query phrase to appear in the item name.")
    parser.add_argument("--category", help="Local filter: ASKcRc category contains this value, such as Slurpee.")
    parser.add_argument("--status", help="Local filter: detail status contains this value, such as Recommended.")
    parser.add_argument("--contains", help="Local filter: any displayed row text contains this value.")
    parser.add_argument("--no-details", action="store_true", help="Do not fetch item detail pages for status/notes.")
    parser.add_argument("--json", action="store_true", help="Print matching rows as JSON.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds. Default: 20.")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        url, total, rows = collect_results(args)
    except urllib.error.URLError as exc:
        print(f"ASKcRc product search failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": search_term(args.query), "source_url": url, "total_rows": total, "results": rows}, indent=2, sort_keys=True))
    else:
        print_text(url, total, rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
