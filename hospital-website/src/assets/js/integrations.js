/*
 * FORM INTEGRATIONS (the "backend" side of the forms).
 *
 * The website itself is static. Form submissions are handed to ONE of these
 * senders, chosen by "forms.mode" in content/site.json:
 *
 *   "whatsapp"  (default) Opens WhatsApp with the message pre-filled. No server needed.
 *   "endpoint"  POSTs JSON to "forms.endpoint". Works with:
 *                 - Google Sheets  (Google Apps Script web app URL, see EDITING.md)
 *                 - Power Automate ("When an HTTP request is received" trigger URL)
 *                 - Any hospital appointment system / REST API
 *               If the request fails, the visitor is offered WhatsApp instead.
 *   "email"     Opens the visitor's email app addressed to "forms.email".
 *
 * Payload sent to an endpoint (JSON):
 *   { formType: "appointment"|"contact", submittedAt: ISO date, page: URL,
 *     data: { patientName, mobile, preferredDate, preferredTime, doctor,
 *             department, reason }  or  { name, mobile, message } }
 *
 * Security: never put secret keys in this file (everything here is public).
 * The receiving service must validate and rate-limit submissions.
 */
(function () {
  "use strict";

  function waUrl(number, text) {
    var digits = String(number).replace(/\D/g, "");
    if (digits.length === 10) digits = "91" + digits;
    return "https://wa.me/" + digits + "?text=" + encodeURIComponent(text);
  }

  function sendWhatsApp(sub) {
    var url = waUrl(sub.whatsapp, sub.message);
    var win = window.open(url, "_blank", "noopener");
    if (!win) window.location.href = url; // popup blocked: open in same tab
    return Promise.resolve({ ok: true, channel: "whatsapp", url: url });
  }

  function sendEndpoint(sub, config) {
    var controller = "AbortController" in window ? new AbortController() : null;
    var timer = controller && setTimeout(function () { controller.abort(); }, 15000);
    return fetch(config.endpoint, {
      method: "POST",
      // text/plain avoids a CORS preflight (needed for Google Apps Script);
      // the body is still JSON.
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({
        formType: sub.formType,
        submittedAt: new Date().toISOString(),
        page: window.location.href,
        data: sub.data,
      }),
      credentials: "omit",
      signal: controller ? controller.signal : undefined,
    }).then(function (res) {
      if (timer) clearTimeout(timer);
      if (!res.ok) throw new Error("HTTP " + res.status);
      return { ok: true, channel: "endpoint" };
    });
  }

  function sendEmail(sub, config) {
    var subject = sub.formType === "appointment" ? "Appointment request" : "Website enquiry";
    window.location.href = "mailto:" + encodeURIComponent(config.email) +
      "?subject=" + encodeURIComponent(subject + " – " + config.hospitalName) +
      "&body=" + encodeURIComponent(sub.message);
    return Promise.resolve({ ok: true, channel: "email" });
  }

  /** Entry point used by main.js. Returns a Promise<{ok, channel, url?}>. */
  window.HospitalForms = {
    waUrl: waUrl,
    submit: function (sub, config) {
      if (config.mode === "endpoint" && config.endpoint) return sendEndpoint(sub, config);
      if (config.mode === "email" && config.email) return sendEmail(sub, config);
      return sendWhatsApp(sub);
    },
  };
})();
