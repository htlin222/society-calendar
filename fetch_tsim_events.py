#!/usr/bin/env python3
"""Fetch upcoming events from Taiwan Society of Internal Medicine (內科醫學會)."""

import json
import os
import re
import ssl
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

# Site has broken SSL cert (missing Subject Key Identifier)
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

BASE_URL = "https://www.tsim.org.tw"
LIST_URL = f"{BASE_URL}/ehc-tsim/s/w/news_acts/articles/20/"
OUTPUT = "tsim_events.json"


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, context=SSL_CTX) as resp:
        return resp.read().decode("utf-8")


def clean_html(text: str) -> str:
    text = re.sub(r"<style>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&mdash;", "—").replace("&ndash;", "–")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def roc_to_iso(roc_str: str) -> str:
    """Convert ROC date '115/03/11' to ISO '2026-03-11'."""
    m = re.match(r"(\d+)/(\d{2})/(\d{2})", roc_str.strip())
    if m:
        year = int(m.group(1)) + 1911
        return f"{year}-{m.group(2)}-{m.group(3)}"
    return ""


def extract_event_date(title: str) -> str:
    """Extract event date from title like '2026/4/26 ...' or '115年3月21日'."""
    # Try AD date: 2026/4/26 or 2026/03/13
    m = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})", title)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # Try ROC with 年月日: 115年3月21日
    m = re.search(r"(\d+)年(\d{1,2})月(\d{1,2})日", title)
    if m:
        year = int(m.group(1)) + 1911
        return f"{year}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def parse_listing_page(html: str) -> list[dict]:
    """Parse listing page, return list of events."""
    items = re.findall(r"<li[^>]*>.*?</li>", html, re.DOTALL)
    article_items = [i for i in items if "news_acts/article/" in i]

    events = []
    now = datetime.now()

    for item in article_items:
        # Extract publish date
        date_match = re.search(r'class="date">(.*?)</div>', item)
        pub_date_roc = date_match.group(1).strip() if date_match else ""

        # Extract title
        title_match = re.search(r"<h4>(.*?)</h4>", item, re.DOTALL)
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else ""

        # Extract detail link
        href_match = re.search(r'href="([^"]+)"', item)
        href = href_match.group(1).strip() if href_match else ""

        # Extract event date from title
        event_date = extract_event_date(title)

        # Skip past events and non-event items (surveys, past lecture notes)
        if not event_date:
            continue
        try:
            dt = datetime.strptime(event_date, "%Y-%m-%d")
            if dt < now:
                continue
        except ValueError:
            continue

        # Generate stable event_id from href
        id_match = re.search(r"article/([a-f0-9]+)", href)
        event_id = id_match.group(1)[:12] if id_match else ""

        event = {
            "date": event_date,
            "title": title,
            "publish_date": roc_to_iso(pub_date_roc),
            "event_id": event_id,
            "url": f"{BASE_URL}{href}" if href else "",
        }
        events.append(event)

    return events


def parse_detail(html: str) -> dict:
    """Parse event detail page."""
    detail = {}

    # Extract articleinfo section
    m = re.search(
        r'class="articleinfo">(.*?)(?:class="articledow"|<footer)', html, re.DOTALL
    )
    if not m:
        return detail

    content = m.group(1)
    text = clean_html(content)

    # Extract structured fields from text
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("主辦單位："):
            detail["organizer"] = line.replace("主辦單位：", "").strip()
        elif line.startswith("地點："):
            detail["location"] = line.replace("地點：", "").strip()
        elif line.startswith("時間："):
            detail["time_info"] = line.replace("時間：", "").strip()
        elif line.startswith("報到方式："):
            detail["registration_method"] = line.replace("報到方式：", "").strip()

    # Extract credits: "A 類2點" pattern
    credits_match = re.search(r"([A-Z])\s*類\s*(\d+)\s*點", text)
    if credits_match:
        detail["credits_category"] = f"{credits_match.group(1)}類"
        detail["credits"] = credits_match.group(2)

    # Full content as program info
    detail["program_info"] = text

    # Extract download links from articledow
    dow = re.search(
        r'class="articledow">(.*?)(?:</div>\s*</div>|<footer)', html, re.DOTALL
    )
    if dow:
        links = re.findall(
            r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', dow.group(1), re.DOTALL
        )
        downloads = []
        for href, label in links:
            label = re.sub(r"<[^>]+>", "", label).strip()
            if label and label != "返回" and "#" not in href:
                if not href.startswith("http"):
                    href = BASE_URL + href
                downloads.append({"text": label, "url": href})
        if downloads:
            detail["downloads"] = downloads

    return detail


def main():
    print("Fetching event listing...")
    all_events = []

    # Fetch pages (URL-based pagination: /articles/20/1, /articles/20/2, ...)
    for page in range(1, 5):  # up to 4 pages
        url = f"{LIST_URL}{page}"
        print(f"  Page {page}...", end=" ", flush=True)
        try:
            html = fetch_html(url)
            events = parse_listing_page(html)
            print(f"{len(events)} future events")
            if not events and page > 1:
                break
            all_events.extend(events)
        except Exception as e:
            print(f"FAIL ({e})")
            break
        time.sleep(0.3)

    # Deduplicate by event_id (some multi-date events may appear once)
    seen = set()
    unique = []
    for e in all_events:
        if e["event_id"] not in seen:
            seen.add(e["event_id"])
            unique.append(e)
    all_events = unique

    print(f"Total unique future events: {len(all_events)}")

    # Fetch detail pages
    for i, event in enumerate(all_events):
        if not event.get("url"):
            continue
        print(
            f"  [{i+1}/{len(all_events)}] {event['title'][:50]}...",
            end=" ",
            flush=True,
        )
        try:
            detail_html = fetch_html(event["url"])
            detail = parse_detail(detail_html)
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
    new_events = [e for e in all_events if e["event_id"] not in existing_ids]

    if new_events:
        merged = existing + new_events
        merged.sort(key=lambda e: e["date"])
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"\nAdded {len(new_events)} new events (total {len(merged)} in {OUTPUT})")
    else:
        if not existing:
            with open(OUTPUT, "w", encoding="utf-8") as f:
                json.dump(all_events, f, ensure_ascii=False, indent=2)
            print(f"\nSaved {len(all_events)} events to {OUTPUT}")
        else:
            print(f"\nNo new events found ({len(existing)} already in {OUTPUT})")


if __name__ == "__main__":
    main()
