# Enrichment Sources

These sources sharpen broad Chicago event discovery with venue-specific calendars,
North Side relevance, art-house film, family programming, Jewish community events,
and kosher updates. Use them after the broad Tier 1 pull or immediately when the
user asks for one of these categories.

Use official venue or organization pages for exact dates, showtimes, prices,
addresses, age restrictions, and registration details. Editorial sources such as
City Cast and Hey Chicago are useful discovery cues, but verify event details on
the primary event page before presenting them.

---

## Art-House Cinema

Best for repertory programming, one-night screenings, festivals, filmmaker Q&As,
35mm/70mm screenings, kid-appropriate matinees, and distinctive local film picks.

Official calendars:

- Music Box Theatre: `https://musicboxtheatre.com/films-and-events`
- Gene Siskel Film Center: `https://www.siskelfilmcenter.org/films-events`
- Davis Theater: `https://www.davistheater.com/showtimes`
- Logan Theatre: `https://www.thelogantheatre.com/movie-theater/logan/showtimes`

Search patterns:

```text
web_search: site:musicboxtheatre.com Chicago [DATE_OR_MONTH] film
web_search: site:siskelfilmcenter.org [DATE_OR_MONTH] Chicago screening
web_search: site:davistheater.com showtimes [DATE]
web_search: site:thelogantheatre.com showtimes [DATE]
```

What to extract:

- film title, date, showtime, theater, series name, format, and guest/Q&A details
- whether it is a one-night screening or part of a limited series
- official ticket or showtime URL

Ranking notes:

- Up-rank repertory series, filmmaker appearances, festivals, 35mm/70mm, and
  family matinees over ordinary first-run showtimes.
- For Shabbat-aware users, flag Friday-night and Saturday-daytime conflicts.

---

## Theater And Performing Arts

Best for opening weeks, previews, limited runs, touring productions, local theater,
and performances that aggregators may miss.

Official calendars:

- Broadway In Chicago: `https://www.broadwayinchicago.com/shows/`
- Goodman Theatre: `https://www.goodmantheatre.org/`
- Steppenwolf Theatre: `https://www.steppenwolf.org/`
- Lookingglass Theatre: `https://lookingglasstheatre.org/`
- Court Theatre: `https://www.courttheatre.org/`

Search patterns:

```text
web_search: site:broadwayinchicago.com/shows Chicago [DATE_OR_MONTH]
web_search: site:goodmantheatre.org [DATE_OR_MONTH] tickets Chicago
web_search: site:steppenwolf.org [DATE_OR_MONTH] tickets Chicago
web_search: site:lookingglasstheatre.org [DATE_OR_MONTH] tickets Chicago
web_search: site:courttheatre.org [DATE_OR_MONTH] tickets Chicago
```

What to extract:

- show title, venue, run dates, exact performance time, ticket link, and whether
  the date is opening night, preview, closing weekend, talkback, or accessibility
  performance

Ranking notes:

- Up-rank opening/closing weekends, talkbacks, limited runs, notable local
  companies, and performances with family relevance.
- Use Chicago Reader or other editorial sources for critical context, but keep
  the official venue page as the date/time source.

---

## Music Venue Calendars

Best for live music picks that are more curated than broad aggregators, especially
North Side venues and jazz/folk/indie programming.

Official calendars:

- Old Town School of Folk Music: `https://www.oldtownschool.org/concerts/`
- Thalia Hall: `https://www.thaliahallchicago.com/`
- Lincoln Hall: `https://lh-st.com/`
- Schubas: `https://lh-st.com/`
- Empty Bottle: `https://www.emptybottle.com/`
- Green Mill: `https://greenmilljazz.com/`
- Constellation: `https://constellation-chicago.com/`

Search patterns:

```text
web_search: site:oldtownschool.org/concerts [DATE_OR_MONTH] Chicago concert
web_search: site:thaliahallchicago.com [DATE_OR_MONTH] Chicago
web_search: site:lh-st.com [DATE_OR_MONTH] Lincoln Hall Schubas
web_search: site:emptybottle.com [DATE_OR_MONTH] Chicago
web_search: site:greenmilljazz.com [DATE_OR_MONTH] Chicago
web_search: site:constellation-chicago.com [DATE_OR_MONTH] Chicago
```

What to extract:

- artist, venue, date, doors/show time, price, age restriction, neighborhood, and
  official ticket URL

Ranking notes:

- Up-rank Old Town School, Green Mill, Constellation, Lincoln Hall, and Schubas
  for North Side relevance.
- Do not assume all music venue listings are family-friendly. Include age
  restrictions when available.

