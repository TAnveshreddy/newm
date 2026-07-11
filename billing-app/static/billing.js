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
    <td><select class="prod" disabled><option value="">-- select --</option></select></td>
    <td><input class="desc" placeholder="Description"></td>
    <td><input class="qty" type="number" min="0" step="any" value="1"></td>
    <td><input class="unit" value="pcs"></td>
    <td><input class="price" type="number" min="0" step="0.01" value="0"></td>
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
  });
  prod.addEventListener("change", () => {
    const p = PRODUCTS.find(x => String(x.id) === prod.value);
    if (p) {
      tr.querySelector(".desc").value = p.description || "";
      tr.querySelector(".unit").value = p.unit || "pcs";
      tr.querySelector(".price").value = p.price;
    }
    recalc();
  });
  tr.querySelectorAll(".qty, .price").forEach(el => el.addEventListener("input", recalc));
  tr.querySelector(".del").addEventListener("click", () => { tr.remove(); recalc(); });
}

function recalc() {
  let subtotal = 0;
  document.querySelectorAll("#items tbody tr").forEach(tr => {
    const amt = (parseFloat(tr.querySelector(".qty").value) || 0) *
                (parseFloat(tr.querySelector(".price").value) || 0);
    tr.querySelector(".amount").textContent = fmt(amt);
    subtotal += amt;
  });
  const discount = parseFloat(document.getElementById("discount").value) || 0;
  document.getElementById("subtotal").textContent = fmt(subtotal);
  document.getElementById("total").textContent = fmt(subtotal - discount);
}

function collectItems() {
  const items = [];
  document.querySelectorAll("#items tbody tr").forEach(tr => {
    const prodSel = tr.querySelector(".prod");
    let name = "";
    if (prodSel.value === "__other__") {
      name = tr.querySelector(".desc").value.trim();
    } else if (prodSel.value) {
      name = prodSel.options[prodSel.selectedIndex].text;
    }
    if (!name) return;
    items.push({
      category: tr.querySelector(".cat").value || "Other",
      product_name: name,
      description: tr.querySelector(".desc").value.trim(),
      unit: tr.querySelector(".unit").value.trim() || "pcs",
      qty: tr.querySelector(".qty").value,
      price: tr.querySelector(".price").value,
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

// Autofill phone when picking a previous customer from the datalist
document.getElementById("customer_name").addEventListener("change", (e) => {
  const opt = [...document.querySelectorAll("#customer_list option")]
    .find(o => o.value === e.target.value);
  if (opt && opt.textContent.trim()) {
    document.getElementById("phone").value = opt.textContent.trim();
  }
});

addRow();
