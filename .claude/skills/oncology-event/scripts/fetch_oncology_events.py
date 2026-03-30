#!/usr/bin/env python3
"""Fetch upcoming events from the Taiwan Oncology Society (癌症醫學會) website."""

import json
import math
import re
import ssl
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# This site has a broken SSL certificate (missing Subject Key Identifier)
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

BASE_URL = "https://www.taiwanoncologysociety.org.tw"
LIST_URL = f"{BASE_URL}/ehc-tos/s/w/edu/scheduleSrh/schedule1"
DETAIL_URL_PREFIX = f"{BASE_URL}/ehc-tos/s/w/edu/scheduleInfo1/schedule1/"
OUTPUT = "oncology_events.json"
PAGE_SIZE = 10


def fetch_html(url: str, post_data: dict | None = None) -> str:
    if post_data:
        data = urlencode(post_data).encode("utf-8")
        req = Request(url, data=data, headers={"User-Agent": "Mozilla/5.0"})
    else:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, context=SSL_CTX) as resp:
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


def roc_to_date(roc_str: str) -> str:
    """Convert ROC date '115/04/18' to ISO '2026-04-18'."""
    m = re.match(r"(\d+)/(\d{2})/(\d{2})", roc_str.strip())
    if m:
        year = int(m.group(1)) + 1911
        return f"{year}-{m.group(2)}-{m.group(3)}"
    return ""


def parse_listing_page(html: str) -> tuple[list[dict], int]:
    """Parse listing page, return (events, total_count)."""
    total_match = re.search(r"totalNum\s*=\s*(\d+)", html)
    total = int(total_match.group(1)) if total_match else 0

    blocks = re.findall(
        r'<div class="title">(.*?)(?=<div class="title"|<div class="page"|</form)',
        html,
        re.DOTALL,
    )

    events = []
    for block in blocks:
        # Extract title + link
        link_match = re.search(
            r'<a href="(/ehc-tos/s/w/edu/scheduleInfo1/schedule1/(\d+))">(.*?)</a>',
            block,
            re.DOTALL,
        )
        if not link_match:
            continue

        href = link_match.group(1)
        event_id = link_match.group(2)
        title = re.sub(r"<[^>]+>", "", link_match.group(3)).strip()

        # Extract text lines from the block
        text = re.sub(r"<[^>]+>", "\n", block)
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Line 0 = title, Line 1 = date range, Line 2 = location, Line 3 = organizer
        # Then pairs: specialty, category, credits
        date_range_raw = lines[1] if len(lines) > 1 else ""
        location = lines[2] if len(lines) > 2 else ""
        organizer = lines[3] if len(lines) > 3 else ""

        # Parse date range: "115/03/31 19:00 - 115/03/31 20:00"
        dm = re.match(
            r"(\d+/\d{2}/\d{2})\s+(\d{2}:\d{2})\s*-\s*(\d+/\d{2}/\d{2})\s+(\d{2}:\d{2})",
            date_range_raw,
        )
        if dm:
            start_date = roc_to_date(dm.group(1))
            start_time = dm.group(2)
            end_date = roc_to_date(dm.group(3))
            end_time = dm.group(4)
        else:
            continue

        # Parse credits from text lines: "腫瘤內科" + "A類" + "1 學分"
        credits_info = []
        for j, line in enumerate(lines):
            if line in ("腫瘤內科", "腫瘤外科"):
                cat = lines[j + 1] if j + 1 < len(lines) else ""
                cred = lines[j + 2] if j + 2 < len(lines) else ""
                cred_match = re.match(r"(\d+)\s*學分", cred)
                if cred_match:
                    credits_info.append(
                        {
                            "specialty": line,
                            "category": cat,
                            "credits": cred_match.group(1),
                        }
                    )

        event = {
            "date": start_date,
            "time": start_time,
            "end_date": end_date,
            "end_time": end_time,
            "title": title,
            "location": location,
            "organizer": organizer,
            "credits_info": credits_info,
            "event_id": event_id,
            "url": f"{BASE_URL}{href}",
        }
        events.append(event)

    return events, total


def parse_detail(html: str) -> dict:
    """Parse event detail page for registration/program info."""
    detail = {}

    # Extract label-value pairs
    sections = re.findall(
        r"<label[^>]*>(.*?)</label>\s*.*?<div[^>]*class=\"[^\"]*form-content[^\"]*\"[^>]*>(.*?)</div>",
        html,
        re.DOTALL,
    )

    for label_html, content_html in sections:
        label = re.sub(r"<[^>]+>", "", label_html).strip().rstrip(":")
        content = clean_html(content_html).strip()

        if not label or not content:
            continue

        if label == "活動地點":
            detail["location_detail"] = content
        elif label == "主講人":
            detail["speakers"] = content
        elif label == "主辦單位":
            detail["organizer_detail"] = content
        elif label == "報名網址(實體會議)" or label == "報名網址":
            detail["registration_url"] = content
        elif label == "活動內容":
            detail["description"] = content
        elif label == "備註":
            detail["notes"] = content
        elif label == "聯絡人":
            detail["contact"] = content
        elif label == "電子信箱":
            detail["email"] = content
        elif label == "網站連結":
            detail["website"] = content
        elif label == "費用":
            detail["fee"] = content
        elif label == "收費備註":
            detail["fee_notes"] = content
        elif label == "餐食":
            detail["meal"] = content
        elif label == "課程表":
            # Extract download link
            link_match = re.search(r'href="([^"]+)"', content_html)
            if link_match:
                href = link_match.group(1)
                if not href.startswith("http"):
                    href = BASE_URL + href
                detail["program_download"] = href

    return detail


def main():
    now = datetime.now()
    roc_year = now.year - 1911
    start_time = now.strftime("%m/%d")

    # Support optional end date via CLI: python3 fetch_oncology_events.py [endYear] [endTime]
    # e.g. python3 fetch_oncology_events.py 115 12/31
    end_params = {}
    if len(sys.argv) >= 3:
        end_params = {"endYear": sys.argv[1], "endTime": sys.argv[2]}

    print("Fetching event listing (page 1)...")
    post_data = {"eduIn": "0", "pageNo": "1", "startYear": str(roc_year), "startTime": start_time}
    post_data.update(end_params)
    html = fetch_html(LIST_URL, post_data)
    events, total = parse_listing_page(html)
    print(f"  Found {total} total upcoming events")

    # Fetch remaining pages
    total_pages = math.ceil(total / PAGE_SIZE)
    for page in range(2, total_pages + 1):
        print(f"Fetching page {page}/{total_pages}...")
        post_data = {"eduIn": "0", "pageNo": str(page), "startYear": str(roc_year), "startTime": start_time}
        post_data.update(end_params)
        html = fetch_html(LIST_URL, post_data)
        page_events, _ = parse_listing_page(html)
        events.extend(page_events)
        time.sleep(0.3)

    print(f"Total events fetched: {len(events)}")

    # Fetch detail pages
    for i, event in enumerate(events):
        print(f"  [{i+1}/{len(events)}] {event['title'][:50]}...", end=" ", flush=True)
        try:
            detail_html = fetch_html(event["url"])
            detail = parse_detail(detail_html)
            event.update(detail)
            print("OK")
        except Exception as e:
            print(f"FAIL ({e})")
        time.sleep(0.3)

    # Merge with existing file (dedup by event_id)
    import os
    existing = []
    if os.path.exists(OUTPUT):
        with open(OUTPUT) as f:
            existing = json.load(f)

    existing_ids = {e["event_id"] for e in existing}
    new_events = [e for e in events if e["event_id"] not in existing_ids]

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
