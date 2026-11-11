# Câu hỏi và trả lời: TrustMesh và Sổ điểm DS

Phần A: 6 câu lý thuyết (sách Distributed Systems, mục 9.4–9.7). Phần B: 6 câu về demo Sổ điểm DS.

## Phần A. Lý thuyết

### Câu A1. Chữ ký số và lỗi Byzantine

**Hỏi:** Chữ ký số chứng minh được điều gì và không chứng minh được điều gì? Vì sao muốn chịu k node Byzantine cần n ≥ 3k + 1?

**Trả lời:**
- Chữ ký chứng minh **nguồn** (ai ký) và **toàn vẹn** (nội dung không bị sửa sau khi ký). Nó không chứng minh nội dung **đúng**: node bị chiếm vẫn ký được báo cáo sai.
- Node Byzantine có thể nói dối và nói khác nhau với từng node. Mỗi node chỉ chờ được n − k phản hồi (k node có thể im lặng). Trong số đó vẫn có thể có k kẻ nói dối, nên số trung thực n − 2k phải lớn hơn k: n > 3k, tức n ≥ 3k + 1.
- Hệ 3 node chỉ chịu được lỗi dừng, chưa chịu được 1 node Byzantine (cần 4).

### Câu A2. ACL và capability

**Hỏi:** ACL và capability khác nhau thế nào? Vì sao capability hợp với hệ phân tán, và nhược điểm của nó là gì?

**Trả lời:**
- Ma trận quyền (chủ thể × tài nguyên) lưu theo cột là **ACL**: tài nguyên giữ danh sách ai được làm gì. Lưu theo hàng là **capability**: chủ thể cầm vé ghi quyền của mình.
- Capability có chữ ký thì máy chủ nào cũng tự kiểm được, không cần tra một máy chủ quyền trung tâm. Dễ ủy quyền: cấp vé con.
- Nhược điểm: **khó thu hồi** vé đã phát (phải chờ hết hạn hoặc giữ danh sách thu hồi), và vé bị lộ có thể bị dùng lại nếu không gắn với người giữ.

### Câu A3. ABAC và Policy Machine

**Hỏi:** ABAC xét những nhóm thuộc tính nào? Trong Policy Machine, assignment, prohibition và obligation là gì?

**Trả lời:**
- ABAC xét thuộc tính của **người dùng** (vai trò, khoa, mức bảo mật), **tài nguyên** (nhãn, chủ sở hữu, môn), **môi trường** (giờ, vị trí), **kết nối** (mạng, thiết bị), và thuộc tính **quản trị** từ nguồn đáng tin.
- **Assignment:** gán người dùng hoặc đối tượng vào thuộc tính (Alice thuộc "giảng viên DS").
- **Prohibition:** điều cấm, thắng cả quyền được cấp.
- **Obligation:** hành động tự chạy khi có sự kiện. Ví dụ: sau khi đọc dữ liệu mật thì cấm ghi sang tài nguyên mức thấp hơn, để chặn rò rỉ.

### Câu A4. OAuth, WAVE và ủy quyền

**Hỏi:** Làm sao ủy quyền mà không đưa mật khẩu? OAuth và WAVE giải quyết phần nào?

**Trả lời:**
- Ủy quyền bằng **token có giới hạn** thay vì mật khẩu. Quy tắc thu hẹp: quyền con ⊆ quyền cha, hạn con ≤ hạn cha, chỉ ủy tiếp khi cha cho phép.
- **OAuth** có 4 vai trò: resource owner, client, resource server, authorization server. Người dùng chấp thuận, client nhận authorization code, đổi lấy access token, rồi dùng token gọi resource server. Client không bao giờ thấy mật khẩu.
- **WAVE** chứng minh quyền bằng **chuỗi attestation có chữ ký**. Người kiểm chỉ cần đủ chuỗi bằng chứng, bên cấp quyền **không cần online**. OAuth thì vẫn cần authorization server.

### Câu A5. Firewall, SIDS, AIDS và chỉ số đánh giá

**Hỏi:** Vì sao firewall chưa đủ? Phân biệt SIDS và AIDS. Cho 10 000 sự kiện có 10 tấn công; IDS bắt được 9, báo nhầm 90. Tính accuracy và precision.

**Trả lời:**
- Firewall lọc lưu lượng theo luật mạng. Nó không thay authorization và không thấy hành vi xấu từ tài khoản hợp lệ bị chiếm.
- **SIDS** khớp mẫu tấn công đã biết: ít báo nhầm, không bắt được tấn công mới. **AIDS** phát hiện lệch khỏi hành vi bình thường: bắt được dấu hiệu mới, nhưng dễ báo nhầm.
- TP = 9, FN = 1, FP = 90, TN = 9 900.
  - Accuracy = (TP + TN) / tổng = 9 909 / 10 000 ≈ **99,1 %**.
  - Precision = TP / (TP + FP) = 9 / 99 ≈ **9,1 %**.
- Khi tấn công hiếm, accuracy cao vẫn đi kèm precision thấp: 10 cảnh báo thì khoảng 9 là nhầm.

### Câu A6. CIDS và nguyên tắc thiết kế (9.7)

**Hỏi:** CIDS khắc phục giới hạn gì của IDS đơn lẻ? So sánh kiến trúc tập trung và phân tán. Mục 9.7 nhấn mạnh những nguyên tắc nào?

