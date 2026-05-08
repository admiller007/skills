#!/usr/bin/env python3
"""Search COR Canada's public kosher product endpoint."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_URL = "https://cor.ca/wp-admin/admin-ajax.php"
SOURCE_URL = "https://cor.ca/consumers/kosher-product-search/"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def norm(value: Any) -> str:
    return clean_text(value).casefold()


def fetch_results(query: str, timeout: float) -> list[dict[str, Any]]:
    body = urllib.parse.urlencode({"action": "cor_product_search", "search": query}).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "accept": "application/json, text/javascript, */*; q=0.01",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://cor.ca",
            "referer": SOURCE_URL,
            "user-agent": "Codex COR Product Search/1.0",
            "x-requested-with": "XMLHttpRequest",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = payload.get("result") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("COR endpoint returned JSON without a result array.")
    return [row for row in rows if isinstance(row, dict)]


def normalize_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "product": clean_text(row.get("name")),
        "brand": clean_text(row.get("brand")),
        "company": clean_text(row.get("brand_owner")),
        "status": clean_text(row.get("status")),
        "certifier": clean_text(row.get("certifier") or "COR"),
        "expires": clean_text(row.get("expires")),
        "ukd_id": clean_text(row.get("ukd_id")),
        "certificate_url": clean_text(row.get("url")),
        "source_url": SOURCE_URL,
    }


def dedupe(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, ...]] = set()
    unique: list[dict[str, str]] = []
    for row in rows:
        key = (
            norm(row.get("product")),
            norm(row.get("brand")),
            norm(row.get("company")),
            norm(row.get("status")),
            norm(row.get("expires")),
            norm(row.get("ukd_id")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def is_active(row: dict[str, str], today: dt.date) -> bool:
    if "inactive" in norm(row.get("status")):
        return False
    expires = row.get("expires", "")
    if not expires:
        return True
    try:
        return dt.date.fromisoformat(expires) >= today
    except ValueError:
        return True


def row_text(row: dict[str, str]) -> str:
    return " ".join(row.values())


def matches_filters(row: dict[str, str], args: argparse.Namespace) -> bool:
    if args.exact and norm(args.query) not in norm(row.get("product")):
        return False
    if args.brand and norm(args.brand) not in norm(row.get("brand")):
        return False
    if args.company and norm(args.company) not in norm(row.get("company")):
        return False
    if args.status and norm(args.status) not in norm(row.get("status")):
        return False
    if args.ukd and norm(args.ukd) not in norm(row.get("ukd_id")):
        return False
    if args.contains and norm(args.contains) not in norm(row_text(row)):
        return False
    if args.active_only and not is_active(row, dt.date.today()):
        return False
    return True


def collect_results(args: argparse.Namespace) -> tuple[int, list[dict[str, str]]]:
    rows = dedupe([normalize_row(row) for row in fetch_results(args.query, args.timeout)])
    filtered = [row for row in rows if matches_filters(row, args)]
    if args.limit:
        filtered = filtered[: args.limit]
    return len(rows), filtered


def print_text(total: int, rows: list[dict[str, str]], args: argparse.Namespace) -> None:
    print(f"Query: {args.query}")
    print(f"COR product matches: {total}")
    print(f"Displayed matches after local filters: {len(rows)}")
    print("Scope note: COR results apply to COR-certified products; verify the package bears the required COR symbol and check expiry/status fields.")
    print()

    for index, row in enumerate(rows, start=1):
        print(f"{index}. {row.get('product', '')}")
        print(f"   Brand: {row.get('brand', '')}")
        print(f"   Company: {row.get('company', '')}")
        print(f"   Status: {row.get('status', '')}")
        print(f"   Certifier: {row.get('certifier', '')}")
        print(f"   Expires: {row.get('expires', '')}")
        if row.get("ukd_id"):
            print(f"   COR UKD: {row.get('ukd_id')}")
        if row.get("certificate_url"):
            print(f"   Certificate URL: {row.get('certificate_url')}")
        print(f"   Source: {row.get('source_url', SOURCE_URL)}")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search COR Canada public product records.")
    parser.add_argument("query", help="Product, brand, company, or UKD keyword to search.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to display after local filters. Default: 50. Use 0 for all.")
    parser.add_argument("--exact", action="store_true", help="Require the query phrase to appear in the product name.")
    parser.add_argument("--brand", help="Local filter: brand contains this value.")
    parser.add_argument("--company", help="Local filter: company/brand owner contains this value.")
    parser.add_argument("--status", help="Local filter: status contains this value, such as Pareve or Dairy.")
    parser.add_argument("--ukd", help="Local filter: COR UKD contains this value.")
    parser.add_argument("--active-only", action="store_true", help="Exclude rows with inactive status or an expired ISO expiry date.")
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
        total, rows = collect_results(args)
    except (urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        print(f"COR product search failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": args.query, "source_url": SOURCE_URL, "total_rows": total, "results": rows}, indent=2, sort_keys=True))
    else:
        print_text(total, rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
