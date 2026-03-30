#!/usr/bin/env python3
"""Fetch upcoming events from the TBMT (骨髓移植學會) website."""

import json
import os
import re
import time
from datetime import datetime
from urllib.request import Request, urlopen

BASE_URL = "https://www.tbmt.org.tw"
CALENDAR_API = f"{BASE_URL}/publicUI/D/D10401.aspx"
DETAIL_URL_PREFIX = f"{BASE_URL}/publicUI/D/D10402.aspx?arg="
OUTPUT = "tbmt_events.json"


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as resp:
        return resp.read().decode("utf-8")


def clean_html(text: str) -> str:
    text = re.sub(r"<style>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&copy;", "").replace("&quot;", '"')
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def fetch_listing(year: int) -> list[dict]:
    """Fetch events from the FullCalendar JSON API."""
    url = f"{CALENDAR_API}?start={year}-01-01&end={year}-12-31"
    raw = fetch(url)
    items = json.loads(raw)

    events = []
    for item in items:
        # Extract time from title if present (e.g., "12:00~14:00 理監事會")
        title = item["title"]
        time_range = ""
        tm = re.match(r"(\d{1,2}:\d{2})\s*[~-]\s*(\d{1,2}:\d{2})\s+(.*)", title)
        if tm:
            time_range = f"{tm.group(1)}-{tm.group(2)}"
            title = tm.group(3)

        # Extract arg from URL
        arg = ""
        if item.get("url"):
            am = re.search(r"arg=([^&]+)", item["url"])
            if am:
                arg = am.group(1)

        events.append({
            "event_id": arg or str(item.get("id", "")),
            "title": title,
            "date": item["start"],
            "end_date": item.get("end", item["start"]),
            "time_range": time_range,
            "detail_url": f"{BASE_URL}{item['url']}" if item.get("url") else "",
        })

    return events


def parse_detail(html: str) -> dict:
    """Parse event detail page for additional info."""
    detail = {}

    # Title
    m = re.search(r'id="ctl00_ContentPlaceHolder1_lbl_title"[^>]*>(.*?)</span>', html, re.DOTALL)
    if m:
        detail["full_title"] = clean_html(m.group(1)).strip()

    # Start date
    m = re.search(r'id="ctl00_ContentPlaceHolder1_lbl_sdate"[^>]*>(.*?)</span>', html)
    if m:
        detail["start_date"] = m.group(1).strip()

    # End date
    m = re.search(r'id="ctl00_ContentPlaceHolder1_lbl_edate"[^>]*>(.*?)</span>', html)
    if m:
        detail["end_date_detail"] = m.group(1).strip()

    # Sponsor/organizer
    m = re.search(r'id="ctl00_ContentPlaceHolder1_lbl_sponsor"[^>]*>(.*?)</span>', html, re.DOTALL)
    if m:
        detail["organizer"] = clean_html(m.group(1)).strip()

    # Location
    m = re.search(r'id="ctl00_ContentPlaceHolder1_lbl_local"[^>]*>(.*?)</span>', html, re.DOTALL)
    if m:
        detail["location"] = clean_html(m.group(1)).strip()

    # Description
    m = re.search(r'id="ctl00_ContentPlaceHolder1_lbl_actdesc"[^>]*>(.*?)</span>', html, re.DOTALL)
    if m:
        desc = clean_html(m.group(1)).strip()
        if desc:
            detail["description"] = desc

    # Attachments — look for download links near 附件
    attachments = re.findall(r'href="([^"]*(?:\.pdf|\.doc[x]?|\.ppt[x]?|\.xls[x]?)[^"]*)"', html, re.IGNORECASE)
    if attachments:
        detail["attachments"] = [
            a if a.startswith("http") else f"{BASE_URL}{a}" for a in attachments
        ]

    return detail


def main():
    now = datetime.now()

    print(f"Fetching TBMT events for {now.year}...")
    events = fetch_listing(now.year)

    # Filter to upcoming events only
    today = now.strftime("%Y-%m-%d")
    upcoming = [e for e in events if e["date"] >= today]
    past = [e for e in events if e["date"] < today]
    print(f"  Total: {len(events)}, upcoming: {len(upcoming)}, past: {len(past)}")

    # Fetch detail pages for upcoming events
    for i, event in enumerate(upcoming):
        if not event["detail_url"]:
            continue
        print(f"  [{i+1}/{len(upcoming)}] {event['title'][:50]}...", end=" ", flush=True)
        try:
            html = fetch(event["detail_url"])
            detail = parse_detail(html)
            event.update(detail)
            print("OK")
        except Exception as e:
            print(f"FAIL ({e})")
        time.sleep(0.3)

    # Merge with existing file (dedup by event_id)
    existing = []
    if os.path.exists(OUTPUT):
        with open(OUTPUT) as f:
            existing = json.load(f)

    existing_ids = {e["event_id"] for e in existing}
    new_events = [e for e in upcoming if e["event_id"] not in existing_ids]

    if new_events:
        # Update existing events that match, add new ones
        merged = existing + new_events
        merged.sort(key=lambda e: e["date"])
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"\nAdded {len(new_events)} new events (total {len(merged)} in {OUTPUT})")
    else:
        print(f"\nNo new events found ({len(existing)} already in {OUTPUT})")


if __name__ == "__main__":
    main()
