#!/usr/bin/env python3
"""Search Sephardi Kashrut Authority public product records."""

from __future__ import annotations

import argparse
import html
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any


BASE_URL = "https://www.ska.org.uk/product-search"
FIELD_PARAMS = {
    "product": "fb-KosherProduct",
    "brand": "fb-KosherBrand",
    "category": "fb-KosherCategory",
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(html.unescape(str(value)).split())


def norm(value: Any) -> str:
    return clean_text(value).casefold()


class SKAResultsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_table = False
        self.in_header = False
        self.in_row = False
        self.in_cell = False
        self.current: list[str] = []
        self.headers: list[str] = []
        self.row: list[str] = []
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value or "" for name, value in attrs}
        classes = attributes.get("class", "")
        if tag == "table" and "results" in classes.split():
            self.in_table = True
            return
        if not self.in_table:
            return
        if tag == "th":
            self.in_header = True
            self.current = []
        elif tag == "tr":
            self.in_row = True
            self.row = []
        elif tag == "td" and self.in_row:
            self.in_cell = True
            self.current = []

    def handle_data(self, data: str) -> None:
        if self.in_header or self.in_cell:
            value = clean_text(data)
            if value:
                self.current.append(value)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_table:
            return
        if tag == "th" and self.in_header:
            self.headers.append(clean_text(" ".join(self.current)))
            self.in_header = False
            self.current = []
        elif tag == "td" and self.in_cell:
            self.row.append(clean_text(" ".join(self.current)))
            self.in_cell = False
            self.current = []
        elif tag == "tr" and self.in_row:
            if self.row:
                self.add_row(self.row)
            self.in_row = False
            self.row = []
        elif tag == "table":
            self.in_table = False

    def add_row(self, values: list[str]) -> None:
        headers = self.headers or [
            "Brand name",
            "Product name",
            "Meat / Pareve / Dairy",
            "SKA Logo",
            "Is it vegan?",
            "Status",
            "Category",
            "Passover",
            "Notes",
        ]
        row = {headers[index]: value for index, value in enumerate(values[: len(headers)])}
        self.rows.append(
            {
                "brand": row.get("Brand name", ""),
                "product": row.get("Product name", ""),
                "designation": row.get("Meat / Pareve / Dairy", ""),
                "ska_logo": row.get("SKA Logo", ""),
                "vegan": row.get("Is it vegan?", ""),
                "status": row.get("Status", ""),
                "category": row.get("Category", ""),
                "passover": row.get("Passover", ""),
                "notes": row.get("Notes", ""),
            }
        )


def search_url(args: argparse.Namespace) -> str:
    field = FIELD_PARAMS[args.field]
    params = {
        "action": "search",
        "fb-searchmode": "1",
        f"{field}-searchtype": "contains",
        field: args.query,
    }
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


def fetch_page(url: str, timeout: float) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "user-agent": "Codex SKA Product Search/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def parse_results(html_text: str) -> list[dict[str, str]]:
    parser = SKAResultsParser()
    parser.feed(html_text)
    return parser.rows


def row_text(row: dict[str, str]) -> str:
    return " ".join(row.values())


def matches_filters(row: dict[str, str], args: argparse.Namespace) -> bool:
    if args.exact and norm(args.query) not in norm(row.get(args.field if args.field != "product" else "product")):
        return False
    if args.brand and norm(args.brand) not in norm(row.get("brand")):
        return False
    if args.category and norm(args.category) not in norm(row.get("category")):
        return False
    if args.status and norm(args.status) not in norm(row.get("status")):
        return False
    if args.designation and norm(args.designation) not in norm(row.get("designation")):
        return False
    if args.logo and norm(args.logo) not in norm(row.get("ska_logo")):
        return False
    if args.passover and norm(args.passover) not in norm(row.get("passover")):
        return False
    if args.contains and norm(args.contains) not in norm(row_text(row)):
        return False
    return True


def collect_results(args: argparse.Namespace) -> tuple[str, list[dict[str, str]]]:
    url = search_url(args)
    rows = parse_results(fetch_page(url, args.timeout))
    for row in rows:
        row["source_url"] = url
    filtered = [row for row in rows if matches_filters(row, args)]
    if args.limit:
        filtered = filtered[: args.limit]
    return url, filtered


def print_text(url: str, rows: list[dict[str, str]], args: argparse.Namespace) -> None:
    print(f"Query: {args.query}")
    print(f"SKA search field: {args.field}")
    print(f"Displayed matches after local filters: {len(rows)}")
    print("Scope note: SKA distinguishes Certified and Approved products; verify status, notes, and whether the package bears the SKA logo when required.")
    print()

    for index, row in enumerate(rows, start=1):
        print(f"{index}. {row.get('product', '')}")
        print(f"   Brand: {row.get('brand', '')}")
        print(f"   Status: {row.get('status', '')}")
        print(f"   Designation: {row.get('designation', '')}")
        print(f"   SKA logo: {row.get('ska_logo', '')}")
        print(f"   Vegan: {row.get('vegan', '')}")
        print(f"   Category: {row.get('category', '')}")
        print(f"   Passover: {row.get('passover', '')}")
        if row.get("notes"):
            print(f"   Notes: {row.get('notes')}")
        print(f"   Source: {url}")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search SKA public product records.")
    parser.add_argument("query", help="Product, brand, or category keyword to search.")
    parser.add_argument("--field", choices=sorted(FIELD_PARAMS), default="product", help="Remote SKA field to search. Default: product.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to display after local filters. Default: 50. Use 0 for all.")
    parser.add_argument("--exact", action="store_true", help="Require the query phrase to appear in the searched field.")
    parser.add_argument("--brand", help="Local filter: brand contains this value.")
    parser.add_argument("--category", help="Local filter: category contains this value.")
    parser.add_argument("--status", help="Local filter: status contains this value, such as Certified or Approved.")
    parser.add_argument("--designation", help="Local filter: designation contains this value, such as Pareve or Dairy.")
    parser.add_argument("--logo", help="Local filter: SKA logo column contains this value, such as Yes or No.")
    parser.add_argument("--passover", help="Local filter: Passover column contains this value.")
    parser.add_argument("--contains", help="Local filter: any displayed row text contains this value.")
    parser.add_argument("--json", action="store_true", help="Print matching rows as JSON.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds. Default: 20.")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        url, rows = collect_results(args)
    except urllib.error.URLError as exc:
        print(f"SKA product search request failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": args.query, "field": args.field, "source_url": url, "results": rows}, indent=2, sort_keys=True))
    else:
        print_text(url, rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
