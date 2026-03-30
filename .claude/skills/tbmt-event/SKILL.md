---
name: tbmt-event
description: Fetches upcoming events from the TBMT (骨髓移植學會), enriches with detail page data, saves to JSON, and syncs to Google Calendar with deduplication. Use when user asks to update, sync, or check bone marrow transplant society events or calendar.
---

# TBMT Event Sync

Scrapes the TBMT (骨髓移植學會) event calendar via its FullCalendar JSON API, enriches each event with detail page data, and creates deduplicated Google Calendar events on the **Study** calendar.

## Quick Start

```bash
python3 .claude/skills/tbmt-event/scripts/fetch_tbmt_events.py   # Fetch → tbmt_events.json
```

## Workflow

```
- [ ] Step 1: Fetch event listing from TBMT calendar API
- [ ] Step 2: Enrich each event with detail page (location, organizer, description)
- [ ] Step 3: Review output
- [ ] Step 4: Deduplicate and sync to Google Calendar
```

### Step 1+2: Fetch and Enrich Events

```bash
python3 .claude/skills/tbmt-event/scripts/fetch_tbmt_events.py
```

**Script**: [scripts/fetch_tbmt_events.py](scripts/fetch_tbmt_events.py) (zero dependencies, stdlib only)

**Data source**: `https://www.tbmt.org.tw/publicUI/D/D10401.aspx?start=YYYY-01-01&end=YYYY-12-31`

**What it does**:
1. Fetches JSON event listing from FullCalendar API endpoint
2. Filters to upcoming events only
3. Visits each event's detail page (`D10402.aspx?arg=...`) and extracts:
   - `full_title`, `organizer` (主辦單位), `location` (地點)
   - `description` (活動內容), `attachments` (附件 PDF/DOC links)
4. Merges with existing `tbmt_events.json` (dedup by `event_id`)

### Step 3: Review Output

```bash
python3 -c "
import json
with open('tbmt_events.json') as f:
    events = json.load(f)
for e in events:
    print(f\"{e['date']}  {e['title'][:60]}  [{e.get('location','')}]\")
print(f'Total: {len(events)} events')
"
```

### Step 4: Sync to Google Calendar

Use Google Calendar MCP tools to create events with deduplication.

**Target calendar**: `Study` (`aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com`)

**Deduplication strategy**:
1. Query existing events with search terms: `TBMT THCTC EBMT Academy 骨髓 移植`
2. Match by date + title to skip already-created events
3. Create only new events

**Event mapping rules**:
- Events with `time_range` → **timed events** (`start.dateTime` / `end.dateTime`, `timeZone: Asia/Taipei`)
- Events without `time_range` → **all-day events** (`start.date` / `end.date`)
- Multi-day events: use start date and end date directly
- `sendUpdates: "none"` to avoid notification spam

**Description format**:
```
主辦單位：{organizer}
地點：{location}
學會頁面：{detail_url}

--- 活動內容 ---
{description}

--- 附件 ---
{attachments}
```

## Site Structure Reference

See [references/site-structure.md](references/site-structure.md) for HTML parsing details.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Empty JSON response | Check date range in API URL; site returns events for the queried year |
| Missing detail fields | Normal — many TBMT events have minimal info (location=待定) |
| SSL errors | Site uses valid SSL; no workaround needed |
| Duplicate calendar events | Run dedup query before creating; search by date+title |
