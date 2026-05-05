# Chicago Park District - Official Neighborhood Events

Chicago Park District's official Event Finder is a high-value source for free,
family-friendly, neighborhood, outdoor, civic, and park-hosted events that may
not appear on Eventbrite, Do312, or Chicago Reader.

Use it when the user asks for:

- family activities
- free things to do
- neighborhood or hyperlocal events
- outdoor activities
- park programming
- West Ridge, Rogers Park, North Side, or zip-specific options

## Primary URLs

- Main list view: `https://www.chicagoparkdistrict.com/events`
- Map view: `https://www.chicagoparkdistrict.com/events/map`
- Local script: `scripts/chicago_park_district_events.py`

Prefer the list view first. It exposes event titles, dates, addresses, times, and
pagination in server-rendered HTML.

## Why This Source Matters

- Official city-operated source
- Strong coverage for family, nature, wellness, volunteer, meeting, and park events
- Strong location filtering by park, community area, and zip code
- Good for finding events in neighborhoods that are underrepresented on larger platforms

## Filters Visible On The Event Finder

The list page exposes these filters:

- park
- community area
- zip code
- category
- age group
- address proximity

Observed categories on the official page include:

- Family Fun
- Festivals
- Movies
- Music
- Nature
- Night Out in the Parks
- Sports
- Theater
- Tours
- Volunteer Workdays
- Wellness
- Community Meetings
- Dance

Observed age groups include:

- Adult
- All Ages
- Early Childhood
- Senior
- Teen
- Youth

## What The List Page Gives You

The list page usually includes:

- event title
- date
- start and end time
- street address
- pagination

Example signals visible directly on the page:

- `### Event Title`
- `1234 W. Example St. Chicago, IL 606xx`
- `6:00 PM - 7:00 PM`

## What The Detail Page Adds

Individual event pages add:

- full date and weekday
- park name
- event fee, often `$0.00`
- age range
- categories
- description

This is useful when curating top picks because it lets you confirm whether an
event is free, family-friendly, or especially relevant.

## Retrieval Strategy

### Broad search

Use the main list page first and scan the first few pages for the requested date
range. This is usually enough for weekend curation.

If shell execution is available, prefer:

```bash
python3 scripts/chicago_park_district_events.py 2026-04-12
```

For a weekend:

```bash
python3 scripts/chicago_park_district_events.py 2026-04-11 2026-04-12
```

The site also supports an exact-date filter via `field_date_value=YYYY-MM-DD`, and
the script uses that filter directly before fetching event detail pages.

### Neighborhood search

If the user names a neighborhood or zip code, use Chicago Park District as a
priority source because the site supports park, community area, and zip filtering.

### Family or free search

Use this source early. It often returns stronger free and family options than
commercial aggregators.

## Output Guidance

- Prefer events with exact park names and addresses when the user wants local options.
- Mention that the event is official Chicago Park District programming when that adds trust.
- Include fee information from the detail page when available.
- Down-rank routine administrative meetings unless the user asked for civic/community events.

## Caveats

- Volume can be high, so this is better for curation than for dumping raw listings.
- Some events are narrowly local or administrative rather than recreational.
- The site is best for near-term discovery, especially this week and this weekend.
