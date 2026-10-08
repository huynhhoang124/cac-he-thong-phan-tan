# Kịch bản slide — Chương 9.4–9.7

Kịch bản cho bộ slide mới, viết lại từ bản v2 (`output/presentation/..._v2.pptx`), `PLAN.md`, `DEMO_SCRIPT.md`, `SPEAKER_NOTES.md` và mã `demo/`.

## Nguyên tắc chung

- **Mỗi slide một ý.** Tiêu đề slide là một câu khẳng định đầy đủ, phần dưới là hình hoặc sơ đồ chứng minh câu đó. Bản v2 dồn 3–4 khối chữ vào một slide; bản mới tách ra và để lời nói gánh phần giải thích.
- **Tối đa ~25 chữ trên một slide**, không tính nhãn trong sơ đồ.
- **Một ví dụ xuyên suốt:** tài nguyên `grades-ds-2026` (bảng điểm môn Hệ phân tán) cùng ba nhân vật Alice, Bob, Mallory và ba node A/B/C. Đây đúng là dữ liệu trong `demo_subjects_resources()`, nên lúc demo khán giả gặp lại những gì đã thấy trên slide.
- **Mã màu theo phần:** Trust = xanh dương, Authorization = xanh lá, Monitoring = cam. Nền sáng, chữ đậm, nhiều khoảng trắng (phong cách tối giản đã chọn).
- **Mỗi khái niệm lý thuyết kết thúc bằng một dòng "Trong TrustMesh"** chỉ ra chỗ đã cài đặt. Tiêu chí nghiệm thu trong PLAN yêu cầu điều này.

Thời lượng: khoảng 13 phút slide + 7 phút demo = 20 phút, còn 5 phút dự phòng cho hỏi đáp.

---

## Phần mở đầu (1:30)

### Slide 1 — Bìa · 0:20
- **Trên slide:** dòng nhỏ "Distributed Systems · Chương 9.4–9.7". Tiêu đề lớn đặt câu hỏi trung tâm: *"Các node không tin nhau. Làm sao hệ thống vẫn kiểm soát quyền và phát hiện tấn công?"* Tên nhóm ở dưới.
- **Lời nói:** đọc câu hỏi trung tâm (PLAN §3). Cả bài sẽ trả lời câu hỏi này.

### Slide 2 — Một bảng điểm, ba con người · 0:40
- **Tiêu đề:** "Suốt bài, ta theo dõi một tài nguyên: bảng điểm `grades-ds-2026`."
- **Hình:** biểu tượng tài liệu ở giữa. Ba nhân vật xung quanh, mỗi người có một nhãn thuộc tính:
  - Alice: teacher · cs · confidential
  - Bob: student · cs
  - Mallory: guest · public
- **Click:** ba node A, B, C hiện ra phía sau bảng điểm, mỗi node giữ một bản sao policy riêng.
- **Lời nói:** ai được đọc? Ai được ghi? Nếu Mallory tấn công thì ai phát hiện? Ba câu hỏi này tương ứng ba phần của bài.

### Slide 3 — Bản đồ · 0:30
- **Tiêu đề:** "Ba lớp, mỗi lớp kiểm chứng lớp trước."
- **Hình:** ba khối ngang nối bằng mũi tên: **Trust** (bằng chứng nào được chấp nhận) → **Authorization** (hành động nào được phép) → **Monitoring** (chính sách có thật sự chạy đúng). Từ Monitoring có mũi tên vòng ngược về Trust.
- **Lời nói:** dùng câu chốt slide 2 bản v2: "Trust cung cấp căn cứ. Authorization đưa ra quyết định. Monitoring kiểm tra giả định."

---

## 9.4 Trust (3:00)

### Slide 4 — Byzantine · 1:00
- **Tiêu đề:** "Không cần tin từng node, chỉ cần tin giả định về cả nhóm."
- **Hình:** công thức `k ≤ (n − 1) / 3` cỡ lớn. Dưới là một dãy n chấm, trong đó k chấm màu đỏ.
- **Click:** bảng nhỏ n = 3 → k = 0, n = 4 → k = 1, n = 7 → k = 2.
- **Lời nói:** định nghĩa trust là sự bảo đảm một thực thể hành động theo kỳ vọng (slide 3 bản v2). Process Byzantine có thể trả lời sai, im lặng hoặc nói mâu thuẫn.
- **Lưu ý (nên nói chủ động):** TrustMesh có 3 node nên theo công thức này **không** chịu được node Byzantine nào. Quorum 2/3 của TrustMesh dùng để xác nhận cảnh báo, không phải Byzantine consensus; muốn chịu 1 node Byzantine thì cần 4 node. Nói trước điều này sẽ tránh bị hỏi vặn.

