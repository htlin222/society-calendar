---
name: tsim-event
description: Fetches upcoming events from the Taiwan Society of Internal Medicine (內科醫學會), enriches with detail page data, saves to JSON, and syncs to Google Calendar with deduplication. Use when user asks to update, sync, or check internal medicine society events or calendar.
---

# Taiwan Society of Internal Medicine Event Sync

Scrapes the TSIM (內科醫學會) 活動訊息 page, enriches each event with detail page data, and creates deduplicated Google Calendar events on the **Study 📚** calendar.

## Quick Start

```bash
python3 fetch_tsim_events.py    # Fetch listing + details → tsim_events.json
```

Then use Google Calendar MCP tools to sync.

## Workflow

```
- [ ] Step 1: Fetch event listing from TSIM website
- [ ] Step 2: Enrich each event with detail page (program, downloads)
- [ ] Step 3: Deduplicate and sync to Google Calendar
```

### Step 1: Fetch Event Listing

```bash
python3 fetch_tsim_events.py
```

**Script**: [scripts/fetch_tsim_events.py](scripts/fetch_tsim_events.py) (zero dependencies, stdlib only)

**Source URL**: `https://www.tsim.org.tw/ehc-tsim/s/w/news_acts/articles/20/{page}`

**What it does**:
1. Fetches paginated listing pages (`/articles/20/1`, `/articles/20/2`, ...)
2. Parses `<li>` items: extracts title, publish date (ROC), detail URL
3. Extracts event date from title text (e.g. `2026/4/26 ...`)
4. Visits each event's detail page and extracts: organizer, location, time, credits, program/schedule, PDF downloads
5. Filters out past events
6. Merges with existing JSON (dedup by event_id)

**Site quirks**: See [references/site-structure.md](references/site-structure.md)

### Step 2: Sync to Google Calendar

**Target calendar**: Study 📚 (`aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com`)

**Dedup query**: `q="內科 TSIM internal medicine"`

**Description format**:
```
主辦單位：{organizer}
地點：{location}
時間：{time_info}
報到方式：{registration_method}
積分：{credits_category} {credits}點
學會頁面：{url}

--- 課程表 ---
{program_info}

--- 下載 ---
{download.text}：{download.url}
```

**Event mapping**: Events are all-day (no specific start/end time in data), `sendUpdates: "none"`.

## Recurring Sync

Re-running is safe — merges new events by `event_id`. TSIM publishes events gradually, so run periodically.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| SSL CERTIFICATE_VERIFY_FAILED | Site has broken cert; script uses `ssl.CERT_NONE` |
| Event date not extracted | Date is embedded in title text, not a separate field; regex handles `2026/M/D` and `115年M月D日` |
| Multi-date articles | Some articles (e.g. flu training) contain multiple event dates in one listing; only first date is extracted |
| 繼續教育活動時間表 has CAPTCHA | Use 活動訊息 page instead (`/news_acts/articles/20/1`) |
