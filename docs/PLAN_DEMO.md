# Plan demo TrustMesh — phủ toàn bộ 9.4 → 9.7

> **Cập nhật 28/10/2026:** 8 kịch bản rời được rút gọn thành một câu chuyện 4 màn "Mallory muốn sửa bảng điểm" (xem `docs/DEMO_SCRIPT.md`). Sybil, Byzantine và Firewall chỉ nói trên slide.
>
> **Cập nhật 21/10/2026:** demo đã được viết lại (v2) và đã làm đủ W1–W10. Dashboard có 8 kịch bản ứng với phím 1–8 và phím R để reset. Kịch bản chạy và lời dẫn nằm trong `docs/DEMO_SCRIPT.md`. Các bảng dưới đây giữ lại làm lịch sử phân tích.

Tài liệu này liệt kê **mọi nội dung sách từ 9.4 đến hết chương**, đối chiếu với những gì demo TrustMesh đang có (`demo/`), rồi chốt phần cần làm thêm, kịch bản chạy và câu hỏi khó.

Ký hiệu trạng thái:
- ✅ Đã có và đã lên dashboard
- 🟡 Có trong code nhưng chưa có nút demo, hoặc còn lỗ hổng cần sửa
- ❌ Chưa có
- 💬 Chỉ nói trên slide, không làm demo

Ký hiệu ưu tiên: **P0** bắt buộc trước buổi trình bày · **P1** nên làm · **P2** chỉ nói.

---

## 1. Bảng phủ nội dung

### 9.4 Trust in distributed systems (Hùng)

| Mục | Nội dung sách | TrustMesh hiện tại | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| 9.4 | Trust = bảo đảm một thực thể hành động đúng kỳ vọng | Lời nói ở slide 4 | 💬 | — |
| 9.4.1 | Process Byzantine: trả lời sai, im lặng, nói mâu thuẫn | Alert ký Ed25519, quorum 2 reporter (`monitoring.py`) | 🟡 | **W7** thêm nút "Node nói dối" (P0) |
| 9.4.1 | Chịu được k node Byzantine khi `n ≥ 3k + 1` | 3 node → k = 0. Quorum 2/3 chỉ để xác nhận cảnh báo | 💬 | Nói chủ động ở slide 4 |
| 9.4.2 | Sybil: một tác nhân tạo nhiều identity để áp đảo biểu quyết, cô lập node trung thực | `/demo/sybil`: naive 10/10, resistant 0/10 | ✅ | — |
| 9.4.2 | Chống Sybil: CA tập trung; phi tập trung thì làm identity tốn kém (PoW, PoS), reputation/accounting | Luật `unique fingerprint + stake ≥ 10` mô phỏng chi phí | ✅ | — |
| 9.4.3 | Trusting a system: blockchain, khối nối bằng hash, nhân bản sổ cái | Audit chain SHA-256 mỗi node, `/audit/verify` trả `broken_at` | ✅ | — |
| 9.4.3 | Nhân bản làm việc sửa mọi bản sao khó hơn | Mỗi node chỉ tự kiểm chuỗi của mình, không so chéo | 💬 | P2: nói "muốn phát hiện khi cả node bị chiếm thì so head hash giữa các node" |
| 9.4.3 | Vẫn phải tin implementation, consensus, smart contract, oracle | Lời nói slide 6 | 💬 | — |

### 9.5 Authorization (Huynh)

