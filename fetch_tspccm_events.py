#!/usr/bin/env python3
"""Fetch upcoming events from the Taiwan Society of Pulmonary and Critical Care Medicine (TSPCCM) website."""

import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

BASE_URL = "https://www.tspccm.org.tw"
LIST_URL = BASE_URL + "/conference/list"
OUTPUT = "tspccm_events.json"

# Fetch current month + next 2 months
MONTHS_AHEAD = 3


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as resp:
        return resp.read().decode("utf-8")


def clean_html(text: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    text = re.sub(r"<style>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&emsp;", " ").replace("&quot;", '"')
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def parse_listing(html: str, year: int, month: int) -> list[dict]:
    """Parse the conference listing table for a given month."""
    events = []

    # Each event is a <tr> row in the conference table
    for row in re.finditer(r"<tr class='[^']*'>(.*?)</tr>", html, re.DOTALL):
        content = row.group(1)

        # Date: <span class='fs-em'>MM-DD</span> (DAY)<br>HH:MM ~ HH:MM
        date_match = re.search(
            r"<span class='fs-em'\s*>(\d{2}-\d{2})</span>.*?"
            r"(\d{2}:\d{2})\s*~\s*(\d{2}:\d{2})",
            content,
            re.DOTALL,
        )
        if not date_match:
            continue

        mm_dd = date_match.group(1)  # MM-DD
        start_time = date_match.group(2)
        end_time = date_match.group(3)
        date_str = f"{year}-{mm_dd}"  # YYYY-MM-DD

        # Title + URL
        title_match = re.search(
            r"<a\s+href='(/conference/\d+)'[^>]*><span class='text\s*'>(.*?)</span></a>",
            content,
            re.DOTALL,
        )
        if not title_match:
            continue

        detail_path = title_match.group(1)
        title = clean_html(title_match.group(2))
        detail_url = f"{BASE_URL}{detail_path}"

        # Organizer (col-division)
        org_match = re.search(
            r"col-division'[^>]*>.*?<div[^>]*>(.*?)</div>", content, re.DOTALL
        )
        organizer = clean_html(org_match.group(1)) if org_match else ""

        # Location (col-site)
        site_match = re.search(
            r"col-site'[^>]*>.*?<div[^>]*>(.*?)</div>", content, re.DOTALL
        )
        location = clean_html(site_match.group(1)) if site_match else ""

        # Credits (col-char7 for score)
        credits_match = re.search(
            r"col-char7'[^>]*>.*?<div[^>]*>(.*?)</div>", content, re.DOTALL
        )
        credits = clean_html(credits_match.group(1)) if credits_match else ""

        # Contact
        # Find the second col-char7 (contact column)
        char7_matches = list(
            re.finditer(r"col-char7'[^>]*>.*?<div[^>]*>(.*?)</div>", content, re.DOTALL)
        )
        contact = ""
        if len(char7_matches) >= 2:
            contact = clean_html(char7_matches[1].group(1))

        # Category
        cat_match = re.search(
            r"col-category'[^>]*>.*?<div[^>]*>(.*?)</div>", content, re.DOTALL
        )
        category = clean_html(cat_match.group(1)) if cat_match else ""

        event = {
            "date": date_str,
            "start_time": start_time,
            "end_time": end_time,
            "title": title,
            "organizer": organizer,
            "location": location,
            "url": detail_url,
        }
        if credits:
            event["credits"] = credits
        if contact:
            event["contact"] = contact
        if category and category != "未分類":
            event["category"] = category

        events.append(event)

    return events


def main():
    now = datetime.now()
    all_events = []

    for i in range(MONTHS_AHEAD):
        m = now.month + i
        y = now.year
        if m > 12:
            m -= 12
            y += 1
        month_str = f"{y}-{m:02d}"
        url = f"{LIST_URL}?display_date={month_str}&category=all"
        print(f"Fetching {month_str}...", end=" ", flush=True)
        try:
            html = fetch_html(url)
            events = parse_listing(html, y, m)
            print(f"{len(events)} events")
            all_events.extend(events)
        except Exception as e:
            print(f"FAIL ({e})")
        time.sleep(0.3)

    # Filter past events
    today = now.strftime("%Y-%m-%d")
    all_events = [e for e in all_events if e["date"] >= today]

    # Sort by date + time
    all_events.sort(key=lambda e: (e["date"], e["start_time"]))

    # Merge with existing file (dedup by url)
    existing = []
    if os.path.exists(OUTPUT):
        with open(OUTPUT) as f:
            existing = json.load(f)

    existing_urls = {e.get("url") for e in existing if e.get("url")}
    new_events = [e for e in all_events if e.get("url") not in existing_urls]

    if new_events:
        merged = existing + new_events
        merged.sort(key=lambda e: (e["date"], e.get("start_time", "00:00")))
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"\nAdded {len(new_events)} new events (total {len(merged)} in {OUTPUT})")
    else:
        print(f"\nNo new events found ({len(existing)} already in {OUTPUT})")


if __name__ == "__main__":
    main()
