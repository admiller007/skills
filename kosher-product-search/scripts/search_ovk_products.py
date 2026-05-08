#!/usr/bin/env python3
"""Search OV Kosher public product table and print concise rows."""

from __future__ import annotations

import argparse
import html
import json
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Any


SEARCH_URL = "https://ovkosher.org/product-search/"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(html.unescape(str(value)).split())


def norm(value: Any) -> str:
    return clean_text(value).casefold()


class OVKTableParser(HTMLParser):
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
        if tag == "table" and attributes.get("id") == "table_1":
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
        headers = self.headers or ["Product Name", "Brand", "Kosher Status", "Passover", "Restriction"]
        row = {headers[index]: value for index, value in enumerate(values[: len(headers)])}
        self.rows.append(
            {
                "product": row.get("Product Name", ""),
                "brand": row.get("Brand", ""),
                "status": row.get("Kosher Status", ""),
                "passover": row.get("Passover", ""),
                "restriction": row.get("Restriction", ""),
                "source_url": SEARCH_URL,
            }
        )


def fetch_page(timeout: float) -> str:
    request = urllib.request.Request(
        SEARCH_URL,
        headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "user-agent": "Codex OVK Product Search/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def parse_results(html_text: str) -> list[dict[str, str]]:
    parser = OVKTableParser()
    parser.feed(html_text)
    return parser.rows


def row_text(row: dict[str, str]) -> str:
    return " ".join(row.get(key, "") for key in ("product", "brand", "status", "passover", "restriction"))


def matches_filters(row: dict[str, str], args: argparse.Namespace) -> bool:
    query = norm(args.query)
    haystack = norm(row_text(row))
    if args.exact and query not in norm(row.get("product")):
        return False
    if query and query not in haystack:
        return False
    if args.brand and norm(args.brand) not in norm(row.get("brand")):
        return False
    if args.status and norm(args.status) not in norm(row.get("status")):
        return False
    if args.passover and norm(args.passover) not in norm(row.get("passover")):
        return False
    if args.restriction and norm(args.restriction) not in norm(row.get("restriction")):
        return False
    return True


def collect_results(args: argparse.Namespace) -> tuple[int, list[dict[str, str]]]:
    rows = parse_results(fetch_page(args.timeout))
    filtered = [row for row in rows if matches_filters(row, args)]
    if args.limit:
        filtered = filtered[: args.limit]
    return len(rows), filtered


def print_text(total: int, rows: list[dict[str, str]], args: argparse.Namespace) -> None:
    print(f"Query: {args.query}")
    print(f"OVK table rows read: {total}")
    print(f"Displayed matches after local filters: {len(rows)}")
    print("Scope note: OVK says this public list only includes some popular OVK consumer certified items.")
    print()

    for index, row in enumerate(rows, start=1):
        print(f"{index}. {row.get('product', '')}")
        print(f"   Brand: {row.get('brand', '')}")
        print(f"   Status: {row.get('status', '')}")
        print(f"   Passover: {row.get('passover', '')}")
        print(f"   Restriction: {row.get('restriction', '')}")
        print(f"   Source: {row.get('source_url', SEARCH_URL)}")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search OV Kosher public product records.")
    parser.add_argument("query", help="Product, brand, keyword, status, or restriction to search.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to display after local filters. Default: 50. Use 0 for all.")
    parser.add_argument("--exact", action="store_true", help="Require the query phrase to appear in the product name.")
    parser.add_argument("--brand", help="Local filter: brand contains this value.")
    parser.add_argument("--status", help="Local filter: kosher status contains this value, such as Pareve or Dairy.")
    parser.add_argument("--passover", help="Local filter: Passover column contains this value, such as Y or N.")
    parser.add_argument("--restriction", help="Local filter: restriction contains this value.")
    parser.add_argument("--json", action="store_true", help="Print matching rows as JSON.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds. Default: 20.")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        total, rows = collect_results(args)
    except urllib.error.URLError as exc:
        print(f"OVK product search request failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": args.query, "total_rows": total, "results": rows}, indent=2, sort_keys=True))
    else:
        print_text(total, rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
