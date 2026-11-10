"use strict";

const $ = (id) => document.getElementById(id);
const SEC = { "9.4": "trust", "9.5": "auth", "9.6": "mon" };
const svg = (d) => `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="${d}"/></svg>`;
const ICON = { allow: svg("M3 8.5l3 3 7-7"), deny: svg("M4 4l8 8M12 4l-8 8"), alert: svg("M8 3v6M8 12.5v.5"),
  info: svg("M8 7v5M8 4v.5"), down: svg("M4 8h8") };
const ICON_LABEL = { allow: "cho phép", deny: "từ chối", alert: "cảnh báo", info: "thông tin", down: "node không phản hồi" };
const INTRO = "Mỗi dòng bên dưới là một yêu cầu thật gửi tới một node, kèm lý do node cho phép hay từ chối.";
const HINT = { delegation: "Mỗi vé con trỏ về hash của vé cha. Quyền và hạn của vé con chỉ được hẹp hơn.",
  chain: "Bản ghi đỏ là chỗ bị sửa. Các bản sau đó không còn kiểm được nữa.",
  summary: "Số yêu cầu theo kết quả, và các mô hình phân quyền đã quyết định.",
  empty: "Kết quả của từng màn hiện ở đây." };
const COLOR = { allow: "#3ddc84", deny: "#ff5c78", alert: "#f0c36a", info: "#949cad", down: "#5b6578" };
const SLOTS = [[50, 22], [32, 76], [68, 76], [50, 50]];
const ACTOR = [9, 50];
const EVIL = new Set(["mallory"]);
const STEP_MS = 650;

let busy = false;
let positions = {};
let selfId = null;

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

async function api(path, method = "GET") {
  const r = await fetch(path, { method, headers: { "Content-Type": "application/json" } });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
  return data;
}

const sleep = (ms) => new Promise((ok) => setTimeout(ok, ms));

/* ---------------- cluster ---------------- */

function renderCluster(c) {
  selfId = c.self;
  const stage = $("stage");
  const edges = $("edges");
  edges.replaceChildren();
  positions = {};
  c.nodes.forEach((n, i) => { positions[n.node_id] = SLOTS[i] || SLOTS[3]; });
  const ids = Object.keys(positions);
  const line = (a, b, cls) => {
    const l = document.createElementNS("http://www.w3.org/2000/svg", "line");
    l.setAttribute("x1", a[0] + "%"); l.setAttribute("y1", a[1] + "%");
    l.setAttribute("x2", b[0] + "%"); l.setAttribute("y2", b[1] + "%");
    if (cls) l.setAttribute("class", cls);
    edges.append(l);
  };
  ids.forEach((a, i) => ids.slice(i + 1).forEach((b) => line(positions[a], positions[b])));
  ids.forEach((a) => line(ACTOR, positions[a], "client"));

  stage.querySelectorAll(".node").forEach((e) => { if (!positions[e.dataset.id]) e.remove(); });
  for (const n of c.nodes) {
    let card = stage.querySelector(`.node[data-id="${n.node_id}"]`);
    if (!card) {
      card = el("div", "node");
      card.dataset.id = n.node_id;
      stage.append(card);
    }
    const [x, y] = positions[n.node_id];
    card.style.left = x + "%";
    card.style.top = y + "%";
    card.classList.toggle("down", !n.reachable);
    card.classList.toggle("self", n.node_id === c.self);
    const meta = el("div", "meta");
    if (n.reachable) {
      const a = n.audit;
      meta.append(line2("key ", n.fingerprint.slice(0, 12) + "…"));
      const chain = a.valid ? `hợp lệ · ${a.length}` : `đứt tại #${a.broken_at}`;
      const row = line2("chain ", chain);
      if (!a.valid) row.lastChild.className = "bad";
      meta.append(row, line2("incident ", String(n.incidents.length)));
    } else {
      meta.append(el("div", "", "unreachable · partial failure"));
    }
    const id = el("div", "id", n.node_id);
    if (n.node_id === c.self) id.append(el("span", "you", "đang xem"));
    card.replaceChildren(id, meta);
  }

  const up = c.nodes.filter((n) => n.reachable).length;
  const pill = $("health");
  pill.textContent = `${up}/${c.nodes.length} node online`;
  pill.className = "pill " + (up === c.nodes.length ? "ok" : "warn");

  const seen = new Map();
  c.nodes.filter((n) => n.reachable).forEach((n) => n.incidents.forEach((i) => {
    const k = i.kind + i.source;
    if (!seen.has(k) || seen.get(k).reporters.length < i.reporters.length) seen.set(k, i);
  }));
  const list = $("incidents");
  list.replaceChildren();
  if (!seen.size) list.append(el("li", "muted", "Chưa có"));
  for (const i of seen.values()) {
    const li = el("li");
    li.append(el("b", "", `${i.kind} · ${i.source}`), el("span", "", `${i.evidence} · ${i.reporters.join(", ")}`));
    list.append(li);
  }

  const me = c.nodes.find((n) => n.node_id === c.self);
  if (me && me.reachable) renderChain($("chain"), me.audit_tail, me.audit.broken_at);
  $("chain-node").textContent = c.self;
}

