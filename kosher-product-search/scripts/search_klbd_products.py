#!/usr/bin/env python3
"""Search KLBD / Is It Kosher UK product records and print concise rows."""

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


API_URL = "https://isitkosher.uk/api/query"


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value:
            self.parts.append(value)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if "<" in text and ">" in text:
        parser = TextExtractor()
        parser.feed(text)
        text = " ".join(parser.parts)
    return " ".join(html.unescape(text).split())


def norm(value: Any) -> str:
    return clean_text(value).casefold()


def fetch_results(query: str, timeout: float) -> dict[str, Any]:
    params = urllib.parse.urlencode({"q": query, "grouped": "false"})
    request = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={
            "accept": "application/json, text/plain, */*",
            "user-agent": "Codex KLBD Product Search/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def row_text(row: dict[str, Any]) -> str:
    return " ".join(
        clean_text(row.get(key))
        for key in ("brand", "product", "category", "kosher_raw_data", "moreinfo", "extrainfo")
    )


def matches_filters(row: dict[str, Any], args: argparse.Namespace) -> bool:
    query = norm(args.query)
    if query and query not in norm(row_text(row)):
        return False
    if args.exact and query not in norm(row.get("product")):
        return False
    if args.brand and norm(args.brand) not in norm(row.get("brand")):
        return False
    if args.category and norm(args.category) not in norm(row.get("category")):
        return False
    if args.status and norm(args.status) not in norm(row.get("kosher_raw_data")):
        return False
    if args.designation and norm(args.designation) not in norm(row.get("milkmeat")):
        return False
    if args.certification and norm(args.certification) not in norm(row.get("certification")):
        return False
    if args.contains and norm(args.contains) not in norm(row_text(row)):
        return False
    return True


def collect_results(args: argparse.Namespace) -> tuple[int | None, int | None, list[dict[str, Any]]]:
    payload = fetch_results(args.query, args.timeout)
    rows = payload.get("results") or []
    filtered = [row for row in rows if matches_filters(row, args)]
    if args.limit:
        filtered = filtered[: args.limit]
    return payload.get("count"), payload.get("age"), filtered


def print_text(total: int | None, age: int | None, rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    print(f"Query: {args.query}")
    if total is not None:
        print(f"KLBD total matches: {total}")
    if age is not None:
        print(f"KLBD data age: {age} hours")
    print(f"Displayed matches after local filters: {len(rows)}")
    print("Scope note: KLBD / Is It Kosher results apply to products manufactured for the UK market.")
    print()

    for index, row in enumerate(rows, start=1):
        brand = clean_text(row.get("brand"))
        product = clean_text(row.get("product"))
        name = " - ".join(part for part in (brand, product) if part)
        print(f"{index}. {name or product or brand}")
        print(f"   Category: {clean_text(row.get('category'))}")
        print(f"   Status: {clean_text(row.get('kosher_raw_data'))}")
        if row.get("milkmeat"):
            print(f"   Designation: {clean_text(row.get('milkmeat'))}")
        certification = clean_text(row.get("certification"))
        if certification:
            print(f"   Certification: {certification}")
        if row.get("logo") is not None:
            print(f"   KLBD logo shown/required: {'Yes' if row.get('logo') else 'No'}")
        notes = clean_text(" ".join([str(row.get("moreinfo") or ""), str(row.get("extrainfo") or "")]))
        if notes:
            print(f"   Notes: {notes}")
        print(f"   Source: https://isitkosher.uk/#{urllib.parse.quote(args.query)}")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search KLBD / Is It Kosher UK product records.")
    parser.add_argument("query", help="Product, brand, category, or keyword to search.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to display after local filters. Default: 50. Use 0 for all.")
    parser.add_argument("--exact", action="store_true", help="Require the query phrase to appear in the product name.")
    parser.add_argument("--brand", help="Local filter: brand contains this value.")
    parser.add_argument("--category", help="Local filter: category contains this value.")
    parser.add_argument("--status", help="Local filter: kosher status contains this value, such as KLBD Parev or Dairy.")
    parser.add_argument("--designation", help="Local filter: milk/meat designation contains this value, such as parev or dairy.")
    parser.add_argument("--certification", help="Local filter: certification contains this value, such as klbd.")
    parser.add_argument("--contains", help="Local filter: any displayed row text contains this value.")
    parser.add_argument("--json", action="store_true", help="Print raw matching rows as JSON.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds. Default: 20.")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        total, age, rows = collect_results(args)
    except urllib.error.URLError as exc:
        print(f"KLBD product search request failed: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"KLBD product search returned invalid JSON: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": args.query, "total": total, "age_hours": age, "results": rows}, indent=2, sort_keys=True))
    else:
        print_text(total, age, rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
