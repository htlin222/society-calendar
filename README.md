# Society Calendar

> 用 AI 自動抓取台灣醫學會行事曆，一鍵同步到 Google Calendar

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill%20Based-blueviolet?logo=anthropic)](https://claude.ai/claude-code)
[![Google Calendar](https://img.shields.io/badge/Google%20Calendar-MCP%20Sync-4285F4?logo=google-calendar&logoColor=white)](#workflow)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero_(stdlib_only)-brightgreen)](#tech-stack)
[![Made in Taiwan](https://img.shields.io/badge/Made%20in-Taiwan%20%F0%9F%87%B9%F0%9F%87%BC-red)](https://github.com/htlin222/society-calendar)

---

## 為什麼需要這個？

身為醫師，每個月要追蹤 3-5 個學會的繼續教育活動、研討會、年會。每個學會網站長得不一樣，有些用民國年，有些有 CAPTCHA，有些 SSL 壞掉。

**手動做法**：逐一開學會網站 → 翻頁找活動 → 手動建 Google Calendar 事件 → 每月重複

**自動化做法**：給 Claude Code 一個 URL → 自動探索、抓取、建立日曆事件

```
你：/distill-events https://www.hematology.org.tw/...
AI：找到 37 筆活動，要建立 skill 嗎？
你：好
AI：skill 建好了，37 筆活動已同步到 Google Calendar ✓
```

---

## 目前支援的學會

| 學會 | Skill | 活動數 | 特性 |
|------|-------|--------|------|
| 🩸 [血液病學會](https://www.hematology.org.tw) | `/hematology-event` | 37 | Bootstrap table，全年活動 |
| 🎗️ [癌症醫學會](https://www.taiwanoncologysociety.org.tw) | `/oncology-event` | 14 | POST 分頁，民國年，SSL 壞掉 |
| 🏥 [內科醫學會](https://www.tsim.org.tw) | `/tsim-event` | 2 | 日期嵌在標題中，SSL 壞掉 |

---

## 快速開始

### 1. 抓取活動

```bash
# 血液病學會（全年 37 筆）
python3 fetch_events.py

# 癌症醫學會（近期 14 筆）
python3 fetch_oncology_events.py

# 內科醫學會（近期 2 筆）
python3 fetch_tsim_events.py
```

### 2. 同步到 Google Calendar

在 Claude Code 中使用對應的 skill：

```
/hematology-event    # 同步血液病學會
/oncology-event      # 同步癌症醫學會
/tsim-event          # 同步內科醫學會
```

### 3. 新增學會

給 Claude Code 任何學會網站的 URL：

```
/distill-events https://www.some-society.org.tw/events
```

Claude 會自動：
1. 找到行事曆頁面
2. 分析 HTML 結構
3. 建立 scraper 腳本
4. 問你要不要建立 local skill
5. 同步到 Google Calendar

---

## Workflow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  學會網站    │────▶│  fetch_*.py   │────▶│  *_events.json│────▶│ Google Cal   │
│  (HTML)      │     │  (scraper)   │     │  (JSON)      │     │ (MCP sync)   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                   │                    │                     │
       │            ┌──────┴──────┐      ┌──────┴──────┐      ┌──────┴──────┐
       │            │ listing page │      │ merge/dedup │      │ Study 📚    │
       │            │ detail pages │      │ by event_id │      │ calendar    │
       │            │ 0.3s delay   │      │ or URL      │      │ batch of 5  │
       │            └─────────────┘      └─────────────┘      └─────────────┘
       │
  /distill-events
  ┌────┴────┐
  │ 7-step  │
  │ workflow│
  │ 自動探索 │
  └─────────┘
```

### 定期同步

Script 支援 **merge + dedup**，重複執行安全無虞：

```bash
# 每月跑一次，新活動自動 append
python3 fetch_events.py           # "No new events found" or "Added 3 new events"
python3 fetch_oncology_events.py  # 同上
```

---

## Tech Stack

| 元件 | 技術 | 說明 |
|------|------|------|
| Scraper | Python 3 (stdlib) | `urllib` + `re`，零外部依賴 |
| 日曆同步 | Google Calendar MCP | Claude Code 內建 MCP 工具 |
| Skill 系統 | Claude Code Skills | `.claude/skills/` 結構化技能 |
| 探索引擎 | `/distill-events` | 7 步驟自動化新學會流程 |

### 為什麼用 stdlib？

- 醫院電腦通常不能 `pip install`
- 零依賴 = 任何有 Python 3 的環境都能跑
- `urllib` + `re` 處理這些簡單 HTML 綽綽有餘

---

## 專案結構

```
society-calendar/
├── fetch_events.py              # 血液病學會 scraper
├── fetch_oncology_events.py     # 癌症醫學會 scraper
├── fetch_tsim_events.py         # 內科醫學會 scraper
├── events.json                  # 血液病學會活動資料
├── oncology_events.json         # 癌症醫學會活動資料
├── tsim_events.json             # 內科醫學會活動資料
├── LICENSE                      # MIT
└── .claude/skills/
    ├── distill-events/          # 通用探索 skill（給新學會用）
    │   ├── SKILL.md
    │   └── references/
    ├── hematology-event/        # 血液病學會 skill
    │   ├── SKILL.md
    │   ├── scripts/
    │   └── references/
    ├── oncology-event/          # 癌症醫學會 skill
    │   ├── SKILL.md
    │   ├── scripts/
    │   └── references/
    └── tsim-event/              # 內科醫學會 skill
        ├── SKILL.md
        ├── scripts/
        └── references/
```

---

## 處理過的網站特性

這些 scraper 已經處理了台灣學會網站常見的坑：

| 問題 | 解法 |
|------|------|
| HTTP 406 (User-Agent blocked) | 加 `Mozilla/5.0` header |
| SSL 憑證壞掉 | `ssl.CERT_NONE` |
| 民國年日期 `115/04/18` | `year + 1911` 轉換 |
| POST 分頁 | 帶完整 hidden fields |
| CAPTCHA 保護 | 改用其他頁面（如活動訊息） |
| Word HTML 嵌入 | strip `<style>` blocks |
| Footer 滲入內容 | 精準 regex 邊界 |
| 日期嵌在標題中 | regex 從標題提取日期 |

---

## 新增學會的開發流程

```
1. 給 URL → /distill-events https://...
2. Claude 自動探索 HTML 結構
3. 建立 scraper，測試並列出活動
4. 詢問是否建立 skill
5. 打包成 .claude/skills/{name}/
6. 可選：同步到 Google Calendar
```

這個 workflow 已成功處理 3 個不同結構的網站，包含：
- Bootstrap table（血液病學會）
- Div blocks + POST pagination（癌症醫學會）
- Simple `<li>` list + UUID detail pages（內科醫學會）

---

## License

[MIT](LICENSE)
