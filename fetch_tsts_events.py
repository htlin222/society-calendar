#!/usr/bin/env python3
"""Fetch upcoming events from the Taiwan Society of Thoracic Surgeons (TSTS) website."""

import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

BASE_URL = "https://www.tsts.org.tw/events/"
DOMESTIC_URL = BASE_URL + "events.php?type=1"
INTERNATIONAL_URL = BASE_URL + "events.php?type=2"
OUTPUT = "tsts_events.json"


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
    text = text.replace("&emsp;", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def parse_listing(html: str, event_type: str) -> list[dict]:
    """Parse the event listing page (domestic or international)."""
    events = []
    now = datetime.now(timezone.utc)

    # Each event is in a <div class="event"> block
    for block in re.finditer(
        r'<div class="event">(.*?)</div><!--/\.event-->',
        html,
        re.DOTALL,
    ):
        content = block.group(1)

        # Date: <time>MM/DD<span class="year">YYYY</span>
        #        optional: <span class="to"><i>~</i>MM/DD<span class="year">YYYY</span></span>
        start_match = re.search(
            r"<time>\s*(\d{2}/\d{2})<span.*?>(\d{4})</span>", content
        )
        if not start_match:
            continue

        start_md = start_match.group(1)  # MM/DD
        start_year = start_match.group(2)
        start_date = f"{start_year}-{start_md.replace('/', '-')}"

        # End date (optional)
        end_match = re.search(
            r'<span class="to">.*?(\d{2}/\d{2})<span.*?>(\d{4})</span>',
            content,
            re.DOTALL,
        )
        end_date = None
        if end_match:
            end_md = end_match.group(1)
            end_year = end_match.group(2)
            end_date = f"{end_year}-{end_md.replace('/', '-')}"

        # Filter past events
        try:
            dt = datetime.strptime(start_date, "%Y-%m-%d")
            if dt < now.replace(tzinfo=None):
                continue
        except ValueError:
            continue

        # Title + URL
        title_match = re.search(
            r'<h4 class="topic"><a href="([^"]+)">(.*?)</a></h4>',
            content,
            re.DOTALL,
        )
        if not title_match:
            continue

        detail_href = title_match.group(1)
        title = clean_html(title_match.group(2))
        # Build absolute detail URL (strip query params we don't need for dedup)
        event_id_match = re.search(r"id=(\d+)", detail_href)
        event_id = event_id_match.group(1) if event_id_match else ""
        detail_url = f"{BASE_URL}content.php?id={event_id}" if event_id else ""

        # Location
        place_match = re.search(r'<div class="place">(.*?)</div>', content)
        location = clean_html(place_match.group(1)) if place_match else ""

        # Credits
        score_match = re.search(
            r'<div class="score">.*?<strong>([\d.]+)</strong>', content
        )
        credits = score_match.group(1) if score_match else ""

        # Robot arm credits
        robot_match = re.search(
            r"機械手臂積分.*?<strong>([\d.]+)</strong>", content
        )
        robot_credits = robot_match.group(1) if robot_match else ""

        # Has online registration?
        has_registration = "線上報名" in content

        event = {
            "date": start_date,
            "title": title,
            "location": location,
            "type": event_type,
        }
        if end_date and end_date != start_date:
            event["end_date"] = end_date
        if credits:
            event["credits"] = credits
        if robot_credits:
            event["robot_credits"] = robot_credits
        if has_registration:
            event["has_registration"] = True
        if detail_url:
            event["url"] = detail_url

        events.append(event)

    return events


def parse_detail(html: str) -> dict:
    """Parse event detail page for extra info."""
    detail = {}

    # Time from detail page header:
    # <time>MM/DD<span class="year">/YYYY</span>&nbsp;HH:MM
    #   <span class="to"><i>~</i> HH:MM</span>
    time_match = re.search(
        r"<time>\s*(\d{2}/\d{2})<span.*?>/(\d{4})</span>&nbsp;(\d{2}:\d{2})"
        r'(?:\s*<span class="to">.*?(\d{2}:\d{2})</span>)?',
        html,
        re.DOTALL,
    )
    if time_match:
        start_time = time_match.group(3)
        end_time = time_match.group(4) or ""
        detail["start_time"] = start_time
        if end_time:
            detail["end_time"] = end_time

    # Organizer (主辦單位)
    org_match = re.search(
        r"<th[^>]*>主辦單位</th>\s*<td[^>]*>(.*?)</td>", html, re.DOTALL
    )
    if org_match:
        org = clean_html(org_match.group(1))
        if org and org != "無":
            detail["organizer"] = org

    # Contact info
    contact_match = re.search(
        r"<th[^>]*>聯\s*絡\s*人</th>\s*<td[^>]*>(.*?)</td>", html, re.DOTALL
    )
    if contact_match:
        contact = clean_html(contact_match.group(1))
        if contact and contact != "無":
            detail["contact"] = contact

    email_match = re.search(
        r"<th[^>]*>電子信箱</th>\s*<td[^>]*>(.*?)</td>", html, re.DOTALL
    )
    if email_match:
        email = clean_html(email_match.group(1))
        if email and email != "無":
            detail["email"] = email

    # Approval number (核准字號)
    approval_match = re.search(
        r"<th[^>]*>核准字號</th>\s*<td[^>]*>(.*?)</td>", html, re.DOTALL
    )
    if approval_match:
        approval = clean_html(approval_match.group(1))
        if approval and approval != "無":
            detail["approval_number"] = approval

    # Credits from detail page
    credits_match = re.search(
        r"<th[^>]*>本會一般積分</th>\s*<td[^>]*>\s*([\d.]+)\s*分", html
    )
    if credits_match:
        detail["credits"] = credits_match.group(1)

    # Registration info
    reg_date_match = re.search(
        r"<th[^>]*>報名日期</th>\s*<td[^>]*>(.*?)</td>", html, re.DOTALL
    )
    if reg_date_match:
        reg_date = clean_html(reg_date_match.group(1))
        if reg_date and reg_date != "無":
            detail["registration_period"] = reg_date

    fee_match = re.search(
        r"<th[^>]*>報名收費</th>\s*<td[^>]*>(.*?)</td>", html, re.DOTALL
    )
    if fee_match:
        fee = clean_html(fee_match.group(1))
        if fee and fee != "無":
            detail["fee"] = fee

    return detail


def main():
    print("Fetching domestic events...")
    domestic_html = fetch_html(DOMESTIC_URL)
    domestic = parse_listing(domestic_html, "國內學術活動")
    print(f"  Found {len(domestic)} domestic events")

    print("Fetching international events...")
    intl_html = fetch_html(INTERNATIONAL_URL)
    intl = parse_listing(intl_html, "國外學術活動")
    print(f"  Found {len(intl)} international events")

    events = domestic + intl

    # Enrich with detail pages
    for i, event in enumerate(events):
        url = event.get("url")
        if not url:
            continue
        print(f"  [{i+1}/{len(events)}] {event['title'][:40]}...", end=" ", flush=True)
        try:
            detail_html = fetch_html(url)
            detail = parse_detail(detail_html)
            event.update(detail)
            print("OK")
        except Exception as e:
            print(f"FAIL ({e})")
        time.sleep(0.3)

    # Sort by date
    events.sort(key=lambda e: e["date"])

    # Merge with existing file (dedup by url)
    existing = []
    if os.path.exists(OUTPUT):
        with open(OUTPUT) as f:
            existing = json.load(f)

    existing_urls = {e.get("url") for e in existing if e.get("url")}
    new_events = [e for e in events if e.get("url") not in existing_urls]

    if new_events:
        merged = existing + new_events
        merged.sort(key=lambda e: e["date"])
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"\nAdded {len(new_events)} new events (total {len(merged)} in {OUTPUT})")
    else:
        print(f"\nNo new events found ({len(existing)} already in {OUTPUT})")


if __name__ == "__main__":
    main()
