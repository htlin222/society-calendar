#!/usr/bin/env python3
"""
Generate events.ics from events.json with a user-customisable filter.

# ── FILTER (edit to taste) ────────────────────────────────────────────────────
Two knobs at the top of this file, OR-ed together:

    LOCATION_KEYWORDS = ["台南", "臺南"]   # location/organizer substring match
    MIN_CREDITS       = 4.0                # numeric threshold (>=)

An event passes if EITHER rule fires. Set `LOCATION_KEYWORDS = []` AND
`MIN_CREDITS = 0` to include everything.

# Worked example — recreate the original tiered rule (台南 always /
# 高雄(含義大) > 2 學分 / 其他 > 3 學分):
#
#     TAINAN_KW    = ["台南", "臺南"]
#     KAOHSIUNG_KW = ["高雄", "義大", "嘉義"]
#     def passes_filter(e):
#         loc  = e.get("location", "") + e.get("organizer", "")
#         cred = credits_value(e.get("credits", ""))
#         if any(kw in loc for kw in TAINAN_KW):    return True
#         if any(kw in loc for kw in KAOHSIUNG_KW): return cred > 2
#         return cred > 3

Run:
    python3 scripts/generate_ics.py
"""

import io
import json
import re
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).parent.parent  # skill root

# ── FILTER (edit to taste) ────────────────────────────────────────────────────
LOCATION_KEYWORDS = ["台南", "臺南"]
MIN_CREDITS       = 4.0
# ──────────────────────────────────────────────────────────────────────────────


def load_events():
    with open(BASE / "events.json", encoding="utf-8") as f:
        return json.load(f)


def credits_value(credits_str):
    """Extract numeric value from '2 學分', '7.5 學分', etc."""
    m = re.search(r"(\d+(?:\.\d+)?)", credits_str or "")
    return float(m.group(1)) if m else 0.0


def passes_filter(e):
    loc  = e.get("location", "") + e.get("organizer", "")
    cred = credits_value(e.get("credits", ""))
    if LOCATION_KEYWORDS and any(kw in loc for kw in LOCATION_KEYWORDS):
        return True
    if MIN_CREDITS and cred >= MIN_CREDITS:
        return True
    return not LOCATION_KEYWORDS and not MIN_CREDITS  # both off → keep all


def parse_time_range(tr):
    """Return (start_date, start_time, end_date, end_time) or None.
    Input: '2026/05/14 12:00 ～ 14:00' or '2026/05/14 ～ 2026/05/15' or '2026/05/14'
    """
    if not tr:
        return None
    tr = tr.strip()
    m = re.match(r"(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s*[～~]\s*(\d{2}:\d{2})$", tr)
    if m:
        d, st, et = m.groups()
        d = d.replace("/", "-")
        return d, st, d, et
    m = re.match(r"(\d{4}/\d{2}/\d{2})\s*[～~]\s*(\d{4}/\d{2}/\d{2})$", tr)
    if m:
        sd, ed = m.groups()
        return sd.replace("/", "-"), None, ed.replace("/", "-"), None
    m = re.match(r"(\d{4}/\d{2}/\d{2})$", tr)
    if m:
        d = m.group(1).replace("/", "-")
        return d, None, d, None
    return None


def esc(s):
    return (
        s.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "")
    )


def fold(name, value):
    """Fold ICS line at 75 octets per RFC 5545 §3.1."""
    line = f"{name}:{value}"
    b = line.encode("utf-8")
    chunks = []
    first = True
    while b:
        limit = 75 if first else 74
        first = False
        cut = min(limit, len(b))
        while cut > 0:
            try:
                b[:cut].decode("utf-8")
                break
            except UnicodeDecodeError:
                cut -= 1
        chunks.append(b[:cut].decode("utf-8"))
        b = b[cut:]
    result = chunks[0]
    for chunk in chunks[1:]:
        result += "\r\n " + chunk
    return result + "\r\n"


def build_desc(e):
    p = []
    if e.get("organizer"):   p.append(f"主辦單位：{e['organizer']}")
    if e.get("speaker"):     p.append(f"主講人：{e['speaker']}")
    if e.get("credits"):     p.append(f"積分：{e['credits']}")
    if e.get("fee"):         p.append(f"費用：{e['fee']}")
    if e.get("url"):         p.append(f"學會頁面：{e['url']}")
    if e.get("program_url"): p.append(f"課程表：{e['program_url']}")
    if e.get("contact"):
        line = f"聯絡人：{e['contact']}"
        if e.get("email"): line += f" ({e['email']})"
        if e.get("phone"): line += f" {e['phone']}"
        p.append(line)
    return "\n".join(p)


def main():
    all_events = load_events()
    events = [e for e in all_events if passes_filter(e)]
    skipped = len(all_events) - len(events)
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = BASE / "events.ics"

    with open(out, "w", encoding="utf-8", newline="") as f:
        def w(line):  f.write(line + "\r\n")
        def wf(name, value): f.write(fold(name, value))

        w("BEGIN:VCALENDAR")
        w("VERSION:2.0")
        w("PRODID:-//AIDS Society Taiwan//Event Calendar//ZH")
        w("CALSCALE:GREGORIAN")
        w("METHOD:PUBLISH")
        w("X-WR-CALNAME:愛滋病學會")
        w("X-WR-TIMEZONE:Asia/Taipei")
        w("BEGIN:VTIMEZONE")
        w("TZID:Asia/Taipei")
        w("BEGIN:STANDARD")
        w("DTSTART:19700101T000000")
        w("TZOFFSETFROM:+0800")
        w("TZOFFSETTO:+0800")
        w("TZNAME:CST")
        w("END:STANDARD")
        w("END:VTIMEZONE")

        for e in events:
            uid = str(uuid.uuid5(uuid.NAMESPACE_URL, e["url"]))
            tr  = parse_time_range(e.get("time_range", ""))

            w("BEGIN:VEVENT")
            w(f"UID:{uid}")
            w(f"DTSTAMP:{now}")
            wf("SUMMARY", esc(e["title"]))
            if e.get("location"):
                wf("LOCATION", esc(e["location"]))
            desc = build_desc(e)
            if desc:
                wf("DESCRIPTION", esc(desc))

            if tr:
                sd, st, ed, et = tr
                if st and et:
                    w(f"DTSTART;TZID=Asia/Taipei:{sd.replace('-','')}T{st.replace(':','')}00")
                    w(f"DTEND;TZID=Asia/Taipei:{ed.replace('-','')}T{et.replace(':','')}00")
                else:
                    sd_d = date.fromisoformat(sd)
                    ed_d = date.fromisoformat(ed) + timedelta(days=1)
                    w(f"DTSTART;VALUE=DATE:{sd_d:%Y%m%d}")
                    w(f"DTEND;VALUE=DATE:{ed_d:%Y%m%d}")
            else:
                d = e["date"].replace("/", "-")
                sd_d = date.fromisoformat(d)
                w(f"DTSTART;VALUE=DATE:{sd_d:%Y%m%d}")
                w(f"DTEND;VALUE=DATE:{(sd_d + timedelta(days=1)):%Y%m%d}")

            w("END:VEVENT")

        w("END:VCALENDAR")

    print(f"OK 通過過濾 {len(events)}/{len(all_events)}，已寫入 {out}（過濾掉 {skipped}）")


if __name__ == "__main__":
    main()
