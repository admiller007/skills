---
name: chicago-events-finder
description: >
  Find events, things to do, activities, and happenings in the Chicago area by
  searching across major Chicago event sources. Use this skill whenever the user
  asks about Chicago events, weekend plans, tonight's options, concerts, comedy,
  festivals, food events, family activities, free things to do, nightlife, or
  similar discovery queries. This skill is designed to work across both Codex-
  style and Claude-style agent environments.
---

# Chicago Events Finder

This skill helps an agent answer "what is happening in Chicago?" questions with
high recall, useful curation, and consistent output.

It is written to be portable across agent runtimes. Do not assume any specific
tool names such as `web_search`, `web_fetch`, or a particular shell wrapper.
Instead, map the instructions below onto whatever capabilities are available in
the current environment.

## Compatibility

This skill should work in both Codex-like and Claude-like environments.

- If web search is available, use it for editorial sources and discovery.
- If direct HTTP fetch is available, use it for known URLs and APIs.
- If shell execution is available, prefer the local helper scripts in `scripts/`
  for repeatable parsing.
- If shell execution is not available, reproduce the same logic directly from the
  local reference docs.
- If a capability is unavailable, fall back to the next-best source instead of
  failing the whole task.

## Local Files

This skill expects these local files to exist beside `SKILL.md`:

- `references/eventbrite.md`
- `references/chicago-park-district.md`
- `references/html-sources.md`
- `references/meetup.md`
- `references/evvnt-sources.md`
- `references/web-sources.md`
- `references/enrichment-sources.md`
- `scripts/do312_events.py`
- `scripts/chicago_on_the_cheap_events.py`
- `scripts/chicago_park_district_events.py`
- `scripts/evvnt_events.py`
- `scripts/meetup_events.py`
- `scripts/secret_chicago_editorial.py`
- `scripts/timeout_chicago_editorial.py`

Read only the files needed for the current query. Do not load every reference by
default unless the user asked for a broad or "surprise me" search.

## Core Rule

Run the high-yield structured sources first. Editorial web search is a supplement,
not the primary source of truth.

Priority order:

1. Structured sources with direct retrieval or local parsing
2. Editorial web sources for curated additions
3. Known URL-pattern sources and broad search fallbacks

## Inputs To Extract

From the user's request, determine:

- When: today, tonight, this weekend, next week, exact date, or open-ended
- What: music, comedy, food, art, theater, family, free, nightlife, festivals,
  outdoor, or broad discovery
- Vibe: budget-friendly, date night, hidden gem, major event, family-friendly
- Constraints: neighborhood, accessibility, indoor/outdoor, kosher-friendly food,
  age restrictions, travel radius
- Enrichment fit: art-house film, repertory cinema, theater, live music,
  museum/library programming, Jewish community events, kosher updates, or
  North Side / 60645 relevance

## Defaulting Rules

Use these rules so different models behave consistently:

- If the user gives a date or date range but no category, ask one short follow-up
  question only if the result set would otherwise be too broad.
- If asking a follow-up is awkward or the environment encourages fewer questions,
  default to a broad "surprise me" pull and curate across categories.
- If the user says "tonight" or "today", bias toward events with explicit times.
- If the user says "this weekend", organize results by day.
- If the user gives no budget, include both free and paid options.
- If the user appears to be on the North Side or mentions West Rogers Park, give a
  small preference to nearby options when relevance is otherwise tied.
- If the user mentions Aaron, 60645, West Rogers Park, Jewish community, kosher
  food, art-house film, repertory screenings, or "Second City Dispatch", run the
  enrichment sources after the broad Tier 1 pull.
- If an otherwise strong event falls Friday night through Saturday daytime and
  the user's context suggests Shabbat observance, include the event but plainly
  flag the scheduling conflict instead of hiding it.

## Source Registry

### Tier 1: Structured and High-Recall Sources

These should be the first sources used for most queries.

| Source | Local reference | Best for |
|---|---|---|
| Eventbrite | `references/eventbrite.md` | Broad coverage, niche events, pop-ups, community, ticketed events |
| Chicago Park District | `references/chicago-park-district.md` | Free, family, outdoor, neighborhood, civic, and park-hosted events |
| Chicago Reader via evvnt | `references/evvnt-sources.md` | Indie theater, comedy, arts, counterculture |
| Do312 | `references/html-sources.md` | Music, nightlife, DJ events, comedy |
| Chicago on the Cheap | `references/html-sources.md` | Free and cheap events, museum days, budget finds |
| Your Chicago Guide via evvnt | `references/evvnt-sources.md` | Community, family, workshops, niche events |
| Meetup | `references/meetup.md` | Workshops, hobby groups, tech, social, volunteer, and community events |

