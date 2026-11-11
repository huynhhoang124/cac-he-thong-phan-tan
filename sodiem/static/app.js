"use strict";

const $ = (id) => document.getElementById(id);
const PEOPLE = { alice: "Alice", bob: "Bob", carol: "Carol", mallory: "Mallory", root: "Quản trị" };
const ACT = { read: "Xem", write: "Sửa", delete: "Xóa" };
let me = null;
let adminTimer = null;

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function token() {
  try { return sessionStorage.getItem("sodiem-token"); } catch { return null; }
}

async function api(path, method = "GET", body) {
  const headers = { "Content-Type": "application/json" };
  if (token()) headers.Authorization = "Bearer " + token();
  const r = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  const data = await r.json().catch(() => ({}));
  if (r.status === 401 && path !== "/app/login") { logout(); throw new Error(data.detail || "Phiên đã hết hạn"); }
  if (!r.ok) {
    const d = data.detail;
    throw new Error(Array.isArray(d) ? d.map((x) => x.msg).join("; ") : d || `Lỗi ${r.status}`);
  }
  return data;
}

function notice(text, kind = "ok") {
  const n = $("notice");
  n.textContent = text;
  n.className = "notice " + kind;
  n.hidden = false;
}

const time = (s) => new Date(s * 1000).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });

/* ---------- đăng nhập ---------- */

async function onLogin(ev) {
  ev.preventDefault();
  $("lg-error").hidden = true;
  try {
    const out = await api("/app/login", "POST", { user: $("lg-user").value.trim(), password: $("lg-pass").value });
    try { sessionStorage.setItem("sodiem-token", out.token); } catch { /* tab riêng tư: phiên chỉ sống trong biến */ }
    $("lg-pass").value = "";
    start(out.profile);
  } catch (e) {
    $("lg-error").textContent = e.message;
    $("lg-error").hidden = false;
  }
}

function logout() {
  try { sessionStorage.removeItem("sodiem-token"); } catch { /* bỏ qua */ }
  me = null;
  clearInterval(adminTimer);
  $("notice").hidden = true;
  $("app-view").hidden = true;
  $("login-view").hidden = false;
  $("lg-user").focus();
}

/* ---------- bảng điểm ---------- */

async function loadGrades() {
  const body = $("grades");
  try {
    const out = await api("/app/grades");
    $("book-meta").textContent = `Phiên bản ${out.version} · xử lý bởi ${out.node}` + (out.via === "capability" ? " · bằng quyền được chia sẻ" : "");
    body.replaceChildren(...Object.entries(out.grades).map(([student, score]) => row(student, score)));
  } catch (e) {
    $("book-meta").textContent = "";
    const tr = el("tr");
    const td = el("td", "empty", e.message);
    td.colSpan = 3;
    tr.append(td);
    body.replaceChildren(tr);
  }
}

function row(student, score) {
  const tr = el("tr");
  tr.append(el("td", "", student));
  const cell = el("td");
  const act = el("td", "right");
  if (me.can_write) {
    const input = el("input");
    Object.assign(input, { type: "number", min: 0, max: 10, step: 0.5, value: score });
    input.setAttribute("aria-label", `Điểm của ${student}`);
    const save = el("button", "ghost", "Lưu");
    save.addEventListener("click", () => saveGrade(student, Number(input.value)));
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") saveGrade(student, Number(input.value)); });
    cell.append(input);
    act.append(save);
  } else {
    cell.append(el("span", "score", String(score)));
  }
  tr.append(cell, act);
  return tr;
}

async function saveGrade(student, score) {
  try {
    const out = await api(`/app/grades/${encodeURIComponent(student)}`, "PUT", { score });
    const reps = Object.entries(out.replicas).map(([n, s]) => `${n} ${s}`).join(", ");
    notice(`Đã lưu điểm ${student}: ${score}. Xử lý bởi ${out.node}, đồng bộ sang ${reps || "không có node khác"}.`);
    loadGrades();
  } catch (e) {
    notice(e.message, "err");
  }
}

/* ---------- chia sẻ ---------- */

async function loadShares() {
  try {
    const out = await api("/app/shares");
    const fill = (ul, list, who) => {
      ul.replaceChildren();
      if (!list.length) ul.append(el("li", "empty", "Chưa có"));
      for (const s of list) {
        const li = el("li");
        li.append(el("b", "", `${who(s)} · ${s.actions.map((a) => ACT[a]).join(", ")}`),
          el("span", "", `đến ${time(s.expires)}` + (s.may_delegate ? " · được chia sẻ tiếp" : "") + (s.depth ? ` · cấp ${s.depth + 1}` : "") + ` · ký bởi ${s.node}`));
        ul.append(li);
      }
    };
    fill($("received"), out.received, (s) => `Từ ${PEOPLE[s.issuer] || s.issuer}`);
    fill($("given"), out.given, (s) => `Cho ${PEOPLE[s.subject] || s.subject}`);
  } catch (e) {
    notice(e.message, "err");
  }
}

async function onShare(ev) {
  ev.preventDefault();
  const actions = [...$("share-form").querySelectorAll("fieldset input:checked")].map((x) => x.value);
  if (!actions.length) return notice("Chọn ít nhất một quyền.", "err");
  const to = $("sh-to").value;
  try {
    const out = await api("/app/shares", "POST", { to, actions, minutes: Number($("sh-min").value), may_delegate: $("sh-deleg").checked });
    notice(`Đã chia sẻ quyền ${actions.map((a) => ACT[a]).join(", ")} cho ${PEOPLE[to]}. Ký bởi ${out.node}.`);
    loadShares();
  } catch (e) {
    notice(e.message, "err");
  }
}