**Trả lời:**
- IDS đơn lẻ chỉ thấy lưu lượng của mình. CIDS chia sẻ và tổng hợp phát hiện từ nhiều IDS để thấy tấn công trải trên nhiều máy.
- **Tập trung:** dễ tổng hợp, nhưng nghẽn và là điểm lỗi duy nhất. **Phân tán:** dễ mở rộng, nhưng khó bảo đảm độ tin cậy của báo cáo và khó ghép báo cáo.
- Nguyên tắc 9.7: mặc định an toàn (fail-safe default), thiết kế mở, tách đặc quyền, quyền tối thiểu, giảm cơ chế dùng chung; phối hợp trust, authorization, monitoring; tính đến security và privacy ngay từ đầu.

## Phần B. Demo Sổ điểm DS

### Câu B1. Ba node có thật độc lập?

**Hỏi:** Làm sao chứng minh đây là 3 node độc lập chứ không phải 3 ô giao diện của một chương trình?

**Trả lời:**
- 3 tiến trình FastAPI ở 3 cổng 9001–9003. Mỗi node có khóa Ed25519 riêng (lưu trong `.data-sodiem\`), nhật ký, sensor, bản sao dữ liệu riêng.
- Bằng chứng: `/identity` của mỗi cổng trả fingerprint khác nhau. Tắt node-b thì 9001 và 9003 vẫn trả lời.
- Giới hạn: cùng một laptop nên không độc lập về phần cứng.

### Câu B2. Mallory tự nhận là admin

**Hỏi:** Mallory sửa phiên đăng nhập thành `root`, hoặc gửi header nội bộ `x-hop` giả. Điều gì chặn cô ta?

**Trả lời:**
- Phiên là `{user, exp, node}` có chữ ký của node cấp. Sửa `user` thì chữ ký không khớp khóa node, server trả **401**.
- Vai trò tra trong directory phía server theo user đã xác thực, không lấy từ client.
- Header `x-hop` phải có chữ ký của node trong cluster và còn hạn 30 giây. Header giả bị trả 401.
- Mallory đăng nhập đúng tài khoản của mình thì bị **MAC** chặn: nhãn public < confidential.

### Câu B3. Chuỗi ủy quyền Alice → Bob → Carol

**Hỏi:** Vì sao Bob không cấp được quyền Xóa cho Carol? Node-c kiểm những gì khi Carol đọc, và có hỏi lại node-a không?

**Trả lời:**
- Vé Bob do node-a ký: [read, write], `may_delegate = true`. Node-b từ chối vì `delete` không nằm trong vé cha (attenuation). Vé Carol: [read], hạn = min(hạn yêu cầu, hạn vé cha), `depth = 1`, `parent` là hash vé cha.
- Node-c kiểm: khóa ký thuộc cluster, chữ ký khớp, còn hạn, `subject` đúng Carol, đúng resource, có action `read`.
- Không hỏi node-a. Node-c chỉ cần khóa của node-b (đã học lần đầu qua `/identity`).
- Giới hạn: `parent` chỉ là hash tham chiếu, không kiểm đủ chuỗi như WAVE.

### Câu B4. Ba kiểu vé của Mallory

**Hỏi:** Ba lần Mallory dùng vé bị chặn bởi ba kiểm tra nào? Như vậy đã chống đánh cắp danh tính đầy đủ chưa?

**Trả lời:**
- Vé nguyên của Carol: **sai người nhận** (`subject` = carol, người đăng nhập = mallory).
- Vé sửa `subject`: **chữ ký không khớp** khóa node-b.
- Vé ghi `node = mallory-laptop`: **khóa không thuộc cluster**; app chỉ học khóa của node có trong cấu hình.
- Thứ tự kiểm: khóa → chữ ký → hạn → người nhận → resource → action.
- Chưa đầy đủ: không có TLS, không có proof of possession. Ai chiếm được phiên của Carol thì dùng được vé của Carol.

### Câu B5. Khi nào cảnh báo thành sự cố?

**Hỏi:** Vì sao một cảnh báo chưa đủ? Khi nào xuất hiện sự cố? SIDS và AIDS có cộng chung không?

**Trả lời:**
- AIDS của app: 3 lần bị từ chối cùng nguồn trong 30 giây. Node phát cảnh báo có chữ ký và gửi cho peer.
- Sự cố khi có **≥ 2 node khác nhau** báo cùng `kind` và cùng `source` trong **600 giây**. Một node báo lặp không tăng phiếu. SIDS và AIDS không cộng chung.
- Trong demo: node-a báo ở bước 2, node-c báo ở bước 4, nên thành sự cố.
- Cần 2 node vì chữ ký chỉ xác định nguồn: node bị chiếm vẫn ký được báo cáo sai.

### Câu B6. Sửa nhật ký và tắt node-b

**Hỏi:** Diễn tập sửa nhật ký cho thấy gì? Tắt node-b thì nhóm được kết luận điều gì? Vì sao node-b phải bật lại với khóa cũ?

**Trả lời:**
- Mỗi bản ghi chứa hash bản trước. Sửa `allowed: false` thành `true` mà không tính lại hash thì `verify` trả `valid = false`, `broken_at` chỉ đúng bản ghi. Node-b, node-c vẫn hợp lệ, giữ bằng chứng riêng. Giới hạn: không chống viết lại cả chuỗi.
- Tắt node-b: node-c ký vé thay, ghi điểm vẫn được; quản trị thấy 2/3 node. Kết luận: chịu được **lỗi dừng** một node, **không** chứng minh chịu lỗi Byzantine.
- Peer đã nhớ khóa cũ của node-b (TOFU). Khóa mới thì mọi chữ ký của node-b bị từ chối. Bật lại, node-b kéo trạng thái mới nhất từ peer. Bản cập nhật cũ bị phát lại thì bị bỏ qua nhờ số `version`, nên không lùi điểm được.
