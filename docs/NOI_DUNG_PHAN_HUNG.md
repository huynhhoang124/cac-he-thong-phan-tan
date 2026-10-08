# Nội dung chi tiết — Phần Vũ Văn Hùng (mở đầu, 9.4 Trust, demo, kết luận)

Tài liệu cho người trình bày, cùng khuôn với `NOI_DUNG_PHAN_HUYNH.md`. Số slide theo deck `output/slides/trustmesh-deck.html` (bấm **N** khi chiếu để xem lời nói ngay trên slide).

| Slide deck | Nội dung | Thời lượng |
|---|---|---|
| 1 | Bìa: câu hỏi trung tâm | 0:20 |
| 2 | Ví dụ xuyên suốt: bảng điểm `grades-ds-2026` | 0:40 |
| 3 | Ba lớp Trust → Authorization → Monitoring | 0:30 |
| 4 | 9.4 Trust là gì | 0:40 |
| 5 | 9.4.1 Byzantine: hành vi | 0:50 |
| 6 | 9.4.1 Giới hạn 3k + 1 | 1:00 |
| 7 | 9.4.2 Sybil | 1:10 |
| 8 | 9.4.3 Hash chain | 1:00 |
| 9 | 9.4.3 Blockchain | 0:50 |
| 26 | Demo: kiến trúc TrustMesh | 0:40 |
| 27 | Dự phòng: tắt node B | (khi demo lỗi) |
| 28 | Kết luận + hỏi đáp | 1:00 |

Tổng phần nói khoảng **8:40**, cộng phần demo Sybil, Tamper, tắt node B.

---

## Slide 4 — Trust là gì

**Ý chính:** Tin một bên là kỳ vọng nó hành xử đúng như đã hứa.

**Dễ hiểu:** Trên một máy, ta tin hệ điều hành vì nó nằm ngay đó. Trong hệ phân tán, bên kia là một máy khác, ta chỉ thấy message. Nên niềm tin phải dựa vào **bằng chứng kiểm được**: chữ ký, đa số phiếu, chuỗi hash. Không dựa vào lời tự nhận.

**Click 1:** sách chia 9.4 thành ba câu hỏi, ba slide sau đi lần lượt:
- 9.4.1 tin một **process** → Byzantine fault tolerance
- 9.4.2 tin một **identity** → Sybil attack
- 9.4.3 tin một **hệ thống** → hash chain, blockchain

**Click 2 — TrustMesh:** mỗi node có khóa Ed25519 riêng. Danh tính node = khóa công khai, công bố ở `/identity`. Node khác dùng khóa này để kiểm chữ ký cảnh báo.

---

## Slide 5 — Byzantine: node có thể nói dối

**Ý chính:** Lỗi crash thì node im lặng. Lỗi Byzantine thì node vẫn chạy nhưng làm sai, có thể cố ý.

**Hình:** client hỏi 4 bản sao A, B, C, D. D trả `x = 9`, ba node còn lại trả `x = 5` → client lấy đa số.

**Click 1 — ba kiểu hành vi:**
1. Trả lời sai (giá trị sai, dữ liệu giả).
2. Im lặng có chủ đích (không trả lời hoặc cố ý rất chậm).
3. **Nói hai lời**: gửi A một giá trị, gửi B giá trị khác. Đây là kiểu nguy hiểm nhất, vì A và B không thống nhất được nếu không trao đổi với nhau.

Crash chỉ là trường hợp riêng: im lặng mãi mãi.

**Click 2:** chống bằng cách nhân bản thành nhóm rồi lấy đa số. Câu hỏi đặt ra: nhóm phải lớn bao nhiêu?

---

## Slide 6 — Giới hạn 3k + 1

**Ý chính:** với n process, tối đa k process Byzantine, cần `k ≤ (n − 1) / 3`, tức `n ≥ 3k + 1`. Không cần biết node nào xấu, chỉ cần tin giả định "số node xấu không vượt k".

**Click 1 — trực giác (nên nói chậm):**
1. k node xấu có thể im lặng → chỉ chắc nhận được **n − k** câu trả lời.
2. Trong n − k câu đó vẫn có thể có **k câu nói dối**.
3. Phe thật phải đông hơn phe dối: **n − 2k > k** ⇒ **n ≥ 3k + 1**.

**Click 2:** n = 3 → k = 0 · n = 4 → k = 1 · n = 7 → k = 2.

**Click 3 — nói chủ động trước khi bị hỏi:** TrustMesh có 3 node nên **không chịu được node Byzantine nào**. Quorum "2 reporter" chỉ dùng để xác nhận cảnh báo, không phải Byzantine consensus. Muốn chịu 1 node Byzantine cần 4 node.

**Nên biết:**
- Một node nói dối **một mình** không tạo được incident (cần 2 reporter khác nhau). Nhưng 2 node cùng nói dối thì tạo được, vì 3 node không đủ cho k = 1.
- Byzantine consensus thật (ví dụ PBFT) cần nhiều vòng trao đổi message giữa các node. TrustMesh không làm phần này.

---

## Slide 7 — Sybil

**Ý chính:** Sybil phá giả định "một identity ứng với một thực thể". Byzantine giả định số node xấu ≤ k. Sybil làm k không còn bị chặn, vì một kẻ tự tạo bao nhiêu identity cũng được.

**Click 1 — hai mục tiêu:**
1. Chiếm đa số trong biểu quyết.
2. **Eclipse**: bao vây một node trung thực bằng toàn hàng giả để cô lập nó khỏi phần còn lại.