---

## Libraries, Museums, And Family Programming

Best for kid-friendly events, free programming, museum exhibits, branch library
events, and weekend options that large event sites miss.

Official calendars:

- Chicago Public Library events: `https://chipublib.bibliocommons.com/events`
- Field Museum events: `https://www.fieldmuseum.org/our-events`
- Art Institute events: `https://www.artic.edu/events`
- MCA Chicago events: `https://visit.mcachicago.org/events`
- Museum of Science and Industry events/exhibits: `https://www.msichicago.org/explore/whats-here/`

Search patterns:

```text
web_search: site:chipublib.bibliocommons.com/events [BRANCH_OR_NEIGHBORHOOD] [DATE]
web_search: site:fieldmuseum.org/our-events [DATE_OR_MONTH] Chicago
web_search: site:artic.edu/events [DATE_OR_MONTH] family Chicago
web_search: site:visit.mcachicago.org/events [DATE_OR_MONTH] Chicago
web_search: site:msichicago.org [DATE_OR_MONTH] exhibit event Chicago
```

Nearby CPL branches to try for West Rogers Park / 60645 queries:

- Northtown
- West Ridge
- Rogers Park
- Edgewater
- Budlong Woods
- Lincoln Belmont

What to extract:

- event title, venue or branch, target age range, date/time, registration
  requirement, price, and official URL

Ranking notes:

- Up-rank free branch programming, kid-specific age ranges, hands-on workshops,
  museum free days, and exhibits with limited dates.

---

## Jewish Community And Kosher Sources

Best for Jewish community lectures, concerts, holiday programming, fundraising
events, school/community programs, and kosher certification updates.

Primary sources:

- JUF news: `https://www.juf.org/news`
- JUF events: search within `juf.org` for events and program pages
- Chicago Jewish News: `https://chicagojewishnews.com/`
- Chicago Rabbinical Council kosher updates: `https://www.crcweb.org/`

Search patterns:

```text
web_search: site:juf.org Chicago Jewish events [DATE_OR_MONTH]
web_search: site:juf.org/news Chicago Jewish [DATE_OR_MONTH]
web_search: site:chicagojewishnews.com Chicago event [DATE_OR_MONTH]
web_search: site:crcweb.org kosher Chicago update
web_search: Chicago Jewish lecture concert holiday event [DATE_OR_MONTH]
```

What to extract:

- event title, organization, speaker/performer, date/time, location, registration
  link, holiday relevance, and any explicitly sourced kosher details

Kosher handling:

- Do not infer kosher status from a Jewish venue or community context.
- Use CRC or the event host's explicit language for kosher claims.
- If kosher status is unclear, say it is unclear and link the source.

Shabbat handling:

- If the user's context suggests Shabbat observance, flag Friday-night and
  Saturday-daytime events as scheduling conflicts rather than excluding them.

---

## City Cast Chicago And Hey Chicago

Best for daily pulse-checks, editor-prioritized local stories, neighborhood event
mentions, and "what Chicago editors think matters today."

Sources:

- City Cast Chicago homepage: `https://chicago.citycast.fm/`
- Hey Chicago newsletter archive: `https://chicago.citycast.fm/newsletter`

Search patterns:

```text
web_search: site:chicago.citycast.fm Chicago events this weekend
web_search: site:chicago.citycast.fm/newsletter Hey Chicago [DATE_OR_MONTH]
web_search: site:chicago.citycast.fm [NEIGHBORHOOD] Chicago events
```

Workflow:

1. Use City Cast / Hey Chicago as an editorial pulse-check after structured sources.
2. Extract event leads, neighborhoods, and sources they mention.
3. Verify exact event details on the primary source before final inclusion.

Do not treat podcast titles or newsletter summaries as final event records unless
they link to a concrete event page with details.

---

## Neighborhood Pulse For 60645 And Nearby Areas

Use these searches when the user asks for local, family, or Aaron-relevant picks.

Neighborhoods:

- West Rogers Park
- Rogers Park
- Edgewater
- Lincoln Square
- Andersonville
- Uptown
- West Ridge

Search patterns:

```text
web_search: [NEIGHBORHOOD] Chicago events this weekend
web_search: site:blockclubchicago.org [NEIGHBORHOOD] event Chicago
web_search: site:choosechicago.com [NEIGHBORHOOD] events Chicago
web_search: site:chipublib.bibliocommons.com/events [NEIGHBORHOOD]
```

Ranking notes:

- Up-rank events within walking distance or a short drive of 60645 when relevance
  is otherwise tied.
- Do not over-weight proximity if a citywide event is clearly stronger.