| Mục | Nội dung sách | TrustMesh hiện tại | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| 9.5.1 | Subject · object · reference monitor; complete mediation, tamperproof, fail-safe | Mỗi node chạy `PolicyEngine` riêng, dòng cuối `evaluate()` là fail-safe | ✅ | — |
| 9.5.1 | Authentication khác authorization | **Client tự khai** `role/clearance` → Mallory khai `admin` là qua | 🟡 | **W5** attribute directory phía server (P1) |
| 9.5.1 | MAC (nhãn do trung tâm đặt) | Luật `clearance < classification` là nhãn kiểu MAC | 🟡 | **W4** cho vào bảng policy matrix (P0) |
| 9.5.1 | DAC (chủ sở hữu quyết) | Luật `subject_id == owner` | 🟡 | **W4** |
| 9.5.1 | RBAC (quyền gắn vai trò) | Luật `role == admin` | 🟡 | **W4** |
| 9.5.1 | Access control matrix; ACL (theo cột) và capability (theo hàng) | Có capability, không có ACL | 💬 | ACL chỉ nói trên slide 10 |
| 9.5.1 | Capability chống giả mạo, có hạn, server tự kiểm không cần hỏi trung tâm | Capability ký Ed25519, có `expires_at` | 🟡 | **W1** trust anchor (P0, đang là lỗ hổng) · **W2** kiểm ở node khác (P0) |
| 9.5.1 | Thu hồi capability khó; dựa vào hạn ngắn | TTL 5 phút | 💬 | P2: demo vé TTL 10 giây hết hạn (tốn thời gian chờ) |
| 9.5.2 | ABAC: thuộc tính subject, object, môi trường, kết nối | `network_zone`, `hour`, department, course | ✅ | Alice allow / Mallory deny đã có |
| 9.5.3 | Delegation: quyền chỉ giữ nguyên hoặc thu hẹp | `delegate()` có đủ 3 luật nhưng **demo chưa gọi** | 🟡 | **W3** chuỗi Alice → Bob → Carol (P0) |
| 9.5.3 | OAuth 2.0: 4 vai trò, access token có scope, client không thấy mật khẩu | Không có | 💬 | Slide hình luồng OAuth |
| 9.5.4 | WAVE: attestation ký, kho chỉ ghi thêm, chứng minh quyền bằng một đường đi trong đồ thị, người cấp không cần online | `parent_hash` nối vé con về vé cha giống một cạnh attestation | 💬 | Nói khi demo W3: "chuỗi `parent_hash` này chính là một đường đi kiểu WAVE" |

### 9.6 Monitoring (Huynh)

| Mục | Nội dung sách | TrustMesh hiện tại | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| 9.6.1 | Firewall: packet filter, application gateway, proxy | Middleware application gateway: 413 khi > 64 KB, 429 khi > 80 req/10 s | 🟡 | **W6** nút "Firewall" (P1) |
| 9.6.1 | Firewall không thay authorization; hệ phân tán không có biên rõ | Rate limit đếm riêng từng node | 🟡 | **W6** cho thấy rải lên 2 node thì lọt (P1) |
| 9.6.2 | SIDS (khớp mẫu) và AIDS (bất thường) | 2 luật ngưỡng 30 giây, gần SIDS | ✅ | Nói rõ AIDS thật cần mô hình hành vi |
| 9.6.2 | NIDS và HIDS | Sensor chạy trong từng node, gần HIDS | 💬 | Slide 13 click thêm |
| 9.6.2 | TP · FP · FN · TN, accuracy, precision | Có tính đủ 4 ô, dashboard chỉ hiện ACC, PRE, TP, FP. Scenario toàn event malicious → không bao giờ có FP | 🟡 | **W8** thêm FN, TN, recall và event benign (P0) |
| 9.6.3 | CIDS: tập trung, phân tán, phân cấp; community và head | 3 node ngang hàng = phân tán | ✅ | Slide 14 vẽ 3 kiến trúc |
| 9.6.3 | Thách thức 1: sensor nói dối | Chữ ký + `/identity` + quorum | 🟡 | **W7** |
| 9.6.3 | Thách thức 2: ghép cảnh báo không có đồng hồ chung | Fingerprint theo phút, dễ lệch ở ranh giới phút | 🟡 | **W9** chống lệch phút (P1) |
| 9.6.3 | Thách thức 3: riêng tư khi chia sẻ cảnh báo | Không xử lý | 💬 | Nêu là giới hạn |
| — | Partial failure | `docker compose stop node-b`, 2/3 node vẫn phục vụ | ✅ | Mở rộng: tắt B rồi chạy W2 + CIDS |

### 9.7 Summary (Hùng)

| Nội dung | Trạng thái | Việc cần làm |
|---|---|---|
| Trust → Authorization → Monitoring phối hợp, không cơ chế nào đứng một mình | 💬 | Slide 18 |
| Giới hạn demo: dữ liệu mô phỏng, không TLS, không thay OAuth/IDS thật | 💬 | Slide 18 dòng nhỏ |

---

## 2. Danh sách việc cần làm (code)

Mọi scenario mới trả về cùng một dạng để dashboard hiển thị dễ đọc thay vì JSON thô:

```json
{"scenario": "...", "steps": [{"label": "Bob đọc ở node-b", "allowed": true, "reason": "...", "node": "node-b"}]}
```

