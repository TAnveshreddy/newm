function fmt(n) { return "₹" + (Number(n) || 0).toFixed(2); }

function productsFor(cat) {
  return PRODUCTS.filter(p => p.category === cat);
}

function addRow() {
  const tb = document.querySelector("#items tbody");
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><select class="cat">
      <option value="">-- select --</option>
      ${CATEGORIES.map(c => `<option>${c}</option>`).join("")}
    </select></td>
    <td><select class="prod" disabled><option value="">-- select --</option></select>
        <div class="stock-hint"></div></td>
    <td><input class="desc" placeholder="Description"></td>
    <td><input class="qty" type="number" min="0" step="any" value="1"></td>
    <td><input class="unit" value="pcs"></td>
    <td><input class="price" type="number" min="0" step="0.01" value="0"></td>
    <td><input class="disc" type="number" min="0" step="0.01" value="0"></td>
    <td><select class="gst">${GST_RATES.map(r => `<option value="${r}">${r}%</option>`).join("")}</select></td>
    <td class="amount right">₹0.00</td>
    <td><button type="button" class="del" title="Remove">✕</button></td>`;
  tb.appendChild(tr);

  const cat = tr.querySelector(".cat"), prod = tr.querySelector(".prod");
  cat.addEventListener("change", () => {
    const opts = productsFor(cat.value);
    prod.disabled = false;
    prod.innerHTML = '<option value="">-- select --</option>' +
      opts.map(p => `<option value="${p.id}">${p.name}</option>`).join("") +
      '<option value="__other__">Other (type manually)</option>';
    tr.querySelector(".stock-hint").textContent = "";
  });
  prod.addEventListener("change", () => {
    const p = PRODUCTS.find(x => String(x.id) === prod.value);
    const hint = tr.querySelector(".stock-hint");
    if (p) {
      tr.querySelector(".desc").value = p.description || "";
      tr.querySelector(".unit").value = p.unit || "pcs";
      tr.querySelector(".price").value = p.price;
      tr.querySelector(".gst").value = String(p.gst_rate || 0);
      hint.textContent = `In stock: ${p.stock} ${p.unit}`;
      hint.className = "stock-hint" + (p.stock <= p.low_stock ? " low" : "");
    } else {
      hint.textContent = "";
    }
    recalc();
  });
  tr.querySelectorAll(".qty, .price, .disc, .gst").forEach(el =>
    el.addEventListener("input", recalc));
  tr.querySelector(".gst").addEventListener("change", recalc);
  tr.querySelector(".del").addEventListener("click", () => { tr.remove(); recalc(); });
}

function rowAmount(tr) {
  const qty = parseFloat(tr.querySelector(".qty").value) || 0;
  const price = parseFloat(tr.querySelector(".price").value) || 0;
  const disc = parseFloat(tr.querySelector(".disc").value) || 0;
  const gst = parseFloat(tr.querySelector(".gst").value) || 0;
  const base = qty * price - disc;
  const gstAmt = base * gst / 100;
  return { sub: qty * price, disc, gstAmt, total: base + gstAmt };
}

function recalc() {
  let sub = 0, disc = 0, gst = 0, total = 0;
  document.querySelectorAll("#items tbody tr").forEach(tr => {
    const a = rowAmount(tr);
    tr.querySelector(".amount").textContent = fmt(a.total);
    sub += a.sub; disc += a.disc; gst += a.gstAmt; total += a.total;
  });
  const extra = parseFloat(document.getElementById("discount").value) || 0;
  document.getElementById("subtotal").textContent = fmt(sub);
  document.getElementById("item_disc").textContent = fmt(disc);
  document.getElementById("gst_total").textContent = fmt(gst);
  document.getElementById("total").textContent = fmt(total - extra);
}

function collectItems() {
  const items = [];
  document.querySelectorAll("#items tbody tr").forEach(tr => {
    const prodSel = tr.querySelector(".prod");
    let name = "", productId = null;
    if (prodSel.value === "__other__") {
      name = tr.querySelector(".desc").value.trim();
    } else if (prodSel.value) {
      name = prodSel.options[prodSel.selectedIndex].text;
      productId = prodSel.value;
    }
    if (!name) return;
    items.push({
      product_id: productId,
      category: tr.querySelector(".cat").value || "Other",
      product_name: name,
      description: tr.querySelector(".desc").value.trim(),
      unit: tr.querySelector(".unit").value.trim() || "pcs",
      qty: tr.querySelector(".qty").value,
      price: tr.querySelector(".price").value,
      discount: tr.querySelector(".disc").value,
      gst_rate: tr.querySelector(".gst").value,
    });
  });
  return items;
}

async function saveBill(print) {
  const msg = document.getElementById("msg");
  msg.textContent = "";
  const payload = {
    customer_name: document.getElementById("customer_name").value.trim(),
    phone: document.getElementById("phone").value.trim(),
    address: document.getElementById("address").value.trim(),
    bill_date: document.getElementById("bill_date").value,
    payment_mode: document.getElementById("payment_mode").value,
    discount: document.getElementById("discount").value,
    items: collectItems(),
  };
  const res = await fetch("/api/bills", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) { msg.textContent = data.error || "Could not save bill"; return; }
  window.location = "/bills/" + data.bill_id + (print ? "?print=1" : "");
}

// Autofill mobile + address when an existing customer is picked
document.getElementById("customer_name").addEventListener("change", (e) => {
  const c = CUSTOMERS.find(c => c.name === e.target.value);
  if (c) {
    document.getElementById("phone").value = c.mobile || "";
    document.getElementById("address").value = c.address || "";
  }
});

addRow();