/* ---------- quản trị ---------- */

async function loadAdmin() {
  try {
    const out = await api("/app/admin");
    const up = out.nodes.filter((n) => n.reachable).length;
    $("admin-meta").textContent = `${up}/${out.nodes.length} node hoạt động · số liệu lấy qua ${out.node}`;
    $("nodes").replaceChildren(...out.nodes.map(nodeCard));
    const seen = new Map();
    out.nodes.filter((n) => n.reachable).forEach((n) => n.incidents.forEach((i) => {
      const k = i.kind + i.source;
      if (!seen.has(k) || seen.get(k).reporters.length < i.reporters.length) seen.set(k, i);
    }));
    const ul = $("incidents");
    ul.replaceChildren();
    if (!seen.size) ul.append(el("li", "empty", "Chưa có sự cố"));
    for (const i of seen.values()) {
      const li = el("li");
      li.append(el("b", "", `${i.kind} · ${i.source}`), el("span", "", `${i.evidence} · báo bởi ${i.reporters.join(", ")}`));
      ul.append(li);
    }
  } catch (e) {
    notice(e.message, "err");
  }
}

function nodeCard(n) {
  const card = el("article", "panel node" + (n.reachable ? "" : " down"));
  const head = el("div", "panel-head");
  head.append(el("h3", "", n.node_id), el("span", n.reachable ? "state ok" : "state off", n.reachable ? "hoạt động" : "không phản hồi"));
  card.append(head);
  if (!n.reachable) {
    card.append(el("p", "meta", "Các node còn lại vẫn phục vụ. Yêu cầu tới node này được chuyển sang node kế tiếp."));
    return card;
  }
  const a = n.audit;
  const dl = el("dl");
  const add = (k, v, cls) => { dl.append(el("dt", "", k), el("dd", cls || "", v)); };
  add("Khóa ký", n.fingerprint);
  add("Tin khóa của", n.keyring.join(", "));
  add("Nhật ký", a.valid ? `hợp lệ · ${a.length} bản ghi` : `đứt tại bản ghi #${a.broken_at}`, a.valid ? "" : "bad");
  add("Bảng điểm", `phiên bản ${n.grades_version}`);
  add("Quyền chia sẻ", String(n.tickets));
  add("Cảnh báo", `${n.alerts} nhận · ${n.incidents.length} sự cố`, n.incidents.length ? "bad" : "");
  card.append(dl);
  const tail = el("ol", "tail");
  n.audit_tail.slice().reverse().forEach((r) => {
    const who = r.data && (r.data.subject || r.data.student || r.data.reporter || r.data.source || "");
    const li = el("li", r.data && r.data.tampered ? "bad" : "", `#${r.index} ${r.event} ${who}`.trim());
    li.append(el("span", "", r.hash.slice(0, 8)));
    tail.append(li);
  });
  card.append(tail);
  const drill = el("button", "ghost danger", "Diễn tập: sửa một bản ghi");
  drill.title = "Giả sử node bị chiếm và kẻ tấn công sửa nhật ký mà không tính lại hash";
  drill.addEventListener("click", async () => {
    try {
      const out = await api("/app/admin/tamper", "POST", { node: n.node_id });
      const v = out.verification;
      notice(`${out.node}: đã sửa bản ghi #${out.index} (${out.event}). Kiểm tra lại: ` + (v.valid ? "chuỗi vẫn hợp lệ." : `chuỗi đứt tại #${v.broken_at}.`), "warn");
      loadAdmin();
    } catch (e) { notice(e.message, "err"); }
  });
  card.append(drill);
  return card;
}

/* ---------- điều hướng ---------- */

function tab(name) {
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  $("page-book").hidden = name !== "book";
  $("page-admin").hidden = name !== "admin";
  clearInterval(adminTimer);
  if (name === "admin") { loadAdmin(); adminTimer = setInterval(loadAdmin, 3000); }
}

function start(profile, home = true) {
  me = profile;
  $("login-view").hidden = true;
  $("app-view").hidden = false;
  $("notice").hidden = true;
  $("me-name").textContent = profile.name;
  $("me-title").textContent = profile.title;
  $("tab-admin").hidden = !profile.admin;
  $("share-form").hidden = !profile.can_share;
  $("share-off").hidden = profile.can_share;
  $("sh-to").replaceChildren(...Object.keys(PEOPLE).filter((u) => u !== profile.user && u !== "root").map((u) => new Option(PEOPLE[u], u)));
  if (home) tab(profile.admin ? "admin" : "book");
  loadGrades();
  loadShares();
}

async function refreshMe(home = true) {
  if (!me) return;
  try { start(await api("/app/me"), home); } catch { /* 401 đã đưa về đăng nhập */ }
}

$("login-form").addEventListener("submit", onLogin);
// Đăng nhập nhanh: vẫn gửi mật khẩu qua /app/login như người dùng gõ tay.
document.querySelectorAll("#quick button").forEach((b) => b.addEventListener("click", () => {
  $("lg-user").value = b.dataset.user;
  $("lg-pass").value = b.dataset.user + "123";
  $("login-form").requestSubmit();
}));
$("logout").addEventListener("click", logout);
$("load").addEventListener("click", () => refreshMe(false));
$("share-form").addEventListener("submit", onShare);
document.querySelectorAll("#tabs button").forEach((b) => b.addEventListener("click", () => tab(b.dataset.tab)));

if (token()) {
  me = {};
  refreshMe();
} else {
  logout();
}
