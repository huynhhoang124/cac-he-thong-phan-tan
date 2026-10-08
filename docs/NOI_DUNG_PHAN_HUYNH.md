# Nội dung chi tiết — Phần Hoàng Văn Huynh (9.5 Authorization, 9.6 Monitoring)

Tài liệu này dành cho người trình bày: giải thích từng khái niệm theo cách dễ hiểu, **nhấn vào câu "vì sao điều này khó hơn trong hệ phân tán"**, và chỉ ra TrustMesh làm gì (kể cả chỗ chưa làm). Mỗi mục ghi rõ phần nào **lên slide**, phần nào **chỉ nói**.

---

## 0. Lăng kính xuyên suốt: 5 điều khiến bảo mật phân tán khó

Đề xuất thêm **một slide mở đầu phần 9.5** (hoặc gộp vào slide 7). Sau đó mỗi slide gắn 1–2 biểu tượng của danh sách này để khán giả thấy "đây là vấn đề phân tán, không phải bảo mật máy đơn".

| Ký hiệu | Đặc trưng phân tán | Hệ quả cho bảo mật |
|---|---|---|
| ⓐ | **Không có điểm kiểm soát trung tâm** | Không có một "kernel" duy nhất quyết định; mỗi node phải tự kiểm tra |
| ⓑ | **Không có bộ nhớ chung, chỉ có message** | Quyền, cảnh báo, bằng chứng đều phải đi qua mạng → phải ký để chống giả mạo |
| ⓒ | **Lỗi cục bộ (partial failure)** | Node cấp quyền hoặc node giám sát có thể chết, phần còn lại vẫn phải chạy đúng |
| ⓓ | **Không có đồng hồ chung** | "Hết hạn lúc 10:00" và "trong cửa sổ 30 giây" phụ thuộc đồng hồ từng node |
| ⓔ | **Quy mô và nhiều tổ chức** | Không thể tra một danh sách trung tâm cho mọi request; quyền phải chuyển qua nhiều bên |

**Lời nói:** "Trên một máy, hệ điều hành là một trọng tài duy nhất thấy mọi thứ. Trong hệ phân tán không có trọng tài đó. Phần của em trả lời: khi không có trọng tài chung, ai quyết định quyền, và ai phát hiện kẻ gian?"

---

## Slide 7 — Reference monitor

**Ý chính:** Mọi request phải đi qua một bộ kiểm tra trước khi chạm vào tài nguyên.

**Dễ hiểu:** Reference monitor giống bảo vệ ở cửa phòng thi: không ai vào phòng mà không qua bảo vệ (complete mediation), không ai sửa được danh sách của bảo vệ (tamperproof), tên không có trong danh sách thì không được vào (fail-safe default).

**Vì sao khó hơn khi phân tán (ⓐ ⓒ):**
- Máy đơn có một reference monitor (kernel). Hệ phân tán có **nhiều cửa vào** — mỗi node, mỗi bản sao dữ liệu là một cửa. Complete mediation nghĩa là **cửa nào cũng phải có bảo vệ**, chỉ cần một node quên kiểm tra là thủng.
- Các bảo vệ phải dùng **cùng một danh sách** (policy). Nếu policy cập nhật ở node A mà node C chưa nhận, C trở thành lỗ hổng → bài toán **nhất quán của policy giữa các bản sao**.
- Fail-safe càng quan trọng: khi node không lấy được thông tin (mạng lỗi, timeout), phải **từ chối** chứ không được "cho qua vì không kiểm được".

**TrustMesh:** mỗi node tự chạy `PolicyEngine` riêng — ba reference monitor độc lập. Policy nằm trong code, cả ba container dùng chung image nên nhất quán *theo triển khai*; muốn đổi policy phải triển khai lại cả ba (không có cơ chế đồng bộ lúc chạy). Dòng cuối `evaluate()` là fail-safe default.

**Lên slide (thêm):** hình 3 cánh cửa A/B/C, mỗi cửa một bảo vệ, cùng cầm một bản policy. **Chỉ nói:** chuyện policy lệch phiên bản.

---

## Slide 7b (đề xuất mới) — Authentication khác Authorization

