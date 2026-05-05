#!/usr/bin/env python3
"""Search OK Kosher product records and print concise product rows."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import PurePosixPath
from typing import Any


SEARCH_URL = "https://www.ok.org/product-search/"


def norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).casefold()


def search_url(search: str) -> str:
    parsed = urllib.parse.urlparse(search)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc not in {"www.ok.org", "ok.org"} or not parsed.path.startswith("/product-search"):
            raise ValueError("OK search URL must be on https://www.ok.org/product-search/")
        return search

    params = urllib.parse.urlencode({"term": search})
    return f"{SEARCH_URL}?{params}"


def fetch_search_page(search: str, timeout: float) -> str:
    request = urllib.request.Request(
        search_url(search),
        headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "user-agent": "Codex OK Kosher Product Search/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


class OKProductTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_row = False
        self.cell: str | None = None
        self.row: dict[str, str] = {}
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value or "" for name, value in attrs}
        classes = attributes.get("class", "")

        if tag == "tr":
            self.in_row = True
            self.cell = None
            self.row = {}
            return

        if self.in_row and tag == "td":
            if "filters-table__table-name" in classes:
                self.cell = "company"
            elif "filters-table__table-product" in classes:
                self.cell = "product"
            elif "filters-table__table-symbol" in classes:
                self.cell = "symbol"
            elif "filters-table__table-status" in classes:
                self.cell = "status"
            elif "filters-table__table-logo" in classes:
                self.cell = "kid"
            else:
                self.cell = None
            return

        if self.in_row and self.cell == "symbol" and tag == "img":
            alt = attributes.get("alt", "")
            src = attributes.get("src", "")
            self.row["symbol_alt"] = alt
            self.row["symbol_src"] = src
            self.row["symbol"] = symbol_from_image(alt, src)
            return

        if self.in_row and self.cell == "kid" and tag == "a":
            href = attributes.get("href", "")
            self.row["kid_url"] = href
            parsed = urllib.parse.urlparse(href)
            kid = urllib.parse.parse_qs(parsed.query).get("kidSearchText", [""])[0]
            self.row["kid"] = kid

    def handle_data(self, data: str) -> None:
        if self.in_row and self.cell in {"company", "product", "status"}:
            existing = self.row.get(self.cell, "")
            value = " ".join(part for part in [existing, data.strip()] if part)
            self.row[self.cell] = value

    def handle_endtag(self, tag: str) -> None:
        if tag == "td":
            self.cell = None
            return

        if tag == "tr":
            if self.row.get("product"):
                self.rows.append(self.row)
            self.in_row = False
            self.cell = None
            self.row = {}


def symbol_from_image(alt: str, src: str) -> str:
    text = " ".join([alt, PurePosixPath(urllib.parse.urlparse(src).path).name]).casefold()
    if "restriction" in text:
        return "Restriction icon"
    if "ok_de" in text or "ok de" in text:
        return "OK-DE"
    if "ok_dairy" in text or "ok d" in text:
        return "OK-D"
    if "ok_p" in text or "ok p" in text:
        return "OK-P"
    if "ok_kosher" in text or "ok symbol" in text:
        return "OK"
    return alt.strip()


def parse_total(html: str) -> int | None:
    match = re.search(r"(\d+)\s+matches\s+for", html, re.I)
    if not match:
        return None
    return int(match.group(1))


def parse_results(html: str) -> list[dict[str, str]]:
    parser = OKProductTableParser()
    parser.feed(html)
    return parser.rows


def matches_filters(row: dict[str, str], args: argparse.Namespace) -> bool:
    product = norm(row.get("product"))
    query = search_term(args.query)
    if args.exact and norm(query) not in product:
        return False
    if args.company and norm(args.company) not in norm(row.get("company")):
        return False
    if args.status and norm(args.status) not in norm(row.get("status")):
        return False
    if args.symbol and norm(args.symbol) not in norm(row.get("symbol")):
        return False
    if args.kid and norm(args.kid) not in norm(row.get("kid")):
        return False
    return True


def search_term(search: str) -> str:
    parsed = urllib.parse.urlparse(search)
    if parsed.scheme in {"http", "https"}:
        values = urllib.parse.parse_qs(parsed.query).get("term")
        if values:
            return values[0]
    return search


def collect_results(args: argparse.Namespace) -> tuple[int | None, list[dict[str, str]]]:
    html = fetch_search_page(args.query, args.timeout)
    total = parse_total(html)
    rows = parse_results(html)
    filtered = [row for row in rows if matches_filters(row, args)]
    if args.limit:
        filtered = filtered[: args.limit]
    return total, filtered


def print_text(total: int | None, rows: list[dict[str, str]], args: argparse.Namespace) -> None:
    print(f"Query: {args.query}")
    if total is not None:
        print(f"OK total matches: {total}")
    print(f"Displayed matches after local filters: {len(rows)}")
    print()

    for index, row in enumerate(rows, start=1):
        print(f"{index}. {row.get('product', '')}")
        print(f"   Company: {row.get('company', '')}")
        print(f"   Symbol: {row.get('symbol', '')}")
        print(f"   Status: {row.get('status', '')}")
        if row.get("kid"):
            print(f"   OK K-ID: {row.get('kid')}")
        if row.get("kid_url"):
            print(f"   K-ID URL: {row.get('kid_url')}")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search OK Kosher product records.")
    parser.add_argument("query", help="Product name, company, keyword, or OK product-search URL.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to display after local filters. Default: 50. Use 0 for all.")
    parser.add_argument("--exact", action="store_true", help="Require the query phrase to appear in the product name.")
    parser.add_argument("--company", help="Local filter: company contains this value.")
    parser.add_argument("--status", help="Local filter: status contains this value, such as Pareve, Dairy, or DE.")
    parser.add_argument("--symbol", help="Local filter: parsed symbol contains this value, such as OK, OK-D, or restriction.")
    parser.add_argument("--kid", help="Local filter: OK K-ID contains this value.")
    parser.add_argument("--json", action="store_true", help="Print raw parsed rows as JSON.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds. Default: 20.")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        total, rows = collect_results(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except urllib.error.URLError as exc:
        print(f"OK product search request failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": args.query, "total": total, "results": rows}, indent=2, sort_keys=True))
    else:
        print_text(total, rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
