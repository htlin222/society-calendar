---
name: idsroc-event
description: |
  抓取台灣感染症醫學會 IDSROC (https://www.idsroc.org.tw) 即將舉辦的國內外
  研討會，依使用者自訂的「地點關鍵字」與「最低學分」過濾，產生 ICS 檔。

  使用時機：使用者說 "更新 IDSROC 行事曆"、"sync IDSROC calendar"、
  "感染症學會行事曆"、"idsroc"，或任何要求同步台灣感染症醫學會活動的變體。
argument-hint: "[optional: fetch | ics | both]"
allowed-tools: [Bash, Read, Write]
---

# IDSROC Event Sync (Public)

抓取 [台灣感染症醫學會](https://www.idsroc.org.tw) 即將舉辦的國內外研討會，
依使用者自訂的過濾規則產生 `events.ics`，可匯入 Google Calendar 或其他
RFC 5545 相容日曆。

## Quick Start

```sh
cd .claude/skills/idsroc-event
python3 scripts/fetch_idsroc_events.py   # 抓取 → events.json (未過濾)
python3 scripts/generate_ics.py          # 套用過濾 → events.ics
```

兩個步驟分開，重新調過濾規則只需要再跑一次 `generate_ics.py`，不必再連線抓資料。

## 過濾規則（可自訂）

打開 `scripts/generate_ics.py`，最上方有兩個常數：

| 常數 | 預設值 | 說明 |
|------|--------|------|
| `LOCATION_KEYWORDS` | `["台南", "臺南"]` | 活動地點或主辦單位包含任一關鍵字 → 通過 |
| `MIN_CREDITS` | `4.0` | 學分數 ≥ 此值 → 通過 |

兩個條件 **OR**，符合任一就保留。把 `LOCATION_KEYWORDS = []` 且 `MIN_CREDITS = 0`
就會保留全部活動。完整的編輯範例與如何還原原本的台南 / 高雄 / 其他三層規則，
見 `generate_ics.py` 開頭的 docstring。

## Workflow

- [ ] Step 1: 抓取活動 → `events.json`
- [ ] Step 2: 套用過濾，產生 ICS → `events.ics`
- [ ] Step 3: 匯入或訂閱到 Google Calendar

## 同步到 Google Calendar

**選項 A — 一次性匯入 ICS**

1. 開啟 `calendar.google.com`（桌面版）
2. ⚙ 設定 → 匯入及匯出 → 匯入
3. 選擇 `events.ics`，挑一個目標日曆
4. 按「匯入」（同一個 UID 重複匯入會自動去重）

**選項 B — 透過 Claude Code 的 Google Calendar MCP**

在 Claude Code 內讀 `events.json` 後，逐筆呼叫 `mcp__google_calendar__create_event`
（一次 5 筆批次，避免 rate limit）。

## 資料來源

- `side.asp?side=in` — 國內研討會（分頁）
- `side.asp?side=out` — 國外研討會
- `side_info.asp?id=...` — 每場活動的詳細頁

## Event JSON schema

```json
{
  "id": "...",
  "side": "in",
  "title": "...",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "time_range": "YYYY-MM-DD的HH:MM至HH:MM",
  "location": "...",
  "organizer": "感染症醫學會",
  "co_organizer": "",
  "category": "A類",
  "credits": "3",
  "fee": "不收費",
  "contact": "...",
  "email": "...",
  "program_url": "https://www.idsroc.org.tw/DB/Edu/<id>.pdf",
  "url": "https://www.idsroc.org.tw/active/side_info.asp?id=...&side=in"
}
```

## ICS DESCRIPTION 格式

```
主辦單位：{organizer}
協辦單位：{co_organizer}   ← 空值時省略
類別：{category}
積分：{credits}分
費用：{fee}
學會頁面：{url}
課程表：{program_url}      ← 空值時省略
聯絡人：{contact} ({email})
```

## Troubleshooting

| 問題 | 解法 |
|------|------|
| `UnicodeEncodeError` (Windows terminal) | `set PYTHONIOENCODING=utf-8` 或 PowerShell `$env:PYTHONIOENCODING="utf-8"` |
| SSL 錯誤 | `ctx.check_hostname = False` 已內建 |
| 抓到 0 筆活動 | 網站 HTML 結構可能改了；檢查 `side.asp` 的 `data-th=` markup |
| 月份切換後新活動沒進 | 再跑一次 `fetch_idsroc_events.py`（會抓所有 upcoming） |
| 某地活動沒進日曆 | 把該地名加進 `LOCATION_KEYWORDS`，或調降 `MIN_CREDITS` |
