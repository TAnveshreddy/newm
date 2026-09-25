#!/usr/bin/env node
/**
 * Static site generator for the Eternal Multi Specialty Hospital website.
 *
 *   node build.mjs
 *
 * Reads content/site.json (all editable content) + src/ (CSS, JS, images)
 * and writes a complete, deployable website to public/.
 * No dependencies: plain Node.js 18+.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(ROOT, "public");
const site = JSON.parse(fs.readFileSync(path.join(ROOT, "content/site.json"), "utf8"));
const H = site.hospital;
const BASE = site.siteUrl.replace(/\/+$/, "");
const TODAY = new Date().toISOString().slice(0, 10);

const doctors = site.doctors;
const services = site.services.filter((s) => s.enabled);
const pendingServices = site.services.filter((s) => !s.enabled);
const facilities = site.facilities.filter((f) => f.enabled);
const pendingFacilities = site.facilities.filter((f) => !f.enabled);
const doctorBySlug = Object.fromEntries(doctors.map((d) => [d.slug, d]));
const primaryPhone = H.phones.find((p) => p.primary) || H.phones[0];
const primaryWa = H.whatsapp.find((w) => w.primary) || H.whatsapp[0];

/* ---------------------------------------------------------------- helpers */

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const abs = (p) => BASE + p;
const intl = (n) => "+91" + n.replace(/\D/g, "").replace(/^91(?=\d{10}$)/, "");
const telHref = (n) => "tel:" + intl(n);
const fmtPhone = (n) => { const d = n.replace(/\D/g, ""); return d.length === 10 ? `${d.slice(0, 5)} ${d.slice(5)}` : n; };
const waHref = (n, text) => `https://wa.me/${intl(n).slice(1)}?text=${encodeURIComponent(text)}`;
const addrLine = `${H.address.street}, ${H.address.locality} – ${H.address.postalCode}, ${H.address.region}, ${H.address.countryName}`;
const { latitude: LAT, longitude: LNG } = H.geo;
const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${LAT},${LNG}`;
const mapsUrl = H.googleMapsUrl || `https://www.google.com/maps/search/?api=1&query=${LAT},${LNG}`;
const mapEmbed = `https://maps.google.com/maps?q=${LAT},${LNG}&z=17&hl=en&output=embed`;

const WA_TEMPLATE = `Hello ${H.name},
I would like to enquire about an appointment.

Patient Name:
Doctor:
Preferred Date:
Preferred Time:
Reason for Visit:`;
const waTemplateFor = (doctor) => WA_TEMPLATE.replace("Doctor:", `Doctor: ${doctor ? doctor.name : ""}`);

const placeholder = (text) =>
  site.showPlaceholders ? `<span class="placeholder" role="note">To be updated: ${esc(text)}</span>` : "";

