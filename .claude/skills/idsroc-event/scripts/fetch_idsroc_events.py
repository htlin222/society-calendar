#!/usr/bin/env python3
"""Fetch upcoming events from IDSROC (台灣感染症醫學會).

Output: events.json (one level up from this script). Unfiltered — the filter
lives in generate_ics.py so you can re-tune it without re-hitting the site.

Run:
    python3 scripts/fetch_idsroc_events.py
"""

import io
import json
import re
import ssl
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_URL    = "https://www.idsroc.org.tw"
LISTING_URL = BASE_URL + "/active/side.asp?side={side}&page={page}"
DETAIL_URL  = BASE_URL + "/active/side_info.asp?id={id}&side={side}"
OUTPUT      = Path(__file__).parent.parent / "events.json"
DELAY       = 0.3


def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        raw = r.read()
    return raw.decode("utf-8", errors="replace")


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).replace("&nbsp;", " ").replace("&amp;", "&").strip()


def clean(s):
    return re.sub(r"\s+", " ", strip_tags(s)).strip()


# ── Listing page ──────────────────────────────────────────────────────────────

def parse_listing_page(html):
    """Return list of {id, title, date, location, category, credits, side}."""
    events = []
    for m in re.finditer(
        r'data-th="活動主題">.*?<a href="side_info\.asp\?id=(\d+)&(?:amp;)?side=(in|out)">(.*?)</a>'
        r'.*?data-th="活動日期">(.*?)</div>'
        r'.*?data-th="活動地點">(.*?)</div>'
        r'.*?data-th="類別積分">(.*?)</div>',
        html,
        re.DOTALL,
    ):
        eid, side, title, date_raw, loc_raw, cred_raw = m.groups()
        date_str = clean(date_raw).replace("/", "-")
        loc = clean(loc_raw)
        cred_block = clean(cred_raw)
        cat_m = re.search(r"([A-Z類]+類)", cred_block)
        pts_m = re.search(r"(\d+)\s*分", cred_block)
        events.append({
            "id": eid,
            "side": side,
            "title": clean(title),
            "date": date_str,
            "location": loc,
            "category": cat_m.group(1) if cat_m else "",
            "credits": pts_m.group(1) if pts_m else "",
        })
    return events


def get_total_pages(html):
    m = re.search(r"第\s*\d+\s*/\s*(\d+)\s*頁", html)
    return int(m.group(1)) if m else 1


def fetch_listing(side="in"):
    all_events = []
    page = 1
    while True:
        url = LISTING_URL.format(side=side, page=page)
        html = fetch_html(url)
        events = parse_listing_page(html)
        all_events.extend(events)
        total = get_total_pages(html)
        if page >= total:
            break
        page += 1
        time.sleep(DELAY)
    return all_events


# ── Detail page ───────────────────────────────────────────────────────────────

def parse_time_range(date_str, active_time_raw):
    text = clean(active_time_raw)
    m = re.search(r"(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s*~\s*(\d{2}:\d{2})", text)
    if m:
        d, st, et = m.groups()
        d = d.replace("/", "-")
        return st, f"{d}的{st}至{et}"
    m2 = re.search(
        r"(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s*~\s*(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2})",
        text,
    )
    if m2:
        d1, st, d2, et = m2.groups()
        d1, d2 = d1.replace("/", "-"), d2.replace("/", "-")
        return st, f"{d1}的{st}至\n{d2}的{et}"
    m3 = re.search(r"(\d{4}/\d{2}/\d{2})\s*~\s*(\d{4}/\d{2}/\d{2})", text)
    if m3:
        d1, d2 = m3.groups()
        d1, d2 = d1.replace("/", "-"), d2.replace("/", "-")
        return "00:00", f"{d1}的00:00至\n{d2}的00:00"
    return "00:00", ""


def extract_dl_field(html, label):
    m = re.search(
        r"<dt>\s*" + re.escape(label) + r"\s*</dt>\s*<dd>(.*?)</dd>",
        html,
        re.DOTALL,
    )
    return clean(m.group(1)) if m else ""


def parse_detail(html, eid, side, listing_date):
    at_m = re.search(r'<time class="activeTime">(.*?)</time>', html, re.DOTALL)
    active_time_raw = at_m.group(1) if at_m else ""
    time_hhmm, time_range = parse_time_range(listing_date, active_time_raw)

    loc_m = re.search(r'<div class="activePlace">活動地點：(.*?)</div>', html)
    location = clean(loc_m.group(1)) if loc_m else ""

    organizer = extract_dl_field(html, "主辦單位：")
    co_org    = extract_dl_field(html, "協辦單位：")
    category  = extract_dl_field(html, "類別：")
    credits   = extract_dl_field(html, "積分：")
    fee       = extract_dl_field(html, "費用：")
    contact   = extract_dl_field(html, "連絡人：")
    email     = extract_dl_field(html, "E-Mail：")

    pdf_m = re.search(r'href="(\.\./DB/Edu/\d+\.pdf[^"]*)"', html)
    program_url = BASE_URL + "/" + pdf_m.group(1).lstrip("./") if pdf_m else ""

    return {
        "time": time_hhmm,
        "time_range": time_range,
        "location": location,
        "organizer": organizer,
        "co_organizer": co_org,
        "category": category,
        "credits": credits,
        "fee": fee,
        "contact": contact,
        "email": email,
        "program_url": program_url,
        "url": DETAIL_URL.format(id=eid, side=side),
    }


def main():
    today = date.today().isoformat()

    print("Fetching domestic events (國內研討會)…")
    events = fetch_listing("in")
    print(f"  Found {len(events)} domestic events")

    print("Fetching international events (國外研討會)…")
    intl = fetch_listing("out")
    print(f"  Found {len(intl)} international events")
    events.extend(intl)

    events = [e for e in events if e["date"] >= today]
    print(f"Upcoming: {len(events)}")

    seen = set()
    unique = []
    for e in events:
        if e["id"] not in seen:
            seen.add(e["id"])
            unique.append(e)
    events = unique

    print("Fetching detail pages…")
    enriched = []
    for i, e in enumerate(events):
        print(f"  [{i+1}/{len(events)}] {e['date']} {e['title'][:40]}")
        try:
            html = fetch_html(DETAIL_URL.format(id=e["id"], side=e["side"]))
            detail = parse_detail(html, e["id"], e["side"], e["date"])
            merged = {**e, **{k: v for k, v in detail.items() if v}}
            enriched.append(merged)
        except Exception as ex:
            print(f"    WARNING: {ex}")
            e.setdefault("time", "00:00")
            e.setdefault("time_range", "")
            e.setdefault("url", DETAIL_URL.format(id=e["id"], side=e["side"]))
            enriched.append(e)
        time.sleep(DELAY)

    enriched.sort(key=lambda x: (x["date"], x.get("time", "00:00")))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"\nOK {len(enriched)} events written to {OUTPUT}")


if __name__ == "__main__":
    main()
