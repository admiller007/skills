# Eventbrite — CSRF + Multi-Query Fan-Out

Eventbrite blocks direct page loads with AWS WAF captcha. Their internal destination
search API is accessible via a two-step CSRF flow.

**CRITICAL: The API returns max 10 unique events per query, and pagination just recycles them.
To get full coverage (~100 unique events for a Friday), you MUST fan out multiple category
queries and deduplicate by event ID.**

---

## Single-Category Query

Use when the user specified a category (e.g., "comedy", "music"):

```bash
COOKIES=$(mktemp)
curl -s -c "$COOKIES" -L -H "User-Agent: Mozilla/5.0" "https://www.eventbrite.com/" > /dev/null 2>&1
CSRF=$(grep csrf "$COOKIES" | awk '{print $NF}')

DATE="2026-04-10"  # YYYY-MM-DD
QUERY="chicago comedy"  # Use category mapping below

curl -s -X POST "https://www.eventbrite.com/api/v3/destination/search/" \
  -b "$COOKIES" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Referer: https://www.eventbrite.com/" \
  -d "{
    \"event_search\": {
      \"dates\": \"current_future\",
      \"date_range\": {\"from\":\"$DATE\",\"to\":\"$DATE\"},
      \"q\": \"$QUERY\"
    }
  }" | python3 -c "
import json, sys
data = json.load(sys.stdin)
results = data.get('events', {}).get('results', [])
print(f'EVENTBRITE — {len(results)} events:\n')
for e in results:
    name = e.get('name', '?')
    time = e.get('start_time', '')
    url = e.get('url', e.get('tickets_url', ''))
    cats = [t.get('display_name','') for t in e.get('tags', []) if t.get('prefix') == 'EventbriteCategory']
    print(f'• {name}')
    print(f'  {time} | {cats[0] if cats else \"\"} | {url}')
    print()
"
rm "$COOKIES"
```

---

## Full Fan-Out Script

Use for broad/"surprise me" queries — pulls ~100 unique events:

```bash
python3 << 'PYEOF'
import json, subprocess, tempfile, os

# Step 1: Get CSRF
cookies = tempfile.mktemp()
subprocess.run(["curl","-s","-c",cookies,"-L","-H","User-Agent: Mozilla/5.0",
    "https://www.eventbrite.com/"], capture_output=True)
csrf = ""
with open(cookies) as f:
    for line in f:
        if "csrf" in line.lower():
            csrf = line.strip().split("\t")[-1]

DATE = "2026-04-10"  # CHANGE THIS to target date

queries = [
    "chicago music concert", "chicago comedy", "chicago food drink",
    "chicago art gallery", "chicago theater", "chicago nightlife party",
    "chicago free", "chicago family kids", "chicago fitness yoga",
    "chicago workshop class", "chicago dance", "chicago outdoor",
    "chicago brunch", "chicago trivia karaoke", "chicago networking social",
]

all_events = {}
for q in queries:
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://www.eventbrite.com/api/v3/destination/search/",
        "-b", cookies, "-H", "Content-Type: application/json",
        "-H", f"X-CSRFToken: {csrf}", "-H", "User-Agent: Mozilla/5.0",
        "-H", "Referer: https://www.eventbrite.com/",
        "-d", json.dumps({"event_search": {"dates": "current_future",
            "date_range": {"from": DATE, "to": DATE}, "q": q}})
    ], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        for e in data.get("events", {}).get("results", []):
            eid = e.get("id", "")
            if eid and eid not in all_events:
                all_events[eid] = e
    except:
        pass

print(f"EVENTBRITE — {len(all_events)} unique events on {DATE}:\n")
for eid, e in sorted(all_events.items(), key=lambda x: x[1].get("start_time", "")):
    name = e.get("name", "?")
    time = e.get("start_time", "")
    url = e.get("url", e.get("tickets_url", ""))
    cats = [t.get("display_name","") for t in e.get("tags",[]) if t.get("prefix") == "EventbriteCategory"]
    locs = [l["name"] for l in e.get("locations",[]) if l.get("type") == "locality"]
    loc = locs[0] if locs else ""
    print(f"• {name}")
    print(f"  {time} | {loc} | {cats[0] if cats else ''} | {url}")

os.unlink(cookies)
PYEOF
```

---

## Category Query Mapping

| User wants | Eventbrite `q` param |
|------------|---------------------|
| Music / concerts | `"chicago music concert live"` |
| Comedy | `"chicago comedy stand-up improv"` |
| Food & drink | `"chicago food drink tasting"` |
| Art & culture | `"chicago art gallery exhibition"` |
| Family / kids | `"chicago family kids"` |
| Free events | `"chicago free"` |
| Nightlife | `"chicago nightlife party DJ"` |
| Theater | `"chicago theater theatre musical"` |
| Outdoor | `"chicago outdoor park festival"` |
| Date night | `"chicago date night dinner"` |
| Surprise me | Run full fan-out script above |

---

## API Behavior Notes

- `event_search.dates`: use `"current_future"` with a `date_range` for specific dates.
  Other presets: `"this_week"`, `"this_weekend"`, `"today"`, `"tomorrow"`.
- `event_search.date_range`: `{"from":"YYYY-MM-DD","to":"YYYY-MM-DD"}`
- **Do NOT include `page_size` as a top-level param — it causes errors.**
- Pagination `continuation` token (top-level param) cycles same events — use fan-out instead.
- Returns: `events.results[]` with `name`, `id`, `start_date`, `start_time`, `end_time`,
  `url`, `tickets_url`, `primary_venue`, `tags[]`, `ticket_availability`, `locations[]`
- Results include broader Chicago metro (suburbs, some virtual). The `locations[]` array
  has `type: "locality"` entries to filter by city if needed.
- Typical counts: ~100 unique events on a Friday, ~40-60 on weekdays, ~80 on weekends.
- Some non-Chicago events leak in (yoga in Nashville, etc.) — ignore in output.
- Late-night events (e.g., 10pm Sat → 6am Sun) have `start_date` on Saturday but
  `end_date` on Sunday — the API may return them for both dates.
