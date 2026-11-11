"""Kiểm tra Sổ điểm DS theo 7 câu hỏi demo (Cau_hoi_TrustMesh, phần hai) trên cluster đang chạy.

Chạy sau khi `.\\run-sodiem.ps1` đã bật 3 node (nên khởi động lại để dữ liệu sạch):
    .venv\\Scripts\\python.exe -m sodiem.check_demo
Câu 7 tự tắt node-b rồi bật lại (Windows).
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
PORTS = {"node-a": 9001, "node-b": 9002, "node-c": 9003}
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(("  ĐẠT  " if ok else "  SAI  ") + name + (f"  ({detail})" if detail else ""))


A, B, C = (f"http://localhost:{p}" for p in PORTS.values())


def login(user: str, base: str = A) -> dict:
    r = httpx.post(f"{base}/app/login", json={"user": user, "password": f"{user}123"})
    r.raise_for_status()
    return {"Authorization": "Bearer " + r.json()["token"]}


def get(path: str, h: dict, base: str = A) -> httpx.Response:
    return httpx.get(base + path, headers=h, timeout=10)


def send(method: str, path: str, h: dict, body: dict, base: str = A) -> httpx.Response:
    return httpx.request(method, base + path, headers=h, json=body, timeout=10)


def admin(root: dict) -> dict:
    return {n["node_id"]: n for n in get("/app/admin", root).json()["nodes"]}


def node_b(stop: bool) -> None:
    if stop:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | ? CommandLine -match "
                        "'sodiem.main:app --port 9002' | % { Stop-Process -Id $_.ProcessId -Force }"], check=False)
        time.sleep(1)
        return
    env = {**os.environ, "NODE_ID": "node-b", "DATA_DIR": ".data-sodiem",
           "PEERS": "node-a=http://localhost:9001,node-c=http://localhost:9003"}
    subprocess.Popen([sys.executable, "-m", "uvicorn", "sodiem.main:app", "--port", "9002"], cwd=ROOT, env=env,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    for _ in range(30):
        try:
            if httpx.get("http://localhost:9002/health", timeout=1).status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.5)


def main() -> None:
    root = login("root")

    print("Câu 1. Ba node độc lập (mỗi cổng một tiến trình)")
    ids = {httpx.get(f"http://localhost:{p}/identity").json()["fingerprint"]: n for n, p in PORTS.items()}
    check("3 node, 3 khóa ký khác nhau", len(ids) == 3, ", ".join(f"{n}={f}" for f, n in ids.items()))
    check("khóa lưu bền ở .data-sodiem", all((ROOT / ".data-sodiem" / f"{n}.pem").exists() for n in PORTS))
    check("mỗi cổng do đúng node của nó trả lời",
          all(httpx.get(f"http://localhost:{p}/health").json()["node_id"] == n for n, p in PORTS.items()))
    check("/status không mở cho client", httpx.get(f"{A}/status").status_code == 403)

    print("Câu 2. Tab node-a: Alice đọc được, Mallory bị chặn")
    alice = login("alice", A)
    r = get("/app/grades", alice, A)
    check("Alice đọc được nhờ ABAC", r.status_code == 200 and r.json()["via"] == "ABAC")
    mallory = login("mallory", A)
    for _ in range(3):
        r = get("/app/grades", mallory, A)
    check("Mallory bị MAC chặn", r.status_code == 403 and "MAC" in r.json()["detail"], r.json()["detail"])
    signed = json.loads(base64.urlsafe_b64decode(mallory["Authorization"][7:]))
    signed["payload"]["user"] = "root"
    forged = {"Authorization": "Bearer " + base64.urlsafe_b64encode(json.dumps(signed).encode()).decode()}
    check("Mallory tự khai thành admin (sửa phiên) bị từ chối", get("/app/me", forged, A).status_code == 401)
    st = admin(root)
    check("3 lần bị chặn: node-a phát AIDS, một reporter chưa thành sự cố",
          st["node-a"]["alerts"] >= 1 and not any(n["incidents"] for n in st.values()))

    print("Câu 3. Alice (node-a) → Bob (node-b) → Carol (node-c)")
    r = send("POST", "/app/shares", alice, {"to": "bob", "actions": ["read", "write"], "may_delegate": True}, A)
    check("node-a cấp Bob [read, write], được ủy tiếp", r.status_code == 200 and r.json()["node"] == "node-a")
    bob = login("bob", B)
    r = send("POST", "/app/shares", bob, {"to": "carol", "actions": ["read", "delete"]}, B)
    check("Bob cấp thêm delete bị chặn", r.status_code == 403 and "delete" in r.json()["detail"], r.json()["detail"])
    r = send("POST", "/app/shares", bob, {"to": "carol", "actions": ["read"]}, B)
    check("node-b ủy Carol chỉ [read]", r.status_code == 200 and r.json()["node"] == "node-b")
    carol = login("carol", C)
    got = get("/app/shares", carol, C).json()["received"]
    parent = get("/app/shares", bob, B).json()["received"][0]
    check("vé con: depth 1, hạn không vượt vé cha", got and got[0]["depth"] == 1 and got[0]["expires"] <= parent["expires"])
    r = get("/app/grades", carol, C).json()
    check("node-c tự kiểm vé con, Carol đọc được", r.get("via") == "capability" and r.get("node") == "node-c")
    check("Carol ghi bị chặn", send("PUT", "/app/grades/carol", carol, {"score": 10}, C).status_code == 403)

    print("Câu 4. Tab node-c: Mallory thử 3 kiểu vé")
    cap = got[0]["ticket"]
    m = login("mallory", C)
    use = lambda t: send("POST", "/app/grades/ticket", m, {"ticket": t}, C).json().get("detail", "")
    edited = {**cap, "payload": {**cap["payload"], "subject": "mallory"}}
    selfsigned = {**edited, "payload": {**edited["payload"], "node": "mallory-laptop"}}
    for name, t, want in (("vé của Carol: sai người nhận", cap, "không phải mallory"),
                          ("vé sửa: chữ ký không khớp khóa node-b", edited, "chữ ký không khớp khóa của node-b"),
                          ("vé tự ký: khóa ngoài cluster", selfsigned, "không thuộc cluster")):
        d = use(t)
        check(name, want in d, d)
    check("header nội bộ x-hop giả bị từ chối", httpx.get(f"{C}/app/grades", headers={**m, "x-hop": "1"}).status_code == 401)

    print("Câu 5. Sự cố")
    time.sleep(0.5)
    st = admin(root)
    inc = [i for n in st.values() for i in n["incidents"] if i["source"].startswith("mallory@")]
    check("AIDS của node-a (câu 2) + node-c (câu 4) thành sự cố",
          bool(inc) and inc[0]["kind"] == "AIDS" and {"node-a", "node-c"} <= set(inc[0]["reporters"]),
          ", ".join(inc[0]["reporters"]) if inc else "")

    print("Câu 6. Sửa nhật ký node-a")
    r = send("POST", "/app/admin/tamper", root, {"node": "node-a"}).json()
    check("node-a: chuỗi đứt sau khi sửa", r["verification"]["valid"] is False, f"broken_at #{r['verification']['broken_at']}")
    st = admin(root)
    check("node-b, node-c vẫn giữ nhật ký hợp lệ", st["node-b"]["audit"]["valid"] and st["node-c"]["audit"]["valid"])

    print("Câu 7. Tắt node-b")
    fp_b = httpx.get(f"{B}/identity").json()["fingerprint"]
    node_b(stop=True)
    check("quản trị thấy node-b mất", not admin(root)["node-b"]["reachable"])
    bob_c = login("bob", C)
    r = send("POST", "/app/shares", bob_c, {"to": "carol", "actions": ["read"]}, C)
    check("node-c nhận phần ủy quyền thay node-b", r.status_code == 200 and r.json()["node"] == "node-c")
    w = send("PUT", "/app/grades/erin", alice, {"score": 5.5}, A)
    check("ghi điểm vẫn được, node-b báo không phản hồi", w.status_code == 200 and w.json()["replicas"]["node-b"] != "ok")
    node_b(stop=False)
    check("node-b bật lại giữ khóa cũ", httpx.get(f"{B}/identity").json()["fingerprint"] == fp_b)
    b = get("/app/grades", alice, B).json()
    check("node-b bắt kịp điểm mới", b["grades"]["erin"] == 5.5, f"erin={b['grades']['erin']} v{b['version']}")

    bad = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} kiểm tra đạt" + ("" if not bad else ": SAI " + "; ".join(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