/** Relative link from the page currently being rendered, so the site works on any host / sub-folder. */
let currentPath = "/";
const rel = (target) => {
  // 404.html is served at any URL, so it uses root-absolute links.
  if (currentPath.endsWith(".html")) return "/" + target.replace(/^\//, "");
  const depth = currentPath.split("/").filter(Boolean).length;
  const prefix = depth ? "../".repeat(depth) : "./";
  const t = target.replace(/^\//, "");
  return t === "" ? prefix : prefix + t;
};

/* Image sizes are read from the generated .webp files (see scripts/optimize-images.py). */
function webpSize(file) {
  const b = fs.readFileSync(file);
  const chunk = b.toString("ascii", 12, 16);
  if (chunk === "VP8 ") return [b.readUInt16LE(26) & 0x3fff, b.readUInt16LE(28) & 0x3fff];
  if (chunk === "VP8L") { const v = b.readUInt32LE(21); return [(v & 0x3fff) + 1, ((v >> 14) & 0x3fff) + 1]; }
  if (chunk === "VP8X") return [b.readUIntLE(24, 3) + 1, b.readUIntLE(27, 3) + 1];
  throw new Error("Unknown WebP format: " + file);
}
const IMAGES = {};
for (const f of fs.readdirSync(path.join(ROOT, "src/images"))) {
  const m = f.match(/^(.+)-(\d+)\.webp$/);
  if (!m) continue;
  const [w, h] = webpSize(path.join(ROOT, "src/images", f));
  (IMAGES[m[1]] ||= []).push({ file: f, w, h });
}
for (const list of Object.values(IMAGES)) list.sort((a, b) => a.w - b.w);

function img(name, alt, { sizes = "100vw", eager = false, cls = "" } = {}) {
  const set = IMAGES[name];
  if (!set) throw new Error(`Missing image "${name}". Run scripts/optimize-images.py`);
  const largest = set[set.length - 1];
  return `<img src="${rel("/images/" + largest.file)}" srcset="${set.map((s) => `${rel("/images/" + s.file)} ${s.w}w`).join(", ")}" sizes="${sizes}" width="${largest.w}" height="${largest.h}" alt="${esc(alt)}"${cls ? ` class="${cls}"` : ""} ${eager ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async">`;
}
const imgUrl = (name) => abs("/images/" + IMAGES[name].at(-1).file);

/* ------------------------------------------------------------------ icons */
const ICONS = {
  phone: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
  whatsapp: '<path d="M3 21l1.6-4.7A8.9 8.9 0 1 1 7.9 19.6z"/><path d="M9 9.5c0 3 2.5 5.5 5.5 5.5l1.2-1.4-1.9-1-1 .8c-1-.4-1.8-1.2-2.2-2.2l.8-1-1-1.9z"/>',
  map: '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
  location: '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
  directions: '<polygon points="3 11 22 2 13 21 11 13 3 11"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  menu: '<path d="M3 6h18M3 12h18M3 18h18"/>',
  close: '<path d="M18 6 6 18M6 6l12 12"/>',
  arrow: '<path d="M5 12h14M12 5l7 7-7 7"/>',
  left: '<path d="M15 18l-6-6 6-6"/>',
  right: '<path d="M9 18l6-6-6-6"/>',
  mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
  award: '<circle cx="12" cy="8" r="6"/><path d="M15.5 13 17 22l-5-3-5 3 1.5-9"/>',
  id: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="11" r="2.5"/><path d="M5.5 17a3.5 3.5 0 0 1 7 0M15 9h3M15 13h3"/>',
  child: '<circle cx="12" cy="5" r="3"/><path d="M12 8v7M8 11h8M9 22l3-7 3 7"/>',
  stethoscope: '<path d="M5 3v6a5 5 0 0 0 10 0V3"/><path d="M10 14v2a5 5 0 0 0 10 0v-3"/><circle cx="20" cy="11" r="2"/><path d="M4 3h2M14 3h2"/>',
  heart: '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21.2l8.8-8.8a5.5 5.5 0 0 0 0-7.8z"/><path d="M3 12h5l2-3 3 6 2-3h6"/>',
  emergency: '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M12 7v10M7 12h10"/>',
  pharmacy: '<rect x="3" y="9" width="18" height="8" rx="4" transform="rotate(-45 12 13)"/><path d="m9.5 10.5 5 5"/>',
  room: '<path d="M3 21h18M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"/><circle cx="15" cy="12" r="1"/>',
  bed: '<path d="M2 4v16M2 8h18a2 2 0 0 1 2 2v10M2 17h20"/><circle cx="7" cy="12" r="2"/>',
  lab: '<path d="M9 2h6M10 2v6L4 20a1.5 1.5 0 0 0 1.3 2h13.4a1.5 1.5 0 0 0 1.3-2L14 8V2"/><path d="M7 15h10"/>',
  users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
  image: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  quote: '<path d="M7 7h4v4c0 3-2 5-4 6M15 7h4v4c0 3-2 5-4 6"/>',
  star: '<path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>',
};
const icon = (name, cls = "icon") =>
  `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${ICONS[name] || ICONS.check}</svg>`;

const LOGO = `<svg class="logo-mark" viewBox="0 0 48 48" aria-hidden="true" focusable="false"><circle cx="24" cy="24" r="23" fill="#0b4f8a"/><path d="M19 10h10v9h9v10h-9v9H19v-9h-9V19h9z" fill="#fff"/><path d="M21.5 12.5h5v9h9v5h-9v9h-5v-9h-9v-5h9z" fill="#d62828"/></svg>`;

/* ----------------------------------------------------------------- blocks */

const btn = (href, label, { variant = "primary", ic, external = false, extra = "" } = {}) =>
  `<a class="btn btn-${variant}" href="${esc(href)}"${external ? ' target="_blank" rel="noopener"' : ""}${extra}>${ic ? icon(ic) : ""}<span>${label}</span></a>`;

const callBtn = (n = primaryPhone.number, label = `Call ${fmtPhone(n)}`, variant = "call") =>
  btn(telHref(n), label, { variant, ic: "phone", extra: ` aria-label="Call ${esc(fmtPhone(n))}"` });
const waBtn = (n = primaryWa.number, label = "WhatsApp Us", text = WA_TEMPLATE, variant = "whatsapp") =>
  btn(waHref(n, text), label, { variant, ic: "whatsapp", external: true, extra: ` aria-label="${esc(label)} on WhatsApp ${esc(fmtPhone(n))} (opens WhatsApp)"` });
const dirBtn = (variant = "outline") =>
  btn(directionsUrl, "Get Directions", { variant, ic: "directions", external: true, extra: ' aria-label="Get directions on Google Maps (opens in new tab)"' });
const bookBtn = (label = "Book an Appointment", query = "", variant = "primary") =>
  btn(rel("/appointment/") + query, label, { variant, ic: "calendar" });

const sectionHead = (eyebrow, title, intro = "", level = 2) =>
  `<header class="section-head"><p class="eyebrow">${esc(eyebrow)}</p><h${level}>${title}</h${level}>${intro ? `<p class="lead">${intro}</p>` : ""}</header>`;

function doctorCard(d, level = 3) {
  const dept = services.find((s) => s.doctors.includes(d.slug));
  const profile = rel(`/doctors/${d.slug}/`);
  return `<article class="doc-card">
  <a class="doc-photo" href="${profile}" tabindex="-1" aria-hidden="true">${img(d.photo, d.photoAlt, { sizes: "(min-width: 900px) 300px, 90vw" })}
    <span class="doc-spec">${icon(dept?.icon || "stethoscope")} ${esc(d.specialization)}</span></a>
  <div class="doc-body">
    <h${level} class="doc-name"><a href="${profile}">${esc(d.name)}</a></h${level}>
    <p class="doc-quals">${esc(d.qualifications)}</p>
    ${d.additionalQualifications.map((q) => `<p class="doc-badge">${icon("award")} ${esc(q)}</p>`).join("")}
    <p class="doc-role">${esc(d.role)}</p>
    <p class="doc-role-te" lang="te">${esc(d.roleTelugu)}</p>
    <ul class="doc-tags" role="list">${d.highlights.map((h) => `<li>${esc(h)}</li>`).join("")}</ul>
    <p class="doc-reg">${icon("id")} Reg. No. <strong>${esc(d.registrationNumber)}</strong></p>
  </div>
  <div class="doc-actions">
    ${bookBtn("Book Appointment", `?doctor=${d.slug}`, "accent")}
    <div class="doc-mini">
      <a href="${telHref(d.phone)}" class="mini mini-call" aria-label="Call ${esc(d.name)} on ${fmtPhone(d.phone)}">${icon("phone")}<span>Call</span></a>
      <a href="${waHref(d.whatsapp, waTemplateFor(d))}" class="mini mini-wa" target="_blank" rel="noopener" aria-label="WhatsApp about ${esc(d.name)} (opens WhatsApp)">${icon("whatsapp")}<span>WhatsApp</span></a>
      <a href="${profile}" class="mini mini-profile">${icon("users")}<span>Profile</span></a>
    </div>
  </div>
</article>`;
}

function serviceCard(s, level = 3) {
  const docs = s.doctors.map((slug) => doctorBySlug[slug]).filter(Boolean);
  return `<article class="spec-card">
  <div class="spec-icon">${icon(s.icon)}</div>
  <h${level}><a href="${rel(`/services/${s.slug}/`)}" class="stretched">${esc(s.name)}</a></h${level}>
  ${s.nameTelugu ? `<p class="te" lang="te">${esc(s.nameTelugu)}</p>` : ""}
  <p>${esc(s.summary)}</p>
  ${docs.map((d) => `<p class="spec-doc">${icon("stethoscope")} <span>${esc(d.name)} · ${esc(d.qualifications)}</span></p>`).join("")}
  <div class="spec-foot"><span class="text-link">Know more ${icon("arrow")}</span>
  <a class="btn btn-accent btn-sm lift" href="${rel("/appointment/")}?department=${s.slug}">${icon("calendar")}<span>Book</span></a></div>
</article>`;
}

function searchIndex() {
  const items = [
    ...doctors.map((d) => ({ t: d.name, s: `${d.specialization} · ${d.qualifications}`, u: rel(`/doctors/${d.slug}/`), k: [d.role, d.specialization, d.headline, ...d.highlights, ...d.additionalQualifications, "doctor"].join(" ") })),
    ...services.map((s) => ({ t: s.name, s: "Department", u: rel(`/services/${s.slug}/`), k: [s.summary, "department speciality"].join(" ") })),
    ...facilities.map((f) => ({ t: f.name, s: "Facility", u: rel("/facilities/"), k: f.description })),
    { t: "Book an Appointment", s: "Appointment", u: rel("/appointment/"), k: "booking book slot opd consultation" },
    { t: "Contact & Location", s: "Address, phone, map", u: rel("/contact/"), k: "address map directions phone whatsapp location bus stand" },
    { t: "Photo Gallery", s: "Hospital photos", u: rel("/gallery/"), k: "photos images pictures" },
    { t: "About Us", s: "About the hospital", u: rel("/about/"), k: "about hospital" },
  ];
  return items;
}

const pendingCard = (title, text, ic = "image") =>
  site.showPlaceholders
    ? `<article class="card placeholder-card" role="note">${icon(ic)}<h3>${esc(title)}</h3><p>${esc(text)}</p><p class="placeholder">To be updated – shown only while "showPlaceholders" is true</p></article>`
    : "";

function facilityCard(f) {
  return `<article class="card facility-card">
  ${f.image ? `<div class="facility-img">${img(f.image, `${f.name} at ${H.name}`, { sizes: "(min-width: 900px) 360px, 100vw" })}</div>` : ""}
  <div class="facility-body"><div class="service-icon small">${icon(f.icon)}</div><h3>${esc(f.name)}</h3><p>${esc(f.description)}</p>
  ${f.icon === "emergency" ? callBtn(H.emergency.phone, `Emergency: ${fmtPhone(H.emergency.phone)}`, "emergency") : ""}</div>
</article>`;
}

function galleryGrid(items) {
  return `<ul class="gallery" role="list">${items
    .map(
      (g, i) => `<li><figure>
  <button type="button" class="gallery-open" data-index="${i}" data-full="${rel("/images/" + IMAGES[g.image].at(-1).file)}" data-caption="${esc(g.caption)}" aria-label="Enlarge photo: ${esc(g.caption)}">${img(g.image, g.alt, { sizes: "(min-width: 900px) 33vw, (min-width: 600px) 50vw, 100vw" })}</button>
  <figcaption>${esc(g.caption)}</figcaption></figure></li>`
    )
    .join("")}${
    site.showPlaceholders
      ? site.galleryPlaceholders.map((p) => `<li class="gallery-ph" role="note">${icon("image")}<span>Photo to be added: ${esc(p)}</span></li>`).join("")
      : ""
  }</ul>
<dialog class="lightbox" aria-label="Photo viewer">
  <button type="button" class="lb-close" aria-label="Close photo viewer">${icon("close")}</button>
  <button type="button" class="lb-prev" aria-label="Previous photo">${icon("left")}</button>
  <figure><img src="" alt=""><figcaption></figcaption></figure>
  <button type="button" class="lb-next" aria-label="Next photo">${icon("right")}</button>
</dialog>`;
}

const addressBlock = () => `<address class="address">
  <strong>${esc(H.name)}</strong><br>
  ${esc(H.address.street)},<br>
  ${esc(H.address.locality)} – ${esc(H.address.postalCode)},<br>
  ${esc(H.address.region)}, ${esc(H.address.countryName)}
</address>`;

const phoneList = () => `<ul class="phone-list" role="list">${H.phones
  .map(
    (p) => `<li><span class="phone-label">${esc(p.label)}</span>
    <a class="phone-number" href="${telHref(p.number)}">${icon("phone")} ${fmtPhone(p.number)}</a>
    ${H.whatsapp.some((w) => w.number === p.number) ? `<a class="wa-link" href="${waHref(p.number, WA_TEMPLATE)}" target="_blank" rel="noopener" aria-label="WhatsApp ${fmtPhone(p.number)} (opens WhatsApp)">${icon("whatsapp")} WhatsApp</a>` : ""}</li>`
  )
  .join("")}</ul>`;

const hoursBlock = () =>
  H.hours
    ? `<ul class="hours" role="list">${H.hours.map((h) => `<li><span>${esc(h.days.join(", "))}</span> <strong>${esc(h.opens)} – ${esc(h.closes)}</strong></li>`).join("")}</ul>`
    : placeholder("Hospital / OPD timings");

const mapBlock = () => `<div class="map-wrap">
  <iframe src="${mapEmbed}" title="Google Map showing the location of ${esc(H.name)}, Palakurthy" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
</div>
<div class="btn-row">${dirBtn("primary")}${btn(mapsUrl, "Find us on Google Maps", { variant: "outline", ic: "map", external: true, extra: ' aria-label="Find us on Google Maps (opens in new tab)"' })}</div>`;

/* ------------------------------------------------------------------ forms */

function appointmentForm() {
  const submitLabel = site.forms.mode === "whatsapp" ? "Send Appointment Request on WhatsApp" : "Request Appointment";
  return `<form class="form" id="appointment-form" data-form="appointment" novalidate>
  <p class="form-note">Fields marked <span class="req" aria-hidden="true">*</span><span class="sr-only">with an asterisk</span> are required. The hospital will contact you to confirm the appointment.</p>
  <div class="field"><label for="ap-name">Patient Name <span class="req" aria-hidden="true">*</span></label>
    <input id="ap-name" name="patientName" type="text" autocomplete="name" required maxlength="80"></div>
  <div class="field"><label for="ap-mobile">Mobile Number <span class="req" aria-hidden="true">*</span></label>
    <input id="ap-mobile" name="mobile" type="tel" inputmode="numeric" autocomplete="tel-national" required pattern="[6-9][0-9]{9}" maxlength="10" aria-describedby="ap-mobile-hint">
    <small id="ap-mobile-hint">10-digit mobile number, e.g. 98765 43210</small></div>
  <div class="field-row">
    <div class="field"><label for="ap-date">Preferred Date <span class="req" aria-hidden="true">*</span></label>
      <input id="ap-date" name="preferredDate" type="date" required></div>
    <div class="field"><label for="ap-time">Preferred Time</label>
      <select id="ap-time" name="preferredTime">${site.forms.timeSlots.map((t) => `<option>${esc(t)}</option>`).join("")}</select></div>
  </div>
  <div class="field"><label for="ap-doctor">Doctor</label>
    <select id="ap-doctor" name="doctor">
      <option value="" data-whatsapp="${primaryWa.number}">Any available doctor</option>
      ${doctors.map((d) => `<option value="${d.slug}" data-name="${esc(d.name)}" data-whatsapp="${d.whatsapp}" data-department="${esc(services.find((s) => s.doctors.includes(d.slug))?.slug || "")}">${esc(d.name)} – ${esc(d.specialization)}</option>`).join("")}
    </select></div>
  <div class="field"><label for="ap-dept">Department / Specialization</label>
    <select id="ap-dept" name="department">
      <option value="">Not sure / General enquiry</option>
      ${services.map((s) => `<option value="${s.slug}" data-name="${esc(s.name)}">${esc(s.name)}</option>`).join("")}
    </select></div>
  <div class="field"><label for="ap-reason">Reason for Visit</label>
    <textarea id="ap-reason" name="reason" rows="4" maxlength="500" placeholder="Briefly describe the reason for your visit"></textarea></div>
  <div class="hp" aria-hidden="true"><label for="ap-website">Leave this field empty</label><input id="ap-website" name="website" type="text" tabindex="-1" autocomplete="off"></div>
  <button class="btn btn-primary btn-block" type="submit">${icon(site.forms.mode === "whatsapp" ? "whatsapp" : "calendar")}<span>${submitLabel}</span></button>
  <p class="form-status" role="status" aria-live="polite"></p>
  <p class="form-privacy">This is an appointment <em>request</em>, not a confirmed booking. For emergencies call <a href="${telHref(H.emergency.phone)}">${fmtPhone(H.emergency.phone)}</a>. See our <a href="${rel("/privacy-policy/")}">Privacy Policy</a>.</p>
</form>`;
}

function contactForm() {
  return `<form class="form" id="contact-form" data-form="contact" novalidate>
  <div class="field"><label for="ct-name">Your Name <span class="req" aria-hidden="true">*</span></label>
    <input id="ct-name" name="name" type="text" autocomplete="name" required maxlength="80"></div>
  <div class="field"><label for="ct-mobile">Mobile Number <span class="req" aria-hidden="true">*</span></label>
    <input id="ct-mobile" name="mobile" type="tel" inputmode="numeric" autocomplete="tel-national" required pattern="[6-9][0-9]{9}" maxlength="10"></div>
  <div class="field"><label for="ct-message">Message <span class="req" aria-hidden="true">*</span></label>
    <textarea id="ct-message" name="message" rows="4" required maxlength="800"></textarea></div>
  <div class="hp" aria-hidden="true"><label for="ct-website">Leave this field empty</label><input id="ct-website" name="website" type="text" tabindex="-1" autocomplete="off"></div>
  <button class="btn btn-primary btn-block" type="submit">${icon(site.forms.mode === "whatsapp" ? "whatsapp" : "mail")}<span>${site.forms.mode === "whatsapp" ? "Send Message on WhatsApp" : "Send Message"}</span></button>
  <p class="form-status" role="status" aria-live="polite"></p>
</form>`;
}

/* ----------------------------------------------------------------- schema */

const HOSPITAL_ID = abs("/#hospital");
const postalAddress = {
  "@type": "PostalAddress",
  streetAddress: H.address.street,
  addressLocality: H.address.locality,
  addressRegion: H.address.region,
  postalCode: H.address.postalCode.replace(/\s/g, ""),
  addressCountry: H.address.country,
};
const geo = { "@type": "GeoCoordinates", latitude: LAT, longitude: LNG };

function hospitalSchema() {
  const s = {
    "@context": "https://schema.org",
    "@type": "Hospital",
    "@id": HOSPITAL_ID,
    name: H.name,
    alternateName: [H.nameTelugu, "Eternal Multispeciality Hospital"],
    url: abs("/"),
    image: [abs("/images/og-image.jpg"), imgUrl("hospital-exterior"), imgUrl("hospital-entrance-team")],
    telephone: intl(primaryPhone.number),
    address: postalAddress,
    geo,
    hasMap: mapsUrl,
    areaServed: { "@type": "City", name: H.address.locality },
    medicalSpecialty: doctors.map((d) => d.schemaSpecialty).filter(Boolean),
    contactPoint: [
      ...(H.emergency.enabled ? [{ "@type": "ContactPoint", telephone: intl(H.emergency.phone), contactType: "emergency", areaServed: "IN", availableLanguage: ["Telugu", "English"] }] : []),
      ...H.phones.filter((p) => !p.primary).map((p) => ({ "@type": "ContactPoint", telephone: intl(p.number), contactType: "appointments", name: p.label, areaServed: "IN" })),
    ],
    employee: doctors.map((d) => ({ "@id": abs(`/doctors/${d.slug}/#physician`) })),
  };
  if (H.logo) s.logo = abs("/images/" + H.logo);
  if (H.email) s.email = H.email;
  if (H.sameAs?.length) s.sameAs = H.sameAs;
  if (H.hours?.length)
    s.openingHoursSpecification = H.hours.map((h) => ({ "@type": "OpeningHoursSpecification", dayOfWeek: h.days, opens: h.opens, closes: h.closes }));
  return s;
}

function physicianSchema(d) {
  const s = {
    "@context": "https://schema.org",
    "@type": "Physician",
    "@id": abs(`/doctors/${d.slug}/#physician`),
    name: d.name,
    url: abs(`/doctors/${d.slug}/`),
    image: imgUrl(d.photo),
    description: `${d.name} (${d.qualifications}${d.additionalQualifications.length ? ", " + d.additionalQualifications.join(", ") : ""}) – ${d.role} at ${H.name}, ${H.address.locality}.`,
    telephone: intl(d.phone),
    address: postalAddress,
    geo,
    hospitalAffiliation: { "@id": HOSPITAL_ID, "@type": "Hospital", name: H.name },
    identifier: { "@type": "PropertyValue", propertyID: "Medical Registration Number", value: d.registrationNumber },
    hasCredential: d.qualificationDetails.map((q) => ({ "@type": "EducationalOccupationalCredential", name: q.full, credentialCategory: q.abbr === "Fellowship" ? "Fellowship" : "degree" })),
  };
  if (d.schemaSpecialty) s.medicalSpecialty = d.schemaSpecialty;
  return s;
}

const breadcrumbSchema = (crumbs) => ({
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: crumbs.map(([name, p], i) => ({ "@type": "ListItem", position: i + 1, name, item: abs(p) })),
});

/* ----------------------------------------------------------------- layout */

const NAV = [
  ["Home", "/"],
  ["About Us", "/about/"],
  ["Doctors", "/doctors/"],
  ["Departments", "/services/"],
  ["Facilities", "/facilities/"],
  ["Gallery", "/gallery/"],
  ["Contact", "/contact/"],
];

function layout({ path: p, title, description, body, schema = [], crumbs = null, ogImage = "/images/og-image.jpg", noindex = false }) {
  currentPath = p;
  const isActive = (href) => (href === "/" ? p === "/" : p.startsWith(href));
  const allSchema = [hospitalSchema(), ...schema, ...(crumbs ? [breadcrumbSchema([["Home", "/"], ...crumbs])] : [])];
  const crumbHtml = crumbs
    ? `<nav class="breadcrumbs container" aria-label="Breadcrumb"><ol><li><a href="${rel("/")}">Home</a></li>${crumbs
        .map(([n, u], i) => (i === crumbs.length - 1 ? `<li aria-current="page">${esc(n)}</li>` : `<li><a href="${rel(u)}">${esc(n)}</a></li>`))
        .join("")}</ol></nav>`
    : "";
  const formConfig = {
    mode: site.forms.mode,
    endpoint: site.forms.endpoint,
    email: site.forms.email,
    whatsapp: primaryWa.number.replace(/\D/g, ""),
    hospitalName: H.name,
  };

  const html = `<!doctype html>
<html lang="${site.language}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<link rel="canonical" href="${abs(p)}">
${noindex ? '<meta name="robots" content="noindex">' : '<meta name="robots" content="index, follow, max-image-preview:large">'}
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-src https://maps.google.com https://www.google.com; connect-src 'self' https:; form-action 'self'; base-uri 'self'; object-src 'none'">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#0b4f8a">
<meta name="format-detection" content="telephone=yes">
<meta name="geo.region" content="IN-TG">
<meta name="geo.placename" content="${esc(H.address.locality)}">
<meta name="geo.position" content="${LAT};${LNG}">
<meta name="ICBM" content="${LAT}, ${LNG}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="${esc(H.name)}">
<meta property="og:locale" content="en_IN">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${abs(p)}">
<meta property="og:image" content="${abs(ogImage)}">
<meta property="og:image:alt" content="${esc(H.name)}, ${esc(H.address.locality)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}">
<meta name="twitter:image" content="${abs(ogImage)}">
<link rel="icon" href="${rel("/favicon.svg")}" type="image/svg+xml">
<link rel="apple-touch-icon" href="${rel("/images/apple-touch-icon.png")}">
<link rel="manifest" href="${rel("/site.webmanifest")}">
<link rel="stylesheet" href="${rel("/assets/css/style.css")}">
${allSchema.map((s) => `<script type="application/ld+json">${JSON.stringify(s).replace(/</g, "\\u003c")}</script>`).join("\n")}
</head>
<body>
<a class="skip-link" href="#main">Skip to main content</a>
<div class="utility"><div class="container utility-inner">
  <span class="u-addr">${icon("map")} ${esc(H.address.street)}, ${esc(H.address.locality)} – ${esc(H.address.postalCode)}</span>
  <div class="u-links">
    ${H.emergency.enabled ? `<a href="${telHref(H.emergency.phone)}" class="u-emergency">${icon("emergency")} <span>Emergency 24/7: <strong>${fmtPhone(H.emergency.phone)}</strong></span></a>` : ""}
    <a href="${waHref(primaryWa.number, WA_TEMPLATE)}" class="u-wa" target="_blank" rel="noopener">${icon("whatsapp")} <span>WhatsApp</span></a>
  </div>
</div></div>
<header class="site-header">
  <div class="container header-main">
    <a class="brand" href="${rel("/")}" aria-label="${esc(H.name)} – Home">${LOGO}<span class="brand-text"><span class="brand-name">Eternal</span><span class="brand-sub">Multi Specialty Hospital</span></span></a>
    <form class="site-search" role="search" action="${rel("/doctors/")}" method="get">
      <label class="sr-only" for="site-q">Search doctors, departments and pages</label>
      ${icon("search", "icon search-icon")}
      <input id="site-q" name="q" type="search" placeholder="Search doctors, specialities…" autocomplete="off" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="site-q-results">
      <ul id="site-q-results" class="search-results" role="listbox" aria-label="Search results" hidden></ul>
    </form>
    <div class="header-actions">
      <a class="header-call" href="${telHref(primaryPhone.number)}">${icon("phone")}<span><small>Appointments &amp; Emergency</small><strong>${fmtPhone(primaryPhone.number)}</strong></span></a>
      <a class="btn btn-accent" href="${rel("/appointment/")}">${icon("calendar")}<span>Book Appointment</span></a>
    </div>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Menu">${icon("menu", "icon icon-open")}${icon("close", "icon icon-close")}</button>
  </div>
  <nav id="site-nav" class="site-nav" aria-label="Main">
    <div class="container nav-inner">
      <ul role="list">${NAV.map(([n, u]) => `<li><a href="${rel(u)}"${isActive(u) ? ' aria-current="page"' : ""}>${n}</a></li>`).join("")}</ul>
      <a class="btn btn-accent nav-cta" href="${rel("/appointment/")}">${icon("calendar")}<span>Book Appointment</span></a>
    </div>
  </nav>
</header>
${crumbHtml}
<main id="main" tabindex="-1">
${body}
</main>
<footer class="site-footer">
  <div class="container footer-grid">
    <section aria-labelledby="ft-about">
      <p class="footer-brand" id="ft-about">${LOGO}<span>${esc(H.name)}</span></p>
      <p lang="te" class="te">${esc(H.nameTelugu)}</p>
      ${addressBlock()}
      <div class="btn-row">${dirBtn("light")}</div>
    </section>
    <section aria-labelledby="ft-contact">
      <h2 id="ft-contact">Contact</h2>
      ${phoneList()}
    </section>
    <nav aria-labelledby="ft-links">
      <h2 id="ft-links">Quick Links</h2>
      <ul role="list">${[...NAV.slice(1), ["Book Appointment", "/appointment/"]].map(([n, u]) => `<li><a href="${rel(u)}">${n}</a></li>`).join("")}</ul>
    </nav>
    <nav aria-labelledby="ft-docs">
      <h2 id="ft-docs">Doctors &amp; Departments</h2>
      <ul role="list">${doctors.map((d) => `<li><a href="${rel(`/doctors/${d.slug}/`)}">${esc(d.name)} – ${esc(d.specialization)}</a></li>`).join("")}
      ${services.map((s) => `<li><a href="${rel(`/services/${s.slug}/`)}">${esc(s.name)}</a></li>`).join("")}</ul>
    </nav>
  </div>
  <div class="container footer-bottom">
    <p>&copy; <span data-year>${new Date().getFullYear()}</span> ${esc(H.name)}, ${esc(H.address.locality)}. All rights reserved.</p>
    <ul role="list" class="legal-links">
      <li><a href="${rel("/privacy-policy/")}">Privacy Policy</a></li>
      <li><a href="${rel("/terms/")}">Terms &amp; Conditions</a></li>
      <li><a href="${rel("/medical-disclaimer/")}">Medical Disclaimer</a></li>
      <li><a href="${mapsUrl}" target="_blank" rel="noopener">Google Maps</a></li>
    </ul>
    <p class="disclaimer-short">Information on this website is for general guidance only and is not a substitute for a consultation with a doctor. In an emergency, call ${fmtPhone(H.emergency.phone)} or 108.</p>
  </div>
</footer>
<nav class="mobile-bar" aria-label="Quick contact">
  <a href="${telHref(primaryPhone.number)}" class="mb-call">${icon("phone")}<span>Call</span></a>
  <a href="${waHref(primaryWa.number, WA_TEMPLATE)}" class="mb-wa" target="_blank" rel="noopener">${icon("whatsapp")}<span>WhatsApp</span></a>
  <a href="${rel("/appointment/")}" class="mb-book">${icon("calendar")}<span>Book</span></a>
</nav>
<a class="fab-wa" href="${waHref(primaryWa.number, WA_TEMPLATE)}" target="_blank" rel="noopener" aria-label="Chat with us on WhatsApp (opens WhatsApp)">${icon("whatsapp")}<span>Chat on WhatsApp</span></a>
<script type="application/json" id="search-index">${JSON.stringify(searchIndex()).replace(/</g, "\\u003c")}</script>
<script type="application/json" id="form-config">${JSON.stringify(formConfig).replace(/</g, "\\u003c")}</script>
<script src="${rel("/assets/js/integrations.js")}" defer></script>
<script src="${rel("/assets/js/main.js")}" defer></script>
</body>
</html>
`;
  write(p, html);
  pages.push({ path: p, noindex });
}

const pages = [];
function write(p, html) {
  const file = p.endsWith(".html") ? path.join(OUT, p) : path.join(OUT, p, "index.html");
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, html);
}

/* ------------------------------------------------------------------ pages */

function home() {
  currentPath = "/";
  const tiles = [
    { href: rel("/appointment/"), ic: "calendar", t: "Book Appointment", d: "Request a consultation" },
    { href: rel("/doctors/"), ic: "stethoscope", t: "Find a Doctor", d: "Our specialists" },
    ...(H.emergency.enabled ? [{ href: telHref(H.emergency.phone), ic: "emergency", t: "Emergency 24/7", d: `Call ${fmtPhone(H.emergency.phone)}`, cls: "tile-emergency" }] : []),
    { href: waHref(primaryWa.number, WA_TEMPLATE), ic: "whatsapp", t: "WhatsApp Us", d: "Quick enquiry", ext: true, cls: "tile-wa" },
    { href: directionsUrl, ic: "directions", t: "Get Directions", d: "Opp. Bus Stand", ext: true },
  ];
  const stats = [
    [String(doctors.length), "Specialist Doctors"],
    [String(services.length), "Departments"],
    ...(H.emergency.enabled ? [["24/7", "Emergency Services"]] : []),
    ...(facilities.some((f) => f.icon === "pharmacy") ? [["In-house", "Pharmacy"]] : []),
  ];
  const specialityTiles = [
    ...services.map((s) => ({ ic: s.icon, t: s.name, te: s.nameTelugu, href: rel(`/services/${s.slug}/`) })),
    ...facilities.filter((f) => ["emergency", "pharmacy"].includes(f.icon)).map((f) => ({ ic: f.icon, t: f.name, href: rel("/facilities/") })),
  ];
  const body = `
<section class="hero-banner">
  ${img("hospital-exterior", `${H.name} building, opposite the Bus Stand on Jangaon Road, Palakurthy`, { sizes: "100vw", eager: true, cls: "hero-bg" })}
  <div class="hero-overlay"></div>
  <div class="container hero-content">
    <p class="hero-chip">${icon("map")} ${esc(H.address.locality)}, ${esc(H.address.region)}</p>
    <h1>${esc(H.name)}</h1>
    <p class="hero-te" lang="te">${esc(H.nameTelugu)}</p>
    <p class="hero-tagline">${esc(H.tagline)}.</p>
    <div class="btn-row hero-actions">
      ${bookBtn("Book an Appointment", "", "accent")}
      ${callBtn(primaryPhone.number, "Call Now", "white")}
      ${waBtn(primaryWa.number, "WhatsApp Us")}
      ${dirBtn("ghost")}
    </div>
  </div>
</section>

<section class="action-panel" aria-label="Quick actions">
  <div class="container">
    <ul class="tiles" role="list">${tiles.map((t) => `<li><a class="tile ${t.cls || ""}" href="${t.href}"${t.ext ? ' target="_blank" rel="noopener"' : ""}><span class="tile-icon">${icon(t.ic)}</span><span class="tile-text"><strong>${esc(t.t)}</strong><small>${esc(t.d)}</small></span></a></li>`).join("")}</ul>
  </div>
</section>

<section class="stats" aria-label="Hospital at a glance">
  <div class="container"><ul class="stats-grid" role="list">${stats.map(([n, l]) => `<li><strong>${esc(n)}</strong><span>${esc(l)}</span></li>`).join("")}</ul></div>
</section>

<section class="section" aria-labelledby="spec-h">
  <div class="container">
    ${sectionHead("Our Specialities", '<span id="spec-h">Care you can reach, close to home</span>', `Specialist consultations and services at ${esc(H.name)}, Palakurthy.`)}
    <ul class="spec-tiles" role="list">${specialityTiles.map((t) => `<li><a href="${t.href}" class="spec-tile"><span class="spec-icon">${icon(t.ic)}</span><strong>${esc(t.t)}</strong>${t.te ? `<small lang="te">${esc(t.te)}</small>` : ""}</a></li>`).join("")}</ul>
  </div>
</section>

<section class="section alt" aria-labelledby="doctors-h">
  <div class="container">
    <div class="head-row">${sectionHead("Meet Our Doctors", '<span id="doctors-h">Qualified doctors in Palakurthy</span>', "Experienced care for your family, from newborns to adults.")}
    ${btn(rel("/doctors/"), "View all doctors", { variant: "outline", ic: "arrow" })}</div>
    <div class="doc-grid">${doctors.map((d) => doctorCard(d)).join("")}</div>
  </div>
</section>

<section class="section" aria-labelledby="services-h">
  <div class="container">
    ${sectionHead("Departments", '<span id="services-h">Departments &amp; services</span>')}
    <div class="card-grid">${services.map((s) => serviceCard(s)).join("")}${pendingServices.map((s) => pendingCard(s.name, s.summary, s.icon)).join("")}</div>
  </div>
</section>

<section class="section why" aria-labelledby="about-h">
  <div class="container split">
    <div class="split-media framed">${img("hospital-entrance-team", `The team of ${H.name} at the hospital entrance`, { sizes: "(min-width: 900px) 50vw, 100vw" })}</div>
    <div>
      ${sectionHead("Why Eternal", `<span id="about-h">A multi specialty hospital in the heart of Palakurthy</span>`)}
      <ul class="why-list" role="list">
        <li>${icon("child")}<div><strong>Children's specialist</strong><span>Dr. M. Naresh – M.B.B.S, DCH, MIAP (Pediatrics)</span></div></li>
        <li>${icon("stethoscope")}<div><strong>General Physician</strong><span>Dr. M. Haritha – M.B.B.S, MD General Medicine, Fellowship in Echocardiography</span></div></li>
        ${H.emergency.enabled ? `<li>${icon("emergency")}<div><strong>24/7 Emergency Services</strong><span>Call ${fmtPhone(H.emergency.phone)} any time</span></div></li>` : ""}
        <li>${icon("map")}<div><strong>Easy to reach</strong><span>Opposite the Bus Stand, Jangaon Road, Palakurthy</span></div></li>
      </ul>
      <div class="btn-row">${btn(rel("/about/"), "More about us", { variant: "primary", ic: "arrow" })}</div>
    </div>
  </div>
</section>

<section class="section alt" aria-labelledby="fac-h">
  <div class="container">
    <div class="head-row">${sectionHead("Facilities", '<span id="fac-h">Hospital facilities</span>')}
    ${btn(rel("/facilities/"), "All facilities", { variant: "outline", ic: "arrow" })}</div>
    <div class="card-grid">${facilities.map(facilityCard).join("")}</div>
  </div>
</section>

<section class="section" aria-labelledby="gal-h">
  <div class="container">
    <div class="head-row">${sectionHead("Gallery", '<span id="gal-h">Inside Eternal Hospital</span>')}
    ${btn(rel("/gallery/"), "View gallery", { variant: "outline", ic: "image" })}</div>
    ${galleryGrid(site.gallery.slice(0, 3)).replace(/<li class="gallery-ph"[\s\S]*?<\/li>/g, "")}
  </div>
</section>

${reviewsSection()}

<section class="section alt" aria-labelledby="loc-h">
  <div class="container split">
    <div class="card contact-card">
      ${sectionHead("Location", '<span id="loc-h">Visit us in Palakurthy</span>')}
      ${addressBlock()}
      ${phoneList()}
      <h3 class="h-small">${icon("clock")} Timings</h3>
      ${H.emergency.enabled ? `<p><strong>Emergency:</strong> 24/7</p>` : ""}
      ${hoursBlock()}
    </div>
    <div>${mapBlock()}</div>
  </div>
</section>

${ctaBand()}`;
  layout({
    path: "/",
    title: `${H.name} | Hospital in Palakurthy, Telangana`,
    description: `${H.name}, Opp. Bus Stand, Jangaon Road, Palakurthy. Pediatrician Dr. M. Naresh and General Medicine doctor Dr. M. Haritha.${H.emergency.enabled ? " 24/7 emergency." : ""} Call ${fmtPhone(primaryPhone.number)}.`,
    body,
    schema: [{ "@context": "https://schema.org", "@type": "WebSite", name: H.name, url: abs("/"), inLanguage: site.language }],
  });
}

function reviewsSection() {
  if (!site.reviews?.length) return "";
  return `<section class="section" aria-labelledby="rev-h"><div class="container">
  ${sectionHead("Patient Reviews", '<span id="rev-h">What patients say</span>')}
  <div class="card-grid">${site.reviews.map((r) => `<figure class="card review"><blockquote>${esc(r.text)}</blockquote><figcaption>— ${esc(r.name)}${r.source ? `, ${esc(r.source)}` : ""}</figcaption></figure>`).join("")}</div>
</div></section>`;
}

const ctaBand = () => `<section class="cta-band">
  <div class="container cta-inner">
    <div class="cta-text"><h2>Need to see a doctor?</h2><p>Book an appointment online or on WhatsApp, or call the hospital directly.</p></div>
    <div class="btn-row">${bookBtn("Book an Appointment", "", "accent")}${callBtn(primaryPhone.number, `Call ${fmtPhone(primaryPhone.number)}`, "white")}${waBtn()}</div>
  </div>
</section>`;

const pageHead = (eyebrow, title, intro = "") => `<section class="page-head"><div class="container">
  <p class="eyebrow">${esc(eyebrow)}</p><h1>${title}</h1>${intro ? `<p class="lead">${intro}</p>` : ""}
</div></section>`;

function about() {
  currentPath = "/about/";
  const body = `${pageHead("About Us", `About ${esc(H.name)}`, `A multi specialty hospital opposite the Bus Stand, Jangaon Road, Palakurthy, Telangana.`)}
<section class="section"><div class="container split">
  <div class="prose">
    <h2>Who we are</h2>
    <p><strong>${esc(H.name)}</strong> (<span lang="te">${esc(H.nameTelugu)}</span>) is a hospital in ${esc(H.address.locality)}, ${esc(H.address.region)}, located opposite the Bus Stand on Jangaon Road. It is easy to reach for families from ${esc(H.address.locality)} and nearby villages.</p>
    ${placeholder("Hospital history / year established / mission statement")}
    <h2>Specialties</h2>
    <ul class="ticks">${services.map((s) => `<li>${icon("check")} <a href="${rel(`/services/${s.slug}/`)}">${esc(s.name)}</a>: ${esc(s.summary)}</li>`).join("")}</ul>
    <h2>Our doctors</h2>
    <ul class="ticks">${doctors.map((d) => `<li>${icon("check")} <a href="${rel(`/doctors/${d.slug}/`)}">${esc(d.name)}</a>, ${esc(d.qualifications)}${d.additionalQualifications.length ? ", " + esc(d.additionalQualifications.join(", ")) : ""}: ${esc(d.role)}</li>`).join("")}</ul>
    <h2>Facilities</h2>
    <ul class="ticks">${facilities.map((f) => `<li>${icon("check")} <strong>${esc(f.name)}</strong>: ${esc(f.description)}</li>`).join("")}</ul>
  </div>
  <div class="stack">
    ${img("hospital-exterior", `${H.name} building on Jangaon Road, Palakurthy`, { sizes: "(min-width: 900px) 45vw, 100vw", cls: "rounded" })}
    ${img("hospital-entrance-team", `Staff of ${H.name} at the hospital entrance`, { sizes: "(min-width: 900px) 45vw, 100vw", cls: "rounded" })}
    <div class="card info-card">
      <h2 class="h-small">At a glance</h2>
      <dl class="facts">
        <dt>Location</dt><dd>${esc(addrLine)}</dd>
        <dt>Departments</dt><dd>${services.map((s) => esc(s.name)).join(", ")}</dd>
        <dt>Doctors</dt><dd>${doctors.map((d) => esc(d.name)).join(", ")}</dd>
        ${H.emergency.enabled ? `<dt>Emergency</dt><dd>24/7 – ${fmtPhone(H.emergency.phone)}</dd>` : ""}
        <dt>Phone</dt><dd>${H.phones.map((p) => `<a href="${telHref(p.number)}">${fmtPhone(p.number)}</a>`).join(", ")}</dd>
      </dl>
    </div>
  </div>
</div></section>
${ctaBand()}`;
  layout({
    path: "/about/",
    title: `About Us | ${H.name}, Palakurthy`,
    description: `Learn about ${H.name}, a multi specialty hospital opposite the Bus Stand, Jangaon Road, Palakurthy, with Pediatrics and General Medicine departments.`,
    body,
    crumbs: [["About Us", "/about/"]],
  });
}

function doctorsIndex() {
  currentPath = "/doctors/";
  const body = `${pageHead("Our Doctors", "Doctors in Palakurthy", `Qualified specialists at ${esc(H.name)}. Book an appointment, call or send a WhatsApp message.`)}
<section class="section"><div class="container"><div class="doc-grid">${doctors.map((d) => doctorCard(d, 2)).join("")}</div></div></section>
${ctaBand()}`;
  layout({
    path: "/doctors/",
    title: `Doctors in Palakurthy | ${H.name}`,
    description: `Meet the doctors at ${H.name}, Palakurthy: ${doctors.map((d) => `${d.name} (${d.specialization})`).join(" and ")}. Book an appointment online or on WhatsApp.`,
    body,
    crumbs: [["Doctors", "/doctors/"]],
  });
}

function doctorPage(d) {
  const p = `/doctors/${d.slug}/`;
  currentPath = p;
  const dept = services.find((s) => s.doctors.includes(d.slug));
  const body = `<section class="profile">
  <div class="container profile-grid">
    <div class="profile-photo">${img(d.photo, d.photoAlt, { sizes: "(min-width: 900px) 360px, 80vw", eager: true })}</div>
    <div class="profile-main">
      <p class="chip">${icon(dept?.icon || "stethoscope")} ${esc(d.specialization)}</p>
      <h1>${esc(d.name)}</h1>
      <p class="profile-headline">${esc(d.headline)}</p>
      <p class="profile-quals">${esc(d.qualifications)}${d.additionalQualifications.length ? ` · ${esc(d.additionalQualifications.join(" · "))}` : ""}</p>
      <p class="doctor-role-te" lang="te">${esc(d.roleTelugu)}</p>
      <p class="reg">${icon("id")} Medical Registration No: <strong>${esc(d.registrationNumber)}</strong></p>
      <div class="btn-row">
        ${bookBtn("Book Appointment", `?doctor=${d.slug}`, "accent")}
        ${callBtn(d.phone, `Call ${fmtPhone(d.phone)}`, "white")}
        ${waBtn(d.whatsapp, "WhatsApp", waTemplateFor(d))}
      </div>
    </div>
  </div>
</section>
<section class="section"><div class="container profile-details">
  <div class="card">
    <h2>${icon("award")} Qualifications</h2>
    <ul class="qual-list" role="list">${d.qualificationDetails.map((q) => `<li><span class="qual-abbr">${esc(q.abbr)}</span><span>${esc(q.full)}</span></li>`).join("")}</ul>
  </div>
  <div class="card">
    <h2>${icon("stethoscope")} Specialization</h2>
    <p><strong>${esc(d.role)}</strong></p>
    ${dept ? `<p>Department: <a href="${rel(`/services/${dept.slug}/`)}">${esc(dept.name)}</a></p>` : ""}
    <h3 class="h-small">Areas of care</h3>
    <ul class="ticks">${d.highlights.map((h) => `<li>${icon("check")} ${esc(h)}</li>`).join("")}</ul>
  </div>
  <div class="card">
    <h2>${icon("users")} About ${esc(d.name)}</h2>
    ${d.bio ? `<p>${esc(d.bio)}</p>` : `<p>${esc(d.name)} (${esc(d.qualifications)}) is the ${esc(d.role.split(" – ")[0])} at ${esc(H.name)}, ${esc(H.address.locality)}.</p>${placeholder("Doctor biography / experience")}`}
    <h3 class="h-small">${icon("clock")} Consultation timings</h3>
    ${d.consultationTimings ? `<p>${esc(d.consultationTimings)}</p>` : `<p>Please call <a href="${telHref(d.phone)}">${fmtPhone(d.phone)}</a> to confirm availability.</p>${placeholder("Consultation timings")}`}
  </div>
</div></section>
<section class="section alt"><div class="container">
  ${sectionHead("Location", `Consult ${esc(d.name)} in Palakurthy`)}
  <div class="split">${addressBlock()}<div>${mapBlock()}</div></div>
</div></section>
${ctaBand()}`;
  const spec = d.specialization === "Pediatrics" ? "Pediatrician" : `${d.specialization} Doctor`;
  layout({
    path: p,
    title: `${d.name} – ${spec} in Palakurthy | ${H.name}`,
    description: `${d.name}, ${d.qualifications}${d.additionalQualifications.length ? ", " + d.additionalQualifications.join(", ") : ""}. ${d.role} at ${H.name}, Palakurthy. Reg. No ${d.registrationNumber}. Book an appointment.`,
    body,
    schema: [physicianSchema(d)],
    crumbs: [["Doctors", "/doctors/"], [d.name, p]],
    ogImage: "/images/" + IMAGES[d.photo].at(-1).file,
  });
}

function servicesIndex() {
  currentPath = "/services/";
  const body = `${pageHead("Departments", "Departments &amp; Services", `Specialist consultations at ${esc(H.name)}, Palakurthy.`)}
<section class="section"><div class="container"><div class="card-grid">${services.map((s) => serviceCard(s, 2)).join("")}${pendingServices.map((s) => pendingCard(s.name, s.summary, s.icon)).join("")}</div></div></section>
${ctaBand()}`;
  layout({
    path: "/services/",
    title: `Departments & Services | ${H.name}, Palakurthy`,
    description: `Departments at ${H.name}, Palakurthy: ${services.map((s) => s.name).join(", ")}. Book a consultation with our specialists.`,
    body,
    crumbs: [["Departments", "/services/"]],
  });
}

function servicePage(s) {
  const p = `/services/${s.slug}/`;
  currentPath = p;
  const docs = s.doctors.map((x) => doctorBySlug[x]).filter(Boolean);
  const body = `${pageHead("Department", `${esc(s.name)} in Palakurthy`, esc(s.summary))}
<section class="section"><div class="container split">
  <div class="prose">
    <h2>About the department</h2>
    <p>${esc(s.description)}</p>
    ${s.nameTelugu ? `<p lang="te" class="te">${esc(s.nameTelugu)}</p>` : ""}
    <div class="btn-row">${bookBtn("Book Appointment", `?department=${s.slug}`)}${callBtn()}</div>
  </div>
  <div>${docs.map((d) => doctorCard(d, 2)).join("")}</div>
</div></section>
${ctaBand()}`;
  const docNames = docs.map((d) => d.name).join(", ");
  layout({
    path: p,
    title: `${s.name} in Palakurthy | ${H.name}`,
    description: `${s.name} at ${H.name}, Palakurthy${docNames ? ` with ${docNames}` : ""}. ${s.summary}`,
    body,
    schema: [{ "@context": "https://schema.org", "@type": "MedicalWebPage", name: `${s.name} – ${H.name}`, url: abs(p), about: { "@type": "MedicalSpecialty", name: s.name }, provider: { "@id": HOSPITAL_ID } }],
    crumbs: [["Departments", "/services/"], [s.name, p]],
  });
}

function facilitiesPage() {
  currentPath = "/facilities/";
  const body = `${pageHead("Facilities", "Hospital Facilities", `Facilities available at ${esc(H.name)}, Palakurthy.`)}
<section class="section"><div class="container"><div class="card-grid">${facilities.map(facilityCard).join("")}${pendingFacilities.map((f) => pendingCard(f.name, f.description, f.icon)).join("")}</div></div></section>
${ctaBand()}`;
  layout({
    path: "/facilities/",
    title: `Facilities | ${H.name}, Palakurthy`,
    description: `Facilities at ${H.name}, Palakurthy: ${facilities.map((f) => f.name).join(", ")}.`,
    body,
    crumbs: [["Facilities", "/facilities/"]],
  });
}

function galleryPage() {
  currentPath = "/gallery/";
  const body = `${pageHead("Gallery", "Photo Gallery", `Photographs of ${esc(H.name)}, Palakurthy. Tap a photo to enlarge it.`)}
<section class="section"><div class="container">${galleryGrid(site.gallery)}</div></section>`;
  layout({
    path: "/gallery/",
    title: `Photo Gallery | ${H.name}, Palakurthy`,
    description: `Photos of ${H.name} on Jangaon Road, Palakurthy: the hospital building, entrance, pharmacy and emergency department.`,
    body,
    crumbs: [["Gallery", "/gallery/"]],
  });
}

function contactPage() {
  currentPath = "/contact/";
  const body = `${pageHead("Contact", `Contact ${esc(H.name)}`, "Call, WhatsApp or visit us opposite the Bus Stand, Jangaon Road, Palakurthy.")}
<section class="section"><div class="container split">
  <div>
    <div class="card">
      <h2 class="h-small">${icon("map")} Address</h2>
      ${addressBlock()}
      <h2 class="h-small">${icon("phone")} Phone &amp; WhatsApp</h2>
      ${phoneList()}
      ${H.emergency.enabled ? `<div class="emergency-box">${icon("emergency")}<div><strong>${esc(H.emergency.title)}</strong><br>${callBtn(H.emergency.phone, `Call ${fmtPhone(H.emergency.phone)}`, "emergency")}</div></div>` : ""}
      <h2 class="h-small">${icon("clock")} Timings</h2>
      ${hoursBlock()}
      ${H.email ? `<h2 class="h-small">${icon("mail")} Email</h2><p><a href="mailto:${esc(H.email)}">${esc(H.email)}</a></p>` : ""}
    </div>
    <div class="card">
      <h2>Send us a message</h2>
      ${contactForm()}
    </div>
  </div>
  <div>
    <h2 class="h-small">${icon("directions")} Find us on Google Maps</h2>
    ${mapBlock()}
    <p class="muted">Landmark: opposite the Palakurthy Bus Stand, Jangaon Road.</p>
  </div>
</div></section>`;
  layout({
    path: "/contact/",
    title: `Contact & Location | ${H.name}, Palakurthy`,
    description: `Contact ${H.name}: ${addrLine}. Phone ${H.phones.map((p) => fmtPhone(p.number)).join(", ")}. Get directions on Google Maps.`,
    body,
    crumbs: [["Contact", "/contact/"]],
  });
}

function appointmentPage() {
  currentPath = "/appointment/";
  const body = `${pageHead("Appointment", "Book an Appointment", `Request an appointment at ${esc(H.name)}, Palakurthy. The hospital will contact you to confirm.`)}
<section class="section"><div class="container split split-form">
  <div class="card">${appointmentForm()}</div>
  <aside class="stack" aria-label="Other ways to book">
    <img src="${rel("/assets/img/illustration-care.svg")}" alt="" width="400" height="300" class="illustration" loading="lazy">
    <div class="card">
      <h2 class="h-small">Prefer to call or WhatsApp?</h2>
      ${phoneList()}
    </div>
    ${doctors.map((d) => `<a class="mini-doc card" href="${rel(`/doctors/${d.slug}/`)}">${img(d.photo, "", { sizes: "72px" })}<span><strong>${esc(d.name)}</strong>${esc(d.qualifications)}<br><em>${esc(d.specialization)}</em></span></a>`).join("")}
    ${H.emergency.enabled ? `<div class="emergency-box">${icon("emergency")}<div><strong>Emergency?</strong> Do not wait for an appointment.<br>${callBtn(H.emergency.phone, `Call ${fmtPhone(H.emergency.phone)}`, "emergency")}</div></div>` : ""}
  </aside>
</div></section>`;
  layout({
    path: "/appointment/",
    title: `Book an Appointment | ${H.name}, Palakurthy`,
    description: `Book an appointment with a Pediatrician or General Medicine doctor at ${H.name}, Palakurthy. Request online, on WhatsApp or call ${fmtPhone(primaryPhone.number)}.`,
    body,
    crumbs: [["Book an Appointment", "/appointment/"]],
  });
}

function legalPage(p, title, sections) {
  currentPath = p;
  const body = `${pageHead("Legal", esc(title))}
<section class="section"><div class="container prose narrow">
  ${site.showPlaceholders ? `<p class="placeholder" role="note">Template text – please have this page reviewed before publishing.</p>` : ""}
  ${sections.map(([h, t]) => `<h2>${esc(h)}</h2><p>${t}</p>`).join("")}
  <p class="muted">Last updated: ${TODAY}</p>
</div></section>`;
  layout({ path: p, title: `${title} | ${H.name}`, description: `${title} for the ${H.name} website.`, body, crumbs: [[title, p]] });
}

function legalPages() {
  const contact = `${esc(H.name)}, ${esc(addrLine)}. Phone: <a href="${telHref(primaryPhone.number)}">${fmtPhone(primaryPhone.number)}</a>.`;
  legalPage("/privacy-policy/", "Privacy Policy", [
    ["Information we collect", "When you use the appointment or contact form, we collect only the details you enter: name, mobile number, preferred date and time, doctor, department and reason for visit."],
    ["How the information is sent", site.forms.mode === "whatsapp"
      ? "The forms on this website do not store your information on a server. When you press the submit button, your message is prepared in WhatsApp on your own device and is only sent to the hospital if you choose to send it."
      : "When you submit a form, your details are sent securely to the hospital's appointment system so that the hospital can contact you."],
    ["How we use it", "Your information is used only to respond to your enquiry and arrange your appointment. We do not sell or share it for marketing."],
    ["Third-party services", "This website shows a Google Maps map and links to WhatsApp. These services are provided by Google and WhatsApp (Meta) under their own privacy policies."],
    ["Cookies", "This website does not set its own tracking cookies. The embedded Google Map may set cookies controlled by Google."],
    ["Contact", contact],
  ]);
  legalPage("/terms/", "Terms & Conditions", [
    ["Use of this website", `This website provides general information about ${esc(H.name)}, its doctors and services.`],
    ["Appointments", "Submitting an appointment request does not confirm an appointment. The hospital will contact you to confirm the date and time, which depend on the doctor's availability."],
    ["Accuracy", "We try to keep the information on this website accurate and up to date. Doctor availability, services and timings may change; please call the hospital to confirm."],
    ["External links", "Links to Google Maps, WhatsApp and other websites are provided for convenience. We are not responsible for their content."],
    ["Contact", contact],
  ]);
  legalPage("/medical-disclaimer/", "Medical Disclaimer", [
    ["General information only", "The information on this website is for general information only. It is not medical advice and is not a substitute for a consultation, diagnosis or treatment by a qualified doctor."],
    ["Emergencies", `In a medical emergency, do not use the website forms. Call the hospital on <a href="${telHref(H.emergency.phone)}">${fmtPhone(H.emergency.phone)}</a> or dial 108 for an ambulance.`],
    ["No doctor–patient relationship", "Using this website or sending a message does not create a doctor–patient relationship."],
    ["Contact", contact],
  ]);
}

function notFound() {
  currentPath = "/";
  layout({
    path: "/404.html",
    title: `Page not found | ${H.name}`,
    description: "The page you are looking for could not be found.",
    noindex: true,
    body: `${pageHead("Error 404", "Page not found", "Sorry, this page does not exist.")}
<section class="section"><div class="container btn-row">${btn("/", "Go to Home page", { ic: "arrow" })}${callBtn()}</div></section>`,
  });
}

/* ----------------------------------------------------------------- output */

fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });
fs.cpSync(path.join(ROOT, "src/assets"), path.join(OUT, "assets"), { recursive: true });
fs.cpSync(path.join(ROOT, "src/images"), path.join(OUT, "images"), { recursive: true });
fs.cpSync(path.join(ROOT, "src/static"), OUT, { recursive: true });

