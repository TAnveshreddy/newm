# Eternal Multi Specialty Hospital – Website

A fast, static, mobile-first website with local SEO, schema.org structured data,
WhatsApp appointment requests and a Google Map. It uses no frameworks and has no running costs.

## Deploy on Netlify

**Option A: drag and drop (easiest)**
1. Download `eternal-hospital-netlify.zip` and unzip it.
2. Open <https://app.netlify.com/drop> and drag the unzipped folder onto the page.
3. The site goes live on a `*.netlify.app` address. You can add your own domain later in
   *Site configuration → Domain management*.

**Option B: from GitHub (updates automatically)**
1. In Netlify, choose *Add new site → Import an existing project* and select this repository.
2. Set **Base directory** to `hospital-website`. The build command (`node build.mjs`) and publish
   directory (`public`) are read from `netlify.toml`.

> After you know the final address (for example `https://eternalhospital.netlify.app` or
> `https://www.eternalhospital.in`), put it in `siteUrl` in `content/site.json` and rebuild.
> SEO canonical links, the sitemap and social-sharing previews all use this address.

## Where to edit (everything is in `content/site.json`)

| What | Key in `content/site.json` |
|---|---|
| Website address (domain) | `siteUrl` |
| Show or hide the yellow "To be updated" notes | `showPlaceholders` (set to `false` before going live) |
| Hospital name, Telugu name, tagline | `hospital.name`, `hospital.nameTelugu`, `hospital.tagline` |
| Address | `hospital.address` |
| Google Maps location | `hospital.geo` (latitude/longitude). Optionally put your Google Business Profile link in `hospital.googleMapsUrl` |
| Phone numbers | `hospital.phones` |
| WhatsApp numbers | `hospital.whatsapp` (first/primary is used by the main WhatsApp buttons); each doctor's `whatsapp` is used for that doctor's buttons and appointment requests |
| 24/7 emergency banner | `hospital.emergency` (`enabled: false` hides it everywhere) |
| Hospital timings | `hospital.hours`: copy the format from `_hoursExample`. Timings are also added to Google structured data |
| Email, social media profiles | `hospital.email`, `hospital.sameAs` (list of official profile URLs) |
| Doctors: name, qualifications, specialization, reg. no., bio, timings | `doctors[]` |
| Departments / services | `services[]` (`enabled: false` hides one) |
| Facilities | `facilities[]` (`enabled: false` hides one) |
| Gallery photos and captions | `gallery[]` |
| Genuine patient reviews | `reviews[]`: e.g. `{ "name": "Patient name", "text": "...", "source": "Google" }`. The section appears only when this list is not empty |
| Appointment form delivery | `forms` (see below) |
| Appointment time choices | `forms.timeSlots` |

After editing, rebuild the site:

```bash
node build.mjs          # writes the finished website to public/
```

### Photos

Original photos are in `originals/`. To add or replace a photo:

1. Put the JPG in `originals/` (e.g. `reception.jpg`).
2. Add a line for it in `scripts/optimize-images.py` (copy an existing `save_sizes(...)` line).
3. Run `pip install pillow` once, then `python3 scripts/optimize-images.py`.
4. Use the image name (e.g. `"reception"`) in `content/site.json` (gallery, facility or doctor `photo`).
5. Run `node build.mjs`.

To replace a doctor photo, overwrite `originals/dr-m-naresh.jpg` or `originals/dr-m-haritha.jpg` and repeat steps 3 and 5.

## Appointment & contact forms

The forms are plain HTML and JavaScript. How they send data is controlled by `forms.mode`:

| `mode` | What happens | Setup |
|---|---|---|
| `"whatsapp"` (default) | Opens WhatsApp with the patient's details filled in. Requests for Dr. Naresh go to 6230533836; others go to 8919431360 | None |
| `"endpoint"` | Sends the form as JSON to `forms.endpoint`. If sending fails, the visitor is offered WhatsApp | See below |
| `"email"` | Opens the visitor's email app addressed to `forms.email` | Set `forms.email` |

All sending code is in `src/assets/js/integrations.js`, kept separate from the page code.

**Google Sheets:** create a Google Sheet, then *Extensions → Apps Script*, and paste:

```js
function doPost(e) {
  var d = JSON.parse(e.postData.contents);
  var s = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var x = d.data;
  s.appendRow([new Date(), d.formType, x.patientName || x.name, x.mobile, x.doctor || "", x.department || "",
               x.preferredDate || "", x.preferredTime || "", x.reason || x.message || ""]);
  return ContentService.createTextOutput(JSON.stringify({ ok: true })).setMimeType(ContentService.MimeType.JSON);
}
```

*Deploy → New deployment → Web app → Who has access: Anyone*, then copy the URL into `forms.endpoint`
and set `forms.mode` to `"endpoint"`.

**Power Automate:** create a flow with the trigger *When an HTTP request is received*, add actions
(e.g. send an email, add a row to Excel, post in Teams), and copy the HTTP POST URL into `forms.endpoint`.

**Hospital system / API:** point `forms.endpoint` at your API. The JSON sent is:

```json
{ "formType": "appointment", "submittedAt": "2026-09-25T10:00:00.000Z", "page": "https://…/appointment/",
  "data": { "patientName": "", "mobile": "", "preferredDate": "2026-10-01", "preferredTime": "Morning",
            "doctor": "Dr. M. Naresh", "department": "Pediatrics", "reason": "" } }
```

Security: never put passwords or API keys in the website files, because everything in them is public.
The service that receives submissions should validate the data and limit how often it can be called.

## Pages

`/`, `/about/`, `/doctors/`, `/doctors/dr-m-naresh/`, `/doctors/dr-m-haritha/`, `/services/`,
`/services/pediatrics/`, `/services/general-medicine/`, `/facilities/`, `/gallery/`, `/contact/`,
`/appointment/`, `/privacy-policy/`, `/terms/`, `/medical-disclaimer/`, plus `sitemap.xml`,
`robots.txt` and `404.html`.

## After going live (local SEO checklist)

1. Claim or verify the **Google Business Profile** for "Eternal Multi Specialty Hospital". Use exactly
   the same name, address and phone number as on the website, and add the website address.
2. Put the Google Business Profile link in `hospital.googleMapsUrl` and rebuild.
3. Submit `https://YOUR-DOMAIN/sitemap.xml` in **Google Search Console**.
4. Check the structured data with <https://search.google.com/test/rich-results>.
5. Ask real patients to leave Google reviews. Add genuine reviews to `reviews[]` only with their permission.
