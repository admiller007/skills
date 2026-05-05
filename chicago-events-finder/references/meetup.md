# Meetup — Chicago GraphQL + Find Page

Meetup's date-scoped Chicago discovery page is useful for filter discovery and
location context, but the visible event list is not fully present in the initial
`__NEXT_DATA__` payload. The live helper follows Meetup's paginated GraphQL flow
at `https://www.meetup.com/gql2` so it can retrieve the later result pages that
load after hydration.

**URL pattern:** `https://www.meetup.com/find/?source=EVENTS&location=us--il--Chicago&customStartDate=...&customEndDate=...`
**Script:** `scripts/meetup_events.py`

---

## Single Day

```bash
python3 scripts/meetup_events.py 2026-04-12
```

## Weekend / Range

```bash
python3 scripts/meetup_events.py 2026-04-10 2026-04-11 2026-04-12
```

## Include Online Or Nearby Suburbs

```bash
python3 scripts/meetup_events.py 2026-04-12 --include-online --include-suburbs
```

## Filter By Meetup Category Bucket

```bash
python3 scripts/meetup_events.py 2026-04-16 --category technology
python3 scripts/meetup_events.py 2026-04-16 --category social-activities --category games
```

## Reproduce An Exact Meetup Find URL

```bash
python3 scripts/meetup_events.py --meetup-url "https://www.meetup.com/find/?location=us--il--Chicago&source=EVENTS&eventType=inPerson&categoryId=571&dateRange=this-week"
```

---

## Content Profile

- Strong for: workshops, hobby groups, tech meetups, social events, volunteer
  activities, classes, and neighborhood community gatherings
- The generic city page is too shallow for date-specific pulls; use the date-scoped
  `customStartDate` and `customEndDate` query params instead
- The helper now uses Meetup's real GraphQL queries from the client bundle:
  `recommendedEventsWithSeries` for the normal event view and
  `eventSearchWithSeries` when a category only has a keyword-backed query mapping
- The helper uses Meetup's real curated query params from the client bundle where
  available, such as `categoryId=546` for Technology and `categoryId=652` for
  Social Activities
- `--meetup-url` reproduces Meetup's own resolved query config from the page
  payload, which is the safest way to match relative ranges like `dateRange=this-week`
  and older or remapped category IDs
- Meetup still includes nearby suburbs and online events in date-scoped search; the
  script excludes those by default and keeps only events that are explicitly in
  Chicago or have no venue city attached
- Some visible buckets still do not expose a stable curated query mapping in the
  page bundle; those fall back to local text classification over title, group,
  venue, and description
- Use `--input-file saved-meetup.html` only to test the legacy HTML parser against
  captured pages

## Parser Notes

- Live fetches page through Meetup's GraphQL `pageInfo.endCursor` until
  `hasNextPage` is false
- Prices come from `feeSettings.amount` and RSVP counts come from `rsvps.totalCount`
- Online events typically have `isOnline=true` or venue name `Online event`
- The HTML parser still reads the `__NEXT_DATA__` script tag for saved-page testing,
  but it only reflects the first server-rendered page of results
