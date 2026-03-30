---
name: oncology-event
description: Fetches upcoming events from the Taiwan Oncology Society (癌症醫學會), enriches with detail page data, saves to JSON, and syncs to Google Calendar with deduplication. Use when user asks to update, sync, or check oncology society events or calendar.
---

# Taiwan Oncology Society Event Sync

Scrapes the TOS (癌症醫學會) domestic academic events, enriches each with detail page data, and creates deduplicated Google Calendar events on the **Study 📚** calendar.

## Quick Start

```
python3 fetch_oncology_events.py    # Step 1+2: Fetch listing + details → oncology_events.json
```

Then use Google Calendar MCP tools to sync (Step 3).

## Workflow

```
- [ ] Step 1: Fetch event listing from TOS website (paginated)
- [ ] Step 2: Enrich each event with detail page (speakers, registration, program)
- [ ] Step 3: Deduplicate and sync to Google Calendar
```

### Step 1: Fetch Event Listing

```bash
python3 fetch_oncology_events.py
```

**Script**: [scripts/fetch_oncology_events.py](scripts/fetch_oncology_events.py) (zero dependencies, stdlib only)

**Source URL**: `https://www.taiwanoncologysociety.org.tw/ehc-tos/s/w/edu/schedule/schedule1?eduIn=0`

**What it does**:
1. POST to listing page with ROC date filter (current date onward), paginated (10/page)
2. Parses each event block: title, ROC date → ISO date, location, organizer, credits (腫瘤內科/外科)
3. Visits each event's detail page and extracts: speakers, description, registration URL, program download link, notes, fee, contact
4. Saves to `oncology_events.json`

**Important**: Site has broken SSL cert — script disables SSL verification.

**Date format**: ROC calendar (`115/04/18` = `2026-04-18`). Conversion: `year + 1911`.

### Step 2: Review Output

```bash
python3 -c "
import json
with open('oncology_events.json') as f:
    events = json.load(f)
has_desc = sum(1 for e in events if 'description' in e)
has_reg = sum(1 for e in events if 'registration_url' in e)
print(f'Total: {len(events)}, with description: {has_desc}, with registration_url: {has_reg}')
"
```

### Step 3: Sync to Google Calendar

Use Google Calendar MCP tools. See [references/sync-logic.md](references/sync-logic.md).

**Target calendar**: `Study 📚` (`aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com`)

**Deduplication**: Query existing events with `q="癌症 oncology TOS ASCO ESMO"`, match by date + title.

**Event mapping**:
- All events have specific times → timed events (`dateTime` with `Asia/Taipei`)
- `sendUpdates: none`

**Description format**:
```
主辦單位：{organizer}
地點：{location_detail or location}
主講人：{speakers}
積分：{credits_info formatted}
學會頁面：{url}

--- 報名資訊 ---
報名網址：{registration_url}
費用：{fee} {fee_notes}
聯絡人：{contact} ({email})

--- 活動內容 ---
{description}

--- 備註 ---
{notes}

--- 下載 ---
課程表：{program_download}
```

## Site Structure Reference

See [references/site-structure.md](references/site-structure.md) for HTML parsing details.

## Recurring Sync

TOS only lists events a few weeks ahead (not the full year). To keep the calendar up to date, run the script periodically:

```bash
# Fetch all upcoming events (merges with existing, dedup by event_id)
python3 fetch_oncology_events.py

# Or specify an end date (ROC year MM/DD)
python3 fetch_oncology_events.py 115 12/31
```

Re-running is safe — the script merges new events into `oncology_events.json` without duplicating existing ones. Then use Claude to sync only the new events to Google Calendar.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| SSL CERTIFICATE_VERIFY_FAILED | Site has broken cert; script uses `ssl.CERT_NONE` |
| Page 2 returns old data | Must POST with `startYear` + `startTime` params |
| ROC dates | `115/04/18` → `year + 1911` → `2026-04-18` |
| Missing credits on detail page | Credits are on listing page, not detail; script merges both |