**Ý chính:** Authentication trả lời "bạn là ai", authorization trả lời "bạn được làm gì". Authorization chỉ đúng khi đầu vào của nó là thật.

**Vì sao khó hơn khi phân tán (ⓑ ⓔ):** Node nhận request chỉ thấy một message. Thuộc tính "Alice là teacher" do **ai** khẳng định? Trong hệ phân tán, thuộc tính phải đến từ một nguồn đáng tin (attribute authority, certificate, token có chữ ký) — đây là chỗ phần 9.5 nối với 9.4 Trust của Hùng.

**TrustMesh (nói thật, giảng viên dễ hỏi):** trong demo, client **tự gửi** `role`, `clearance`, `department` trong request. Nghĩa là Mallory có thể tự khai `role: admin` và được RBAC cho qua. Đây là giới hạn có chủ ý của demo (PLAN §10: danh tính là dữ liệu mô phỏng). Hệ thật sẽ lấy thuộc tính từ token đã ký (ví dụ OAuth/OpenID) thay vì tin client.

**Lên slide:** hai ô "AuthN: bạn là ai?" → "AuthZ: được làm gì?", mũi tên ghi "thuộc tính phải có người bảo lãnh (9.4)".

---

## Slide 8 — Bốn mô hình MAC · DAC · RBAC · ABAC

**Ý chính:** Bốn mô hình khác nhau ở chỗ quyết định dựa vào cái gì.

**Dễ hiểu (một ví dụ mỗi mô hình, cùng bảng điểm):**
- **MAC** — nhãn bảo mật do quản trị trung tâm đặt: bảng điểm là "confidential", chỉ ai có clearance ≥ confidential mới đọc. Người dùng không tự đổi được.
- **DAC** — chủ sở hữu tự quyết: giảng viên tạo bảng điểm thì tự chia sẻ cho trợ giảng. Linh hoạt nhưng chủ sở hữu có thể chia sẻ nhầm.
- **RBAC** — quyền gắn vào vai trò: "mọi teacher được ghi điểm". Đổi người không cần sửa quyền, chỉ đổi vai trò.
- **ABAC** — kết hợp nhiều thuộc tính: "teacher **của đúng môn**, **cùng khoa**, đang ở **mạng campus**". Chi tiết nhất nhưng policy phức tạp nhất.

**Vì sao khó hơn khi phân tán (ⓐ ⓔ):**
- MAC cần một **cơ quan trung tâm** gán nhãn — khó khi hệ trải qua nhiều tổ chức.
- RBAC cần **mọi node hiểu vai trò giống nhau** — "teacher" ở trường A có giống "teacher" ở trường B?
- ABAC cần thuộc tính đến từ **nhiều nguồn ở nhiều máy** (phòng đào tạo giữ danh sách môn, gateway biết vùng mạng). Mỗi lần quyết định có thể phải hỏi qua mạng → chậm, và nguồn thuộc tính có thể đang lỗi (ⓒ).

**TrustMesh:** `PolicyEngine` xét theo thứ tự admin → RBAC, owner → DAC, còn lại → ABAC (có thuộc tính môi trường `network_zone`: tài nguyên restricted yêu cầu campus hoặc VPN).

---

## Slide 9 — ABAC trong thực tế

Giữ nguyên. **Thêm lời nói:** "Quyết định này được tính **tại chỗ, trên node nhận request**, không cần hỏi node khác — nên node B chết thì node A vẫn quyết định được." (nối sang ⓒ và đoạn demo tắt node B).

---

## Slide 10 — ACL và capability

**Ý chính:** Cùng một ma trận quyền, cắt theo hai chiều.

**Dễ hiểu:**
- **ACL** = danh sách khách mời dán ở cửa phòng. Người giữ cửa tra danh sách.
- **Capability** = vé vào cửa người dùng cầm theo. Người giữ cửa chỉ cần kiểm vé thật hay giả.

**Vì sao đây là slide "phân tán" nhất (ⓐ ⓑ ⓒ ⓓ ⓔ):**

