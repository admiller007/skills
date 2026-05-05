# evvnt API Sources — Chicago Reader & Your Chicago Guide

Both sites use the evvnt discovery platform for their event calendars. The JS widget on
each site is invisible to web_search/web_fetch, but the REST API is fully accessible.

**API endpoint:** `https://discovery.evvnt.com/api/events`

| Site | Publisher ID | Best For | Typical Friday count |
|------|-------------|----------|---------------------|
| Chicago Reader | `9072` | Indie theater, comedy, art, counterculture | ~29 events |
| Your Chicago Guide | `7780` | Community events, family, niche | ~6 events |

---

## Chicago Reader (publisher_id=9072) — INDIE ARTS POWERHOUSE

**IMPORTANT: The `from`/`to` date params do NOT work reliably for this publisher.**
The API always returns events starting from the nearest upcoming dates regardless of
date filters. You MUST use `page=` pagination to reach your target date.

### Script (with pagination)
```bash
python3 scripts/evvnt_events.py chicago-reader 2026-04-10
```

### Content profile
- The pagination and filtering logic now lives in `scripts/evvnt_events.py`
- Very strong for: indie theater (Factory Theater, Den Theatre, Theater Wit, Steppenwolf,
  City Lit, Oil Lamp), improv/comedy (Second City, Annoyance Theatre), art openings,
  live music at small venues, burlesque/variety, counterculture
- Minimal overlap with Do312 — complementary sources
- Community-submitted events — different flavor than editorial sources
- Use `--max-pages` to widen the Chicago Reader scan window
- Use `--input-file saved-reader.json` to test parser changes against captured API payloads
- ~29 events Friday, ~25 Saturday, ~15 Sunday

---

## Your Chicago Guide (publisher_id=7780) — COMMUNITY & FAMILY

For this publisher, the `from`/`to` params generally work, but results may extend
beyond the requested range. Always filter by `start_date` in your parser.

### Script
```bash
python3 scripts/evvnt_events.py your-chicago-guide 2026-04-10
```

### Content profile
- The fetch and `start_date` filtering logic now lives in `scripts/evvnt_events.py`
- Community-submitted via evvnt platform
- Heavier on: family events, workshops, farmers markets, wellness, niche hobby events
- Pass multiple dates to cover a weekend or short range in one call
- Use `--input-file saved-ycg.json` to test parser changes against captured API payloads
- ~6 events per day on average
- Occasionally overlaps with Chicago Reader (same API platform, different curators)

---

## evvnt API Response Format

Both publishers return the same JSON structure:

```json
{
  "events": [
    {
      "title": "Event Name",
      "start_date": "2026-04-10",
      "venue": {
        "name": "Venue Name",
        "address": "123 Main St",
        "city": "Chicago"
      },
      "url": "https://...",
      "description": "Event description text...",
      "price": "optional price string"
    }
  ]
}
```

- Each page returns max 30 events
- Use `page=N` for pagination (1-indexed)
- `limit=30` is the max per page
- Events are sorted chronologically by start_date
