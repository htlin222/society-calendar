# TSPCCM Site Structure

## Listing Page

**URL**: `https://www.tspccm.org.tw/conference/list?display_date=YYYY-MM&category=all`

- `display_date`: Month to display (e.g., `2026-04`)
- `category`: Filter — `all`, `4` (一般學術研討會 B), `5` (胸重主辦研討會), `3` (聯甄重症認證課程)
- `city`: Optional city filter (e.g., `taipei_city`)

### HTML Structure

Events are in a `<table id='conferenceTable'>` with rows:

```html
<tr class=''>
  <td class='col-datetime'>
    <span class='fs-em'>MM-DD</span> (DAY)<br>HH:MM ~ HH:MM
  </td>
  <td colspan="2">
    <a href='/conference/NNNN'><span class='text'>Title</span></a>
  </td>
  <td class='col-char3'>...</td>
  <td class='col-division'>Organizer</td>
  <td class='col-site'>Location</td>
  <td class='col-char7'>Credits (e.g., "B類 1 分")</td>
  <td class='col-char7'>Contact info</td>
  <td class='col-category'>Category</td>
</tr>
```

### Key columns
- `col-datetime`: Date (MM-DD) + time range (HH:MM ~ HH:MM)
- `col-division`: Organizer name
- `col-site`: Location/venue
- First `col-char7`: Credits (e.g., "B類 1 分", "B類 3 分")
- Second `col-char7`: Contact person + phone
- `col-category`: Category label

## Detail Pages

**URL pattern**: `https://www.tspccm.org.tw/conference/NNNN`

Detail pages exist but are not needed — the listing already has all relevant fields.

## Notes
- No SSL issues
- No CAPTCHA
- No ROC calendar dates (uses Western MM-DD format)
- No pagination — each month is one page
- ~40-50 events per month (many are weekly recurring hospital meetings)
- The `display_date` parameter controls which month to show