### Slide 5 — Sybil · 1:00
- **Tiêu đề:** "Sybil phá giả định một identity ứng với một thực thể."
- **Hình:** một attacker ở bên trái, các mũi tên tỏa ra S1…S4, những identity này chiếm đa số trong vòng biểu quyết.
- **Click:** cột "Chống lại" gồm CA ràng buộc identity, PoW/PoS làm identity tốn kém, accounting dựa trên reputation.
- **Trong TrustMesh:** hai con số cạnh nhau, cùng một attacker (dashboard gửi `count: 10, stake_per_identity: 0`):
  - Naive: nhận **10/10** identity
  - Resistant: nhận **0/10** (luật `unique fingerprint và stake ≥ 10`; nếu stake đủ thì nhận tối đa 1, vì cả 10 identity chung một fingerprint)
- **Lời nói:** đây là mô hình minh họa, không phải giải pháp Sybil hoàn chỉnh. Dùng đúng câu `lesson` trong code.

### Slide 6 — Trusting a system · 1:00
- **Tiêu đề:** "Hash chain cho bằng chứng bị sửa, không cho niềm tin tuyệt đối."
- **Hình:** bốn khối B0 → B3, mỗi khối có `h(trước)`.
- **Click:** B2 chuyển đỏ (bị sửa), mắt xích B2 → B3 đứt, B3 hiện dấu ✗.
- **Trong TrustMesh:** mỗi audit record = SHA-256(hash trước + nội dung). `/audit/verify` trả về `broken_at`.
- **Lời nói:** vẫn phải tin implementation, consensus, smart contract và các dịch vụ trung gian.

---

## 9.5 Authorization (4:30)

### Slide 7 — Reference monitor · 0:50
- **Tiêu đề:** "Mọi request phải đi qua reference monitor."
- **Hình:** Subject → [Reference Monitor] → Object, với nhánh allow (xanh) và deny (đỏ).
- **Click:** ba thẻ: complete mediation · tamperproof · fail-safe default.
- **Trong TrustMesh:** một dòng code thật ở cuối `PolicyEngine.evaluate`:
  `return Decision(False, "Fail-safe default: không có luật cho phép phù hợp")`
- **Lời nói:** không có luật cho phép thì từ chối.

### Slide 8 — Bốn mô hình · 0:50
- **Tiêu đề:** "Bốn mô hình khác nhau ở chỗ: quyết định dựa vào cái gì."
- **Hình:** bốn cột MAC · DAC · RBAC · ABAC. Mỗi cột trả lời một câu "dựa vào…": nhãn bảo mật / chủ sở hữu / vai trò / nhiều thuộc tính.
- **Trong TrustMesh:** `PolicyEngine` dùng ba trong bốn mô hình theo thứ tự: admin → **RBAC**, owner → **DAC**, còn lại → **ABAC**. Tô sáng ba cột tương ứng.
- **Lời nói:** ABAC chi tiết hơn RBAC nhưng policy và việc quản lý thuộc tính phức tạp hơn.

### Slide 9 — ABAC trong thực tế · 1:00
- **Tiêu đề:** "Cùng một bảng điểm, hai kết quả khác nhau."
- **Hình:** hai cột đối xứng Alice | Mallory. Mỗi cột liệt kê thuộc tính, rồi một con dấu kết quả:
  - Alice: teacher · cs · confidential · campus → **ALLOW** "teacher đúng course được đọc/ghi"
  - Mallory: guest · public → **DENY** "clearance thấp hơn classification"
- **Lời nói:** chuỗi lý do lấy nguyên văn từ code, đúng như dashboard sẽ hiện lúc demo.

### Slide 10 — ACL và capability · 0:50
- **Tiêu đề:** "Cùng một ma trận quyền, cắt theo hai chiều."
- **Hình:** access matrix (hàng = subject, cột = object).
- **Click 1:** tô một cột → **ACL** (object giữ danh sách).
- **Click 2:** tô một hàng → **Capability** (subject mang token).
- **Trong TrustMesh:** thẻ capability của Bob: `subject: bob · resource: grades-ds-2026 · actions: [read] · expires_at · signature Ed25519`.
- **Lời nói:** capability hợp với hệ phân tán vì server tự kiểm chữ ký mà không cần tra danh sách trung tâm. Đổi lại phải xử lý hạn dùng và việc thu hồi.

### Slide 11 — Delegation · 1:00
- **Tiêu đề:** "Ủy quyền chỉ được giữ nguyên hoặc thu hẹp."
- **Hình:** chuỗi Alice [read, write] → Bob [read] → (C) [read], mỗi bước ngắn lại. Một mũi tên thử mở rộng sang [write] bị gạch đỏ.
- **Trong TrustMesh:** ba luật trong `delegate()`:
  - actions ⊆ actions cha
  - expires_at = min(ttl mới, hạn của cha)
  - `parent_hash` nối về capability cha
- **Lời nói:** OAuth cho ứng dụng hành động thay người dùng mà không cần mật khẩu. WAVE biểu diễn chuỗi delegation bằng đồ thị attestation.

---

## 9.6 Monitoring (3:30)

