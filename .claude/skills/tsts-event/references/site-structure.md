# TSTS Site Structure

## Listing Pages

**Domestic**: `https://www.tsts.org.tw/events/events.php?type=1`
**International**: `https://www.tsts.org.tw/events/events.php?type=2`

### HTML Structure

Each event is a `<div class="event">` block:

```html
<div class="event">
  <figure class="cover" style="background-image:url(...)"></figure>
  <time>
    MM/DD<span class="year">YYYY</span>
    <span class="to"><i>~</i>MM/DD<span class="year">YYYY</span></span>  <!-- optional end date -->
  </time>
  <span class="type">國內學術活動</span>
  <h4 class="topic"><a href="content.php?type=1&id=XXX&pageNo=1&continue=Y">Title</a></h4>
  <div class="place">Location</div>
  <div class="score">本會一般積分：<strong>N</strong></div>           <!-- optional -->
  <div class="score">機械手臂積分：<strong>N</strong></div>           <!-- optional -->
  <div class="status"><a class="btn" href="...#register">線上報名</a></div>  <!-- optional -->
</div><!--/.event-->
```

### Pagination

Uses `pageNo` GET parameter. Check `<select class="pageTo">` for total pages. Currently single page.

## Detail Pages

**URL pattern**: `https://www.tsts.org.tw/events/content.php?id=XXX`

### Header Section

```html
<div class="eventHeader">
  <div class="event">
    <time>
      MM/DD<span class="year">/YYYY</span>&nbsp;HH:MM
      <span class="to"><i>~</i> HH:MM</span>
    </time>
    <span class="type">國內學術活動</span>
    <h3 class="topic">Title</h3>
    <div class="place">Location</div>
  </div>
</div>
```

### Info Tables

```html
<table class="tableContent">
  <!-- 主辦單位 -->
  <tr><th>主辦單位</th><td>Organizer name</td></tr>
</table>

<!-- 聯絡資訊 -->
<table class="tableContent">
  <tr><th>聯絡人</th><td>Name</td><th>電子信箱</th><td>Email</td></tr>
  <tr><th>聯絡電話</th><td>Phone</td><th>傳真</th><td>Fax</td></tr>
</table>

<!-- 繼續教育 -->
<table class="tableContent">
  <tr><th>核准字號</th><td colspan="3">Number</td></tr>
  <tr><th>本會一般積分</th><td>N 分</td><th>本會時數</th><td>N 小時</td></tr>
</table>

<!-- 線上報名 (optional) -->
<table class="tableContent">
  <tr><th>報名日期</th><td colspan="3">Start ~ End</td></tr>
  <tr><th>報名身份</th><td>會員、非會員</td><th>人數限制</th><td>不限制</td></tr>
  <tr><th>報名收費</th><td>不收費</td><th>提供餐食</th><td>不提供</td></tr>
</table>
```

### Notes
- Date format is Western (MM/DD/YYYY), no ROC calendar conversion needed
- Empty fields show `<font color=grey>無</font>`
- Event content is often an embedded image (`<img>` in `.eventContent`)
- No SSL issues
- No CAPTCHA
