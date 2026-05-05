# HTML Scrape Sources — Do312 & Chicago on the Cheap

Both sites render server-side HTML. Web search/web_fetch cannot see the event data reliably.
Use `bash_tool` with `curl` to scrape.

---

## Do312 — BEST FOR MUSIC/NIGHTLIFE (~25 events/Friday)

Server-side rendered date pages with full event listings.

**URL pattern:** `https://do312.com/events/YYYY/MM/DD`
**Script:** `scripts/do312_events.py`

### Single Day
```bash
python3 scripts/do312_events.py 2026-04-10
```

### Weekend (both days)
```bash
python3 scripts/do312_events.py 2026-04-10 2026-04-11
```

### Notes
- The regex parser now lives in `scripts/do312_events.py`
- Match the anchor with `ds-listing-event-title`, then extract the nested
  `ds-listing-event-title-text` span for the visible title
- Extract the event URL alongside the title so every result can include a source link
- Venue/time data is in the page but requires more complex parsing; titles + event URLs
  are sufficient for discovery, and the event page can be fetched for details
- Use `--input-file saved-do312.html` to test parser changes against captured HTML
- ~25 events on Fridays, ~20 Saturdays, ~10-15 Sundays, ~5 weekdays

---

## Chicago on the Cheap — BEST FOR FREE/CHEAP EVENTS (~10 events/Friday)

WordPress events plugin renders server-side HTML with times, prices, and venues.

**URL pattern:** `https://chicagoonthecheap.com/events/view-date/MM-DD-YYYY/`
**Script:** `scripts/chicago_on_the_cheap_events.py`

### Single Day
```bash
python3 scripts/chicago_on_the_cheap_events.py 2026-04-10
```

### Weekend (both days)
```bash
python3 scripts/chicago_on_the_cheap_events.py 2026-04-11 2026-04-12
```

### Notes
- The regex parser now lives in `scripts/chicago_on_the_cheap_events.py`
- Event details include time ranges, prices (or "FREE"), and venue names inline
- Raw text format: `10:00 am to 5:00 pm | FREE | Garfield Park Conservatory`
- Each event links to a detail page on chicagoonthecheap.com with full descriptions
- Use `--input-file saved-cotc.html` to test parser changes against captured HTML
- ~10 events on Fridays, ~5-8 on weekends, ~3-5 on weekdays
- Strong for: free museum days, happy hours, free walking tours, budget dining