| | ACL | Capability |
|---|---|---|
| Ai giữ thông tin quyền | Server giữ object | Người dùng mang theo |
| Kiểm tra cần gì | Biết chắc người gửi là ai (authN) và tra danh sách | Chỉ cần khóa công khai của bên cấp để kiểm chữ ký |
| Object có nhiều bản sao | Phải đồng bộ ACL tới mọi bản sao | Không cần — vé hợp lệ ở mọi nơi |
| Bên cấp quyền đang chết | Có thể không tra được | Vẫn kiểm được (vé tự chứa bằng chứng) |
| Thu hồi quyền | Dễ: xóa khỏi danh sách | **Khó**: vé đã phát ra, phải báo cho mọi node, hoặc để vé hết hạn nhanh |
| Hạn dùng | Không cần | Phụ thuộc **đồng hồ của node kiểm tra** (ⓓ) |

**Kết luận để nói:** capability hợp với hệ phân tán vì **không cần hỏi trung tâm**, đổi lại phải trả giá ở **thu hồi** và **đồng bộ đồng hồ**. Cách phổ biến: cho vé sống ngắn (TrustMesh: Bob nhận vé 5 phút).

**TrustMesh:** capability là JSON ký Ed25519 gồm `subject`, `resource`, `actions`, `expires_at`. Node nào cũng kiểm được mà không gọi node cấp.

**Nên biết trước khi bị hỏi:** hiện `verify()` lấy khóa công khai **nằm ngay trong capability** để kiểm chữ ký, chưa so với danh sách khóa của các node đã biết. Tức là ai tự sinh khóa, tự ký một capability `write` cũng sẽ qua. Hệ đúng phải có **trust anchor**: chỉ chấp nhận chữ ký của khóa thuộc node trong cụm (cách mà `/alerts/receive` đã làm bằng `/identity`). Sửa được bằng vài dòng nếu muốn.

---

## Slide 11 — Delegation

**Ý chính:** Ủy quyền chỉ được giữ nguyên hoặc thu hẹp.

**Dễ hiểu:** Alice nhờ Bob nhập điểm hộ. Alice đưa Bob một "giấy ủy quyền" chỉ ghi quyền đọc, có hạn 5 phút. Bob không thể tự viết thêm "được ghi" vào giấy, và giấy của Bob không thể sống lâu hơn giấy gốc của Alice.

**Vì sao khó hơn khi phân tán (ⓐ ⓒ ⓔ):**
- Chuỗi ủy quyền đi qua **nhiều bên, nhiều máy, có khi nhiều tổ chức**. Người kiểm tra cuối chuỗi phải tin được cả chuỗi **mà không gọi lại từng người** (họ có thể offline).
- Không để lộ mật khẩu: bên được ủy quyền chỉ cầm token phạm vi hẹp.

**Hai ví dụ trong sách — đề xuất tách thành 2 slide hình:**

**OAuth 2.0** — 4 vai trò nằm ở **4 nơi khác nhau** (đây chính là tính phân tán):
1. *Resource owner* (Alice) — người có quyền.
2. *Client* (ứng dụng nhập điểm) — muốn hành động thay Alice.
3. *Authorization server* — nơi Alice đăng nhập và đồng ý.
4. *Resource server* — nơi giữ bảng điểm.

Luồng: client chuyển Alice sang authorization server → Alice đăng nhập, bấm đồng ý → client nhận mã, đổi lấy **access token** có scope `read` → client gọi resource server kèm token. Điểm phân tán: **resource server tự kiểm token**, client không bao giờ thấy mật khẩu của Alice.

**WAVE** — ủy quyền **không cần máy chủ trung tâm**: mỗi lần cấp quyền là một *attestation* đã ký, lưu ở kho chung chỉ ghi thêm. Muốn chứng minh có quyền thì đưa ra **một đường đi** trong đồ thị attestation từ chủ tài nguyên đến mình; quyền thu hẹp dần dọc đường. Người cấp quyền **không cần online** lúc người nhận dùng quyền (ⓒ).

**TrustMesh:** `delegate()` áp 3 luật: actions ⊆ actions cha, `expires_at = min(ttl mới, hạn cha)`, `parent_hash` nối về vé cha. Node kiểm vé cha **tại thời điểm ủy quyền**, rồi ký vé con.

---

## Slide 12 — Firewall

**Ý chính:** Firewall lọc lưu lượng ở biên, không thay được authorization.

