#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


BASE_URL = "https://www.meetup.com/find/"
GQL_URL = "https://www.meetup.com/gql2"
LOCATION = "us--il--Chicago"
CHICAGO_TZ = ZoneInfo("America/Chicago")
USER_AGENT = "chicago-events-skill/1.0"
CHICAGO_LAT = 41.880001068115234
CHICAGO_LON = -87.62000274658203
DEFAULT_RADIUS_MILES = 25
DEFAULT_PAGE_SIZE = 12
DEFAULT_INDEX_ALIAS = '"{\\"filterOutWrongLanguage\\": \\"true\\",\\"modelVersion\\": \\"split_offline_online\\"}"'
NEXT_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
)
TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")
CATEGORY_ALIASES = {
    "all-events": "all-events",
    "social-activities": "social-activities",
    "hobbies-passions": "hobbies-passions",
    "sports-fitness": "sports-fitness",
    "travel-outdoor": "travel-outdoor",
    "career-business": "career-business",
    "technology": "technology",
    "community-environment": "community-environment",
    "identity-language": "identity-language",
    "games": "games",
    "dancing": "dancing",
    "support-coaching": "support-coaching",
    "music": "music",
    "health-wellbeing": "health-wellbeing",
    "art-culture": "art-culture",
    "science-education": "science-education",
    "pets-animals": "pets-animals",
    "religion-spirituality": "religion-spirituality",
    "writing": "writing",
    "parents-family": "parents-family",
    "movements-politics": "movements-politics",
}
CATEGORY_QUERY_PARAMS = {
    "social-activities": {"categoryId": "652"},
    "hobbies-passions": {"keywords": "crafts"},
    "sports-fitness": {"categoryId": "482"},
    "travel-outdoor": {"categoryId": "684"},
    "career-business": {"categoryId": "405"},
    "technology": {"categoryId": "546"},
    "community-environment": {"categoryId": "604"},
    "identity-language": {"categoryId": "622"},
    "games": {"categoryId": "535"},
    "dancing": {"categoryId": "612"},
    "support-coaching": {"categoryId": "449"},
    "music": {"categoryId": "395"},
    "health-wellbeing": {"categoryId": "522"},
    "art-culture": {"categoryId": "521"},
    "science-education": {"categoryId": "436"},
    "pets-animals": {"categoryId": "701"},
    "religion-spirituality": {"categoryId": "593"},
    "writing": {"categoryId": "467"},
    "parents-family": {"categoryId": "673"},
    "movements-politics": {"keywords": "Movements Politics"},
}
CATEGORY_LABELS = {
    "all-events": "All events",
    "social-activities": "Social Activities",
    "hobbies-passions": "Hobbies & Passions",
    "sports-fitness": "Sports & Fitness",
    "travel-outdoor": "Travel & Outdoor",
    "career-business": "Career & Business",
    "technology": "Technology",
    "community-environment": "Community & Environment",
    "identity-language": "Identity & Language",
    "games": "Games",
    "dancing": "Dancing",
    "support-coaching": "Support & Coaching",
    "music": "Music",
    "health-wellbeing": "Health & Wellbeing",
    "art-culture": "Art & Culture",
    "science-education": "Science & Education",
    "pets-animals": "Pets & Animals",
    "religion-spirituality": "Religion & Spirituality",
    "writing": "Writing",
    "parents-family": "Parents & Family",
    "movements-politics": "Movements & Politics",
}
CATEGORY_KEYWORDS = {
    "social-activities": (
        "social",
        "meetup",
        "mixer",
        "happy hour",
        "coffee",
        "bar crawl",
        "friends",
        "networking",
    ),
    "hobbies-passions": (
        "hobby",
        "craft",
        "knit",
        "mahjong",
        "ukulele",
        "photography",
        "puzzle",
        "stitch",
    ),
    "sports-fitness": (
        "soccer",
        "tennis",
        "volleyball",
        "softball",
        "kickball",
        "ride",
        "cycling",
        "fitness",
        "yoga",
        "run",
    ),
    "travel-outdoor": (
        "outdoor",
        "walk",
        "hike",
        "park",
        "garden",
        "lake",
        "beach",
        "trail",
        "sailing",
    ),
    "career-business": (
        "founder",
        "startup",
        "business",
        "career",
        "professional",
        "leadership",
        "funding",
        "entrepreneur",
        "roundtable",
    ),
    "technology": (
        "python",
        "ai",
        "agent",
        "copilot",
        "sql",
        ".net",
        "github",
        "data",
        "developer",
        "tech",
        "blockchain",
        "bitcoin",
    ),
    "community-environment": (
        "community",
        "volunteer",
        "cleanup",
        "charity",
        "neighborhood",
        "environment",
        "civic",
    ),
    "identity-language": (
        "language",
        "spanish",
        "french",
        "cafe conversation",
        "español",
        "hola amigos",
        "intl'l cafe",
        "int'l cafe",
    ),
    "games": (
        "game",
        "gaming",
        "board game",
        "mahjong",
        "poker",
        "trivia",
        "puzzle",
        "chess",
    ),
    "dancing": (
        "dance",
        "dancing",
        "salsa",
        "swing",
        "israeli dancing",
        "flash mob",
    ),
    "support-coaching": (
        "support",
        "coaching",
        "therapy",
        "toastmasters",
        "enneagram",
        "meditation",
        "mindfulness",
        "reiki",
    ),
    "music": (
        "music",
        "concert",
        "choir",
        "ukulele",
        "karaoke",
        "dj",
        "jam",
    ),
    "health-wellbeing": (
        "health",
        "wellbeing",
        "wellness",
        "meditation",
        "qigong",
        "reiki",
        "mindfulness",
        "healing",
    ),
    "art-culture": (
        "art",
        "painting",
        "figure drawing",
        "film",
        "filmmaking",
        "gallery",
        "museum",
        "culture",
        "philosophy",
    ),
    "science-education": (
        "science",
        "education",
        "class",
        "workshop",
        "lesson",
        "learn",
        "study",
        "philosophy",
    ),
    "pets-animals": (
        "pets",
        "animals",
        "dogs",
        "cats",
        "bird",
    ),
    "religion-spirituality": (
        "spiritual",
        "spirituality",
        "bhakti",
        "ceremony",
        "sacred",
        "kirtan",
        "christian",
        "dharma",
    ),
    "writing": (
        "writing",
        "writers",
        "write",
        "critique",
        "book club",
        "reader",
    ),
    "parents-family": (
        "family",
        "kids",
        "children",
        "parents",
        "seniors",
    ),
    "movements-politics": (
        "politics",
        "activism",
        "movement",
        "policy",
        "organizing",
        "civic",
    ),
}
RECOMMENDED_EVENTS_QUERY = """
query recommendedEventsWithSeries(
  $lat: Float!
  $lon: Float!
  $categoryId: ID
  $topicCategoryId: ID
  $startDateRange: String
  $endDateRange: String
  $first: Int
  $after: String
  $eventType: EventType
  $radius: Float
  $isHappeningNow: Boolean
  $isStartingSoon: Boolean
  $sortField: RecommendedEventsSortField
  $doConsolidateEvents: Boolean
  $doPromotePaypalEvents: Boolean
  $indexAlias: String
  $dataConfiguration: String
  $shouldInjectNgaEvents: Boolean
) {
  result: recommendedEvents(
    filter: {
      lat: $lat
      lon: $lon
      categoryId: $categoryId
      topicCategoryId: $topicCategoryId
      startDateRange: $startDateRange
      endDateRange: $endDateRange
      eventType: $eventType
      radius: $radius
      isHappeningNow: $isHappeningNow
      isStartingSoon: $isStartingSoon
      doConsolidateEvents: $doConsolidateEvents
      doPromotePaypalEvents: $doPromotePaypalEvents
      indexAlias: $indexAlias
      shouldInjectNgaEvents: $shouldInjectNgaEvents
    }
    first: $first
    after: $after
    sort: { sortField: $sortField }
    dataConfiguration: $dataConfiguration
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        title
        dateTime
        description
        eventUrl
        eventType
        isOnline
        feeSettings {
          amount
          currency
        }
        group {
          id
          name
          urlname
          city
          state
          country
        }
        venue {
          id
          name
          address
          city
          state
          country
        }
        rsvps {
          totalCount
        }
      }
      metadata {
        recId
        recSource
      }
    }
  }
}
"""
EVENT_SEARCH_QUERY = """
query eventSearchWithSeries(
  $query: String!
  $lat: Float!
  $lon: Float!
  $startDateRange: DateTime
  $endDateRange: DateTime
  $eventType: EventType
  $radius: Float
  $isHappeningNow: Boolean
  $isStartingSoon: Boolean
  $categoryId: ID
  $topicCategoryId: ID
  $city: String
  $state: String
  $country: String
  $zip: String
  $sortField: KeywordSortField
  $first: Int
  $after: String
  $doConsolidateEvents: Boolean
  $dataConfiguration: String
) {
  results: eventSearch(
    filter: {
      query: $query
      lat: $lat
      lon: $lon
      startDateRange: $startDateRange
      endDateRange: $endDateRange
      eventType: $eventType
      radius: $radius
      isHappeningNow: $isHappeningNow
      isStartingSoon: $isStartingSoon
      categoryId: $categoryId
      topicCategoryId: $topicCategoryId
      city: $city
      state: $state
      country: $country
      zip: $zip
      doConsolidateEvents: $doConsolidateEvents
    }
    first: $first
    after: $after
    sort: { sortField: $sortField }
    dataConfiguration: $dataConfiguration
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        title
        dateTime
        description
        eventUrl
        eventType
        isOnline
        feeSettings {
          amount
          currency
        }
        group {
          id
          name
          urlname
          city
          state
          country
        }
        venue {
          id
          name
          address
          city
          state
          country
        }
        rsvps {
          totalCount
        }
      }
      metadata {
        recId
        recSource
      }
    }
  }
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and parse Meetup Chicago event listings for one or more dates."
    )
    parser.add_argument(
        "dates",
        metavar="DATE",
        nargs="*",
        help="Target date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--meetup-url",
        help=(
            "Fetch events by reproducing the exact filters from a Meetup find URL. "
            "This preserves Meetup's own relative date-range resolution, category "
            "IDs, and suburb-inclusive result set."
        ),
    )
    parser.add_argument(
        "--input-file",
        help="Parse a saved Meetup HTML file instead of fetching. Requires exactly one DATE.",
    )
    parser.add_argument(
        "--include-online",
        action="store_true",
        help="Include Meetup events whose venue is listed as Online event.",
    )
    parser.add_argument(
        "--include-suburbs",
        action="store_true",
        help="Include events with an explicit venue city outside Chicago.",
    )
    parser.add_argument(
        "--description-limit",
        type=int,
        default=140,
        help="Maximum description characters to print per event.",
    )
    parser.add_argument(
        "--category",
        action="append",
        choices=sorted(CATEGORY_ALIASES),
        help=(
            "Filter Meetup events to one or more Meetup category buckets. "
            "Uses Meetup's real category query params when available and falls "
            "back to local text classification only when the client bundle does "
            "not expose a stable query mapping."
        ),
    )
    return parser.parse_args()


def normalize_date(raw_date: str) -> str:
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Invalid date {raw_date!r}; expected YYYY-MM-DD.") from exc


def clean_text(raw_text: str) -> str:
    without_tags = TAG_PATTERN.sub(" ", raw_text or "")
    return WHITESPACE_PATTERN.sub(" ", html.unescape(without_tags)).strip()


def keyword_matches(keyword: str, haystack: str) -> bool:
    pattern = re.compile(rf"(?<!\w){re.escape(keyword.lower())}(?!\w)")
    return bool(pattern.search(haystack))


def infer_categories(event: dict[str, str]) -> list[str]:
    haystack = " ".join(
        [
            event["title"],
            event["group"],
            event["venue"],
            event["address"],
            event["description"],
        ]
    ).lower()
    matched: list[str] = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword_matches(keyword, haystack) for keyword in keywords):
            matched.append(category)
    return matched


def build_list_url(date: str, *, include_online: bool, category: str | None = None) -> str:
    start = datetime.strptime(date, "%Y-%m-%d").replace(
        hour=0,
        minute=0,
        second=0,
        tzinfo=CHICAGO_TZ,
    )
    end = start + timedelta(days=1) - timedelta(seconds=1)
    query_params = {
        "source": "EVENTS",
        "location": LOCATION,
        "customStartDate": start.isoformat(timespec="seconds"),
        "customEndDate": end.isoformat(timespec="seconds"),
    }
    if not include_online:
        query_params["eventType"] = "inPerson"
    if category and category in CATEGORY_QUERY_PARAMS:
        query_params.update(CATEGORY_QUERY_PARAMS[category])
    query = urllib.parse.urlencode(query_params)
    return f"{BASE_URL}?{query}"


def fetch_html(date: str, *, include_online: bool, category: str | None = None) -> str:
    url = build_list_url(date, include_online=include_online, category=category)
    return fetch_html_url(url)


def fetch_html_url(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch {url}: {exc}") from exc


def build_time_range(date: str) -> tuple[str, str]:
    start = datetime.strptime(date, "%Y-%m-%d").replace(
        hour=0,
        minute=0,
        second=0,
        tzinfo=CHICAGO_TZ,
    )
    end = start + timedelta(days=1) - timedelta(seconds=1)
    return (
        start.isoformat(timespec="seconds"),
        end.isoformat(timespec="seconds"),
    )


def graphql_request(operation_name: str, query: str, variables: dict) -> dict:
    payload = json.dumps(
        {
            "operationName": operation_name,
            "query": query,
            "variables": variables,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        GQL_URL,
        data=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.URLError as exc:
        raise SystemExit(f"Failed to fetch Meetup GraphQL data: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse Meetup GraphQL response: {exc}") from exc


def paginate_graphql_edges(
    operation_name: str,
    query: str,
    variables: dict,
    *,
    result_key: str,
) -> list[dict]:
    edges: list[dict] = []
    after: str | None = None

    while True:
        page_variables = dict(variables)
        if after:
            page_variables["after"] = after

        payload = graphql_request(operation_name, query, page_variables)
        if payload.get("errors"):
            raise SystemExit(f"Meetup GraphQL error: {payload['errors'][0].get('message', 'unknown error')}")

        result = payload.get("data", {}).get(result_key, {})
        if not isinstance(result, dict):
            raise SystemExit("Meetup GraphQL response did not contain an event result set.")

        edges.extend(result.get("edges") or [])
        page_info = result.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")
        if not after:
            break

    return edges


def fetch_graphql_edges(
    date: str,
    *,
    include_online: bool,
    category: str | None = None,
) -> tuple[list[dict], str | None]:
    start_date, end_date = build_time_range(date)
    query_params = CATEGORY_QUERY_PARAMS.get(category or "", {})
    is_keyword_search = "keywords" in query_params
    operation_name = "eventSearchWithSeries" if is_keyword_search else "recommendedEventsWithSeries"
    query = EVENT_SEARCH_QUERY if is_keyword_search else RECOMMENDED_EVENTS_QUERY
    variables = {
        "lat": CHICAGO_LAT,
        "lon": CHICAGO_LON,
        "startDateRange": start_date,
        "endDateRange": end_date,
        "first": 60 if is_keyword_search else DEFAULT_PAGE_SIZE,
        "radius": DEFAULT_RADIUS_MILES,
        "doConsolidateEvents": True,
        "indexAlias": DEFAULT_INDEX_ALIAS,
    }
    if not include_online:
        variables["eventType"] = "PHYSICAL"
    if "categoryId" in query_params:
        variables["topicCategoryId"] = query_params["categoryId"]
    if "keywords" in query_params:
        variables["query"] = query_params["keywords"]
    if not is_keyword_search:
        variables["sortField"] = "RELEVANCE"

    result_key = "results" if is_keyword_search else "result"
    edges = paginate_graphql_edges(
        operation_name,
        query,
        variables,
        result_key=result_key,
    )
    return edges, category


def extract_find_query_from_html(page_html: str) -> tuple[str, dict, dict]:
    apollo_state = extract_apollo_state(page_html)
    root_query = apollo_state.get("ROOT_QUERY")
    if not isinstance(root_query, dict):
        raise SystemExit("Meetup page did not contain a ROOT_QUERY payload.")

    for key in root_query:
        if key.startswith("recommendedEvents:") or key.startswith("eventSearch:"):
            query_name, raw_config = key.split(":", 1)
            try:
                result = root_query.get(key, {})
                if not isinstance(result, dict):
                    raise SystemExit("Meetup page query payload was not an object.")
                return query_name, json.loads(raw_config), result
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Failed to parse Meetup ROOT_QUERY config: {exc}") from exc

    raise SystemExit("Meetup page did not contain a recognized event search query key.")


def fetch_events_for_meetup_url(meetup_url: str) -> list[dict[str, str]]:
    page_html = fetch_html_url(meetup_url)
    query_name, config, first_page_result = extract_find_query_from_html(page_html)
    filter_config = config.get("filter")
    if not isinstance(filter_config, dict):
        raise SystemExit("Meetup URL did not expose a usable filter config.")

    is_keyword_search = query_name == "eventSearch"
    operation_name = "eventSearchWithSeries" if is_keyword_search else "recommendedEventsWithSeries"
    query = EVENT_SEARCH_QUERY if is_keyword_search else RECOMMENDED_EVENTS_QUERY
    result_key = "results" if is_keyword_search else "result"

    variables = dict(filter_config)
    if "lat" in variables and "lon" in variables and "radius" not in variables:
        variables["radius"] = DEFAULT_RADIUS_MILES
    sort_config = config.get("sort")
    if isinstance(sort_config, dict) and sort_config.get("sortField"):
        variables["sortField"] = sort_config["sortField"]

    first_page_edges = first_page_result.get("edges") if isinstance(first_page_result, dict) else None
    variables["first"] = len(first_page_edges) if first_page_edges else DEFAULT_PAGE_SIZE

    if is_keyword_search and "query" not in variables:
        raise SystemExit("Meetup URL eventSearch config did not contain a search query.")

    edges = paginate_graphql_edges(
        operation_name,
        query,
        variables,
        result_key=result_key,
    )

    events: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for edge in edges:
        event = normalize_graphql_event(
            edge.get("node", {}),
            include_online=variables.get("eventType") != "PHYSICAL",
            include_suburbs=True,
            fetched_category=None,
        )
        if not event or event["url"] in seen_urls:
            continue
        events.append(event)
        seen_urls.add(event["url"])

    events.sort(key=lambda event: (event["date_time"], event["title"]))
    return events


def normalize_graphql_event(
    node: dict,
    *,
    include_online: bool,
    include_suburbs: bool,
    fetched_category: str | None,
) -> dict[str, str] | None:
    if not isinstance(node, dict):
        return None

    date_time = node.get("dateTime") or ""
    title = clean_text(node.get("title") or "")
    url = node.get("eventUrl") or ""
    if not date_time or not title or not url:
        return None

    venue = node.get("venue") if isinstance(node.get("venue"), dict) else {}
    venue_name = clean_text(venue.get("name") or "")
    venue_address = clean_text(venue.get("address") or "")
    venue_city = clean_text(venue.get("city") or "")
    is_online = bool(node.get("isOnline")) or venue_name.lower() == "online event"
    if is_online and not include_online:
        return None
    if venue_city and venue_city.lower() != "chicago" and not include_suburbs:
        return None

    group = node.get("group") if isinstance(node.get("group"), dict) else {}
    rsvp_total = ""
    if isinstance(node.get("rsvps"), dict):
        total_count = node["rsvps"].get("totalCount")
        if total_count is not None:
            rsvp_total = str(total_count)

    event = {
        "title": title,
        "date": date_time[:10],
        "time": date_time[11:16] if len(date_time) >= 16 else "",
        "date_time": date_time,
        "group": clean_text(group.get("name") or "") if isinstance(group, dict) else "",
        "venue": venue_name,
        "address": venue_address,
        "city": venue_city,
        "price": format_price(node.get("feeSettings")),
        "rsvp_count": rsvp_total,
        "description": clean_text(node.get("description") or ""),
        "url": url,
    }
    inferred_categories = infer_categories(event)
    event["categories"] = [fetched_category] if fetched_category else inferred_categories
    return event


def fetch_events_for_date(
    date: str,
    *,
    include_online: bool,
    include_suburbs: bool,
    categories: set[str] | None = None,
) -> list[dict[str, str]]:
    selected_categories = set(categories or [])
    supported_categories = {
        category for category in selected_categories if category in CATEGORY_QUERY_PARAMS
    }
    fallback_categories = {
        category
        for category in selected_categories
        if category not in CATEGORY_QUERY_PARAMS and category != "all-events"
    }

    if not selected_categories or "all-events" in selected_categories:
        fetch_categories: list[str | None] = [None]
    else:
        fetch_categories = sorted(supported_categories) or [None]

    by_url: dict[str, dict[str, str]] = {}
    for fetch_category in fetch_categories:
        edges, fetched_category = fetch_graphql_edges(
            date,
            include_online=include_online,
            category=fetch_category,
        )
        for edge in edges:
            event = normalize_graphql_event(
                edge.get("node", {}),
                include_online=include_online,
                include_suburbs=include_suburbs,
                fetched_category=fetched_category,
            )
            if not event or event["date"] != date:
                continue

            existing = by_url.get(event["url"])
            if existing:
                existing_categories = set(existing["categories"])
                existing_categories.update(event["categories"])
                existing["categories"] = sorted(existing_categories)
            else:
                by_url[event["url"]] = event

    events = list(by_url.values())
    if fallback_categories:
        events = [
            event
            for event in events
            if any(category in infer_categories(event) for category in fallback_categories)
        ]

    events.sort(key=lambda event: (event["date_time"], event["title"]))
    return events


def extract_apollo_state(page_html: str) -> dict:
    match = NEXT_DATA_PATTERN.search(page_html)
    if not match:
        raise SystemExit("Could not find Meetup __NEXT_DATA__ payload.")

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse Meetup __NEXT_DATA__ payload: {exc}") from exc

    apollo_state = payload.get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
    if not isinstance(apollo_state, dict) or not apollo_state:
        raise SystemExit("Meetup page did not contain an __APOLLO_STATE__ event payload.")

    return apollo_state


def format_price(fee_settings: dict | None) -> str:
    if not isinstance(fee_settings, dict):
        return ""

    amount = fee_settings.get("amount")
    currency = (fee_settings.get("currency") or "").upper()
    if amount is None:
        return ""

    if currency == "USD":
        if isinstance(amount, float) and amount.is_integer():
            amount = int(amount)
        if isinstance(amount, int):
            return f"${amount}"
        return f"${amount:.2f}"

    return f"{currency} {amount}"


def parse_events(
    page_html: str,
    target_dates: set[str],
    *,
    include_online: bool,
    include_suburbs: bool,
    categories: set[str] | None = None,
    fetched_category: str | None = None,
) -> dict[str, list[dict[str, str]]]:
    apollo_state = extract_apollo_state(page_html)
    grouped = {date: [] for date in sorted(target_dates)}
    seen_urls: set[str] = set()

    for key, node in apollo_state.items():
        if not key.startswith("Event:") or not isinstance(node, dict):
            continue

        date_time = node.get("dateTime") or ""
        event_date = date_time[:10]
        if event_date not in grouped:
            continue

        url = node.get("eventUrl") or ""
        title = clean_text(node.get("title") or "")
        if not url or not title or url in seen_urls:
            continue

        venue = node.get("venue") if isinstance(node.get("venue"), dict) else {}
        venue_name = clean_text(venue.get("name") or "")
        venue_address = clean_text(venue.get("address") or "")
        venue_city = clean_text(venue.get("city") or "")
        is_online = venue_name.lower() == "online event"
        if is_online and not include_online:
            continue
        if venue_city and venue_city.lower() != "chicago" and not include_suburbs:
            continue

        group_ref = node.get("group", {}).get("__ref") if isinstance(node.get("group"), dict) else None
        group = apollo_state.get(group_ref, {}) if group_ref else {}
        rsvp_total = ""
        if isinstance(node.get("rsvps"), dict):
            total_count = node["rsvps"].get("totalCount")
            if total_count is not None:
                rsvp_total = str(total_count)

        event = {
            "title": title,
            "date": event_date,
            "time": date_time[11:16] if len(date_time) >= 16 else "",
            "date_time": date_time,
            "group": clean_text(group.get("name") or "") if isinstance(group, dict) else "",
            "venue": venue_name,
            "address": venue_address,
            "city": venue_city,
            "price": format_price(node.get("feeSettings")),
            "rsvp_count": rsvp_total,
            "description": clean_text(node.get("description") or ""),
            "url": url,
        }
        inferred_categories = infer_categories(event)
        event["categories"] = [fetched_category] if fetched_category else inferred_categories
        if categories and "all-events" not in categories and fetched_category is None:
            if not any(category in inferred_categories for category in categories):
                continue

        grouped[event_date].append(event)
        seen_urls.add(url)

    for date in grouped:
        grouped[date].sort(key=lambda event: (event["date_time"], event["title"]))

    return grouped


def print_events(
    date: str,
    events: list[dict[str, str]],
    description_limit: int,
    multiple_dates: bool,
) -> None:
    if multiple_dates:
        print(f"=== {date} ===")
        print()

    print(f"MEETUP — {len(events)} events on {date}:")
    print()
    for event in events:
        print(f"• {event['title']}")

        summary_parts = [part for part in [event["time"], event["group"]] if part]
        if summary_parts:
            print(f"  {' | '.join(summary_parts)}")

        location_parts = [part for part in [event["venue"], event["address"], event["city"]] if part]
        if location_parts:
            print(f"  {', '.join(location_parts)}")

        detail_parts = []
        if event["price"]:
            detail_parts.append(event["price"])
        if event["rsvp_count"]:
            detail_parts.append(f"RSVPs: {event['rsvp_count']}")
        if detail_parts:
            print(f"  {' | '.join(detail_parts)}")

        if event["categories"]:
            labels = [CATEGORY_LABELS[category] for category in event["categories"]]
            print(f"  Categories: {', '.join(labels)}")

        print(f"  {event['url']}")
        if event["description"]:
            print(f"  {event['description'][:description_limit]}")
        print()


def main() -> None:
    args = parse_args()
    dates = [normalize_date(raw_date) for raw_date in args.dates]
    selected_categories = set(args.category or [])

    if args.input_file and len(dates) != 1:
        raise SystemExit("--input-file supports exactly one DATE.")
    if args.input_file and args.meetup_url:
        raise SystemExit("--input-file and --meetup-url cannot be used together.")
    if args.meetup_url and dates:
        raise SystemExit("DATE arguments cannot be combined with --meetup-url.")
    if not args.meetup_url and not dates:
        raise SystemExit("Provide at least one DATE or use --meetup-url.")

    if args.meetup_url:
        events = fetch_events_for_meetup_url(args.meetup_url)
        print_events(
            "Meetup URL Results",
            events,
            args.description_limit,
            multiple_dates=False,
        )
        return

    multiple_dates = len(dates) > 1
    for date in dates:
        if args.input_file:
            with open(args.input_file, "r", encoding="utf-8") as handle:
                page_html = handle.read()
            grouped = parse_events(
                page_html,
                {date},
                include_online=args.include_online,
                include_suburbs=args.include_suburbs,
                categories=selected_categories,
            )
            print_events(date, grouped[date], args.description_limit, multiple_dates)
            continue

        events = fetch_events_for_date(
            date,
            include_online=args.include_online,
            include_suburbs=args.include_suburbs,
            categories=selected_categories,
        )
        print_events(date, events, args.description_limit, multiple_dates)


if __name__ == "__main__":
    main()