| ID | Ưu tiên | Việc | File | Người demo | Test |
|---|---|---|---|---|---|
| **W1** | P0 | **Trust anchor cho capability.** `verify()` chỉ nhận chữ ký của khóa thuộc cluster (khóa của chính node + khóa lấy từ `/identity` của peer, cache lại). Thêm scenario Mallory tự sinh khóa, tự ký vé `write` → bị từ chối "khóa ký không thuộc cluster". | `policy.py`, `main.py` | Huynh | `test_self_signed_capability_rejected` |
| **W2** | P0 | **Kiểm vé ở node khác.** Node A cấp vé `read` cho Bob, rồi gửi vé tới `/access/check` của B và C: cả hai cho đọc, từ chối ghi, **không gọi lại A**. Phụ thuộc W1 (B phải biết khóa A). | `main.py` | Huynh | API test với 2 `CapabilityService` khác khóa |
| **W3** | P0 | **Chuỗi delegation thật.** Alice cấp Bob `[read, write]`, `may_delegate=true` → Bob ủy cho Carol `[read]` thành công (`depth=1`, hạn = min) → Bob thử ủy `[delete]` bị 403 → Carol (vé `may_delegate=false`) thử ủy tiếp bị 403. Hiện `parent_hash`. | `main.py` | Huynh | đã có `test_delegated_capability_is_attenuated`, thêm case `may_delegate=false` |
| **W4** | P0 | **Policy matrix.** Một nút chạy 6 request, mỗi request rơi vào một luật: admin → RBAC allow · registrar (owner) → DAC allow · Alice ở campus → ABAC allow · Mallory → nhãn MAC deny · Alice đọc tài nguyên `restricted` từ mạng public → môi trường deny · Bob ghi không có vé → fail-safe deny. | `main.py` | Huynh | `test_policy_matrix_hits_each_rule` |
| **W7** | P0 | **Node nói dối.** (a) Node A một mình phát cảnh báo vu cho IP vô tội `198.51.100.10` → peer ghi 1 reporter, **không** có incident. (b) Gửi tới C một cảnh báo mạo danh `node-b` ký bằng khóa lạ → C trả 400. | `main.py` | Hùng | đã có `test_detector_requires_two_reporters`, thêm API test chữ ký giả |
| **W8** | P0 | **Đủ 4 ô metrics.** Thêm `recall`; dashboard hiện TP, FP, FN, TN, accuracy, precision, recall. CIDS scenario thêm event benign: Alice đọc bình thường (→ TN) và một sinh viên gõ nhầm 3 lần (benign nhưng bị bắt → FP). | `monitoring.py`, `main.py`, `app.js` | Huynh | `test_metrics_counts_all_cells` |
| **W10** | P0 | **Dashboard:** nút cho W2, W3, W4, W6, W7; hiển thị `steps` thành bảng ✓/✗ + lý do; nút **Reset demo** (xóa audit + detector) để tập lại nhiều lần. | `index.html`, `app.js`, `styles.css`, `monitoring.py` | — | chạy tay |
| **W5** | P1 | **Attribute directory.** Mỗi node giữ bảng `subject_id → thuộc tính` (cùng image nên giống nhau). `/access/check` bỏ thuộc tính client tự khai nếu subject có trong bảng. Scenario: Mallory khai `role: admin` → bị từ chối. | `main.py` | Huynh | `test_claimed_attributes_ignored` |
| **W6** | P1 | **Firewall.** Node A bắn 90 request vào C → khoảng 80 × 200, 10 × 429; gửi payload 70 KB → 413. Sau đó rải 90 request lên B và C (45 mỗi node) → không bị chặn: rate limit phân tán cần chia sẻ bộ đếm. **Chạy sau CIDS** vì làm A bị C chặn 10 giây. | `main.py` | Huynh | — |
| **W9** | P1 | **Chống lệch ranh giới phút.** Khi nhận cảnh báo, ghép cả fingerprint của phút hiện tại và phút trước. Đồng thời là ví dụ ⓓ (không có đồng hồ chung). | `monitoring.py` | Huynh | test với 2 timestamp cách nhau qua mốc phút |
| — | P2 | Vé TTL 10 giây hết hạn · so head hash audit giữa các node · AIDS theo baseline · OAuth/WAVE thật | — | — | Chỉ nói |

Ước lượng: P0 khoảng 250–350 dòng code + test. P1 thêm khoảng 100 dòng.

---

## 3. Kịch bản demo mới (~8 phút)

Thứ tự đi theo sách (9.4 → 9.5 → 9.6), riêng Firewall đặt cuối phần Huynh vì nó làm A bị chặn 10 giây. Bấm **Reset demo** trước khi bắt đầu.