**Dễ hiểu:** Firewall là tường rào và cổng bảo vệ của khu nhà. Ba kiểu (đề xuất thêm 1 click):
- **Packet filter** — xem địa chỉ, cổng trên phong bì, không mở thư.
- **Application gateway** — mở thư ra đọc nội dung theo giao thức (HTTP...).
- **Proxy** — đứng ra nói chuyện thay, hai bên không chạm nhau trực tiếp.

**Vì sao không đủ trong hệ phân tán (ⓐ ⓔ):**
- Hệ phân tán **không có một biên rõ ràng**: node nằm ở nhiều mạng, nhiều cloud; người dùng hợp lệ ở khắp nơi. Không có "bên trong an toàn".
- Kẻ tấn công dùng **tài khoản hợp lệ bị đánh cắp** thì lưu lượng trông bình thường → vẫn cần authorization ở từng node và IDS bên trong.

**TrustMesh:** middleware application gateway ở **mỗi node**: payload > 64 KB → 413, > 80 request/10 giây/nguồn → 429, cộng các header bảo mật.

**Nên biết trước khi bị hỏi:** bộ đếm rate limit nằm **riêng từng node**. Kẻ tấn công rải request lên cả 3 node được 3 × 80 = 240 request/10 giây. Đây đúng là bài toán **rate limiting phân tán** — muốn chặn chung thì các node phải chia sẻ bộ đếm, tức lại cần trao đổi message.

---

## Slide 13 — SIDS và AIDS

**Ý chính:** SIDS nhận ra mẫu đã biết, AIDS phát hiện điều bất thường.

**Dễ hiểu:**
- **SIDS** như danh sách ảnh truy nã: khớp mặt là bắt, không khớp thì bỏ qua. Không bắt được kẻ mới (zero-day).
- **AIDS** như bảo vệ quen mặt cư dân: thấy ai cư xử lạ thì báo. Bắt được kẻ mới nhưng hay báo nhầm.

**Thêm 1 click — đặt sensor ở đâu:** **NIDS** (nghe trên mạng) và **HIDS** (chạy trên từng máy).

**Vì sao khó hơn khi phân tán (ⓐ ⓓ):**
- "Bình thường" của hệ phân tán **khác nhau ở từng node** (node A nhận nhiều đọc, node B nhiều ghi) → mô hình hành vi phải theo từng node.
- Luật "3 lần trong 30 giây" đếm theo **đồng hồ của từng node**; một tấn công rải đều trên 3 node có thể không node nào thấy đủ ngưỡng — **mỗi node chỉ thấy một mảnh**. Đây là lý do dẫn sang slide 14.

**TrustMesh:** hai luật ngưỡng trong cửa sổ 30 giây (`denied_access_burst`, `sybil_identity_burst`), gần SIDS hơn. Nói chủ động: AIDS thật cần mô hình hành vi.

---

## Slide 14 — Collaborative IDS

**Ý chính:** Một sensor nhìn một góc; nhiều sensor ghép lại mới thấy toàn cảnh.

**Dễ hiểu:** Camera ở một cổng chỉ thấy một người lạ đi qua — chưa đáng ngại. Camera ở 2–3 cổng cùng thấy người đó thử cửa → đây là một cuộc đột nhập.

**Ba kiến trúc (lên slide, 3 hình nhỏ):**
- **Tập trung** — mọi sensor gửi về một máy phân tích. Chính xác (thấy hết) nhưng **nghẽn và là điểm lỗi đơn** (ⓒ).
- **Phân tán** — các sensor trao đổi ngang hàng. Mở rộng tốt, không điểm lỗi đơn, nhưng mỗi node chỉ có một phần thông tin.
- **Phân cấp** — sensor gom theo community, mỗi community có head; head trao đổi với nhau.

**Ba thách thức của CIDS (đề xuất 1 click — đây là chỗ móc lại phần Trust của Hùng):**
1. **Sensor nói dối** — một node bị chiếm gửi cảnh báo giả để vu cho người vô tội, hoặc im lặng để che kẻ gian → chính là lỗi Byzantine (9.4.1).
2. **Ghép cảnh báo** — hai node phải nhận ra "đây là cùng một vụ" dù không có đồng hồ chung (ⓓ).
3. **Riêng tư** — chia sẻ cảnh báo có thể lộ dữ liệu nội bộ của từng bên (ⓔ).