### Slide 12 — Firewall · 0:50
- **Tiêu đề:** "Firewall lọc lưu lượng, không thay được authorization."
- **Hình:** OUTSIDE | FIREWALL | INSIDE. Một gói tin xấu bị chặn ở tường.
- **Click:** Mallory dùng tài khoản hợp lệ bị đánh cắp và đi xuyên qua firewall.
- **Trong TrustMesh** (application gateway middleware): payload > 64 KB → `413` · > 80 request/10 giây → `429` · Trusted host + CORS.

### Slide 13 — SIDS và AIDS · 0:50
- **Tiêu đề:** "SIDS nhận ra mẫu đã biết, AIDS phát hiện điều bất thường."
- **Hình:** hai cột so sánh: khớp mẫu / dễ giải thích / mù với zero-day ↔ học hành vi bình thường / bắt được cái mới / nhiều cảnh báo nhầm.
- **Trong TrustMesh:** hai luật của sensor, theo cửa sổ 30 giây:
  - ≥ 3 lần bị từ chối từ cùng nguồn → `denied_access_burst`
  - ≥ 4 tên `sybil-*` khác nhau → `sybil_identity_burst`
- **Lưu ý:** cả hai đều là luật ngưỡng, gần với SIDS hơn. Nên nói rõ AIDS thật cần một mô hình hành vi.

### Slide 14 — Collaborative IDS · 1:00
- **Tiêu đề:** "Một sensor nhìn một góc; nhiều sensor ghép lại mới thấy toàn cảnh."
- **Hình:** hai community (S1–S3 → H1, S4–S6 → H2) trao đổi "signed detections".
- **Click:** chuyển sang TrustMesh: node A, B, C, mỗi node một sensor. Năm request bị từ chối từ `203.0.113.77` → cảnh báo ký Ed25519 → **incident khi có 2 reporter**.
- **Lời nói:** centralized thường chính xác hơn nhưng dễ nghẽn; distributed mở rộng tốt hơn và không có điểm lỗi đơn.

### Slide 15 — Đo chất lượng phát hiện · 0:50
- **Tiêu đề:** "Đếm số cảnh báo chưa đủ, phải đo đúng và sai."
- **Hình:** ma trận 2×2 TP · FP · FN · TN.
- **Click:** hai công thức: `ACC = (TP+TN)/tất cả` · `PRE = TP/(TP+FP)`.
- **Trong TrustMesh:** dashboard tính bốn ô này từ `ground_truth` của mỗi event.
- **Lời nói:** muốn giảm FN mà không làm người vận hành ngập trong FP.

---

## Demo (7:00 + 0:40 slide)

### Slide 16 — TrustMesh · 0:40
- **Tiêu đề:** "Ba node, không bộ nhớ chung, chỉ nói chuyện qua HTTP."
- **Hình:** ba khối node; mỗi khối có 4 dòng: ABAC + capability · khóa Ed25519 · sensor · audit chain. Mũi tên "signed alerts" nối giữa các node.
- **Dưới hình:** dòng thời gian demo 6 bước, mỗi bước gắn số mục sách:
  `ABAC + delegation (9.5)` → `Sybil (9.4.2)` → `CIDS (9.6)` → `Tamper (9.4.3)` → `Tắt node B` → `Kết luận`
- **Chuyển sang demo trực tiếp** theo `docs/DEMO_SCRIPT.md`.

### Slide 17 — Dự phòng: partial failure · (chỉ dùng khi demo lỗi)
- **Hình:** hai ảnh chụp thật trong `output/3node/`: `01-3-node-online.png` và `02-node-b-down-van-phuc-vu.png`.
- **Tiêu đề:** "Tắt node B: 2/3 node vẫn phục vụ."

---

## 9.7 Kết luận (1:00)

### Slide 18 — Kết luận · 1:00
- **Tiêu đề:** quay lại câu hỏi ở slide 1, giờ có câu trả lời: *"Không cơ chế nào đứng một mình."*
- **Hình:** ba dòng, mỗi dòng một màu phần:
  - **Trust**: nêu rõ kỳ vọng, bằng chứng và giới hạn lỗi.
  - **Authorization**: mặc định từ chối, kiểm tra mọi request, không mở rộng quyền khi ủy quyền.
  - **Monitoring**: nhiều điểm quan sát, đo cả FP lẫn FN.
- **Dòng nhỏ cuối:** giới hạn của demo (PLAN §10): dữ liệu mô phỏng, không TLS, không thay thế OAuth/IDS production.
- **Click cuối:** "Hỏi đáp".

---

## Điểm cần bạn quyết định

1. **Nhóm 2 hay 3 người?** Quyết định ai nói slide nào (PLAN §7). Kịch bản đã chia theo phần nên dễ gắn tên người.
2. **18 slide hay gọn lại 15?** Nếu cần gọn: gộp slide 2 vào 3, gộp slide 15 vào 14, bỏ slide 17 (giữ làm phụ lục).
3. **Có nói hai lưu ý ở slide 4 và 13 không?** Mình khuyên nên nói vì giảng viên dễ hỏi đúng chỗ đó.
4. **Công cụ dựng slide:** PowerPoint, Slidev hay reveal.js. Kịch bản này không phụ thuộc công cụ.
