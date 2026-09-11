/* Power BI AI Analyst — frontend logic (vanilla JS + Chart.js) */
(() => {
  "use strict";

  const PALETTE = ["#118dff","#01b8aa","#f2c811","#d13438","#8764b8","#00a4ef",
                   "#107c10","#ff8c00","#e3008c","#5c2d91","#00b7c3","#ca5010"];
  const state = { session: null, model: null, charts: new Map(), vseq: 0, busy: false };

  const $ = (id) => document.getElementById(id);
  const api = (path, opts = {}) => fetch(path, {
    ...opts,
    headers: { "Content-Type": "application/json",
               ...(state.session ? { "X-Session": state.session } : {}),
               ...(opts.headers || {}) },
  }).then(async (r) => ({ status: r.status, body: await r.json() }));

  // ---------- formatting ----------
  const fmt = (v, f) => {
    if (v === null || v === undefined || Number.isNaN(v)) return "—";
    if (f === "currency") return "$" + Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
    if (f === "percent")  return (Number(v) * 100).toLocaleString(undefined, { maximumFractionDigits: 1 }) + "%";
    if (f === "int")      return Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
    if (f === "number")   return Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
    return String(v);
  };
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const mdBold = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
                              .replace(/\*(.+?)\*/g, "<em>$1</em>");

  // ---------- connect ----------
  $("connect-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = $("email").value.trim();
    const btn = $("connect-btn");
    $("connect-err").textContent = "";
    btn.disabled = true; btn.textContent = "Connecting to Microsoft…";
    try {
      const { status, body } = await api("/api/connect", { method: "POST", body: JSON.stringify({ email }) });
      if (status !== 200 || !body.ok) throw new Error(body.error || "Sign-in failed.");
      state.session = body.session;
      $("user-name").textContent = body.user.name;
      $("user-avatar").textContent = (body.user.name[0] || "?").toUpperCase();
      if (body.rls) $("rls-badge").classList.remove("hidden");
      await loadModel();
      $("connect").classList.add("hidden");
      $("app").classList.remove("hidden");
      greet(body.user.name);
    } catch (err) {
      $("connect-err").textContent = err.message;
    } finally {
      btn.disabled = false; btn.textContent = "Connect to Power BI";
    }
  });

  async function loadModel() {
    const { body } = await api("/api/model");
    state.model = body;
    $("model-name").textContent = body.name || "Semantic model";
    const nMeas = body.measures.length, nRel = body.relationships.length;
    $("model-meta").textContent = `${body.tables.length} tables · ${nRel} relationships · ${nMeas} measures`;
    $("topbar-title").textContent = body.name || "Sales Analytics";
    $("engine-badge").textContent = body.llm ? "Claude AI" : "AI (rule-based)";
    if (!body.llm) $("engine-badge").classList.add("rule");
    $("sb-foot").textContent = `Data covers ${body.years[0]}–${body.years[body.years.length-1]}.`;
    // suggested prompts
    const sug = $("suggest"); sug.innerHTML = "";
    (body.suggestedPrompts || []).forEach((p) => {
      const b = document.createElement("button"); b.textContent = p;
      b.onclick = () => submit(p); sug.appendChild(b);
    });
    // chips (first 4)
    const chips = $("chips"); chips.innerHTML = "";
    (body.suggestedPrompts || []).slice(0, 4).forEach((p) => {
      const c = document.createElement("button"); c.className = "chip"; c.textContent = p;
      c.onclick = () => submit(p); chips.appendChild(c);
    });
    // tables list
    const tl = $("tables-list"); tl.innerHTML = "";
    body.tables.forEach((t) => {
      const d = document.createElement("div");
      d.innerHTML = `<div class="t">${esc(t.name)} <span style="font-weight:400;color:var(--muted)">(${t.rowCount})</span></div>`;
      tl.appendChild(d);
    });
  }

  // ---------- chat ----------
  function bubble(role, html) {
    const wrap = document.createElement("div");
    wrap.className = `msg ${role}`;
    wrap.innerHTML = `<div class="who">${role === "user" ? "You" : "AI"}</div><div class="bubble">${html}</div>`;
    $("chat-inner").appendChild(wrap);
    scroll();
    return wrap.querySelector(".bubble");
  }
  const scroll = () => { const c = $("chat"); c.scrollTop = c.scrollHeight; };

  function greet(name) {
    bubble("ai", `<p>Hi ${esc(name.split(" ")[0])} 👋 I'm your Power BI AI analyst, connected to
      <strong>${esc(state.model.name)}</strong>. Ask me for any report in plain English — I'll
      pick the fields, write the DAX, run it against the semantic model, and chart the result.</p>
      <p><em>Try:</em> “Create a dashboard showing sales, profit, quantity and YoY growth”.</p>`);
  }

  function submit(text) {
    $("input").value = text;
    autosize();
    send();
  }

  async function send() {
    if (state.busy) return;
    const input = $("input");
    const text = input.value.trim();
    if (!text) return;
    input.value = ""; autosize();
    bubble("user", `<p>${mdBold(text)}</p>`);
    state.busy = true; $("send").disabled = true;
    const thinking = bubble("ai", `<span class="typing"><i></i><i></i><i></i></span>`);
    try {
      const { status, body } = await api("/api/chat", { method: "POST", body: JSON.stringify({ message: text }) });
      thinking.closest(".msg").remove();
      if (status === 401) { bubble("ai", `<p>Your session expired. Please reload and reconnect.</p>`); return; }
      renderResponse(body);
    } catch (err) {
      thinking.closest(".msg").remove();
      bubble("ai", `<p>Sorry — I couldn't reach the reporting service. ${esc(err.message)}</p>`);
    } finally {
      state.busy = false; $("send").disabled = false; input.focus();
    }
  }

  function renderResponse(resp) {
    const b = bubble("ai", `<p>${mdBold(resp.reply || "")}</p>`);
    if (!resp.ok || !resp.visuals || !resp.visuals.length) return;

    const cards = resp.visuals.filter((v) => v.viz.chartType === "card");
    const others = resp.visuals.filter((v) => v.viz.chartType !== "card");

    // KPI cards row
    if (cards.length) {
      const row = document.createElement("div"); row.className = "kpi-row";
      cards.forEach((v) => (v.viz.cards || []).forEach((c) => row.appendChild(kpiCard(c))));
      b.appendChild(row);
    }
    // other visuals
    if (others.length) {
      const grid = document.createElement("div"); grid.className = "report-grid";
      const sizeClass = others.length >= 3 ? "half" : (others.length === 2 ? "half" : "");
      others.forEach((v) => grid.appendChild(renderVisual(v, others.length > 1 ? sizeClass : "")));
      b.appendChild(grid);
    }
    if (resp.elapsed_ms !== undefined) {
      const n = document.createElement("div"); n.className = "note";
      n.textContent = `Answered in ${resp.elapsed_ms} ms · ${resp.using_llm ? "Claude planner" : "rule-based planner"}`;
      b.appendChild(n);
    }
    scroll();
  }

  function kpiCard(c) {
    const el = document.createElement("div");
    let cls = "kpi";
    if (c.format === "percent" && typeof c.value === "number") cls += c.value >= 0 ? " pos" : " neg";
    el.className = cls;
    el.innerHTML = `<div class="k-label">${esc(c.label)}</div>
      <div class="k-value">${fmt(c.value, c.format)}</div>
      ${c.definition ? `<div class="k-def">${esc(c.definition)}</div>` : ""}`;
    return el;
  }

  // ---------- visual card ----------
  const CHART_OPTIONS = ["column","bar","line","area","pie","donut","table"];
  function renderVisual(v, sizeClass) {
    const id = `v${++state.vseq}`;
    const el = document.createElement("div");
    el.className = "visual" + (sizeClass ? " " + sizeClass : "");
    el.dataset.id = id;

    const opts = CHART_OPTIONS.map((o) =>
      `<option value="${o}" ${o === v.viz.chartType ? "selected" : ""}>${o[0].toUpperCase()+o.slice(1)}</option>`).join("");

    el.innerHTML = `
      <div class="visual-head">
        <div class="vt">${esc(v.viz.title || "")}</div>
        <div class="visual-actions">
          <select title="Change chart type">${opts}</select>
          <button data-act="dax" title="View generated DAX">DAX</button>
          <button data-act="csv" title="Export data (CSV)">⤓</button>
          <button data-act="expand" title="Expand">⤢</button>
        </div>
      </div>
      <div class="visual-body"></div>`;

    const body = el.querySelector(".visual-body");
    try { drawInto(body, v, id); }
    catch (err) { body.innerHTML = `<div class="note">Couldn't render this visual: ${esc(err.message)}</div>`; }

    // actions
    el.querySelector("select").addEventListener("change", (e) => {
      v.viz.chartType = e.target.value;
      destroyChart(id);
      body.innerHTML = ""; drawInto(body, v, id);
    });
    el.querySelector('[data-act="dax"]').onclick = () => openModal("Generated DAX",
      `<pre class="dax">${esc(v.dax || "-- no query --")}</pre>
       <p class="note">This is the query the AI would run against the Power BI semantic model.</p>`);
    el.querySelector('[data-act="csv"]').onclick = () => exportCsv(v);
    el.querySelector('[data-act="expand"]').onclick = () => {
      const holder = document.createElement("div");
      openModal(v.viz.title || "Visual", "");
      const mb = document.querySelector(".modal-body");
      mb.appendChild(holder);
      drawInto(holder, v, id + "-x", true);
    };
    return el;
  }

  function drawInto(body, v, id, big) {
    const viz = v.viz;
    if (viz.chartType === "table" || viz.chartType === "matrix") {
      body.appendChild(tableEl(viz.table));
      return;
    }
    if (viz.chartType === "error") {
      body.innerHTML = `<p class="note">${esc(viz.message)}</p>`; return;
    }
    const holder = document.createElement("div"); holder.className = "chart-holder";
    if (big) holder.style.height = "60vh";
    const canvas = document.createElement("canvas");
    holder.appendChild(canvas); body.appendChild(holder);
    if (typeof Chart === "undefined") {   // chart library unavailable -> table fallback
      holder.remove();
      body.appendChild(tableEl(viz.table));
      const n = document.createElement("div"); n.className = "note";
      n.textContent = "Charting library unavailable — showing the data as a table.";
      body.appendChild(n);
      return;
    }
    const cfg = chartConfig(viz);
    if (!cfg) { holder.remove(); body.appendChild(tableEl(viz.table)); return; }
    if (viz.explanation && !big) {
      const n = document.createElement("div"); n.className = "note"; n.textContent = viz.explanation;
      body.appendChild(n);
    }
    state.charts.set(id, new Chart(canvas.getContext("2d"), cfg));
  }

  function tableEl(table) {
    if (!table) { const d = document.createElement("div"); d.className = "note"; d.textContent = "No data."; return d; }
    const wrap = document.createElement("div"); wrap.className = "table-scroll";
    const cols = table.columns || [];
    const head = cols.map((c) => `<th class="${c.role === "measure" ? "num" : ""}">${esc(c.name)}</th>`).join("");
    const rows = (table.rows || []).map((r) =>
      "<tr>" + cols.map((c) => {
        const val = r[c.name];
        const isNum = c.role === "measure";
        return `<td class="${isNum ? "num" : ""}">${isNum ? fmt(val, c.format) : esc(val)}</td>`;
      }).join("") + "</tr>").join("");
    wrap.innerHTML = `<table class="data"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table>`;
    return wrap;
  }

  // ---------- Chart.js config ----------
  function chartConfig(viz) {
    const t = viz.chartType;
    const labels = viz.labels || [];
    const datasets = viz.datasets || [];
    if (!datasets.length && !["pie","donut"].includes(t)) return null;
    const firstFmt = (viz.measures && viz.measures[0] && viz.measures[0].format) || "number";
    const axisFmt = (val) => fmt(val, firstFmt === "percent" ? "percent" : (firstFmt === "currency" ? "currency" : "number"));

    const common = {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: datasets.length > 1 || ["pie","donut"].includes(t),
                  position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } },
        tooltip: { callbacks: { label: (ctx) => {
          const dsFmt = (datasets[ctx.datasetIndex] && datasets[ctx.datasetIndex].format) || firstFmt;
          const lbl = ctx.dataset.label ? ctx.dataset.label + ": " : "";
          return lbl + fmt(ctx.parsed.y ?? ctx.parsed ?? ctx.raw, dsFmt);
        } } },
      },
    };

    if (t === "pie" || t === "donut") {
      const ds = datasets[0] || { data: [] };
      return {
        type: "doughnut",
        data: { labels, datasets: [{ data: ds.data, backgroundColor: labels.map((_, i) => PALETTE[i % PALETTE.length]) }] },
        options: { ...common, cutout: t === "donut" ? "60%" : 0,
          plugins: { ...common.plugins, tooltip: { callbacks: { label: (ctx) =>
            `${ctx.label}: ${fmt(ctx.parsed, ds.format)}` } } } },
      };
    }

    const isHorizontal = t === "bar";
    const stacked = t === "stackedBar" || t === "stackedColumn";
    const type = (t === "line" || t === "area") ? "line" : "bar";
    const chartDatasets = datasets.map((d, i) => {
      const color = PALETTE[i % PALETTE.length];
      const base = {
        label: d.label, data: d.data, format: d.format,
        backgroundColor: (type === "line") ? (t === "area" ? color + "33" : color) : color,
        borderColor: color, borderWidth: type === "line" ? 2 : 0, borderRadius: type === "bar" ? 4 : 0,
        fill: t === "area", tension: 0.3, pointRadius: 2, pointHoverRadius: 4,
      };
      if (d.kind === "line") { base.type = "line"; base.backgroundColor = color; }
      return base;
    });

    const valScale = {
      beginAtZero: true, stacked,
      ticks: { callback: axisFmt, font: { size: 11 } }, grid: { color: "#f0eff0" },
    };
    const catScale = { stacked, ticks: { font: { size: 11 }, autoSkip: true, maxRotation: 0 }, grid: { display: false } };

    return {
      type,
      data: { labels, datasets: chartDatasets },
      options: {
        ...common,
        indexAxis: isHorizontal ? "y" : "x",
        scales: isHorizontal ? { x: valScale, y: catScale } : { x: catScale, y: valScale },
      },
    };
  }

  function destroyChart(id) {
    for (const [k, c] of state.charts) {
      if (k === id || k === id + "-x") { c.destroy(); state.charts.delete(k); }
    }
  }

  // ---------- export ----------
  function exportCsv(v) {
    const table = v.viz.table;
    let cols, rows;
    if (table && table.columns) {
      cols = table.columns.map((c) => c.name);
      rows = table.rows.map((r) => cols.map((c) => r[c]));
    } else if (v.viz.cards) {
      cols = ["Measure", "Value"]; rows = v.viz.cards.map((c) => [c.label, c.value]);
    } else { return; }
    const csv = [cols.join(","), ...rows.map((r) => r.map((x) =>
      `"${String(x ?? "").replace(/"/g, '""')}"`).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = (v.viz.title || "export").replace(/[^a-z0-9]+/gi, "_") + ".csv";
    a.click(); URL.revokeObjectURL(a.href);
  }

  // ---------- modal ----------
  function openModal(title, html) {
    const root = $("modal-root");
    root.innerHTML = `<div class="modal-backdrop"><div class="modal">
      <div class="modal-head">${esc(title)}<button class="x">×</button></div>
      <div class="modal-body">${html}</div></div></div>`;
    const close = () => (root.innerHTML = "");
    root.querySelector(".x").onclick = close;
    root.querySelector(".modal-backdrop").onclick = (e) => { if (e.target.classList.contains("modal-backdrop")) close(); };
  }

  // ---------- input ----------
  const autosize = () => { const i = $("input"); i.style.height = "auto"; i.style.height = Math.min(i.scrollHeight, 140) + "px"; };
  $("input").addEventListener("input", autosize);
  $("input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  });
  $("send").addEventListener("click", send);
  $("newchat").addEventListener("click", () => {
    for (const [, c] of state.charts) c.destroy();
    state.charts.clear();
    $("chat-inner").innerHTML = "";
    greet($("user-name").textContent || "there");
  });
})();