**TrustMesh xử lý từng thách thức thế nào:**
1. Cảnh báo **ký Ed25519**; node nhận gọi `/identity` của node gửi để lấy đúng khóa rồi mới tin. Một node báo **một mình** không tạo incident — cần **2 reporter khác nhau** (quorum). Một node nói dối không đủ để vu oan.
2. Hai cảnh báo được coi là cùng vụ nếu có cùng *fingerprint* = hash(loại, nguồn, **phút**). *Nên biết:* nếu tấn công rơi đúng ranh giới phút (node A thấy lúc 10:00:59, node B lúc 10:01:00) hoặc đồng hồ hai node lệch nhau, fingerprint khác → không đủ quorum. Ví dụ rất tốt cho ⓓ.
3. Chưa xử lý (dữ liệu demo là mô phỏng).

**Chỉ nói (partial failure):** cảnh báo gửi kiểu "bắn rồi quên", timeout 1,5 giây, không gửi lại. Node B chết thì cảnh báo của B mất, nhưng A và C vẫn đủ 2 reporter → incident vẫn được xác nhận. Mỗi node tự giữ danh sách incident của mình, **không có đồng thuận** — các node có thể tạm thời thấy khác nhau.

---

## Slide 15 — Đo chất lượng phát hiện

**Ý chính:** Đếm số cảnh báo chưa đủ, phải đo đúng và sai.

**Dễ hiểu:** bốn ô TP (bắt đúng), FP (báo nhầm), FN (bỏ sót), TN (yên đúng).

**Thêm 1 click — recall:** `REC = TP / (TP + FN)` — trong các vụ tấn công thật, bắt được bao nhiêu. Precision đo "cảnh báo có đáng tin không", recall đo "có bỏ sót không".

**Thêm 1 click — ví dụ bằng số (base-rate), rất dễ hiểu:**
> 10.000 request, chỉ 1 là tấn công. IDS bắt đúng 99% và báo nhầm 1%.
> → Báo nhầm ≈ 100 lần, báo đúng ≈ 1 lần. **Accuracy ≈ 99%** nhưng **precision ≈ 1%**: 100 cảnh báo thì 99 cái là nhầm.

Kết luận: accuracy cao không có nghĩa là cảnh báo đáng tin, vì tấn công hiếm.

**Vì sao liên quan phân tán (ⓐ ⓔ):** mỗi node tự đo trên dữ liệu nó thấy. Ghép nhiều sensor (CIDS) là cách tăng recall (thấy vụ mà một node bỏ sót) và quorum là cách tăng precision (một cảnh báo lẻ không tạo incident).

**TrustMesh:** dashboard tính TP/FP/FN/TN từ `ground_truth`, **riêng từng node**.

---

## Tóm tắt đề xuất thay đổi deck

| Loại | Slide | Nội dung |
|---|---|---|
| Mới | 7a | 5 đặc trưng phân tán (ⓐ–ⓔ), dùng làm biểu tượng cho các slide sau |
| Mới | 7b | AuthN và AuthZ, thuộc tính phải có người bảo lãnh |
| Thêm click | 7 | 3 cửa A/B/C, mỗi cửa một reference monitor |
| Thêm click | 10 | Bảng ACL và capability trong hệ phân tán (thu hồi, đồng hồ, node chết) |
| Mới | 11a, 11b | OAuth 4 vai trò + luồng; WAVE đồ thị attestation |
| Thêm click | 12 | 3 loại firewall; hệ phân tán không có biên rõ ràng |
| Thêm click | 13 | NIDS/HIDS; mỗi node chỉ thấy một mảnh |
| Thêm click | 14 | 3 kiến trúc CIDS; 3 thách thức, móc về Byzantine |
| Thêm click | 15 | Recall; ví dụ base-rate bằng số |

Thời gian phần Huynh tăng từ khoảng 8 lên khoảng 11 phút. Nếu cần giữ 8 phút: bỏ 7a (chỉ dùng biểu tượng), đưa 11b (WAVE) vào phụ lục.
