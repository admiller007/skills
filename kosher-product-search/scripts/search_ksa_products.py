#!/usr/bin/env python3
"""Search KSA Kosher's public product directory endpoint."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_URL = "https://portal.ksakosher.org/directories/products/filter-products"
SOURCE_URL = "https://portal.ksakosher.org/directories/products"
FIELD_PARAMS = {
    "product": "FilterForm[name]",
    "ukid": "FilterForm[ukid]",
    "manufacturer": "FilterForm[manufacturer]",
    "brand": "FilterForm[brand]",
}
STATUS_PARAMS = {
    "dairy": "isdairy",
    "dairy-equipment": "isdairyeq",
    "de": "isdairyeq",
    "pas-yisroel": "ispasyisroel",
    "pas yisroel": "ispasyisroel",
    "pareve": "ispareve",
    "parve": "ispareve",
}
PASSOVER_PARAMS = {
    "yes": "kosher",
    "y": "kosher",
    "true": "kosher",
    "kosher": "kosher",
    "passover": "kosher",
    "no": "non_kosher",
    "n": "non_kosher",
    "false": "non_kosher",
    "non-kosher": "non_kosher",
    "non_kosher": "non_kosher",
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def norm(value: Any) -> str:
    return clean_text(value).casefold()


def form_status(value: str) -> str:
    key = norm(value).replace("_", "-")
    return STATUS_PARAMS.get(key, "")


def form_passover(value: str) -> str:
    return PASSOVER_PARAMS.get(norm(value).replace(" ", "-"), "")


def request_params(args: argparse.Namespace, page: int, per_page: int) -> dict[str, str]:
    params = {
        "perPage": str(per_page),
        "page": str(page),
        "totalResults": "0",
    }
    if args.query:
        params[FIELD_PARAMS[args.field]] = args.query
    if args.manufacturer:
        params["FilterForm[manufacturer]"] = args.manufacturer
    if args.brand:
        params["FilterForm[brand]"] = args.brand
    if args.status and form_status(args.status):
        params["FilterForm[kosherStatus]"] = form_status(args.status)
    if args.passover and form_passover(args.passover):
        params["FilterForm[ispassover]"] = form_passover(args.passover)
    return params


def fetch_page(args: argparse.Namespace, page: int, per_page: int) -> dict[str, Any]:
    url = f"{API_URL}?{urllib.parse.urlencode(request_params(args, page, per_page))}"
    request = urllib.request.Request(
        url,
        headers={
            "accept": "application/json, text/javascript, */*; q=0.01",
            "referer": SOURCE_URL,
            "user-agent": "Codex KSA Product Search/1.0",
            "x-requested-with": "XMLHttpRequest",
        },
    )
    with urllib.request.urlopen(request, timeout=args.timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def truthy(value: Any) -> bool:
    return clean_text(value) in {"1", "true", "True", "yes", "Yes"}


def normalize_model(model: dict[str, Any]) -> dict[str, Any]:
    company_product = model.get("companyProducts") or {}
    company = company_product.get("company") or {}
    designation = model.get("productDesignation") or {}
    brand = clean_text(company_product.get("brand")) or clean_text(company.get("name"))
    flags = [
        name
        for field, name in (
            ("fish", "Fish"),
            ("passover", "Passover"),
            ("pas_yisroel", "Pas Yisroel"),
            ("cholov_yisroel", "Cholov Yisroel"),
            ("bishul_yisroel", "Bishul Yisroel"),
            ("kitniyos", "Kitniyos"),
            ("mevushal", "Mevushal"),
            ("vegan_verified", "Vegan Verified"),
            ("paleo", "Paleo"),
            ("non_gmo", "Non-GMO"),
            ("keto", "Keto"),
        )
        if truthy(model.get(field))
    ]
    designation_name = clean_text(designation.get("designation"))
    symbol = "KSA-D" if norm(designation_name) == "dairy" else "KSA"
    return {
        "product": clean_text(model.get("name") or company_product.get("name")),
        "brand": brand,
        "company": clean_text(company.get("name")),
        "designation": designation_name,
        "symbol": symbol,
        "passover": "Yes" if truthy(model.get("passover")) else "No",
        "product_code": clean_text(company_product.get("product_code")),
        "ukid": clean_text(company_product.get("VKD") or company_product.get("KID")),
        "record_id": clean_text(model.get("id")),
        "notes": clean_text(model.get("notes")),
        "admin_notes": clean_text(model.get("admin_notes")),
        "flags": flags,
        "source_url": SOURCE_URL,
    }


def row_text(row: dict[str, Any]) -> str:
    values = [clean_text(value) for key, value in row.items() if key != "flags"]
    values.extend(row.get("flags") or [])
    return " ".join(values)


def matches_filters(row: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.exact and norm(args.query) not in norm(row.get("product")):
        return False
    if args.brand and norm(args.brand) not in norm(row.get("brand")):
        return False
    if args.manufacturer and norm(args.manufacturer) not in norm(row.get("company")):
        return False
    if args.status and norm(args.status) not in norm(row.get("designation")) and not form_status(args.status):
        return False
    if args.passover and norm(args.passover) not in norm(row.get("passover")) and not form_passover(args.passover):
        return False
    if args.ukid and norm(args.ukid) not in norm(row.get("ukid")):
        return False
    if args.product_code and norm(args.product_code) not in norm(row.get("product_code")):
        return False
    if args.contains and norm(args.contains) not in norm(row_text(row)):
        return False
    return True


def collect_results(args: argparse.Namespace) -> tuple[int | None, list[dict[str, Any]]]:
    per_page = 100 if args.limit == 0 else max(1, min(100, args.limit))
    page = 0
    total: int | None = None
    rows: list[dict[str, Any]] = []

    while True:
        payload = fetch_page(args, page, per_page)
        models = payload.get("models") or []
        pagination = payload.get("pagination") or {}
        try:
            total = int(pagination.get("totalResults", total or 0))
        except (TypeError, ValueError):
            total = total

        rows.extend(row for row in (normalize_model(model) for model in models if isinstance(model, dict)) if matches_filters(row, args))
        if args.limit and len(rows) >= args.limit:
            rows = rows[: args.limit]
            break
        if not args.all_pages:
            break
        if args.max_pages and page + 1 >= args.max_pages:
            break
        if not models:
            break
        if total is not None and (page + 1) * per_page >= total:
            break
        page += 1

    return total, rows


def print_text(total: int | None, rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    print(f"Query: {args.query}")
    print(f"KSA search field: {args.field}")
    if total is not None:
        print(f"KSA total matches: {total}")
    print(f"Displayed matches after local filters: {len(rows)}")
    print("Scope note: KSA states that all products must bear the KSA symbol of certification.")
    print()

    for index, row in enumerate(rows, start=1):
        print(f"{index}. {row.get('product', '')}")
        print(f"   Brand: {row.get('brand', '')}")
        print(f"   Company: {row.get('company', '')}")
        print(f"   Designation: {row.get('designation', '')}")
        print(f"   Symbol: {row.get('symbol', '')}")
        print(f"   Passover: {row.get('passover', '')}")
        if row.get("product_code"):
            print(f"   Product code: {row.get('product_code')}")
        if row.get("ukid"):
            print(f"   KSA UKID/VKD: {row.get('ukid')}")
        if row.get("flags"):
            print(f"   Flags: {', '.join(row.get('flags') or [])}")
        if row.get("notes") or row.get("admin_notes"):
            print(f"   Notes: {row.get('notes') or row.get('admin_notes')}")
        print(f"   Source: {SOURCE_URL}")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search KSA Kosher public product records.")
    parser.add_argument("query", help="Product, UKID/VKD, manufacturer, or brand keyword to search.")
    parser.add_argument("--field", choices=sorted(FIELD_PARAMS), default="product", help="Remote KSA field to search. Default: product.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to display after local filters. Default: 50. Use 0 for all.")
    parser.add_argument("--all-pages", action="store_true", help="Continue fetching pages until all remote rows have been read or --max-pages is reached.")
    parser.add_argument("--max-pages", type=int, default=0, help="Maximum pages when using --all-pages. Default: no cap.")
    parser.add_argument("--exact", action="store_true", help="Require the query phrase to appear in the product name.")
    parser.add_argument("--manufacturer", help="Remote/local filter: manufacturer/company contains this value.")
    parser.add_argument("--brand", help="Remote/local filter: brand contains this value.")
    parser.add_argument("--status", help="Filter designation, such as Pareve, Dairy, Dairy Equipment, or Pas Yisroel.")
    parser.add_argument("--passover", help="Filter Passover status: yes/no.")
    parser.add_argument("--ukid", help="Local filter: KSA UKID/VKD/KID contains this value.")
    parser.add_argument("--product-code", help="Local filter: product code contains this value.")
    parser.add_argument("--contains", help="Local filter: any displayed row text contains this value.")
    parser.add_argument("--json", action="store_true", help="Print matching rows as JSON.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds. Default: 20.")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    if args.max_pages < 0:
        parser.error("--max-pages must be >= 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        total, rows = collect_results(args)
    except (urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        print(f"KSA product search failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": args.query, "field": args.field, "source_url": SOURCE_URL, "total_rows": total, "results": rows}, indent=2, sort_keys=True))
    else:
        print_text(total, rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
