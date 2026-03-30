# TBMT Site Structure

## Event Listing

**URL**: `https://www.tbmt.org.tw/publicUI/D/D10401.aspx`

The listing page uses **FullCalendar** (v4) which fetches events via GET request:

```
GET /publicUI/D/D10401.aspx?start=2026-01-01&end=2026-12-31
```

**Response**: JSON array of event objects:

```json
[
  {
    "id": 1,
    "title": "2026 TBMT-HST聯合學術研討會",
    "start": "2026-04-18",
    "end": "2026-04-19",
    "url": "/publicUI/D/D10402.aspx?arg=8DDA74095FD799E071",
    "color": "#77DD77"
  }
]
```

**Notes**:
- Some titles embed time: `"12:00~14:00 理監事會"` — extract time_range from title prefix
- The `url` field contains relative path with `arg` parameter for detail page
- No pagination needed — all events returned in single response
- Date range query covers full year

## Event Detail Page

**URL pattern**: `https://www.tbmt.org.tw/publicUI/D/D10402.aspx?arg={arg}`

**ASP.NET controls** (extract via `id` attribute):

| Field | Control ID | Example |
|-------|-----------|---------|
| Title | `ctl00_ContentPlaceHolder1_lbl_title` | 2026 TBMT-HST聯合學術研討會 |
| Start date | `ctl00_ContentPlaceHolder1_lbl_sdate` | 2026/04/18 |
| End date | `ctl00_ContentPlaceHolder1_lbl_edate` | 2026/04/19 |
| Organizer | `ctl00_ContentPlaceHolder1_lbl_sponsor` | TBMT & HST |
| Location | `ctl00_ContentPlaceHolder1_lbl_local` | 臺大醫院國際會議中心 |
| Description | `ctl00_ContentPlaceHolder1_lbl_actdesc` | (often empty) |
| Attachments | Near `附件：` label | PDF/DOC download links |

**Structure**: Simple table layout with label-value pairs. The `arg` parameter is an encoded event identifier.
