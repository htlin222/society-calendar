# HST Website HTML Structure

## Listing Page

**URL**: `https://www.hematology.org.tw/web2/project/index.php?act=tag_p`

Uses bootstrap-table. Events are in `<tbody>` as `<tr>` rows:

```html
<table data-toggle='table' class='table table-striped' data-search='true' data-pagination='true'>
  <thead>
    <tr>
      <th>日期</th>
      <th>會議名稱</th>
      <th>地點</th>
      <th>主辦單位</th>
      <th>分類</th>
      <th>積分</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width='15%'>2026-04-18<br>09:00</td>
      <td width='37%'><a href=index.php?act=point&id=2623>Title<br>Subtitle</a></td>
      <td width='15%'>Location</td>
      <td width='15%'>Organizer</td>
      <td width='10%'>甲類</td>
      <td width='8%'>15</td>
    </tr>
  </tbody>
</table>
```

**Key patterns**:
- Date cell: `YYYY-MM-DD<br>HH:MM`
- Title cell: `<a href=index.php?act=point&id=XXXX>Title<br>Subtitle</a>`
- Width percentages are consistent: 15%, 37%, 15%, 15%, 10%, 8%

## Detail Page

**URL pattern**: `https://www.hematology.org.tw/web2/project/index.php?act=point&id={ID}`

Uses bootstrap nav-tabs with 3 panels:

```html
<ul class='nav nav-tabs' role='tablist'>
  <li><a href='#home'>資訊</a></li>
  <li><a href='#profile'>交通</a></li>
  <li><a href='#messages'>報名/節目表</a></li>
</ul>

<div class='tab-content'>
  <!-- Tab 1: 資訊 (Info) -->
  <div role='tabpanel' class='tab-pane active' id='home'>
    <table class='table table-condensed'>
      <tr><td>時間</td><td>2026-04-18的09:00至<br>2026-04-19的15:30</td></tr>
      <tr><td>類型</td><td>甲類</td></tr>
      <tr><td>積分</td><td>15</td></tr>
      <tr><td>主辦單位</td><td>TBMT、HST</td></tr>
      <tr><td>會議地點</td><td>台大醫院國際會議中心</td></tr>
    </table>
  </div>

  <!-- Tab 2: 交通 (Transport) - usually empty -->
  <div role='tabpanel' class='tab-pane' id='profile'>
    <div class='single-post-content'></div>
  </div>

  <!-- Tab 3: 報名/節目表 (Registration/Program) -->
  <div role='tabpanel' class='tab-pane' id='messages'>
    <div class='single-post-content'>
      <!-- Free-form HTML content with event details, links, etc. -->
      <!-- May contain embedded Word HTML (style tags, font-face defs) -->
      <!-- Ends before footer "Contacts 中華民國血液病學會" -->
    </div>
  </div>
</div>
```

**Extraction boundary**: Content in `#messages` tab ends at `<div class='col-sm` (the page layout boundary). The tab-content section is matched with:

```python
re.search(r"<div class='tab-content'>(.*?)</div>\s*</div>\s*<div class='col-sm", html, re.DOTALL)
```

## Important Notes

- **User-Agent required**: Server returns HTTP 406 without `User-Agent: Mozilla/5.0`
- **Encoding**: UTF-8
- **Rate limiting**: Add 0.3s delay between detail page fetches
- **Word HTML**: Some 報名/節目表 content contains embedded Microsoft Word HTML with `<style>` blocks — must be stripped
- **Footer bleed**: The `Contacts 中華民國血液病學會` footer can leak into content if not properly bounded by the tab-content regex
