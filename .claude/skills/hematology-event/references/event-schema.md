# Event JSON Schema

Each event in `events.json` has these fields:

## Required Fields

| Field | Type | Example |
|-------|------|---------|
| `date` | `YYYY-MM-DD` | `"2026-04-18"` |
| `time` | `HH:MM` | `"09:00"` or `"00:00"` (all-day) |
| `title` | string | `"2026 TBMT-HST聯合學術演講年會"` |
| `location` | string | `"台大醫院國際會議中心"` (may be empty) |
| `organizer` | string | `"TBMT、HST"` |
| `category` | string | `"甲類"`, `"乙類"`, `"丙類"`, `"無學分"` |

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `subtitle` | string | English name or alternate title |
| `credits` | string | CME credit points (e.g. `"15"`, `"0.5"`) |
| `url` | URL | Detail page on HST website |
| `time_range` | string | Full start-end from detail page (e.g. `"2026-04-18的09:00至\n2026-04-19的15:30"`) |
| `registration_program` | string | Cleaned plaintext from 報名/節目表 tab |
| `links` | array | External links `[{"text": "...", "url": "..."}]` |

## Time Range Parsing

The `time_range` field has these patterns:

```
# Same day
"2026-04-16的19:00至20:00"

# Multi-day
"2026-04-18的09:00至\n2026-04-19的15:30"

# All-day (no specific time)
"2026-05-02的00:00至00:00"

# Multi-day all-day
"2026-06-11的00:00至\n2026-06-14的00:00"
```

Regex to parse:
```python
r'(\d{4}-\d{2}-\d{2})的(\d{2}:\d{2})至\s*(?:(\d{4}-\d{2}-\d{2})的)?(\d{2}:\d{2})'
```

## Example

```json
{
  "date": "2026-04-18",
  "time": "09:00",
  "title": "2026 TBMT-HST聯合學術演講年會",
  "location": "台大醫院國際會議中心",
  "organizer": "TBMT、 HST",
  "category": "甲類",
  "subtitle": "2026  Joint Annual Congress of TBMT-HST",
  "credits": "15",
  "url": "https://www.hematology.org.tw/web2/project/index.php?act=point&id=2623",
  "time_range": "2026-04-18的09:00至\n2026-04-19的15:30",
  "registration_program": "敬愛的會員：您好!\n本年度年會暨會員大會...",
  "links": [
    {
      "text": "(節目表更新_0327版_隨時即時更新節目表內容)",
      "url": "https://drive.google.com/file/d/1y0s6wF--hR158p74tfFRxGIC6Yem5VBk/view"
    }
  ]
}
```
