#!/usr/bin/env python3
"""Search Kosher Check public product records and print concise rows."""

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


STORE_API_URL = "https://www.koshercheck.org/wp-json/wc/store/v1/products"


class HeadingTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_heading = False
        self.depth = 0
        self.current: list[str] = []
        self.values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value or "" for name, value in attrs}
        classes = attributes.get("class", "")
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p"} and "elementor-heading-title" in classes:
            self.in_heading = True
            self.depth = 1
            self.current = []
        elif self.in_heading:
            self.depth += 1

    def handle_data(self, data: str) -> None:
        if self.in_heading:
            value = " ".join(data.split())
            if value:
                self.current.append(value)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_heading:
            return
        self.depth -= 1
        if self.depth <= 0:
            value = clean_text(" ".join(self.current))
            if value:
                self.values.append(value)
            self.in_heading = False
            self.current = []


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value)).replace('","', ", ").replace('""', '"').strip('"')
    text = " ".join(text.split())
    if re.fullmatch(r"[,;\s]+", text):
        return ""
    return text


def norm(value: Any) -> str:
    return clean_text(value).casefold()


def fetch_json(url: str, timeout: float) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "accept": "application/json, text/plain, */*",
            "user-agent": "Codex Kosher Check Product Search/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str, timeout: float) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "user-agent": "Codex Kosher Check Product Search/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def search_products(query: str, limit: int, timeout: float) -> list[dict[str, Any]]:
    per_page = min(max(limit or 100, 1), 100)
    params = urllib.parse.urlencode({"search": query, "per_page": per_page})
    return fetch_json(f"{STORE_API_URL}?{params}", timeout)


def parse_detail_page(url: str, timeout: float) -> dict[str, str]:
    html_text = fetch_text(url, timeout)
    parser = HeadingTextParser()
    parser.feed(html_text)
    values = [value for value in parser.values if value not in {"Certified Product", "This is not a kosher certificate."}]

    details: dict[str, str] = {}
    labels = {
        "Brand": "brand",
        "Product Owner": "company",
        "UKD": "record_id",
        "Product Category": "category",
        "Country of Origin": "country",
        "Consumer or Industrial": "market",
        "Conditions": "conditions",
        "Expiration Date": "expiration_date",
        "Kosher Symbol": "symbol_condition",
    }
    designation_re = re.compile(r"^(pareve|dairy|meat|fish|passover)", re.I)

    index = 0
    while index < len(values):
        value = values[index]
        if value in labels and index + 1 < len(values):
            if values[index + 1] not in labels:
                details[labels[value]] = values[index + 1]
                index += 2
            else:
                index += 1
            continue
        if designation_re.search(value) and "designation" not in details:
            details["designation"] = value
        index += 1
    return details


def normalize_product(product: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    categories = product.get("categories") or []
    row = {
        "agency": "Kosher Check",
        "product": clean_text(product.get("name")),
        "sku": clean_text(product.get("sku")),
        "record_id": clean_text(product.get("sku")),
        "url": product.get("permalink") or "",
        "categories": [clean_text(category.get("name")) for category in categories if isinstance(category, dict)],
    }
    if args.details and row["url"]:
        try:
            row.update(parse_detail_page(row["url"], args.timeout))
        except urllib.error.URLError as exc:
            row["detail_error"] = str(exc)
    return row


def row_text(row: dict[str, Any]) -> str:
    values: list[str] = []
    for value in row.values():
        if isinstance(value, list):
            values.extend(clean_text(item) for item in value)
        else:
            values.append(clean_text(value))
    return " ".join(values)


def matches_filters(row: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.exact and norm(args.query) not in norm(row.get("product")):
        return False
    if args.brand and norm(args.brand) not in norm(row.get("brand")):
        return False
    if args.company and norm(args.company) not in norm(row.get("company")):
        return False
    if args.category and norm(args.category) not in norm(" ".join(row.get("categories", [])) + " " + str(row.get("category", ""))):
        return False
    if args.designation and norm(args.designation) not in norm(row.get("designation")):
        return False
    if args.record_id and norm(args.record_id) not in norm(row.get("record_id")):
        return False
    if args.contains and norm(args.contains) not in norm(row_text(row)):
        return False
    return True


def collect_results(args: argparse.Namespace) -> list[dict[str, Any]]:
    products = search_products(args.query, args.limit, args.timeout)
    rows = [normalize_product(product, args) for product in products]
    filtered = [row for row in rows if matches_filters(row, args)]
    if args.limit:
        filtered = filtered[: args.limit]
    return filtered


def print_text(rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    print(f"Query: {args.query}")
    print(f"Displayed matches after local filters: {len(rows)}")
    print("Scope note: Kosher Check records are public product listings; verify package symbol and any listed conditions.")
    print()

    for index, row in enumerate(rows, start=1):
        print(f"{index}. {row.get('product', '')}")
        if row.get("brand"):
            print(f"   Brand: {row.get('brand')}")
        if row.get("company"):
            print(f"   Product owner: {row.get('company')}")
        categories = row.get("categories") or []
        category = row.get("category") or ", ".join(categories)
        if category:
            print(f"   Category: {category}")
        if row.get("designation"):
            print(f"   Designation: {row.get('designation')}")
        if row.get("symbol_condition"):
            print(f"   Symbol/condition: {row.get('symbol_condition')}")
        if row.get("conditions"):
            print(f"   Conditions: {row.get('conditions')}")
        if row.get("expiration_date"):
            print(f"   Expiration: {row.get('expiration_date')}")
        if row.get("record_id"):
            print(f"   Kosher Check record/SKU: {row.get('record_id')}")
        if row.get("detail_error"):
            print(f"   Detail warning: {row.get('detail_error')}")
        print(f"   URL: {row.get('url', '')}")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search Kosher Check public product records.")
    parser.add_argument("query", help="Product, brand, company, keyword, or Kosher Check SKU to search.")
    parser.add_argument("--limit", type=int, default=25, help="Maximum rows to display after local filters. Default: 25. Use 0 for up to 100.")
    parser.add_argument("--no-details", dest="details", action="store_false", help="Skip per-product detail pages and only use the product API.")
    parser.set_defaults(details=True)
    parser.add_argument("--exact", action="store_true", help="Require the query phrase to appear in the product name.")
    parser.add_argument("--brand", help="Local filter: parsed brand contains this value.")
    parser.add_argument("--company", help="Local filter: product owner contains this value.")
    parser.add_argument("--category", help="Local filter: category contains this value.")
    parser.add_argument("--designation", help="Local filter: designation contains this value, such as Pareve or Dairy.")
    parser.add_argument("--record-id", help="Local filter: Kosher Check SKU/record contains this value.")
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
        rows = collect_results(args)
    except urllib.error.URLError as exc:
        print(f"Kosher Check product search request failed: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Kosher Check product search returned invalid JSON: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": args.query, "results": rows}, indent=2, sort_keys=True))
    else:
        print_text(rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