### Tier 2: Editorial and Curated Sources

Use these after Tier 1 or when the user wants major events, seasonal roundups, or
more editorial recommendations.

| Source | Local reference | Best for |
|---|---|---|
| Choose Chicago | `references/web-sources.md` | Major festivals, tourism, annual events |
| Time Out Chicago | `references/web-sources.md` | Best-of guides, attractions, monthly curation, cool-stuff discovery |
| Secret Chicago | `references/web-sources.md` | Hidden gems, immersive experiences, unique outings, buzzier pop-up discovery |

### Enrichment Sources: High-Signal Local Calendars

Use these after the broad structured pull when the user wants sharper curation,
North Side relevance, Jewish/community programming, family options, art-house
film, or venue-specific recommendations.

| Source group | Local reference | Best for |
|---|---|---|
| Art-house cinemas | `references/enrichment-sources.md` | Music Box, Siskel, Davis, Logan screenings, repertory series, Q&As |
| Theater calendars | `references/enrichment-sources.md` | Broadway in Chicago, Goodman, Steppenwolf, Lookingglass, Court |
| Music venues | `references/enrichment-sources.md` | Old Town School, Thalia Hall, Lincoln Hall, Schubas, Empty Bottle, Green Mill, Constellation |
| Library and museums | `references/enrichment-sources.md` | Chicago Public Library, Field Museum, Art Institute, MCA, MSI, family programming |
| Jewish and kosher sources | `references/enrichment-sources.md` | JUF, Chicago Jewish News, CRC kosher updates, holiday-adjacent events |
| City Cast / Hey Chicago | `references/enrichment-sources.md` | Daily pulse-check, neighborhood picks, editor-prioritized event leads |

### Tier 3: Broad Fallback Search

Use broad web search only when:

- a source is blocked
- a monthly roundup has not published yet
- the user wants a very recent major event
- you need to find a known event that did not appear in Tier 1

## Source Expansion Queue

Use this as the running list of source work.

### Added

| Source | Status | Notes |
|---|---|---|
| Eventbrite | Implemented | Broad high-recall source |
| Chicago Park District | Implemented | Official neighborhood, free, family, and outdoor events |
| Chicago Reader via evvnt | Implemented | Indie arts, theater, comedy |
| Do312 | Implemented | Music, nightlife, comedy |
| Chicago on the Cheap | Implemented | Free and cheap events |
| Your Chicago Guide via evvnt | Implemented | Community and family events |
| Meetup | Implemented | Workshops, hobby groups, tech, social, and community events |
| Choose Chicago | Documented | Editorial and major events |
| Time Out Chicago | Implemented | Editorial guide parser for weekend and guide pages |
| Secret Chicago | Implemented | Editorial roundup parser for monthly roundups |
| Art-house cinema calendars | Documented | Music Box, Siskel, Davis, and Logan screenings |
| Theater calendars | Documented | Broadway in Chicago, Goodman, Steppenwolf, Lookingglass, Court |
| Music venue calendars | Documented | Old Town School, Thalia Hall, Lincoln Hall, Schubas, Empty Bottle, Green Mill, Constellation |
| Library and museum calendars | Documented | CPL, Field Museum, Art Institute, MCA, MSI, family programming |
| Jewish and kosher sources | Documented | JUF, Chicago Jewish News, CRC kosher updates |
| City Cast / Hey Chicago | Documented | Editorial pulse-check and neighborhood-scale picks |

### Next Sources To Add

| Source | Priority | Why add it |
|---|---|---|
| Navy Pier | High | Seasonal, family, waterfront, and major public events |
| Songkick | High | Biggest likely coverage gain for concerts and live music |
| Chicago Children's Museum | Medium | Strong family and kids event coverage |
| Synagogue and JCC calendars | Medium | Hyperlocal Jewish lectures, concerts, classes, and holiday programming |

## Which References To Read

Read the smallest useful set:

