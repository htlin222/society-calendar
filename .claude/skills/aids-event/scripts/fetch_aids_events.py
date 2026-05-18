#!/usr/bin/env python3
"""Fetch upcoming events from 台灣愛滋病學會 (Taiwan AIDS Society).

Output: events.json (one level up from this script). Unfiltered — the filter
lives in generate_ics.py so you can re-tune it without re-hitting the site.

Run from the repo root or from anywhere — the script self-locates its output.
"""

import json
import re
import ssl
import time
from datetime import date
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.request import Request, build_opener, HTTPCookieProcessor, HTTPSHandler

BASE_URL = "https://www.aids-care.org.tw"
LIST_URL = f"{BASE_URL}/events/index.php"
OUTPUT   = Path(__file__).parent.parent / "events.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def make_opener():
    jar = CookieJar()
    https_handler = HTTPSHandler(context=CTX)
    return build_opener(HTTPCookieProcessor(jar), https_handler)


def fetch(opener, url, referer=None):
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer
    req = Request(url, headers=headers)
    with opener.open(req) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_list(html):
    items = re.findall(
        r'class="events-list__item">(.*?)(?=class="events-list__item"|class="paging)',
        html,
        re.S,
    )
    events = []
    for item in items:
        date_m  = re.search(r'<time[^>]*>([^<]+)</time>', item)
        title_m = re.search(r'<a href="(content\.php\?id=(\d+)[^"]*)"[^>]*>([^<]+)</a>', item)
        place_m = re.search(r'events-list__place">([^<]+)', item)
        score_m = re.search(r'events-list__socre">([^<]+)', item)
        if not (date_m and title_m):
            continue
        events.append({
            "id": title_m.group(2),
            "date": date_m.group(1).strip(),
            "title": title_m.group(3).strip(),
            "url": BASE_URL + "/events/" + title_m.group(1).strip(),
            "location": place_m.group(1).strip() if place_m else "",
            "credits": score_m.group(1).strip() if score_m else "",
        })
    return events


def parse_detail(html):
    info = {}
    dt = re.search(r'活動日期[^<]*</label>\s*([^<]+)', html)
    if dt:
        info["time_range"] = dt.group(1).strip()
    for label, key in [("主辦單位", "organizer"), ("主講人", "speaker")]:
        m = re.search(rf'{label}</label>\s*([^<\n]+)', html)
        if m:
            info[key] = m.group(1).strip()
    cred_m = re.search(r'<strong>(\d+(?:\.\d+)?)</strong>\s*學分', html)
    if cred_m:
        info["credits"] = cred_m.group(1) + " 學分"
    fee_m = re.search(r'活動收費</label>.*?<font[^>]*>([^<]+)</font>', html, re.S)
    if fee_m:
        info["fee"] = fee_m.group(1).strip()
    dl_m = re.search(r'下載檔案.*?href="(/upload/events/files/[^"]+)"', html, re.S)
    if dl_m:
        info["program_url"] = BASE_URL + dl_m.group(1)
    contact_m = re.search(r'聯絡人</label>\s*([^<\n]+)', html)
    if contact_m:
        info["contact"] = contact_m.group(1).strip()
    email_m = re.search(r'聯絡信箱</label>\s*([^<\n]+)', html)
    if email_m:
        info["email"] = email_m.group(1).strip()
    phone_m = re.search(r'電話</label>\s*([^<\n]+)', html)
    if phone_m:
        info["phone"] = phone_m.group(1).strip()
    return info


def main():
    today = date.today().isoformat()
    opener = make_opener()

    print(f"Fetching list from {LIST_URL} ...")
    html = fetch(opener, LIST_URL)
    events = parse_list(html)
    print(f"  Found {len(events)} events on list page")

    # Keep upcoming only (date >= today). Dates are 'YYYY-MM-DD' from the time tag.
    events = [e for e in events if e["date"] >= today]
    print(f"  Upcoming: {len(events)}")

    # Cache by id from previous runs — skip detail fetch if we already have it.
    existing = {}
    if OUTPUT.exists():
        try:
            for e in json.loads(OUTPUT.read_text("utf-8")):
                existing[e["id"]] = e
        except Exception:
            pass

    enriched = []
    for i, ev in enumerate(events, 1):
        eid = ev["id"]
        print(f"  [{i}/{len(events)}] {ev['title'][:50]}", end=" ")
        if eid in existing and existing[eid].get("organizer"):
            enriched.append(existing[eid])
            print("(cached)")
            continue
        time.sleep(0.3)
        try:
            detail_html = fetch(opener, ev["url"], referer=LIST_URL)
            detail = parse_detail(detail_html)
            ev.update(detail)
            print("OK")
        except Exception as ex:
            print(f"ERR: {ex}")
        enriched.append(ev)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), "utf-8")
    print(f"\nOK {len(enriched)} events written to {OUTPUT}")


if __name__ == "__main__":
    main()
