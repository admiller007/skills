#!/usr/bin/env python3
"""Search the OU Kosher product API and print concise product records."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_URL = "https://productsearch-v2.oukosher.org/api/v1/product"


def fetch_page(query: str, page: int, limit: int, timeout: float) -> dict[str, Any]:
    params = urllib.parse.urlencode({"page": page, "limit": limit, "query": query})
    request = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={
            "accept": "application/json, text/plain, */*",
            "origin": "https://oukosher.org",
            "user-agent": "Claude OU Kosher Product Search/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).casefold()


def designation(result: dict[str, Any]) -> str:
    values = result.get("dpm") or []
    return ", ".join(item.get("dpm", "") for item in values if item.get("dpm"))


def symbols(result: dict[str, Any]) -> str:
    values = result.get("symbol") or []
    return ", ".join(str(value) for value in values)


def category(result: dict[str, Any]) -> str:
    value = result.get("category") or {}
    if isinstance(value, dict):
        return value.get("category") or value.get("categorySort") or ""
    return str(value)


def matches_filters(result: dict[str, Any], args: argparse.Namespace) -> bool:
    product_name = norm(result.get("productName"))
    if args.exact and norm(args.query) not in product_name:
        return False
    if args.brand and norm(args.brand) not in norm(result.get("brandName")):
        return False
    if args.company and norm(args.company) not in norm(result.get("company")):
        return False
    if args.category and norm(args.category) not in norm(category(result)):
        return False
    return True


def collect_results(args: argparse.Namespace) -> tuple[int | None, list[dict[str, Any]]]:
    page = args.page
    total: int | None = None
    results: list[dict[str, Any]] = []
    pages_read = 0

    while True:
        payload = fetch_page(args.query, page, args.limit, args.timeout)
        if total is None:
            total = payload.get("total")
        page_results = payload.get("results") or []
        results.extend(item for item in page_results if matches_filters(item, args))

        pages_read += 1
        if not args.all_pages:
            break
        if not page_results:
            break
        if args.max_pages and pages_read >= args.max_pages:
            break
        if isinstance(total, int) and page * args.limit >= total:
            break
        page += 1

    return total, results


def print_text(total: int | None, results: list[dict[str, Any]], args: argparse.Namespace) -> None:
    filtered = len(results)
    print(f"Query: {args.query}")
    if total is not None:
        print(f"OU total matches: {total}")
    print(f"Displayed matches after local filters: {filtered}")
    print()

    for index, result in enumerate(results, start=1):
        passover = "No" if result.get("passoverStatus") == "N" else str(result.get("passoverStatus") or "")
        print(f"{index}. {result.get('productName', '')}")
        print(f"   Brand: {result.get('brandName') or ''}")
        print(f"   Company: {result.get('company') or ''}")
        print(f"   Category: {category(result)}")
        print(f"   Symbol: {symbols(result)}")
        print(f"   DPM: {designation(result)}")
        print(f"   Passover: {passover}")
        print(f"   Status: {result.get('status') or ''}")
        print(f"   Conditions: {result.get('conditions') or ''}")
        print(f"   OU record: {result.get('agencyUniqueId') or ''}")
        certified_since = result.get("certifiedSince")
        if certified_since:
            print(f"   Certified since: {certified_since[:10]}")
        score = result.get("_score")
        if score is not None:
            print(f"   Search score: {score}")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search OU Kosher product records.")
    parser.add_argument("query", help="Product name, brand, company, UPC, or OU record ID to search.")
    parser.add_argument("--page", type=int, default=1, help="API page to request. Default: 1.")
    parser.add_argument("--limit", type=int, default=50, help="Results per page, usually 1-50. Default: 50.")
    parser.add_argument("--all-pages", action="store_true", help="Fetch every page until all results are read.")
    parser.add_argument("--max-pages", type=int, default=0, help="Maximum pages when using --all-pages. Default: no cap.")
    parser.add_argument("--exact", action="store_true", help="Require the query phrase to appear in productName.")
    parser.add_argument("--brand", help="Local filter: brandName contains this value.")
    parser.add_argument("--company", help="Local filter: company contains this value.")
    parser.add_argument("--category", help="Local filter: category contains this value.")
    parser.add_argument("--json", action="store_true", help="Print raw matching records as JSON.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds. Default: 20.")
    args = parser.parse_args(argv)
    if args.page < 1:
        parser.error("--page must be >= 1")
    if args.limit < 1 or args.limit > 50:
        parser.error("--limit must be between 1 and 50")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        total, results = collect_results(args)
    except urllib.error.URLError as exc:
        print(f"OU API request failed: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"OU API returned invalid JSON: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": args.query, "total": total, "results": results}, indent=2, sort_keys=True))
    else:
        print_text(total, results, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