| Query type | Read these files |
|---|---|
| Broad or surprise me | `references/eventbrite.md`, `references/chicago-park-district.md`, `references/html-sources.md`, `references/meetup.md`, `references/evvnt-sources.md`, `references/web-sources.md` |
| Aaron, 60645, West Rogers Park, or Second City Dispatch | Broad set plus `references/enrichment-sources.md` |
| Music or concerts | `references/html-sources.md`, `references/eventbrite.md` |
| Venue-specific live music | `references/enrichment-sources.md`, `references/html-sources.md` |
| Comedy, theater, improv | `references/evvnt-sources.md`, `references/eventbrite.md` |
| Theater or performing arts | `references/enrichment-sources.md`, `references/evvnt-sources.md` |
| Art-house film or repertory cinema | `references/enrichment-sources.md` |
| Free or cheap | `references/chicago-park-district.md`, `references/html-sources.md`, `references/eventbrite.md`, `references/web-sources.md` |
| Food or drink | `references/eventbrite.md`, `references/web-sources.md`, `references/meetup.md` |
| Family or kids | `references/chicago-park-district.md`, `references/evvnt-sources.md`, `references/eventbrite.md`, `references/meetup.md`, `references/enrichment-sources.md` |
| Museum or library programming | `references/enrichment-sources.md`, `references/chicago-park-district.md` |
| Jewish community or kosher | `references/enrichment-sources.md`, `references/eventbrite.md`, `references/meetup.md` |
| Neighborhood or hyperlocal | `references/chicago-park-district.md`, `references/eventbrite.md`, `references/meetup.md` |
| Workshops, tech, hobby, or social | `references/meetup.md`, `references/eventbrite.md`, `references/evvnt-sources.md` |
| Hidden gems | `references/web-sources.md`, `references/evvnt-sources.md`, `references/eventbrite.md` |

## Capability Mapping

Translate the skill into the current runtime rather than assuming exact tool names.

### If shell execution is available

- Prefer the local scripts in `scripts/` for Do312, Chicago on the Cheap, evvnt, and Meetup.
- Use direct HTTP requests for Eventbrite if the environment allows it.
- Use web search only for editorial sources and broad fallback search.

### If shell execution is not available but HTTP fetch is available

- Recreate the source-specific logic from the local reference docs.
- Prefer direct API calls or URL fetches over generic web search.
- Use editorial web search only for curated sources and fallback discovery.

### If only web search and page fetch are available

- Use editorial sources first.
- Use search-engine indexing to locate source pages that are not easily fetched.
- Be explicit that coverage is lower than the full structured-source workflow.

## Deterministic Workflow

Follow these steps in order.

### Step 1: Normalize the request

- Convert relative dates into exact calendar dates before querying any source.
- Keep a normalized internal representation for each target day.
- If the user asks for a range, preserve both the display phrasing and the exact dates.

### Step 2: Choose sources

- Start with the Tier 1 sources that best match the category.
- For broad discovery, hit all Tier 1 sources.
- Add Tier 2 editorial sources only after the structured pull.
- Add enrichment sources when the query calls for Aaron-specific curation,
  venue-specific programming, family/library/museum picks, Jewish/kosher
  programming, or North Side / 60645 relevance.
- Use Tier 3 fallback search only if needed.
- Treat Time Out Chicago and Secret Chicago as editorial discovery sources.
- Do not assume a guide page proves an item happens on the requested day; verify the
  exact date and time on the linked event page before presenting it as a specific-date
  recommendation.

### Step 3: Retrieve candidate events

- Gather more results than you plan to show.
- Prefer source-native filtering where available.
- For source-specific retrieval details, follow the corresponding local reference file.

### Step 4: Filter the candidates

Exclude or down-rank:

- events outside Chicago when the user asked for Chicago specifically
- virtual events unless the user asked for online options
- obvious suburbs unless the event is exceptional or the user allowed a wider radius
- duplicate event listings from multiple sources
- listings with missing title, date, or usable link

### Step 5: Deduplicate across sources

Deduplicate across all sources, not just within each source.

Use a normalized identity based on:

- title after lowercasing and stripping punctuation
- start date
- venue name when available

If two rows appear to be the same event:

- keep the richest record
- preserve a list of supporting sources internally
- prefer the cleanest public link for the final answer

### Step 6: Rank

Rank by:

1. relevance to the user's category and vibe
2. fit to the requested date and neighborhood
3. event specificity and completeness
4. editorial interest or uniqueness
5. price fit if the user mentioned budget

