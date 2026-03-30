# Google Calendar Sync Logic

## Calendar Target

- **Calendar**: Study 📚
- **ID**: `aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com`
- **Timezone**: `Asia/Taipei`

## Deduplication

Before creating events, query existing:

```
gcal_list_events(
  calendarId="aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com",
  q="癌症 oncology TOS ASCO ESMO",
  timeMin="<earliest>T00:00:00",
  timeMax="<latest>T23:59:59",
  timeZone="Asia/Taipei",
  maxResults=250,
)
```

Match by `date + title` to skip duplicates.

## Event Mapping

All TOS events have specific times — use `dateTime` (not `date`):

```python
event = {
    "summary": title,
    "location": location_detail or location,
    "description": build_description(e),
    "start": {"dateTime": f"{date}T{time}:00", "timeZone": "Asia/Taipei"},
    "end": {"dateTime": f"{end_date}T{end_time}:00", "timeZone": "Asia/Taipei"},
}
```

## Description Builder

```python
def build_description(e):
    parts = []
    if e.get("organizer_detail") or e.get("organizer"):
        parts.append(f"主辦單位：{e.get('organizer_detail') or e['organizer']}")
    if e.get("location_detail"):
        parts.append(f"地點：{e['location_detail']}")
    if e.get("speakers"):
        parts.append(f"主講人：{e['speakers']}")

    # Credits
    for ci in e.get("credits_info", []):
        parts.append(f"{ci['specialty']}：{ci['category']} {ci['credits']}學分")

    parts.append(f"學會頁面：{e['url']}")

    if e.get("registration_url"):
        parts.append(f"\n--- 報名資訊 ---")
        parts.append(f"報名網址：{e['registration_url']}")
    if e.get("fee"):
        parts.append(f"費用：{e['fee']}")
    if e.get("fee_notes"):
        parts.append(f"收費備註：{e['fee_notes']}")
    if e.get("contact"):
        contact = e["contact"]
        if e.get("email"):
            contact += f" ({e['email']})"
        parts.append(f"聯絡人：{contact}")

    if e.get("description"):
        parts.append(f"\n--- 活動內容 ---")
        parts.append(e["description"])

    if e.get("notes"):
        parts.append(f"\n--- 備註 ---")
        parts.append(e["notes"])

    if e.get("program_download"):
        parts.append(f"\n--- 下載 ---")
        parts.append(f"課程表：{e['program_download']}")

    return "\n".join(parts)
```

## Batch Creation

Create 5 events per parallel MCP call with `sendUpdates: "none"`.
