/* Eternal Multi Specialty Hospital – site behaviour (no libraries). */
(function () {
  "use strict";

  /* ---------- mobile navigation ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("open", open);
    };
    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) { setOpen(false); toggle.focus(); }
    });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) setOpen(false); });
  }

  /* ---------- gallery lightbox ---------- */
  var lightbox = document.querySelector(".lightbox");
  var openers = Array.prototype.slice.call(document.querySelectorAll(".gallery-open"));
  if (lightbox && openers.length && typeof lightbox.showModal === "function") {
    var lbImg = lightbox.querySelector("img");
    var lbCap = lightbox.querySelector("figcaption");
    var current = 0;
    var show = function (i) {
      current = (i + openers.length) % openers.length;
      var btn = openers[current];
      lbImg.src = btn.getAttribute("data-full");
      lbImg.alt = btn.querySelector("img").alt;
      lbCap.textContent = btn.getAttribute("data-caption");
    };
    openers.forEach(function (btn, i) {
      btn.addEventListener("click", function () { show(i); lightbox.showModal(); });
    });
    lightbox.querySelector(".lb-close").addEventListener("click", function () { lightbox.close(); });
    lightbox.querySelector(".lb-prev").addEventListener("click", function () { show(current - 1); });
    lightbox.querySelector(".lb-next").addEventListener("click", function () { show(current + 1); });
    lightbox.addEventListener("click", function (e) { if (e.target === lightbox) lightbox.close(); });
    lightbox.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") show(current - 1);
      if (e.key === "ArrowRight") show(current + 1);
    });
  }

  /* ---------- forms (frontend: validation + message building) ---------- */
  var configEl = document.getElementById("form-config");
  var config = configEl ? JSON.parse(configEl.textContent) : { mode: "whatsapp" };

  function clean(value, max) {
    // strip control characters, collapse whitespace, limit length
    return String(value || "").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "").replace(/[ \t]+/g, " ").trim().slice(0, max || 500);
  }
  function todayISO() {
    var d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 10);
  }
  function formatDate(iso) {
    if (!iso) return "";
    var p = iso.split("-");
    return p.length === 3 ? p[2] + "-" + p[1] + "-" + p[0] : iso;
  }
  function setError(field, msg) {
    var wrap = field.closest(".field");
    var err = wrap.querySelector(".field-error");
    if (msg) {
      field.setAttribute("aria-invalid", "true");
      if (!err) {
        err = document.createElement("p");
        err.className = "field-error";
        err.id = field.id + "-error";
        wrap.appendChild(err);
        field.setAttribute("aria-describedby", ((field.getAttribute("aria-describedby") || "") + " " + err.id).trim());
      }
      err.textContent = msg;
    } else {
      field.removeAttribute("aria-invalid");
      if (err) err.textContent = "";
    }
  }
  function validate(form) {
    var firstBad = null;
    Array.prototype.forEach.call(form.querySelectorAll("input, select, textarea"), function (f) {
      if (f.closest(".hp")) return;
      var v = f.value.trim();
      var msg = "";
      if (f.required && !v) msg = "Please fill in this field.";
      else if (f.type === "tel" && v && !/^[6-9]\d{9}$/.test(v.replace(/\D/g, "").replace(/^91(?=\d{10}$)/, ""))) msg = "Please enter a valid 10-digit mobile number.";
      else if (f.type === "date" && v && f.min && v < f.min) msg = "Please choose today or a future date.";
      setError(f, msg);
      if (msg && !firstBad) firstBad = f;
    });
    if (firstBad) firstBad.focus();
    return !firstBad;
  }
  function selectedText(select, attr) {
    var opt = select.options[select.selectedIndex];
    return opt && opt.value ? (opt.getAttribute(attr) || opt.textContent) : "";
  }

  var params = new URLSearchParams(window.location.search);

  var ap = document.getElementById("appointment-form");
  if (ap) {
    var date = ap.querySelector("#ap-date");
    var doctor = ap.querySelector("#ap-doctor");
    var dept = ap.querySelector("#ap-dept");
    date.min = todayISO();
    // Pre-select doctor / department from links such as /appointment/?doctor=dr-m-naresh
    if (params.get("doctor")) doctor.value = params.get("doctor");
    if (params.get("department")) dept.value = params.get("department");
    var syncDept = function () {
      var opt = doctor.options[doctor.selectedIndex];
      var d = opt && opt.getAttribute("data-department");
      if (d) dept.value = d;
    };
    doctor.addEventListener("change", syncDept);
    syncDept();
  }

  Array.prototype.forEach.call(document.querySelectorAll("form[data-form]"), function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var status = form.querySelector(".form-status");
      status.className = "form-status";
      status.textContent = "";
      if (form.querySelector('[name="website"]').value) return; // honeypot: bot
      if (!validate(form)) {
        status.className = "form-status err";
        status.textContent = "Please correct the highlighted fields.";
        return;
      }
      var type = form.getAttribute("data-form");
      var sub = { formType: type, whatsapp: config.whatsapp };
      var get = function (name, max) { return clean(form.elements[name].value, max); };

      if (type === "appointment") {
        var docSel = form.elements.doctor;
        var docOpt = docSel.options[docSel.selectedIndex];
        sub.whatsapp = (docOpt && docOpt.getAttribute("data-whatsapp")) || config.whatsapp;
        sub.data = {
          patientName: get("patientName", 80),
          mobile: get("mobile", 13),
          preferredDate: get("preferredDate", 10),
          preferredTime: get("preferredTime", 30),
          doctor: selectedText(docSel, "data-name") || "Any available doctor",
          department: selectedText(form.elements.department, "data-name"),
          reason: get("reason", 500),
        };
        sub.message =
          "Hello " + config.hospitalName + ",\n" +
          "I would like to enquire about an appointment.\n\n" +
          "Patient Name: " + sub.data.patientName + "\n" +
          "Mobile Number: " + sub.data.mobile + "\n" +
          "Doctor: " + sub.data.doctor + "\n" +
          (sub.data.department ? "Department: " + sub.data.department + "\n" : "") +
          "Preferred Date: " + formatDate(sub.data.preferredDate) + "\n" +
          "Preferred Time: " + sub.data.preferredTime + "\n" +
          "Reason for Visit: " + sub.data.reason;
      } else {
        sub.data = { name: get("name", 80), mobile: get("mobile", 13), message: get("message", 800) };
        sub.message =
          "Hello " + config.hospitalName + ",\n\n" + sub.data.message + "\n\n" +
          "Name: " + sub.data.name + "\nMobile Number: " + sub.data.mobile;
      }

      var button = form.querySelector('button[type="submit"]');
      button.disabled = true;
      window.HospitalForms.submit(sub, config).then(function (result) {
        status.className = "form-status ok";
        status.textContent = result.channel === "whatsapp"
          ? "WhatsApp has opened with your details. Please press Send in WhatsApp to complete your request."
          : result.channel === "email"
            ? "Your email app has opened with your details. Please press Send."
            : "Thank you! Your request has been received. The hospital will call you to confirm.";
        if (result.channel === "endpoint") form.reset();
      }).catch(function () {
        status.className = "form-status err";
        status.textContent = "Sorry, we could not send your request. ";
        var a = document.createElement("a");
        a.href = window.HospitalForms.waUrl(sub.whatsapp, sub.message);
        a.target = "_blank";
        a.rel = "noopener";
        a.textContent = "Send it on WhatsApp instead";
        status.appendChild(a);
      }).then(function () { button.disabled = false; });
    });
  });
})();