Do not simply sort by source.

### Step 7: Curate the final set

- Return 10 to 15 events for broad requests.
- Return fewer if the user asked for a narrow category and only a few strong matches exist.
- For "surprise me", include variety across categories.
- For weekend requests, group by day.
- For tonight requests, group roughly by start time.

## Output Contract

Use this structure unless the user asked for a different format:

```md
## Chicago Events: [date range or category]

### [Day or category]

**[Event name]** - [venue or area]
[Date and time] | [Price or "Free"] | [Source](URL)
[1 to 2 sentence summary]

---

### Tips

### Source Scorecard
| Source | Method | Events Found |
```

Output rules:

- Lead with the strongest recommendations, not the noisiest source.
- Always include a working source link when possible.
- Include price info when available.
- Be transparent when time or price is unknown.
- Mention neighborhood when it helps the user choose.
- For food events, note kosher-friendliness only when you have evidence or a clear reason.
- For venue calendars, prefer official venue links for exact showtimes, addresses,
  ticket prices, age restrictions, and accessibility details.
- For Shabbat-aware queries, flag Friday-night and Saturday-daytime timing conflicts
  in plain language.
- Keep the source scorecard based on actual counts gathered in the run, not static estimates.

## Special Query Handling

### Free this weekend

- Start with Chicago Park District and Chicago on the Cheap
- Add Eventbrite with free-oriented queries
- Add Choose Chicago or Time Out for big free festivals and museum days

### Music or concerts tonight

- Start with Do312
- Add Chicago Reader for smaller venues
- Add Eventbrite for overflow and niche listings
- For North Side or higher-curation requests, check the music venue calendars in
  `references/enrichment-sources.md`, especially Old Town School, Lincoln Hall,
  Schubas, Empty Bottle, Green Mill, Thalia Hall, and Constellation.

### Theater, comedy, improv

- Start with Chicago Reader
- Add Eventbrite
- Use Do312 only if it produces relevant overlap
- For theater-specific requests, check official theater calendars in
  `references/enrichment-sources.md` before relying on aggregators.

### Art-house film or repertory screenings

- Start with official cinema calendars in `references/enrichment-sources.md`.
- Prioritize one-night screenings, repertory series, 35mm/70mm presentations,
  filmmaker Q&As, festivals, and kid-appropriate matinees.
- Verify exact showtimes on the official cinema page.

### Hidden gems or unique experiences

- Start with Secret Chicago and Chicago Reader
- Add Eventbrite for niche events
- Down-rank generic tourist attractions unless they are timely

### Family activities

- Start with Chicago Park District
- Start with Your Chicago Guide
- Add Eventbrite
- Add Chicago Public Library and museum calendars from `references/enrichment-sources.md`
  for kid-friendly workshops, story times, free days, and special exhibits.
- Add editorial sources if the user wants highly curated picks

### Neighborhood or hyperlocal activities

- Start with Chicago Park District
- Use its park, community area, zip code, and proximity filters when available
- Add Eventbrite only as a secondary source for overflow
- For 60645 / North Side relevance, add CPL branch events, nearby theater/cinema
  calendars, Old Town School, and City Cast / Hey Chicago pulse-checks from
  `references/enrichment-sources.md`.

### Jewish community or kosher events

- Start with JUF, Chicago Jewish News, CRC, Eventbrite, and Meetup.
- Prefer official organization or certifying-agency pages for dates, locations,
  registration links, and kosher claims.
- Do not infer kosher status from event vibe or venue name. State kosher relevance
  only when the source supports it.

## Fallback Behavior

If a source is unavailable:

- say briefly that the source could not be queried
- continue with the remaining sources
- do not abandon the request if partial coverage is still possible

If coverage is weak:

- say that the result set is lower confidence
- broaden with editorial sources or broad web search
- prefer quality over padding the answer with weak events

## Notes

- Eventbrite can leak suburbs and virtual events; filter carefully.
- Chicago Park District is one of the best sources for official neighborhood and family events.
- Chicago Reader and Do312 often complement each other rather than overlap.
- Fridays and Saturdays usually have the highest volume.
- Mondays and Tuesdays are thinner, so editorial sources may matter more.
- For major annual events, Choose Chicago is often the authority.
- Use the local scripts when possible because they make behavior more repeatable across runs.