function line2(label, value) {
  const d = el("div", "", label);
  d.append(el("b", "", value));
  return d;
}

function renderChain(box, records, brokenAt) {
  box.replaceChildren();
  if (!records.length) { box.append(el("div", "muted", "Chưa có bản ghi")); return; }
  for (const r of records) {
    const b = el("div", "block");
    if (brokenAt !== null && brokenAt !== undefined) {
      if (r.index === brokenAt) b.classList.add("broken");
      else if (r.index > brokenAt) b.classList.add("after");
    }
    const what = r.data && r.data.subject ? `${r.event} ${r.data.subject}` : r.event;
    b.append(el("span", "", `#${r.index} ${what}`), el("span", "h", r.hash.slice(0, 8)));
    box.append(b);
  }
}

async function refresh() {
  if (busy) return;
  try { renderCluster(await api("/cluster")); } catch (e) { $("health").textContent = "Mất kết nối"; }
}

/* ---------------- animation ---------------- */

function pos(id) {
  const stage = $("stage");
  const p = positions[id] || ACTOR;
  return [(p[0] / 100) * stage.clientWidth, (p[1] / 100) * stage.clientHeight];
}

function pulse(id, color) {
  const card = document.querySelector(`.node[data-id="${id}"]`);
  if (!card) return;
  card.style.setProperty("--hc", color);
  card.classList.remove("hit");
  void card.offsetWidth;
  card.classList.add("hit");
}

async function animate(s) {
  if (!s.node || !positions[s.node]) return;
  const color = COLOR[s.status];
  const fromNode = s.from && positions[s.from] && s.from !== s.node;
  if (s.from && !positions[s.from]) {
    const actor = $("actor");
    actor.firstChild.textContent = s.from;
    actor.classList.toggle("evil", EVIL.has(s.from));
  }
  if (fromNode || (s.from && !positions[s.from])) {
    const [x1, y1] = fromNode ? pos(s.from) : pos("__actor");
    const [x2, y2] = pos(s.node);
    const dot = el("div", "packet");
    dot.style.background = color;
    $("stage").append(dot);
    await dot.animate([{ left: x1 + "px", top: y1 + "px" }, { left: x2 + "px", top: y2 + "px" }],
      { duration: 420, easing: "cubic-bezier(.5,0,.3,1)", fill: "forwards" }).finished;
    dot.remove();
  }
  pulse(s.node, color);
}

/* ---------------- màn ---------------- */

function renderStep(s) {
  const li = el("li", "step " + s.status);
  const icon = el("span", "icon");
  icon.innerHTML = ICON[s.status] || ICON.info;
  icon.title = ICON_LABEL[s.status] || "";
  li.append(icon);
  const body = el("div");
  body.append(el("div", "label", s.label));
  if (s.reason) body.append(el("div", "reason", s.reason));
  if (s.detail) body.append(el("div", "detail", s.detail));
  li.append(body);
  const chips = el("div", "chips");
  if (s.model) chips.append(el("span", "chip", s.model));
  if (s.node) chips.append(el("span", "chip node", s.node));
  li.append(chips);
  return li;
}

