# TSIM Website HTML Structure

## Listing Page

**URL**: `https://www.tsim.org.tw/ehc-tsim/s/w/news_acts/articles/20/{page}`

Pagination is URL-based (page 1, 2, 3...). Events are `<li>` items containing article links.

```html
<li>
  <a href="/ehc-tsim/s/w/news_acts/article/{uuid}">
    <div class="Txt">
      <div class="date">115/03/11</div>
      <h4>2026/4/26 內科醫學會預防醫學暨健康促進研討會(台中場)</h4>
    </div>
  </a>
</li>
```

**Key characteristics**:
- `div.date` = publish date (ROC format), NOT the event date
- `<h4>` = title, which **embeds the event date** (e.g. `2026/4/26 ...` or `115年3月21日 ...`)
- Event date must be extracted via regex from the title text
- Some articles contain multiple events (e.g. flu training with 4 dates in one title)

**Date extraction patterns**:
```python
# AD year: 2026/4/26
re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', title)

# ROC year: 115年3月21日
re.search(r'(\d+)年(\d{1,2})月(\d{1,2})日', title)
```

## Detail Page

**URL**: `https://www.tsim.org.tw/ehc-tsim/s/w/news_acts/article/{uuid}`

Content is in two sections:

### `div.articleinfo` — Event Details

Free-form HTML with structured lines:

```
發佈時間：115/03/11
內科醫學會預防醫學暨健康促進研討會(台中場)
主辦單位：台灣內科醫學會
地點：中山醫學大學行政大樓12樓國際會議廳(台中市南區建國北路一段110號)
時間：2026年4月26日 (星期日)
報到方式：直接到現場簽到。
學分：內科醫學會 A 類2點
課程表：
Time    Topic    Speaker    Moderator
09:00~09:05    Opening    ...
```

Extract by line prefix: `主辦單位：`, `地點：`, `時間：`, `報到方式：`

Credits pattern: `([A-Z])\s*類\s*(\d+)\s*點`

### `div.articledow` — Downloads

```html
<div class="articledow">
  <a href="/ehc-tsim/s/viewFile?documentId=xxx&fileId=">filename.pdf</a>
  <a href="#">返回</a>
</div>
```

Filter out `href="#"` and `返回` links.

## Important Notes

- **SSL**: Broken cert — use `ssl.CERT_NONE`
- **繼續教育活動時間表** (`/edu/schedule/schedule`): Has CAPTCHA, cannot be scraped. Use 活動訊息 page instead.
- **Low volume**: TSIM posts ~2-5 upcoming events at a time
- **Multi-date articles**: Some articles contain multiple event sessions (e.g. flu training across 4 cities). Only the first date in the title is extracted; the detail page contains all dates.
- **No specific start/end times**: Events list dates but not precise hours — create as all-day calendar events
