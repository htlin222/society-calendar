---
name: distill-events
description: Explores a medical society website to find its event calendar, reverse-engineers the HTML structure, builds a scraper, and optionally creates a local skill for recurring sync. Use when user provides a new society website URL and wants to extract events.
---

# Distill Events from Society Websites

Given a society website URL, systematically explore its event/calendar pages, understand the data structure, build a working scraper, and package it as a reusable local skill.

## Quick Start

User gives a URL like:
```
https://www.some-society.org.tw/events
```

Follow the workflow below. Do NOT skip the confirmation step before creating the skill.

## Workflow

```
- [ ] Step 1: Discover — find the event calendar page
- [ ] Step 2: Explore — reverse-engineer the HTML structure
- [ ] Step 3: Prototype — build and test the scraper
- [ ] Step 4: Enrich — fetch detail pages for registration/program info
- [ ] Step 5: Confirm — show results and ask user about skill creation
- [ ] Step 6: Package — create the local skill (if user agrees)
- [ ] Step 7: Sync — create Google Calendar events (if user wants)
```

### Step 1: Discover

Find the event/calendar page from the given URL:

1. **WebFetch** the homepage or given URL — look for navigation links containing: 行事曆, 學術活動, 近期會議, calendar, events, schedule, 繼續教育
2. If the page loads dynamically (empty table), try alternate pages (e.g., 近期會議 vs 行事曆)
3. Identify the **listing page URL** and any **detail page URL pattern**

**Output**: The working listing URL and a sample of events to confirm with the user.

### Step 2: Explore

Reverse-engineer the HTML structure using `curl` + inspection:

1. **Fetch raw HTML** — `curl -s -L -H 'User-Agent: Mozilla/5.0' '<URL>'`
2. **Identify the event container** — look for `<table>`, `<div class="title">`, repeating blocks
3. **Map the fields** — for each event, identify where these live in the HTML:

| Field | Priority | Examples |
|-------|----------|---------|
| date/time | Required | `2026-04-18`, `115/04/18` (ROC), `09:00-17:00` |
| title | Required | Event name, possibly with subtitle |
| location | Required | Venue, address, or "線上/視訊" |
| organizer | Important | 主辦單位 |
| credits/category | Important | 甲類/乙類/A類, 學分數 |
| detail page link | Important | URL to individual event page |

4. **Check pagination** — look for `pageNo`, `totalNum`, next page links, or POST-based paging
5. **Check date format** — ROC calendar (民國) needs `year + 1911` conversion

**Common patterns** (see [references/common-patterns.md](references/common-patterns.md)):
- Bootstrap table with `<tr>` rows (like HST)
- Div blocks with title + info sections (like TOS)
- POST-based pagination with hidden form fields
- JavaScript-rendered content (may need alternate URL)

### Step 3: Prototype

Build the scraper script:

**Requirements**:
- Python 3, stdlib only (no pip dependencies)
- `User-Agent: Mozilla/5.0` header (many society sites block default urllib agent)
- SSL verification disabled if needed (some sites have broken certs)
- 0.3s delay between requests
- Output: `{society_name}_events.json`

**Script template**:
```python
#!/usr/bin/env python3
"""Fetch upcoming events from {Society Name} website."""

import json, re, time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

URL = "..."
BASE_URL = "..."
OUTPUT = "{name}_events.json"

def fetch_html(url, post_data=None):
    # Add User-Agent, handle SSL if needed
    ...

def parse_listing(html):
    # Extract events from listing page
    # Return list of event dicts
    ...

def parse_detail(html):
    # Extract registration/program info from detail page
    ...

def main():
    # 1. Fetch listing (handle pagination)
    # 2. Fetch each detail page
    # 3. Merge with existing JSON (dedup)
    # 4. Save
    ...
```

**Test the script** and show the user a sample event (first 2-3 events) before proceeding.

### Step 4: Enrich

Visit each event's detail page and extract:

| Field | Where to look |
|-------|--------------|
| `time_range` | Full start/end datetime |
| `registration_url` | 報名網址, registration links |
| `program_download` | 課程表, agenda PDF links |
| `speakers` | 主講人, speaker list |
| `description` | 活動內容, event description |
| `notes` | 備註, additional notes |
| `contact` | 聯絡人, email |
| `fee` | 費用, 收費 |

Not all fields will exist — only extract what's available.

### Step 5: Confirm

**STOP HERE and ask the user**:

> Found {N} upcoming events from {Society Name}. Here's a sample:
>
> | Date | Event | Location | Credits |
> |------|-------|----------|---------|
> | ... | ... | ... | ... |
>
> Would you like me to:
> 1. Create a local skill (`/skill-name`) for recurring sync?
> 2. Sync these events to your Google Calendar now?
> 3. Both?

### Step 6: Package (if user agrees)

Create the skill at `.claude/skills/{skill-name}/`:

```
{skill-name}/
├── SKILL.md                    # Workflow instructions (<100 lines)
├── scripts/
│   └── fetch_{name}_events.py  # The working scraper
└── references/
    ├── site-structure.md       # HTML structure documentation
    └── sync-logic.md           # Calendar sync reference
```

**SKILL.md template** — follow the same structure as `hematology-event` and `oncology-event` skills in this project. Key sections:
- Quick Start (run command)
- Workflow checklist (fetch → review → sync)
- Event mapping rules for Google Calendar
- Description format template
- Troubleshooting table

### Step 7: Sync to Google Calendar (if user wants)

**Target calendar**: Study 📚 (`aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com`)

1. Query existing events for dedup (search by relevant keywords)
2. Build description with all details and links
3. Create events in batches of 5 via MCP, `sendUpdates: "none"`
4. Report results

**Description format** (adapt based on available fields):
```
{subtitle}
主辦單位：{organizer}
分類：{category}
積分：{credits}
學會頁面：{url}

--- 報名資訊 ---
報名網址：{registration_url}

--- 活動內容 ---
{description}

--- 下載 ---
課程表：{program_download}
```

## Troubleshooting Reference

See [references/common-patterns.md](references/common-patterns.md) for site-specific gotchas.