function renderViz(data) {
  const box = $("viz");
  box.replaceChildren();
  box.className = "viz";
  const v = data.viz;
  if (v && v.type === "delegation") {
    $("viz-title").textContent = "Chuỗi ủy quyền";
    $("viz-hint").textContent = HINT.delegation;
    v.chain.forEach((p, i) => {
      const t = el("div", "ticket");
      if (p.parent) t.dataset.parent = p.parent;
      t.style.animationDelay = i * 200 + "ms";
      t.append(el("b", "", `${p.issuer} → ${p.subject}`), el("div", "", `[${p.actions.join(", ")}] · depth ${p.depth}`),
        el("div", "", `hết hạn ${new Date(p.expires * 1000).toLocaleTimeString("vi-VN")} · may_delegate ${p.may_delegate}`));
      box.append(t);
    });
  } else if (v && v.type === "chain") {
    $("viz-title").textContent = "Chỗ chuỗi bị đứt";
    $("viz-hint").textContent = HINT.chain;
    renderChain(box, v.records, v.broken_at);
  } else {
    $("viz-title").textContent = "Tổng kết";
    $("viz-hint").textContent = HINT.summary;
    const count = (st) => data.steps.filter((s) => s.status === st).length;
    box.append(el("div", "", `${count("allow")} cho phép · ${count("deny")} từ chối · ${count("alert")} cảnh báo`));
    const models = [...new Set(data.steps.map((s) => s.model).filter(Boolean))];
    if (models.length) box.append(el("div", "vrow", "Mô hình đã dùng: " + models.join(" · ")));
  }
}

let lastAct = 0;

async function run(n) {
  if (busy) return;
  busy = true;
  lastAct = n;
  document.querySelectorAll("[data-run]").forEach((b) => {
    b.disabled = true;
    b.classList.toggle("active", Number(b.dataset.run) === n);
    b.classList.toggle("done", Number(b.dataset.run) < n);
  });
  const steps = $("steps");
  steps.replaceChildren();
  $("lesson").hidden = true;
  const why = document.querySelector(`[data-run="${n}"] .why`);
  $("scn-intro").textContent = why ? why.textContent : INTRO;
  try {
    const data = await api("/demo/act/" + n, "POST");
    const sec = $("scn-sec");
    sec.textContent = data.section;
    sec.className = "sec " + (SEC[data.section.slice(0, 3)] || "");
    $("scn-title").textContent = `Màn ${data.act} · ${data.title}`;
    for (const s of data.steps) {
      await animate(s);
      const li = renderStep(s);
      steps.append(li);
      li.scrollIntoView({ block: "nearest", behavior: "smooth" });
      await sleep(STEP_MS);
    }
    $("lesson").textContent = data.lesson;
    $("lesson").hidden = false;
    renderViz(data);
  } catch (e) {
    steps.append(renderStep({ status: "deny", label: "Lỗi khi chạy màn này", reason: e.message }));
  } finally {
    busy = false;
    document.querySelectorAll("[data-run]").forEach((b) => { b.disabled = false; });
    refresh();
  }
}

async function reset() {
  if (busy) return;
  await api("/admin/reset", "POST");
  $("steps").replaceChildren();
  $("lesson").hidden = true;
  lastAct = 0;
  $("scn-title").textContent = "Đã reset · bấm → để bắt đầu màn 1";
  $("scn-sec").textContent = "TrustMesh";
  $("scn-sec").className = "sec";
  $("viz").replaceChildren();
  $("viz-hint").textContent = HINT.empty;
  $("scn-intro").textContent = INTRO;
  $("viz-title").textContent = "Minh họa";
  document.querySelectorAll("[data-run]").forEach((b) => b.classList.remove("active", "done"));
  refresh();
}

const buttons = [...document.querySelectorAll("[data-run]")];
buttons.forEach((b) => b.addEventListener("click", () => run(Number(b.dataset.run))));
$("reset").addEventListener("click", reset);
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const i = Number(e.key);
  if (i >= 1 && i <= buttons.length) run(i);
  if ((e.key === "ArrowRight" || e.key === " ") && lastAct < buttons.length) { e.preventDefault(); run(lastAct + 1); }
  if (e.key === "r" || e.key === "R") reset();
});

refresh();
setInterval(refresh, 2500);
