---
name: aids-event
description: |
  抓取台灣愛滋病學會 (Taiwan AIDS Society) 即將舉辦的活動，產生過濾後的 ICS，
  可匯入 Google Calendar 或其他 RFC 5545 相容日曆。

  使用時機：使用者說 "更新愛滋病學會行事曆"、"sync AIDS calendar"、
  "aids events"、"愛滋病學會"，或任何要求同步 Taiwan AIDS Society 活動的變體。
allowed-tools: [Bash, Read, Write]
---

# AIDS Society Event Sync (Public)

抓取 [台灣愛滋病學會](https://www.aids-care.org.tw) 即將舉辦的活動，依使用者
自訂的「地點關鍵字」與「最低學分」過濾，產生 `events.ics` 供匯入或訂閱。

## Quick Start

```sh
cd .claude/skills/aids-event
python3 scripts/fetch_aids_events.py   # 抓取 → events.json (未過濾)
python3 scripts/generate_ics.py        # 套用過濾 → events.ics
```

兩個步驟分開，重新調過濾規則只需要再跑一次 `generate_ics.py`，不必再連線抓資料。

## 過濾規則（可自訂）

打開 `scripts/generate_ics.py`，最上方有兩個常數：

| 常數 | 預設值 | 說明 |
|------|--------|------|
| `LOCATION_KEYWORDS` | `["台南", "臺南"]` | 活動地點或主辦單位包含任一關鍵字 → 通過 |
| `MIN_CREDITS` | `4.0` | 學分數 ≥ 此值 → 通過 |

兩個條件 **OR**，符合任一就保留。把 `LOCATION_KEYWORDS = []` 且 `MIN_CREDITS = 0`
就會保留全部活動。詳細範例（含原本的台南 always / 高雄 > 2 / 其他 > 3 三層規則
怎麼還原）見 `generate_ics.py` 開頭的 docstring。

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
（一次 5 筆批次，避免 rate limit）。這條路徑與本 repo 其他 skill 一致。

## 資料來源

- **列表頁**：`https://www.aids-care.org.tw/events/index.php`
- **詳細頁**：`https://www.aids-care.org.tw/events/content.php?id={id}&pageno=1&continue=Y`
- 詳細頁需要列表頁帶過來的 session cookie，腳本已自動處理

## Event 欄位

| 欄位 | 來源 |
|------|------|
| `date` | `<time class="events-list__date">` |
| `title` | `<a href="content.php?...">` |
| `location` | `<div class="events-list__place">` |
| `credits` | `<span class="events-list__socre">`（原網站 typo） |
| `time_range` | 詳細頁 `活動日期：` |
| `organizer` | 詳細頁 `主辦單位` |
| `speaker` | 詳細頁 `主講人` |
| `fee` | 詳細頁 `活動收費` |
| `program_url` | 詳細頁 `下載檔案` 連結 |
| `contact / email / phone` | 詳細頁 `聯絡資訊` |

## Troubleshooting

| 問題 | 解法 |
|------|------|
| 詳細頁回 `資料讀取有誤` | 腳本必須先打列表頁拿 session cookie — 已內建 |
| 抓到 0 筆活動 | 檢查 `index.php` HTML 裡 `events-list__item` class 是否還在 |
| 某地活動沒進日曆 | 把該地名加進 `LOCATION_KEYWORDS`，或調降 `MIN_CREDITS` |
| `events.json` 裡 credits 是空字串 | 該活動官網沒填學分；會被當作 0 分處理 |