| # | Thời gian | Người | Nút / lệnh | Khán giả thấy | Mục sách |
|---|---|---|---|---|---|
| 0 | 0:30 | Hùng | Mở `localhost:8001` | 3/3 node online, mỗi node một fingerprint khóa | Kiến trúc |
| 1 | 0:45 | Hùng | **Sybil attack** | Naive 10/10, resistant 0/10 | 9.4.2 |
| 2 | 0:45 | Hùng | **Node nói dối** (W7) | Vu cáo 1 reporter → không incident; alert mạo danh → 400 | 9.4.1 |
| 3 | 0:30 | Hùng | **Tamper audit log** | "Phát hiện chỉnh sửa tại bản ghi #0" | 9.4.3 |
| 4 | 1:00 | Huynh | **Policy matrix** (W4) | 6 dòng, mỗi dòng gắn nhãn RBAC/DAC/MAC/ABAC/fail-safe | 9.5.1, 9.5.2 |
| 5 | 1:00 | Huynh | **Capability xuyên node** (W1 + W2) | Vé do A ký, B và C tự kiểm; vé Mallory tự ký bị từ chối | 9.5.1 |
| 6 | 0:45 | Huynh | **Delegation chain** (W3) | Alice → Bob → Carol thu hẹp dần; mở rộng bị 403; `parent_hash` (liên hệ WAVE) | 9.5.3, 9.5.4 |
| 7 | 1:00 | Huynh | **Collaborative IDS** (W8) | Incident có 3 reporter; đủ TP/FP/FN/TN, precision, recall | 9.6.2, 9.6.3 |
| 8 | 0:30 | Huynh | **Firewall** (W6) | 429 khi dồn vào 1 node; rải lên 2 node thì lọt | 9.6.1 |
| 9 | 1:00 | Hùng | `docker compose stop node-b` → **Capability xuyên node** + **CIDS** | B unreachable; C vẫn kiểm vé; incident vẫn đủ quorum nhờ A + C | Partial failure |
| — | — | Hùng | `docker compose start node-b` | Khôi phục | — |

Tổng khoảng 7:45. Nếu thiếu thời gian: bỏ bước 8 (Firewall), chỉ nói trên slide 12.

Slide 16 trong deck cần sửa dòng thời gian demo theo thứ tự trên.

---

## 4. Câu hỏi khó và câu trả lời chuẩn bị sẵn

| Câu hỏi | Trả lời |
|---|---|
| "3 node thì chịu được mấy node Byzantine?" | Không chịu được node nào (`n ≥ 3k+1`). Quorum 2/3 chỉ để một node không tự tạo được incident, không phải Byzantine consensus. Muốn chịu 1 node cần 4 node. |
| "Mallory tự khai `role: admin` thì sao?" | Trước W5: qua được, vì demo tin thuộc tính client gửi. Sau W5: thuộc tính lấy từ directory phía server. Hệ thật lấy từ token có chữ ký (OAuth/OpenID). |
| "Ai cũng tự ký capability được à?" | Trước W1: đúng, đó là lỗ hổng. Sau W1: chỉ nhận chữ ký của khóa thuộc cluster, đây là trust anchor, nối về 9.4. |
| "Thu hồi capability thế nào?" | Khó trong hệ phân tán vì vé đã phát ra. TrustMesh để vé sống ngắn (5 phút); cách khác là phát danh sách thu hồi tới mọi node. |
| "Rải request lên 3 node thì sao?" | Lọt 3 × 80 vì mỗi node đếm riêng. Chặn chung phải chia sẻ bộ đếm, tức lại cần trao đổi message. |
| "Đồng hồ hai node lệch thì CIDS sao?" | Fingerprint theo phút có thể khác nhau → thiếu quorum. W9 ghép thêm phút trước. Đây đúng là vấn đề không có đồng hồ chung. |
| "Node B chết thì cảnh báo của B?" | Mất (gửi một lần, timeout 1,5 giây, không gửi lại). A và C vẫn đủ 2 reporter. Mỗi node giữ danh sách incident riêng, không có đồng thuận. |
| "Accuracy 99% là tốt chứ?" | Không chắc. 10.000 request, 1 tấn công, báo nhầm 1% → ~100 cảnh báo nhầm, 1 đúng: accuracy ≈ 99% nhưng precision ≈ 1%. |

---

## 5. Checklist trước ngày trình bày

- [ ] Làm xong W1, W2, W3, W4, W7, W8, W10; `pytest` xanh.
- [ ] `docker compose up --build`, chạy đủ 9 bước 2 lần liên tiếp (có Reset giữa 2 lần).
- [ ] Chụp ảnh từng bước vào `output/demo/` làm slide dự phòng (thay slide 17).
- [ ] Sửa slide 16 theo thứ tự demo mới.
- [ ] Hai người tập riêng phần mình, rồi tập chung một lượt có bấm giờ (mục tiêu ≤ 25 phút cả bài).
- [ ] Commit `docs/`, `output/slides/`, code mới.
