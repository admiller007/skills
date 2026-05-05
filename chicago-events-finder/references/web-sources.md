# Web Search Sources — Tier 1 & Tier 3

These sources work via standard `web_search` + `web_fetch`. They provide curated
editorial content that complements the raw calendar data from Tier 2 APIs.

---

## Tier 1: Choose Chicago & Time Out

### Choose Chicago (choosechicago.com)

Best for major festivals, annual events, and curated tourism content.

**Search patterns:**
```
web_search: site:choosechicago.com events [CATEGORY] [DATE_RANGE]
web_search: site:choosechicago.com free events [MONTH YEAR]
web_search: site:choosechicago.com festivals [YEAR]
```

Key pages that index well:
- `choosechicago.com/events/` — main events calendar
- `choosechicago.com/blog/free-cheap/10-free-things-to-do-in-chicago/` — monthly free roundup
- `choosechicago.com/articles/festivals-special-events/chicago-festival-event-guide/` — annual guide

### Time Out Chicago (timeout.com/chicago)

Best for curated "best of" guides, museums, and monthly event roundups.
Local helper: `scripts/timeout_chicago_editorial.py`

Use Time Out as an editorial discovery source, not a strict date-filtered calendar.
It is best for finding cool, high-signal ideas, then verifying the exact day and
time on the linked event page.

**Search patterns:**
```
web_search: site:timeout.com/chicago [CATEGORY] [DATE_RANGE]
web_search: site:timeout.com/chicago best things to do [MONTH] [YEAR]
web_search: site:timeout.com/chicago events calendar [MONTH]
```

Key pages:
- `timeout.com/chicago/events-calendar/april-events-calendar` — monthly calendar
- `timeout.com/chicago/things-to-do/best-things-to-do-this-weekend-in-chicago` — weekend guide
- Monthly "best of" roundups index well in search

Example script usage:
```bash
python3 scripts/timeout_chicago_editorial.py
python3 scripts/timeout_chicago_editorial.py --url "https://www.timeout.com/chicago/events-calendar/april-events-calendar"
```

Recommended workflow:
1. Start from a weekend guide, monthly calendar, or category guide.
2. Pull the linked items from the guide page.
3. Open the linked event pages for any promising picks.
4. Verify the exact date/time on the destination page before using the result for
   a specific-day answer.

### General Broad Search

Catches Ticketmaster, SeatGeek, and other JS-walled sites via search engine snippets:
```
web_search: things to do in Chicago [this weekend / tonight / DATE]
web_search: Chicago events [DATE]
web_search: Chicago concerts [DATE]
```

### Category Keyword Mappings for Web Search

| User says | Search keywords |
|-----------|----------------|
| music, concerts | live music, concerts, shows |
| comedy | comedy shows, stand-up, improv |
| food, dining | food events, food festival, restaurant |
| art, culture | art exhibition, gallery, museum |
| family, kids | family-friendly, kids events |
| free, cheap | free events, cheap, budget-friendly |
| nightlife | nightlife, DJ, party, bar events |
| theater | theater, theatre, performing arts |
| festivals | festival, street fair, block party |
| outdoor | outdoor events, parks, lakefront |

---

## Tier 3: Secret Chicago

Secret Chicago publishes curated monthly roundup articles with server-rendered HTML.
These are editorially curated — expect 8-15 recommendations per month covering
restaurants, experiences, concerts, and seasonal activities.
Local helper: `scripts/secret_chicago_editorial.py`

Use Secret Chicago as a monthly or thematic idea generator, not a precise day-by-day
 event calendar. It is strongest for uncovering pop-ups, immersive experiences,
 openings, and unique seasonal picks that should then be date-checked on the linked
 destination page.

**URL pattern:** `secretchicago.com/things-to-do-in-chicago-[month]-[year]/`

Example: `secretchicago.com/things-to-do-in-chicago-april-2026/`

Example script usage:
```bash
python3 scripts/secret_chicago_editorial.py 2026-04-12
python3 scripts/secret_chicago_editorial.py --url "https://secretchicago.com/things-to-do-in-chicago-april-2026/"
```

Recommended workflow:
1. Use the monthly roundup or a thematic article to collect candidate ideas.
2. Prioritize items with words like `new`, `opening`, `immersive`, `popup`,
   `festival`, `market`, or `limited-time`.
3. Verify the exact day and hours on the linked event or venue page before using
   the item in a specific-date answer.

### Steps
1. Search for the roundup:
```
web_search: site:secretchicago.com things to do [MONTH] [YEAR]
```

2. Fetch the URL matching the pattern above via `web_fetch`.

### Fallback
If the monthly roundup doesn't exist yet:
```
web_search: site:secretchicago.com Chicago [CATEGORY] [YEAR]
```
This surfaces evergreen "best of" lists (candlelight concerts, dining in the dark, etc.)

### Content profile
- Curated hidden gems: new restaurant openings, unique pop-up experiences, candlelight
  concerts, seasonal activities, immersive experiences
- Strong on food/drink and unique experiences
- Less overlap with calendar-based sources — editorial perspective adds value
