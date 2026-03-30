#!/usr/bin/env python3
"""Fetch upcoming events from the Hematology Society of Taiwan website."""

import json
import re
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

URL = "https://www.hematology.org.tw/web2/project/index.php?act=tag_p"
BASE_URL = "https://www.hematology.org.tw/web2/project/"
OUTPUT = "events.json"


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
    text = text.replace("&copy;", "").replace("&quot;", '"')
    # Collapse whitespace within lines, preserve newlines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def extract_links(html: str) -> list[dict]:
    """Extract meaningful links (skip mailto, admin links)."""
    links = []
    for m in re.finditer(r'<a[^>]+href=["\']?([^"\' >]+)["\']?[^>]*>(.*?)</a>', html, re.DOTALL):
        href, label = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if not label or "mailto:" in href or "hemaadmin" in href:
            continue
        if not href.startswith("http"):
            href = BASE_URL + href
        links.append({"text": label, "url": href})
    return links


def parse_detail(html: str) -> dict:
    """Parse event detail page into structured data."""
    detail = {}

    # Extract tab-content section
    tab_match = re.search(r"<div class='tab-content'>(.*?)</div>\s*</div>\s*<div class='col-sm", html, re.DOTALL)
    if not tab_match:
        return detail

    tab_content = tab_match.group(1)

    # Split into panels by tabpanel divs
    panels = re.split(r"<div role='tabpanel'", tab_content)

    for panel in panels:
        if "id='home'" in panel:
            time_match = re.search(
                r"<td>時間</td>\s*<td>(.*?)</td>", panel, re.DOTALL
            )
            if time_match:
                detail["time_range"] = clean_html(time_match.group(1))

        elif "id='messages'" in panel:
            # Get content inside single-post-content div
            content_match = re.search(
                r"<div class='single-post-content'>(.*)", panel, re.DOTALL
            )
            if not content_match:
                continue
            content = content_match.group(1)

            # Remove trailing </div> closers
            content = re.sub(r"(</div>\s*)+$", "", content)

            # Extract links before cleaning
            links = extract_links(content)
            if links:
                detail["links"] = links

            # Clean to plain text
            text = clean_html(content)
            text = text.strip()

            if text:
                detail["registration_program"] = text

    return detail


def parse_events(html: str) -> list[dict]:
    """Parse the event listing page."""
    row_pattern = re.compile(r"<tr><td.*?</tr>", re.DOTALL)
    td_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
    link_pattern = re.compile(r"<a href=([^>]+)>(.*?)</a>", re.DOTALL)

    events = []
    now = datetime.now(timezone.utc)

    for row_match in row_pattern.finditer(html):
        row = row_match.group()
        cells = td_pattern.findall(row)
        if len(cells) < 6:
            continue

        # Parse date + time
        date_raw = re.sub(r"<[^>]+>", "\n", cells[0]).strip()
        date_parts = [line.strip() for line in date_raw.split("\n") if line.strip()]
        date_str = date_parts[0] if date_parts else ""
        time_str = date_parts[1] if len(date_parts) > 1 else "00:00"

        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            continue

        if dt < now.replace(tzinfo=None):
            continue

        # Parse title + link
        link_match = link_pattern.search(cells[1])
        if link_match:
            href = link_match.group(1).strip("'\"")
            title_raw = link_match.group(2)
        else:
            href = ""
            title_raw = cells[1]

        title_lines = [
            line.strip()
            for line in re.sub(r"<[^>]+>", "\n", title_raw).split("\n")
            if line.strip()
        ]
        title = title_lines[0] if title_lines else ""
        subtitle = title_lines[1] if len(title_lines) > 1 else ""

        def clean(text: str) -> str:
            return re.sub(r"<[^>]+>", "", text).strip()

        event = {
            "date": date_str,
            "time": time_str,
            "title": title,
            "location": clean(cells[2]),
            "organizer": clean(cells[3]),
            "category": clean(cells[4]),
        }
        if subtitle:
            event["subtitle"] = subtitle
        if clean(cells[5]):
            event["credits"] = clean(cells[5])
        if href:
            event["url"] = f"{BASE_URL}{href}"

        events.append(event)

    return events


def main():
    print("Fetching event listing...")
    html = fetch_html(URL)
    events = parse_events(html)
    print(f"Found {len(events)} upcoming events")

    for i, event in enumerate(events):
        url = event.get("url")
        if not url:
            continue
        print(f"  [{i+1}/{len(events)}] {event['title']}...", end=" ", flush=True)
        try:
            detail_html = fetch_html(url)
            detail = parse_detail(detail_html)
            if detail.get("time_range"):
                event["time_range"] = detail["time_range"]
            if detail.get("registration_program"):
                event["registration_program"] = detail["registration_program"]
            if detail.get("links"):
                event["links"] = detail["links"]
            print("OK")
        except Exception as e:
            print(f"FAIL ({e})")
        time.sleep(0.3)  # be polite

    # Merge with existing file (dedup by url)
    import os
    existing = []
    if os.path.exists(OUTPUT):
        with open(OUTPUT) as f:
            existing = json.load(f)

    existing_urls = {e.get("url") for e in existing if e.get("url")}
    new_events = [e for e in events if e.get("url") not in existing_urls]

    if new_events:
        merged = existing + new_events
        merged.sort(key=lambda e: (e["date"], e["time"]))
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"\nAdded {len(new_events)} new events (total {len(merged)} in {OUTPUT})")
    else:
        print(f"\nNo new events found ({len(existing)} already in {OUTPUT})")


if __name__ == "__main__":
    main()
