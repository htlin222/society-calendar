# Common Patterns & Gotchas for Taiwan Society Websites

## Known Site Patterns

### Pattern A: Bootstrap Table (e.g., 血液病學會)
- `<table>` with `<tr>` rows, `<td>` cells
- Columns: 日期, 會議名稱, 地點, 主辦單位, 分類, 積分
- Detail pages via `<a href="index.php?act=point&id=XXXX">`
- Tab panels (`#home`, `#profile`, `#messages`) for detail sections
- All data server-rendered in HTML

### Pattern B: Div Blocks + POST Pagination (e.g., 癌症醫學會)
- `<div class="title">` blocks with `<div class="row info">`
- Pagination via POST with hidden `pageNo` field
- ROC dates (民國年): `115/04/18` = `2026-04-18`
- Detail pages use `<label>` + `<div class="form-content">` pairs
- Program downloads via `/viewDocument1?documentId=xxx`

### Pattern C: JavaScript-Rendered Calendar
- Empty HTML on initial load, data fetched via AJAX/API
- **Solution**: Look for the API endpoint in network requests or JS source
- Sometimes there's a non-JS fallback page (e.g., 近期會議 vs 行事曆)

### Pattern D: WordPress / CMS Plugin
- Events in `<article>` or `<div class="event-item">` blocks
- Usually has REST API at `/wp-json/wp/v2/events` or similar
- Calendar plugins (The Events Calendar, etc.) have their own API patterns

## Common Gotchas

| Issue | Symptom | Fix |
|-------|---------|-----|
| HTTP 406 | `urllib` blocked | Add `User-Agent: Mozilla/5.0` header |
| SSL cert error | `CERTIFICATE_VERIFY_FAILED` | Use `ssl.CERT_NONE` context |
| Empty page | JavaScript renders content | Find API endpoint or alternate page |
| ROC dates | Dates like `115/04/18` | `roc_year + 1911 = ad_year` |
| POST pagination | Page 2 returns old data | Must include all hidden form fields (startYear, etc.) |
| Encoding | Garbled Chinese text | Try `big5` or `utf-8` decoding |
| Rate limiting | Connection refused after many requests | Add `time.sleep(0.3)` between requests |
| Word HTML in content | `<style>` blocks, font-face definitions | Strip `<style>.*?</style>` before cleaning |
| Footer bleed | Page footer leaks into event content | Use tighter regex boundaries (e.g., match up to layout div) |

## Field Extraction Cheatsheet

### Dates
```python
# ISO date in HTML
re.search(r'(\d{4}-\d{2}-\d{2})', text)

# ROC date
m = re.match(r'(\d+)/(\d{2})/(\d{2})', roc_str)
year = int(m.group(1)) + 1911

# Time range
re.match(r'(\d{2}:\d{2})\s*[-~至]\s*(\d{2}:\d{2})', text)
```

### Links
```python
# Extract href + label
re.findall(r'<a[^>]+href=["\']?([^"\' >]+)["\']?[^>]*>(.*?)</a>', html, re.DOTALL)

# Filter out noise (mailto, admin links)
[l for l in links if 'mailto:' not in l[0] and 'admin' not in l[0]]
```

### Clean HTML to Text
```python
text = re.sub(r'<style>.*?</style>', '', html, flags=re.DOTALL)
text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
text = re.sub(r'<[^>]+>', ' ', text)
text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
```

## Google Calendar Mapping Quick Reference

| Event Type | Calendar API |
|-----------|-------------|
| Timed event | `start.dateTime` + `end.dateTime` + `timeZone: Asia/Taipei` |
| All-day event | `start.date` + `end.date` (YYYY-MM-DD) |
| Multi-day timed | Same as timed, end date differs from start |
| Multi-day all-day | `end.date` = day after last day (exclusive) |

**Target calendar**: Study 📚 — `aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com`
**Always**: `sendUpdates: "none"`, batch 5 per parallel MCP call.
