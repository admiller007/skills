#!/usr/bin/env python3
"""Search STAR-K listing records and print concise company/category rows."""

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


BASE_URL = "https://www.star-k.org/listings"
SECTIONS = ("star-k", "star-d", "star-s")
RECORD_ID_LOOKUP_RE = re.compile(r"[A-Z0-9]{8}", re.I)
RECORD_RE = re.compile(
    r'<a\s+class="fancybox"\s+href="#Div(?P<href_id>[^"]+)"\s+id="(?P<id>[^"]+)"[^>]*>(?P<title>.*?)</a>',
    re.I | re.S,
)
FOOTER_RE = re.compile(r'<div\s+id="footerwrapper"', re.I)


def norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).casefold()


def clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = clean_text(value)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def search_term(search: str) -> str:
    parsed = urllib.parse.urlparse(search)
    if parsed.scheme in {"http", "https"}:
        query = urllib.parse.parse_qs(parsed.query)
        values = query.get("q") or query.get("fullSearch")
        if values:
            return values[0]
    return search


def section_from_url(search: str) -> str | None:
    parsed = urllib.parse.urlparse(search)
    if parsed.scheme not in {"http", "https"}:
        return None
    query = urllib.parse.parse_qs(parsed.query)
    values = query.get("section")
    if values and values[0] in SECTIONS:
        return values[0]
    path = parsed.path.strip("/").split("/")
    if len(path) >= 2 and path[0] == "listings" and path[1] in SECTIONS:
        return path[1]
    return None


def looks_like_record_id(value: str) -> bool:
    return bool(RECORD_ID_LOOKUP_RE.fullmatch(value.strip()))


def record_id_filter(args: argparse.Namespace) -> str:
    if args.record_id:
        return args.record_id
    query = search_term(args.query)
    if looks_like_record_id(query):
        return query
    return ""


def search_url(search: str, section: str) -> str:
    parsed = urllib.parse.urlparse(search)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc not in {"www.star-k.org", "star-k.org"} or not parsed.path.startswith("/listings"):
            raise ValueError("STAR-K search URL must be on https://www.star-k.org/listings")
        return search

    params = urllib.parse.urlencode({"section": section, "q": search})
    return f"{BASE_URL}?{params}"


def fetch_search_page(search: str, section: str, timeout: float) -> tuple[str, str]:
    url = search_url(search, section)
    request = urllib.request.Request(
        url,
        headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "user-agent": "Codex STAR-K Product Search/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return url, response.read().decode("utf-8", "replace")


def symbol_from_alt(alt: str) -> str:
    value = clean_text(alt)
    key = value.casefold()
    if key == "star-d":
        return "STAR-D"
    if key == "star-s":
        return "STAR-S"
    if key == "star-k":
        return "STAR-K"
    if "star-d" in key:
        return "STAR-D"
    if "star-s" in key:
        return "STAR-S"
    if "star-k" in key:
        return "STAR-K"
    return value


class STARListingFragmentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cell: str | None = None
        self.names: list[str] = []
        self.categories: list[str] = []
        self.location_parts: list[str] = []
        self.phone_parts: list[str] = []
        self.symbols: list[str] = []
        self.website_url = ""
        self.letter_url = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value or "" for name, value in attrs}
        classes = attributes.get("class", "")

        if tag == "div" and "name" in classes.split():
            self.cell = "name"
            return

        if tag == "li" and "blue" in classes.split():
            self.cell = "category"
            return

        if tag == "span" and "number" in classes.split():
            self.cell = "phone"
            return

        if tag == "i":
            self.cell = "location"
            return

        if tag == "img":
            symbol = symbol_from_alt(attributes.get("alt", ""))
            if symbol.startswith("STAR-"):
                self.symbols.append(symbol)
            return

        if tag == "a":
            href = attributes.get("href", "")
            absolute = urllib.parse.urljoin("https://www.star-k.org/", href)
            if "/api/Loc/LoadLoc/" in absolute:
                self.letter_url = absolute
            elif href.startswith(("http://", "https://")) and "star-k.org" not in urllib.parse.urlparse(href).netloc:
                self.website_url = href

    def handle_data(self, data: str) -> None:
        value = clean_text(data)
        if not value:
            return
        if self.cell == "name":
            self.names.append(value)
        elif self.cell == "category":
            self.categories.append(value.removeprefix("Category:").strip())
        elif self.cell == "location":
            self.location_parts.append(value)
        elif self.cell == "phone":
            self.phone_parts.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"div", "li", "span", "i"}:
            self.cell = None


def parse_fragment(fragment: str) -> STARListingFragmentParser:
    parser = STARListingFragmentParser()
    parser.feed(fragment)
    return parser


