# TOS Website HTML Structure

## Listing Page

**URL**: `https://www.taiwanoncologysociety.org.tw/ehc-tos/s/w/edu/schedule/schedule1?eduIn=0`

Pagination via POST to `/ehc-tos/s/w/edu/scheduleSrh/schedule1`:

```
POST fields:
  eduIn=0           (domestic events)
  pageNo=1          (page number)
  startYear=115     (ROC year)
  startTime=03/31   (MM/dd)
```

JavaScript variables indicate totals:
```javascript
totalNum = 16       // total events
pageSize = 10       // per page
currentPageNum = 1  // current page
```

### Event Block Structure

Each event is a `<div class="title">` followed by `<div class="row info">`:

```html
<div class="title">
  <a href="/ehc-tos/s/w/edu/scheduleInfo1/schedule1/7536">Event Title</a>
</div>
<div class="row info">
  <!-- Date in ROC format -->
  <span>115/04/11 08:45 - 115/04/12 12:30</span>
  <!-- Location -->
  <span>台大癌醫中心醫院國際會議廳</span>
  <!-- Organizer -->
  <span>中華民國癌症醫學會</span>
  <!-- Credits (repeated per specialty) -->
  <span>腫瘤內科</span>
  <span>A類</span>
  <span>15 學分</span>
  <span>腫瘤外科</span>
  <span>A類</span>
  <span>15 學分</span>
</div>
```

**Parsing strategy**: Split by `<div class="title">`, extract text lines in order:
- Line 0: title
- Line 1: date range (ROC format `YYY/MM/DD HH:MM - YYY/MM/DD HH:MM`)
- Line 2: location
- Line 3: organizer
- Lines 4+: credits triplets (specialty, category, credits)

## Detail Page

**URL pattern**: `https://www.taiwanoncologysociety.org.tw/ehc-tos/s/w/edu/scheduleInfo1/schedule1/{ID}`

Uses `<label>` + `<div class="form-content">` pairs:

```html
<label>課程表</label>
<div class="form-content"><a href="/ehc-tos/s/viewDocument1?documentId=xxx">下載</a></div>

<label>活動地點</label>
<div class="form-content">台大癌醫中心醫院國際會議廳</div>

<label>主講人</label>
<div class="form-content">James Yang、Toshihiko Doi...</div>

<label>主辦單位</label>
<div class="form-content">中華民國癌症醫學會</div>

<label>報名網址(實體會議)</label>
<div class="form-content">https://reurl.cc/vKY93y</div>

<label>活動內容</label>
<div class="form-content">Conference description text...</div>

<label>備註</label>
<div class="form-content">Notes about registration, fees...</div>

<label>聯絡人</label>
<div class="form-content">鄭s</div>

<label>電子信箱</label>
<div class="form-content">email@example.com</div>

<label>費用</label>
<div class="form-content">收費</div>

<label>收費備註</label>
<div class="form-content">會員免報名費</div>

<label>餐食</label>
<div class="form-content">不提供</div>
```

Regex to extract:
```python
re.findall(
    r'<label[^>]*>(.*?)</label>\s*.*?<div[^>]*class="[^"]*form-content[^"]*"[^>]*>(.*?)</div>',
    html, re.DOTALL
)
```

## Important Notes

- **SSL**: Site cert is broken (missing Subject Key Identifier). Must use `ssl.CERT_NONE`.
- **ROC Calendar**: All dates are ROC year (民國). Convert: `ROC_year + 1911 = AD_year`.
- **Pagination**: POST-based. Must include `startYear` and `startTime` to get upcoming events; without these, page 2+ returns archived content from 1996.
- **Rate limiting**: 0.3s delay between requests.
- **Also available**: International events at `schedule2?eduIn=1`.
