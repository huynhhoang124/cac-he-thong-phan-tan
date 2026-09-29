const resultEl = document.getElementById("result");
const healthEl = document.getElementById("health");
const nodesEl = document.getElementById("nodes");
const metricsEl = document.getElementById("metrics");
const incidentsEl = document.getElementById("incidents");
const auditEl = document.getElementById("audit");
const auditSummaryEl = document.getElementById("audit-summary");

function text(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = value;
  return element;
}

async function jsonFetch(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
  return payload;
}

async function refreshCluster() {
  const cluster = await jsonFetch("/cluster");
  nodesEl.replaceChildren();
  const nodes = [{ url: "current", reachable: true, ...cluster.self }, ...cluster.peers];
  for (const node of nodes) {
    const card = text("div", `node ${node.reachable ? "" : "down"}`, "");
    card.append(text("strong", "", node.node_id || node.url));
    card.append(text("span", "", node.reachable ? `online · ${String(node.fingerprint || "").slice(0, 12)}` : "unreachable · partial failure"));
    nodesEl.append(card);
  }
  const online = nodes.filter((node) => node.reachable).length;
  healthEl.textContent = `${online}/${nodes.length} node online`;
  healthEl.className = `status ${online >= Math.ceil(nodes.length / 2) ? "valid" : "invalid"}`;
}

async function refreshMonitoring() {
  const data = await jsonFetch("/monitoring");
  metricsEl.replaceChildren();
  const metrics = data.metrics;
  for (const [label, value] of [["Accuracy", metrics.accuracy], ["Precision", metrics.precision], ["True positive", metrics.tp], ["False positive", metrics.fp]]) {
    const box = text("div", "metric", "");
    box.append(text("span", "", label));
    box.append(text("strong", "", value === null ? "—" : String(value)));
    metricsEl.append(box);
  }
  incidentsEl.replaceChildren();
  if (!data.incidents.length) incidentsEl.append(text("p", "", "Chưa có incident đạt quorum."));
  for (const incident of data.incidents.slice().reverse()) {
    incidentsEl.append(text("div", "incident", `${incident.kind} · ${incident.source} · ${incident.reporters.join(", ")}`));
  }
}

async function refreshAudit() {
  const data = await jsonFetch("/audit");
  const verification = data.verification;
  auditSummaryEl.textContent = verification.valid
    ? `Chuỗi hợp lệ · ${verification.records} bản ghi`
    : `Phát hiện chỉnh sửa tại bản ghi #${verification.broken_at}`;
  auditSummaryEl.className = verification.valid ? "valid" : "invalid";
  auditEl.replaceChildren();
  for (const record of data.records.slice().reverse()) {
    const row = text("div", "audit-row", "");
    row.append(text("span", "", `#${record.index}`));
    row.append(text("span", "", record.event_type));
    row.append(text("span", "", record.hash.slice(0, 24)));
    auditEl.append(row);
  }
}

async function runScenario(name) {
  const routes = {
    authorization: ["/demo/authorization", {}],
    sybil: ["/demo/sybil", { count: 10, stake_per_identity: 0 }],
    cids: ["/demo/cids", {}],
    tamper: ["/audit/tamper-demo", {}],
  };
  if (name === "refresh") {
    await refreshAll();
    return;
  }
  const [path, body] = routes[name];
  const data = await jsonFetch(path, { method: "POST", body: JSON.stringify(body) });
  resultEl.textContent = JSON.stringify(data, null, 2);
  await refreshAll();
}

async function refreshAll() {
  await Promise.all([refreshCluster(), refreshMonitoring(), refreshAudit()]);
}

for (const button of document.querySelectorAll("button[data-scenario]")) {
  button.addEventListener("click", async () => {
    const buttons = Array.from(document.querySelectorAll("button"));
    buttons.forEach((item) => { item.disabled = true; });
    try {
      await runScenario(button.dataset.scenario);
    } catch (error) {
      resultEl.textContent = `Lỗi: ${error.message}`;
    } finally {
      buttons.forEach((item) => { item.disabled = false; });
    }
  });
}

refreshAll().catch((error) => { resultEl.textContent = `Không thể tải dashboard: ${error.message}`; });
setInterval(() => refreshAll().catch(() => {}), 5000);
