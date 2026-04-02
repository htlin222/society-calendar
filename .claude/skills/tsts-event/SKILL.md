---
name: tsts-event
description: Fetches upcoming events from the Taiwan Society of Thoracic Surgeons (胸腔外科醫學會), enriches with detail page data, saves to JSON, and syncs to Google Calendar with deduplication. Use when user asks to update, sync, or check thoracic surgery society events or calendar.
---

# TSTS Event Sync

Scrapes the TSTS (台灣胸腔外科醫學會) event listings (domestic + international), enriches each event with detail page data (time, organizer, registration, credits), and creates deduplicated Google Calendar events on the **Study 📚** calendar.

## Quick Start

```bash
python3 fetch_tsts_events.py    # Fetch listing + details → tsts_events.json
```

## Workflow

```
- [ ] Step 1: Fetch event listings from TSTS website (domestic + international)
- [ ] Step 2: Review output (verify JSON)
- [ ] Step 3: Deduplicate and sync to Google Calendar
```

### Step 1: Fetch Event Listings

Run the scraper to fetch all upcoming events:

```bash
python3 fetch_tsts_events.py
```

**Script**: [scripts/fetch_tsts_events.py](scripts/fetch_tsts_events.py) (zero dependencies, stdlib only)

**Source URLs**:
- Domestic: `https://www.tsts.org.tw/events/events.php?type=1`
- International: `https://www.tsts.org.tw/events/events.php?type=2`

**What it does**:
1. Fetches both listing pages (div-based event blocks)
2. Parses each block: date, end_date, title, location, type, credits
3. Visits each event's detail page and extracts: start_time, end_time, organizer, approval_number, registration_period, fee, contact
4. Filters out past events
5. Merges with existing `tsts_events.json` (dedup by URL)

### Step 2: Review Output

```bash
python3 -c "
import json
with open('tsts_events.json') as f:
    events = json.load(f)
domestic = sum(1 for e in events if e['type'] == '國內學術活動')
intl = sum(1 for e in events if e['type'] == '國外學術活動')
print(f'Total: {len(events)}, domestic: {domestic}, international: {intl}')
"
```

### Step 3: Sync to Google Calendar

Use the Google Calendar MCP tools to create events with deduplication.

**Target calendar**: `Study 📚` (`aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com`)

**Deduplication strategy**:
1. Query existing events on Study calendar with search terms: `TSTS 胸腔外科 thoracic APITS ERAS`
2. Match by date + title to skip already-created events
3. Create only new events

**Event mapping rules**:
- Events with `start_time=00:00` and `end_time=00:00` → **all-day events** (use `start.date` / `end.date`)
- Events with specific times → **timed events** (use `start.dateTime` / `end.dateTime` with `timeZone: Asia/Taipei`)
- Multi-day events → use `end_date` for the end
- `sendUpdates: none` to avoid notification spam

**Description format**:
```
主辦單位：{organizer}
分類：{type}
積分：{credits}
{robot_credits ? "機械手臂積分：" + robot_credits : ""}
核准字號：{approval_number}
學會頁面：{url}

--- 報名資訊 ---
報名期間：{registration_period}
費用：{fee}
```

## Recurring Sync

Re-running the script is safe — it merges new events into `tsts_events.json` without duplicating existing ones (dedup by URL).

## Site Structure Reference

See [references/site-structure.md](references/site-structure.md) for HTML parsing details.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Empty listing | Check if the page uses pagination (`pageNo` param) |
| Missing time | Some events (especially international) don't have specific times |
| Credits missing | International events usually don't have credits |
| Duplicate events | Dedup by URL in JSON; dedup by date+title in Calendar |
