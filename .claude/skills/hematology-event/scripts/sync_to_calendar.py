#!/usr/bin/env python3
"""
Reference logic for syncing events.json to Google Calendar.

This script is NOT executed directly — it documents the MCP tool calls
that Claude should make to sync events to Google Calendar.

Claude reads this file and executes the logic via MCP tools:
  - mcp__claude_ai_Google_Calendar__gcal_list_events (dedup check)
  - mcp__claude_ai_Google_Calendar__gcal_create_event (create events)
"""

import json
import re

CALENDAR_ID = "aqpiqrg5f97kc6eu7j23vbovvc@group.calendar.google.com"  # Study 📚
TIMEZONE = "Asia/Taipei"


def load_events(path="events.json"):
    with open(path) as f:
        return json.load(f)


def deduplicate(events):
    """Remove duplicate events by (date, title) key."""
    seen = set()
    unique = []
    for e in events:
        key = (e["date"], e["title"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def parse_time_range(tr):
    """Parse time_range string into (start_date, start_time, end_date, end_time).

    Patterns:
      '2026-04-16的19:00至20:00'           → same day
      '2026-04-18的09:00至\\n2026-04-19的15:30' → multi-day
    """
    tr = tr.replace("\n", " ")
    m = re.match(
        r"(\d{4}-\d{2}-\d{2})的(\d{2}:\d{2})至\s*(?:(\d{4}-\d{2}-\d{2})的)?(\d{2}:\d{2})",
        tr,
    )
    if m:
        start_date, start_time, end_date, end_time = m.groups()
        if not end_date:
            end_date = start_date
        return start_date, start_time, end_date, end_time
    return None


def build_description(e):
    """Build calendar event description with all details and links."""
    parts = []
    if e.get("subtitle"):
        parts.append(e["subtitle"])
    if e.get("organizer"):
        parts.append(f"主辦單位：{e['organizer']}")
    if e.get("category"):
        parts.append(f"分類：{e['category']}")
    if e.get("credits"):
        parts.append(f"積分：{e['credits']}")
    if e.get("url"):
        parts.append(f"學會頁面：{e['url']}")

    if e.get("links"):
        parts.append("")
        parts.append("--- 相關連結 ---")
        for link in e["links"]:
            parts.append(f"{link['text']}：{link['url']}")

    if e.get("registration_program"):
        parts.append("")
        parts.append("--- 報名/節目表 ---")
        parts.append(e["registration_program"])

    return "\n".join(parts)


def to_calendar_event(e):
    """Convert a JSON event to Google Calendar API event object.

    Returns dict suitable for gcal_create_event MCP tool.
    """
    is_allday = e["time"] == "00:00"
    tr = parse_time_range(e.get("time_range", ""))

    cal_event = {
        "summary": e["title"],
        "description": build_description(e),
    }

    if e.get("location"):
        cal_event["location"] = e["location"]

    if tr:
        start_date, start_time, end_date, end_time = tr
        if is_allday and start_time == "00:00" and end_time == "00:00":
            # All-day event
            cal_event["start"] = {"date": start_date}
            cal_event["end"] = {"date": end_date}
        else:
            # Timed event
            cal_event["start"] = {
                "dateTime": f"{start_date}T{start_time}:00",
                "timeZone": TIMEZONE,
            }
            cal_event["end"] = {
                "dateTime": f"{end_date}T{end_time}:00",
                "timeZone": TIMEZONE,
            }
    else:
        # Fallback: all-day on the listed date
        cal_event["start"] = {"date": e["date"]}
        cal_event["end"] = {"date": e["date"]}

    return cal_event


# --- MCP Tool Call Reference ---
#
# Step 1: Check for existing events (dedup)
#
#   gcal_list_events(
#     calendarId=CALENDAR_ID,
#     q="血液 hematology HST TBMT EHA ASH Myeloma MPN",
#     timeMin="<earliest event date>T00:00:00",
#     timeMax="<latest event date>T23:59:59",
#     timeZone=TIMEZONE,
#     maxResults=250,
#     condenseEventDetails=False,
#   )
#
# Step 2: For each new event, create via MCP:
#
#   gcal_create_event(
#     calendarId=CALENDAR_ID,
#     sendUpdates="none",
#     event=to_calendar_event(e),
#   )
#
# Batch 5 events per parallel MCP call for efficiency.
