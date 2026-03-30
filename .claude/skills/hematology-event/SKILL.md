---
name: hematology-event
description: Fetches upcoming events from the Hematology Society of Taiwan (血液病學會), enriches with registration/program details, saves to JSON, and syncs to Google Calendar with deduplication. Use when user asks to update, sync, or check hematology society events or calendar.
---

# Hematology Society Event Sync

Scrapes the HST (血液病學會) event calendar, enriches each event with detail page data (報名/節目表), and creates deduplicated Google Calendar events on the **Study 📚** calendar.

## Quick Start

```
python3 fetch_events.py        # Step 1+2: Fetch listing + details → events.json
python3 sync_to_calendar.py    # Step 3: Create events in Google Calendar
```

## Workflow

```
- [ ] Step 1: Fetch event listing from HST website
- [ ] Step 2: Enrich each event with detail page (報名/節目表, links)
- [ ] Step 3: Deduplicate and sync to Google Calendar
```

### Step 1: Fetch Event Listing

Run the scraper to fetch all upcoming events from the 近期會議 page:

```bash
python3 fetch_events.py
```

**Script**: [scripts/fetch_events.py](scripts/fetch_events.py) (zero dependencies, stdlib only)

**Source URL**: `https://www.hematology.org.tw/web2/project/index.php?act=tag_p`

**What it does**:
1. Fetches the listing page (bootstrap-table with `<tr>` rows)
2. Parses each row: date, time, title, subtitle, location, organizer, category, credits, detail URL
3. Visits each event's detail page and extracts from 3 tabs:
   - `#home` (資訊): `time_range` — full start/end datetime
   - `#messages` (報名/節目表): `registration_program` — cleaned plaintext + `links` — external URLs (program PDFs, registration forms)
4. Filters out past events
5. Saves to `events.json`

**Output schema**: See [references/event-schema.md](references/event-schema.md)

### Step 2: Review Output

After fetching, verify the JSON:

```bash
python3 -c "
import json
with open('events.json') as f:
    events = json.load(f)
has_reg = sum(1 for e in events if 'registration_program' in e)
has_links = sum(1 for e in events if 'links' in e)
print(f'Total: {len(events)}, with registration info: {has_reg}, with links: {has_links}')
"
```

### Step 3: Sync to Google Calendar

Use the Google Calendar MCP tools to create events with deduplication.

**Script**: [scripts/sync_to_calendar.py](scripts/sync_to_calendar.py) (reference logic — executed by Claude via MCP tools)

**Target calendar**: `Study 📚` (`aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com`)

**Deduplication strategy**:
1. Query existing events on Study calendar with search terms: `血液 hematology HST TBMT EHA ASH Myeloma MPN`
2. Match by date + title to skip already-created events
3. Create only new events

**Event mapping rules**:
- Events with `time=00:00` and time_range `00:00至...00:00` → **all-day events** (use `start.date` / `end.date`)
- Events with specific times → **timed events** (use `start.dateTime` / `end.dateTime` with `timeZone: Asia/Taipei`)
- Multi-day events with same title on consecutive days → add `(Day 1)`, `(Day 2)` suffix
- `sendUpdates: none` to avoid notification spam

**Description format**:
```
{subtitle}
主辦單位：{organizer}
分類：{category}
積分：{credits}
學會頁面：{url}

--- 相關連結 ---
{link.text}：{link.url}

--- 報名/節目表 ---
{registration_program}
```

## Recurring Sync

Re-running the script is safe — it merges new events into `events.json` without duplicating existing ones (dedup by URL). Then use Claude to sync only the new events to Google Calendar.

```bash
python3 fetch_events.py   # merges new events into events.json
```

## Site Structure Reference

See [references/site-structure.md](references/site-structure.md) for HTML parsing details.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| HTTP 406 | Must include `User-Agent: Mozilla/5.0` header |
| Empty 報名/節目表 | Normal — not all events have registration info posted yet |
| Duplicate calendar events | Run dedup query before creating; search by date+title |
| Script timeout | Add `time.sleep(0.3)` between detail page fetches |