home();
about();
doctorsIndex();
doctors.forEach(doctorPage);
servicesIndex();
services.forEach(servicePage);
facilitiesPage();
galleryPage();
contactPage();
appointmentPage();
legalPages();
notFound();

const indexable = pages.filter((p) => !p.noindex);
const priority = (p) => (p === "/" ? "1.0" : p.split("/").filter(Boolean).length === 1 ? "0.8" : "0.7");
fs.writeFileSync(
  path.join(OUT, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${indexable.map((p) => `  <url><loc>${abs(p.path)}</loc><lastmod>${TODAY}</lastmod><priority>${priority(p.path)}</priority></url>`).join("\n")}
</urlset>
`
);
fs.writeFileSync(path.join(OUT, "robots.txt"), `User-agent: *\nAllow: /\n\nSitemap: ${abs("/sitemap.xml")}\n`);
fs.writeFileSync(
  path.join(OUT, "site.webmanifest"),
  JSON.stringify({ name: H.name, short_name: H.shortName, start_url: "./", display: "browser", background_color: "#ffffff", theme_color: "#0b4f8a", icons: [{ src: "favicon.svg", sizes: "any", type: "image/svg+xml" }, { src: "images/apple-touch-icon.png", sizes: "180x180", type: "image/png" }] }, null, 2)
);

console.log(`Built ${pages.length} pages into public/  (siteUrl: ${BASE})`);
if (BASE.includes("YOUR-DOMAIN")) console.warn("⚠  Set \"siteUrl\" in content/site.json to your real domain before publishing.");
if (site.showPlaceholders) console.warn("⚠  showPlaceholders is true: 'To be updated' notes are visible. Set it to false before going live.");