**Click 2 — ba cách chống:**
1. **CA tập trung**: một người, một chứng chỉ. Hiệu quả nhưng cần một trung tâm, trái với tinh thần phi tập trung.
2. **PoW / PoS**: mỗi identity tốn công tính toán hoặc tiền cược, nên tạo nhiều identity rất đắt.
3. **Reputation**: identity mới chưa có uy tín, ảnh hưởng nhỏ. Phải tích lũy theo thời gian.

**Click 3 — TrustMesh** (`/demo/sybil`, dashboard gửi `count: 10, stake_per_identity: 0`):
- Naive: nhận **10/10** identity.
- Resistant: nhận **0/10**. Luật: stake ≥ 10 **và** fingerprint thiết bị chưa dùng. Nếu đủ stake thì nhận tối đa **1**, vì cả 10 identity chung một fingerprint.
- Đọc nguyên câu `lesson` trong code: ràng buộc tài nguyên làm nhiều identity tốn kém, nhưng không loại bỏ mọi Sybil attack.

**Nên biết:** fingerprint trong demo là chuỗi cố định do server gán (`attacker-device-fingerprint`), không phải fingerprint thiết bị thật. Kẻ tấn công thật có thể giả fingerprint, nên chỉ mình fingerprint là không đủ.

---

## Slide 8 — Hash chain

**Ý chính:** Hash chain cho thấy bằng chứng bị sửa, nhưng không cho niềm tin tuyệt đối.

**Dễ hiểu:** mỗi bản ghi chứa hash của bản ghi trước. Sửa một bản ghi cũ thì hash của nó đổi, mọi mắt xích sau đều lệch.

**Click 1:** B2 bị sửa → mắt xích B2 → B3 đứt.

**Click 2 — chỗ giảng viên hay hỏi:** hash chain chỉ phát hiện sửa khi có **ai đó giữ hash mới nhất ở nơi khác**. Kẻ chiếm được cả node có thể tính lại toàn bộ chuỗi cho khớp. Vì vậy phải neo hash mới nhất ở bên khác hoặc nhân bản chuỗi. Đây là ý của blockchain ở slide sau.

**TrustMesh:** `hash = SHA-256(previous_hash + nội dung bản ghi)`. Demo `/audit/tamper-demo` sửa **bản ghi đầu tiên** → `/audit/verify` trả `valid: false, broken_at: 0`.

---

## Slide 9 — Blockchain

**Ý chính:** Blockchain = hash chain + **nhân bản** + **đồng thuận**. Muốn sửa lịch sử phải sửa đồng thời đa số bản sao. Niềm tin chuyển từ người sang hệ thống, nhưng không biến mất.

**Click 1 — bốn thứ vẫn phải tin:**
1. **Implementation**: code tính hash, kiểm chữ ký có thể có lỗi.
2. **Consensus**: giả định đa số node hoặc tài nguyên trung thực. Lại chính là giả định của 9.4.1.
3. **Smart contract**: code tự chạy, lỗi trong code là lỗi trong luật.
4. **Oracle và dịch vụ trung gian**: dữ liệu từ thế giới ngoài, ví, sàn vẫn là bên thứ ba.

**Click 2 — TrustMesh:** mỗi node giữ chuỗi audit **riêng**, chưa nhân bản, chưa đồng thuận → phát hiện được sửa, chưa chống được kẻ chiếm cả node.

---

## Slide 26–28 — Demo và kết luận

**Slide 26:** ba node, không bộ nhớ chung, chỉ nói chuyện qua HTTP. Dòng thời gian demo ghi rõ ai dẫn từng bước:
1. ABAC + delegation (Huynh)
2. Sybil (Hùng)
3. CIDS (Huynh)
4. Tamper (Hùng)
5. Tắt node B (Hùng)
6. Kết luận (Hùng)

**Lời dẫn khi tắt node B:** "Mỗi node tự quyết định quyền tại chỗ và tự giữ audit, nên node B chết chỉ là partial failure. A và C vẫn phục vụ và vẫn đủ 2 reporter để xác nhận incident."

**Slide 28:** quay lại câu hỏi ở slide 1, trả lời bằng câu "Không cơ chế nào đứng một mình", kèm ba dòng Trust, Authorization, Monitoring. Nêu giới hạn demo: dữ liệu mô phỏng, không TLS, không thay thế OAuth hay IDS production.

---

## Câu hỏi dễ gặp (phần Hùng)

| Câu hỏi | Trả lời ngắn |
|---|---|
| 3 node thì chịu được bao nhiêu node Byzantine? | 0. Cần 4 node để chịu 1. Quorum 2/3 của TrustMesh chỉ xác nhận cảnh báo. |
| Sao không dùng 2/3 làm đồng thuận luôn? | Đồng thuận Byzantine cần n ≥ 3k + 1 và nhiều vòng trao đổi. 2 trên 3 chỉ là đếm phiếu cảnh báo, một node nói hai lời vẫn phá được. |
| Resistant chặn được Sybil thật không? | Không hoàn toàn. Chỉ làm identity tốn kém (stake) và gom theo fingerprint. Kẻ có nhiều tiền hoặc giả được fingerprint vẫn vượt qua. |
| Hash chain có chống sửa không? | Chỉ **phát hiện** sửa. Kẻ chiếm cả node tính lại được chuỗi, trừ khi hash mới nhất được neo ở nơi khác. |
| Blockchain có phải "không cần tin ai"? | Không. Vẫn phải tin implementation, giả định đa số trung thực, smart contract và oracle. |
