---
name: tspccm-event
description: Fetches upcoming events from the Taiwan Society of Pulmonary and Critical Care Medicine (胸腔暨重症加護醫學會), saves to JSON, and syncs to Google Calendar with deduplication. Use when user asks to update, sync, or check pulmonary/critical care society events or calendar.
---

# TSPCCM Event Sync

Scrapes the TSPCCM (台灣胸腔暨重症加護醫學會) conference listing, covering current + next 2 months, and creates deduplicated Google Calendar events on the **Study 📚** calendar.

## Quick Start

```bash
python3 fetch_tspccm_events.py    # Fetch 3 months of events → tspccm_events.json
```

## Workflow

```
- [ ] Step 1: Fetch event listings from TSPCCM website (3 months)
- [ ] Step 2: Review output (verify JSON)
- [ ] Step 3: Deduplicate and sync to Google Calendar
```

### Step 1: Fetch Event Listings

```bash
python3 fetch_tspccm_events.py
```

**Script**: [scripts/fetch_tspccm_events.py](scripts/fetch_tspccm_events.py) (zero dependencies, stdlib only)

**Source URL**: `https://www.tspccm.org.tw/conference/list?display_date=YYYY-MM&category=all`

**What it does**:
1. Fetches listing pages for current month + next 2 months
2. Parses the HTML table: date, time, title, organizer, location, credits, contact, category
3. Filters out past events
4. Merges with existing `tspccm_events.json` (dedup by URL)

**Note**: This site has ~40-50 events per month (many are recurring weekly hospital meetings). The listing page already contains all fields — no detail page visits needed.

### Step 2: Review Output

```bash
python3 -c "
import json
with open('tspccm_events.json', encoding='utf-8') as f:
    events = json.load(f)
print(f'Total: {len(events)}')
"
```

### Step 3: Sync to Google Calendar

Use the Google Calendar MCP tools to create events with deduplication.

**Target calendar**: `Study 📚` (`aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com`)

**Deduplication strategy**:
1. Query existing events on Study calendar with search terms: `TSPCCM 胸腔 重症 pulmonary`
2. Match by date + title to skip already-created events
3. Create only new events

**Event mapping rules**:
- All events have specific start/end times → **timed events** (use `start.dateTime` / `end.dateTime` with `timeZone: Asia/Taipei`)
- `sendUpdates: none` to avoid notification spam

**Description format**:
```
主辦：{organizer}
地點：{location}
積分：{credits}
聯絡：{contact}
學會頁面：{url}
```

## Recurring Sync

Re-running the script is safe — dedup by URL prevents duplicates.

## Site Structure Reference

See [references/site-structure.md](references/site-structure.md) for HTML parsing details.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No events for a month | Normal — some months have fewer scheduled events |
| Many similar events | Expected — hospitals hold recurring weekly meetings |
| Category filtering | Use `category=4` (一般B), `category=5` (胸重主辦), `category=3` (聯甄重症) |