def parse_results(html_text: str, section: str, source_url: str) -> list[dict[str, Any]]:
    matches = list(RECORD_RE.finditer(html_text))
    if not matches:
        return []

    footer = FOOTER_RE.search(html_text)
    footer_start = footer.start() if footer else len(html_text)
    rows: list[dict[str, Any]] = []

    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else footer_start
        fragment = html_text[match.end() : next_start]
        parser = parse_fragment(fragment)
        names = unique(parser.names)
        record_id = match.group("id")
        title = clean_text(re.sub(r"<[^>]+>", "", match.group("title")))
        company = names[0] if names else title
        symbols = unique(parser.symbols)

        rows.append(
            {
                "agency": "STAR-K",
                "section": section,
                "company": company,
                "display_name": title,
                "aliases": names[1:],
                "categories": unique(parser.categories),
                "symbols": symbols,
                "symbol": ", ".join(symbols),
                "location": ", ".join(unique(parser.location_parts)),
                "phone": " ".join(unique(parser.phone_parts)),
                "record_id": record_id,
                "record_url": urllib.parse.urljoin("https://www.star-k.org/", f"listings?section={section}#{record_id}"),
                "letter_url": parser.letter_url,
                "website_url": parser.website_url,
                "source_url": source_url,
            }
        )

    return rows


def matches_filters(row: dict[str, Any], args: argparse.Namespace) -> bool:
    query = search_term(args.query)
    wanted_record_id = record_id_filter(args)
    haystack = " ".join(
        [
            row.get("company", ""),
            row.get("display_name", ""),
            " ".join(row.get("aliases", [])),
            " ".join(row.get("categories", [])),
        ]
    )
    if args.exact and not wanted_record_id and norm(query) not in norm(haystack):
        return False
    if wanted_record_id and norm(wanted_record_id) not in norm(row.get("record_id")):
        return False
    if args.company and norm(args.company) not in norm(row.get("company")):
        return False
    if args.category and norm(args.category) not in norm(" ".join(row.get("categories", []))):
        return False
    if args.symbol and norm(args.symbol) not in norm(row.get("symbol")):
        return False
    return True


def sections_to_search(args: argparse.Namespace) -> list[str]:
    if urllib.parse.urlparse(args.query).scheme in {"http", "https"}:
        return [section_from_url(args.query) or "star-k"]
    if args.section == "all":
        return list(SECTIONS)
    return [args.section]


def collect_results(args: argparse.Namespace) -> tuple[list[str], list[dict[str, Any]]]:
    sections = sections_to_search(args)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    lookup_record_id = record_id_filter(args)
    query_is_url = urllib.parse.urlparse(args.query).scheme in {"http", "https"}
    fetch_query = "" if lookup_record_id and not query_is_url else args.query

    for section in sections:
        source_url, html_text = fetch_search_page(fetch_query, section, args.timeout)
        for row in parse_results(html_text, section, source_url):
            key = row.get("record_id", "")
            if key in seen:
                continue
            seen.add(key)
            if matches_filters(row, args):
                rows.append(row)

    if args.limit:
        rows = rows[: args.limit]
    return sections, rows


def print_text(sections: list[str], rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    print(f"Query: {args.query}")
    print(f"STAR-K sections searched: {', '.join(sections)}")
    print(f"Displayed matches after local filters: {len(rows)}")
    print()

    for index, row in enumerate(rows, start=1):
        print(f"{index}. {row.get('company', '')}")
        if row.get("aliases"):
            print(f"   Also listed as: {', '.join(row.get('aliases', []))}")
        if row.get("categories"):
            print(f"   Categories: {', '.join(row.get('categories', []))}")
        print(f"   Symbols: {row.get('symbol', '')}")
        if row.get("location"):
            print(f"   Location: {row.get('location')}")
        if row.get("phone"):
            print(f"   Phone: {row.get('phone')}")
        print(f"   STAR-K record ID: {row.get('record_id', '')}")
        if row.get("letter_url"):
            print(f"   Letter URL: {row.get('letter_url')}")
        if row.get("website_url"):
            print(f"   Website: {row.get('website_url')}")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search STAR-K listing records.")
    parser.add_argument("query", help="Company, product/category keyword, or STAR-K listings URL.")
    parser.add_argument("--section", choices=[*SECTIONS, "all"], default="star-k", help="STAR-K listing section to search. Default: star-k.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows to display after local filters. Default: 50. Use 0 for all.")
    parser.add_argument("--exact", action="store_true", help="Require the query phrase to appear in company, alias, or category text.")
    parser.add_argument("--company", help="Local filter: company contains this value.")
    parser.add_argument("--category", help="Local filter: category contains this value.")
    parser.add_argument("--symbol", help="Local filter: symbol contains this value, such as STAR-K, STAR-D, or STAR-S.")
    parser.add_argument("--record-id", help="Local filter: STAR-K record ID contains this value.")
    parser.add_argument("--json", action="store_true", help="Print raw parsed rows as JSON.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds. Default: 20.")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        sections, rows = collect_results(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except urllib.error.URLError as exc:
        print(f"STAR-K listings request failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"query": args.query, "sections": sections, "results": rows}, indent=2, sort_keys=True))
    else:
        print_text(sections, rows, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
