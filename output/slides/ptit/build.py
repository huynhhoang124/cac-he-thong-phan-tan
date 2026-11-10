# Build trustmesh-ptit.html: 22 slides, 1440x810, PTIT frame like Nhóm1_Chương2.pdf
R, BL, TE, OR, VI, NV, GR = '#d9202a', '#2563eb', '#0f766e', '#ea580c', '#6d28d9', '#14213d', '#15803d'

CSS = """
@page{size:1440px 810px;margin:0}
*{box-sizing:border-box}
body{margin:0;background:#888;font-family:Arial,Helvetica,sans-serif;color:#0f172a}
.s{width:1440px;height:810px;position:relative;background:#f4f5fb;overflow:hidden;page-break-after:always}
.s.w{background:#fff}
.hd{position:absolute;left:0;top:0;width:1440px;height:128px}
.t{position:absolute;left:56px;top:136px;font-size:36px;font-weight:700;color:#0f172a;}
.ln{position:absolute;left:0;top:751px;width:1440px;height:2px;background:#d9202a}
.mk{position:absolute;left:6px;top:772px;font:italic 700 19px Courier New,monospace;color:#d9202a}
.nb{position:absolute;left:1294px;top:740px;width:48px;height:70px;background:#d9202a;color:#fff;font:400 20px Arial,sans-serif;text-align:center;padding-top:17px}
.c{position:absolute;background:#fff;border:1px solid #e3e7f1;border-radius:14px;padding:16px 22px}
.c h3{margin:0 0 8px;font-size:28px;line-height:1.2}
.c p{margin:0;font-size:22px;line-height:1.38;color:#334155}
.c.k{border-top:5px solid var(--a)}
.c.d{background:#14213d;border-color:#14213d;color:#fff}
.c.d p{color:#e2e8f0}
.c.d h3{color:#fcd34d}
.c.r{background:#d9202a;border-color:#d9202a;color:#fff}
.c.r p{color:#fff}
.p{display:inline-block;padding:3px 12px;border-radius:999px;font-size:17px;font-weight:700;background:var(--b);color:var(--a);margin:0 6px 4px 0}
.ar{position:absolute;font-size:40px;font-weight:700;text-align:center;line-height:1}
.lb{position:absolute;font-size:16px;font-weight:700;color:#475569;text-align:center;line-height:1.2}
.nd{position:absolute;border-radius:12px;background:#fff;border:2px solid var(--a);color:var(--a);font-weight:700;font-size:21px;text-align:center;display:flex;align-items:center;justify-content:center;flex-direction:column;line-height:1.2}
.nd small{font-weight:400;font-size:16px;color:#475569}
.cir{position:absolute;width:44px;height:44px;border-radius:50%;background:var(--a);color:#fff;font-weight:700;font-size:22px;display:flex;align-items:center;justify-content:center}
.mono{font-family:Courier New,monospace}
.hl{height:8px;border-radius:4px;background:var(--a)}
"""


def S(n, title, body, cls=''):
    hd = 'header_cover.png' if cls == 'w' else 'header.png'
    return (f'<section class="s {cls}"><img class="hd" src="{hd}">'
            f'<div class="t">{title}</div>{body}'
            f'<div class="ln"></div><div class="mk">#MakeInPTIT</div><div class="nb">{n}</div></section>')


def B(x, y, w, h, inner, cls='c', a=None, b=None, extra=''):
    v = ''
    if a: v += f'--a:{a};'
    if b: v += f'--b:{b};'
    return f'<div class="{cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{v}{extra}">{inner}</div>'


def K(x, y, w, h, title, text, a, pills=''):  # card with colored top border
    return B(x, y, w, h, f'<h3 style="color:{a}">{title}</h3><p>{text}</p>{pills}', 'c k', a)


def D(x, y, w, h, title, text):  # dark card
    return B(x, y, w, h, f'<h3>{title}</h3><p>{text}</p>', 'c d')


def P(txt, a, b):
    return f'<span class="p" style="--a:{a};--b:{b}">{txt}</span>'


def AR(x, y, w=60, c=BL, t='→'):
    return f'<div class="ar" style="left:{x}px;top:{y}px;width:{w}px;color:{c}">{t}</div>'


def LB(x, y, w, txt):
    return f'<div class="lb" style="left:{x}px;top:{y}px;width:{w}px">{txt}</div>'


def ND(x, y, w, h, txt, a, sub='', bg='#fff', fg=None):
    st = f'background:{bg};' + (f'color:{fg};' if fg else '')
    return (f'<div class="nd" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;--a:{a};{st}">'
            f'<span>{txt}</span>' + (f'<small style="{"color:#e2e8f0" if fg else ""}">{sub}</small>' if sub else '') + '</div>')


def CIR(x, y, n, a):
    return f'<div class="cir" style="left:{x}px;top:{y}px;--a:{a}">{n}</div>'


TINT = {R: '#fde8e9', BL: '#e6efff', TE: '#e0f5f1', OR: '#ffeede', VI: '#efe7fd', GR: '#e3f5e8'}
slides = []

# 1 cover
slides.append(
    '<section class="s w"><img class="hd" src="header_cover.png">'
    '<div style="position:absolute;left:0;top:215px;width:1440px;text-align:center">'
    f'<div style="font-size:58px;font-weight:700;color:{R}">TrustMesh</div>'
    f'<div style="font-size:34px;font-weight:700;color:{R};margin-top:14px">Trust, Authorization và Monitoring trong hệ phân tán</div>'
    f'<div style="font-size:26px;font-weight:700;color:{R};margin-top:10px">Chương 9.4–9.7</div></div>'
    f'<div style="position:absolute;left:0;top:570px;width:1440px;height:240px;background:{R}"></div>'
    '<div style="position:absolute;right:70px;top:650px;text-align:right;font:italic 700 24px/1.6 Courier New,monospace;color:#fff">'
    'Vũ Văn Hùng<br>Hoàng Văn Huynh - B23DCCC086</div></section>')

# 2 agenda
b = ''
items = [(R, '9.4', 'Trust', 'Byzantine, 3k+1, Sybil, hash chain và blockchain.', 'Vũ Văn Hùng'),
         (BL, '9.5', 'Authorization', 'Mô hình, MAC/DAC/RBAC/ABAC, ACL, capability, delegation.', 'Hoàng Văn Huynh'),
         (TE, '9.6–9.7', 'Giám sát', 'Firewall, SIDS/AIDS, CIDS, metrics, demo và kết luận.', 'Huynh · Hùng')]
for i, (a, num, ti, tx, who) in enumerate(items):
    x = 56 + i * 452
    b += K(x, 215, 424, 250, f'{ti}', tx, a, '<div style="margin-top:14px">' + P(num, a, TINT[a]) + P(who, '#475569', '#eef1f7') + '</div>')
b += D(56, 495, 1328, 215, 'Câu hỏi xuyên suốt',
       '<span style="font-size:24px">Khi các node không hoàn toàn tin nhau, hệ thống dựa vào cơ chế nào để cấp quyền và nhận ra tấn công?</span>'
       '<div style="margin-top:22px;font-size:20px;color:#fcd34d;font-weight:700">Trust  →  Authorization  →  Monitoring</div>')
slides.append(S(2, 'Nội dung trình bày', b))

# 3 running example
b = B(56, 205, 1328, 250, '', 'c')
for i, nm in enumerate(['node-a', 'node-b', 'node-c']):
    x = 190 + i * 400
    b += ND(x, 235, 220, 80, nm, BL, 'Ed25519 · audit · IDS')
    b += f'<div class="mono" style="position:absolute;left:{x}px;top:325px;width:220px;text-align:center;font-size:16px;color:#475569">grades-ds</div>'
    if i < 2: b += AR(x + 225, 245, 170, BL, '↔')
for i, (nm, tx, a) in enumerate([('Alice', 'đọc hợp lệ', GR), ('Bob', 'được ủy quyền', BL), ('Carol', 'nhận quyền ủy', TE), ('Mallory', 'kẻ tấn công', R)]):
    b += f'<div style="position:absolute;left:{110 + i * 300}px;top:385px">' + P(f'{nm}: {tx}', a, TINT[a]) + '</div>'
for i, (ti, tx, a) in enumerate([('Trust', 'Vé và cảnh báo có chữ ký; khóa của peer được ghim.', R),
                                 ('Authorization', 'MAC và ABAC, vé do node ký, mặc định từ chối.', BL),
                                 ('Monitoring', 'Audit hash chain, AIDS/SIDS ở từng node, quorum hai reporter.', TE)]):
    b += K(56 + i * 452, 490, 424, 215, ti, tx, a)
slides.append(S(3, 'Ví dụ xuyên suốt: Mallory muốn sửa bảng điểm', b))

# 4 trust
b = ND(56, 215, 380, 120, 'Node · đường truyền · phần mềm', R, 'đều có thể sai hoặc bị chiếm')
b += AR(446, 240, 60, BL) + ND(516, 215, 408, 120, 'Bằng chứng', BL, 'chữ ký số, hash, khóa công khai đã biết trước') + AR(934, 240, 60, BL)
b += ND(1004, 215, 380, 120, 'Chấp nhận / từ chối', TE, 'tin cả nhóm, không tin từng node')
for i, (ti, tx, a, tg) in enumerate([('Node nói dối', 'Gửi giá trị mâu thuẫn cho từng peer.', R, '9.4.1'),
                                     ('Nhiều node giả', 'Một kẻ tạo nhiều danh tính để chiếm đa số.', OR, '9.4.2'),
                                     ('Sửa log', 'Xóa hoặc đổi bản ghi cũ để che dấu vết.', VI, '9.4.3')]):
    b += K(56 + i * 452, 365, 424, 190, ti, tx, a, '<div style="margin-top:10px">' + P(tg, a, TINT[a]) + '</div>')
b += D(56, 585, 1328, 125, 'TrustMesh', 'Mỗi node ghim khóa Ed25519 của peer, tự kiểm chữ ký trên vé và cảnh báo, không hỏi lại node đã ký.')
slides.append(S(4, '9.4 Trust: chọn bằng chứng nào được chấp nhận', b))

# 5 byzantine
b = B(56, 205, 660, 330, '', 'c')
b += ND(90, 330, 170, 80, 'Node xấu', R, 'Byzantine', '#fde8e9')
b += AR(262, 295, 90, R, '↗') + AR(262, 370, 90, R, '↘')
b += ND(360, 250, 330, 70, 'peer 1 nhận: "đồng ý"', BL) + ND(360, 410, 330, 70, 'peer 2 nhận: "từ chối"', BL)
b += LB(70, 440, 260, 'gửi hai giá trị khác nhau cho từng peer') + LB(360, 490, 330, 'node trung thực nhận dữ liệu mâu thuẫn')
for i, (ti, tx, a, tg) in enumerate([('Crash', 'Node dừng hẳn, không trả lời nữa.', TE, 'nhẹ'),
                                     ('Omission', 'Node mất hoặc bỏ qua một số thông điệp.', OR, 'vừa'),
                                     ('Byzantine', 'Node gửi giá trị tùy ý, kể cả mâu thuẫn.', R, 'nặng nhất')]):
    b += K(746, 205 + i * 112, 638, 100, ti, tx, a, f'<div style="position:absolute;right:22px;top:18px">' + P(tg, a, TINT[a]) + '</div>')
b += D(56, 560, 1328, 150, 'Cách chống', 'Nhân bản và biểu quyết đa số; ký thông điệp để lộ mâu thuẫn. Không tin một node, tin đa số trung thực.')
slides.append(S(5, 'Byzantine: node có thể nói dối', b))

# 6 3k+1
b = B(56, 205, 470, 330, f'<div style="text-align:center;font-size:76px;font-weight:700;color:{R};margin-top:28px" class="mono">n ≥ 3k+1</div>'
      '<p style="margin-top:22px;font-size:20px"><b>n</b>: tổng số node trong nhóm<br><b>k</b>: số node xấu tối đa hệ thống chịu được<br><b>quorum</b>: cần n − k phản hồi khớp nhau</p>', 'c k', R)
rows = [('k = 0', 'n ≥ 1', 1), ('k = 1', 'n ≥ 4', 4), ('k = 2', 'n ≥ 7', 7), ('k = 3', 'n ≥ 10', 10)]
inner = '<h3 style="color:#0f172a">Cần bao nhiêu node?</h3>'
for lab, nn, cnt in rows:
    dots = ''.join(f'<span style="display:inline-block;width:{20 if cnt<=7 else 16}px;height:{20 if cnt<=7 else 16}px;border-radius:50%;background:{BL};margin-right:5px"></span>' for _ in range(cnt))
    inner += f'<div style="display:flex;align-items:center;margin:14px 0"><b style="width:80px;font-size:20px">{lab}</b><b class="mono" style="width:100px;font-size:20px;color:{R}">{nn}</b><div>{dots}</div></div>'
b += B(556, 205, 828, 330, inner, 'c')
b += D(56, 565, 650, 145, 'Vì sao 3k + 1', 'Node xấu có thể im lặng hoặc nói dối; phần còn lại vẫn phải thắng đa số.')
b += B(736, 565, 648, 145, f'<h3 style="color:{R}">TrustMesh: n = 3</h3><p>Byzantine chịu được k = 0, chưa đủ. Dùng chữ ký và quorum 2 reporter độc lập cho cảnh báo.</p>', 'c k', R)
slides.append(S(6, 'Giới hạn n ≥ 3k + 1', b))

# 7 sybil
b = B(56, 205, 720, 330, '', 'c')
b += ND(90, 340, 150, 80, 'Kẻ tấn công', R, '', '#fde8e9')
b += AR(240, 350, 70, R)
for i in range(4):
    b += ND(320 + (i % 2) * 150, 240 + (i // 2) * 130, 130, 60, f'giả #{i+1}', R, '', '#fde8e9')
b += ND(620, 240, 130, 60, 'node A', BL) + ND(620, 330, 130, 60, 'node B', BL) + ND(620, 420, 130, 60, 'node C', BL)
b += LB(320, 500, 260, '4 danh tính giả') + LB(610, 500, 150, '3 node thật')
b += P('Phá vỡ: một danh tính = một thực thể', R, TINT[R]).replace('class="p"', 'class="p" style="position:absolute;left:0"') if False else ''
for i, (ti, tx, a) in enumerate([('CA tập trung', 'Cấp và ràng buộc danh tính.', BL), ('Phi tập trung', 'PoW, PoS hoặc reputation làm danh tính tốn kém.', OR), ('TrustMesh', 'Cụm đóng: chỉ khóa đã ghim mới được tham gia.', TE)]):
    b += K(806, 205 + i * 112, 578, 100, ti, tx, a)
b += D(56, 565, 1328, 145, 'Hậu quả của Sybil', 'Tăng quyền biểu quyết, cô lập node trung thực. Phá vỡ giả định mỗi danh tính là một thực thể.')
slides.append(S(7, 'Sybil: nhiều danh tính giả', b))

# 8 hash chain
b = ''
blocks = [('#1', '0000', 'điểm: 8.0', 'a1f3', BL, False), ('#2', 'a1f3', 'điểm: 10.0', '9c7e', R, True), ('#3', 'b72d', 'điểm: 7.5', 'e0c5', R, True)]
for i, (no, prv, data, h, a, bad) in enumerate(blocks):
    x = 56 + i * 452
    note = ('<div style="margin-top:6px">' + P('đã bị sửa → hash đổi', R, TINT[R]) + '</div>') if i == 1 else (('<div style="margin-top:6px">' + P('prev lệch → chuỗi đứt', R, TINT[R]) + '</div>') if i == 2 else '')
    b += B(x, 205, 380, 200, f'<h3 style="color:{a}">Bản ghi {no}</h3><p class="mono" style="font-size:17px">prev: {prv}<br>data: {data}<br>hash: {h}</p>{note}', 'c k', a)
    if i < 2: b += AR(x + 384, 280, 60, a)
for i, (ti, tx, a) in enumerate([('Hash chain', 'Mỗi bản ghi chứa hash của bản ghi trước; sửa một bản ghi làm các bản sau lệch.', BL),
                                 ('Blockchain', 'Hash chain nhân bản, đồng thuận giữa nhiều bên; khó sửa đồng thời mọi bản sao.', TE),
                                 ('Giới hạn', 'Chỉ phát hiện sửa, không ngăn được. Vẫn phải tin implementation và consensus.', OR)]):
    b += K(56 + i * 452, 425, 424, 175, ti, tx, a)
b += D(56, 620, 1328, 90, 'TrustMesh', 'Mallory sửa audit log của node-a: chuỗi hash đứt, node-b và node-c còn bằng chứng.')
slides.append(S(8, 'Hash chain và blockchain', b))

# 9 five traits
b = ''
tr = [('Đồng hồ', 'Không có đồng hồ toàn cục chung.', R), ('Lỗi riêng', 'Một node hỏng, phần còn lại vẫn chạy.', OR), ('Mạng', 'Thông điệp có thể trễ, mất hoặc đảo thứ tự.', BL),
      ('Đồng thời', 'Nhiều tiến trình cùng truy cập dữ liệu chung.', TE), ('Không điểm duy nhất', 'Không có một cổng kiểm soát chung.', VI)]
for i, (ti, tx, a) in enumerate(tr):
    x = 56 + i * 269
    b += B(x, 215, 252, 300, f'<h3 style="color:{a};margin-top:44px">{ti}</h3><p>{tx}</p>', 'c k', a) + CIR(x + 20, 195 + 40, i + 1, a)
b += D(56, 550, 1328, 160, 'Hệ quả cho bảo mật', 'Chính sách phải được thực thi ở từng node; không thể dựa vào một cổng duy nhất hay một đồng hồ chung.')
slides.append(S(9, 'Vì sao bảo mật phân tán khó', b))

# 10 reference monitor
b = ND(56, 235, 270, 110, 'Subject', BL, 'người dùng · tiến trình')
b += AR(336, 255, 80, BL) + LB(332, 305, 90, 'yêu cầu operation')
b += B(426, 205, 400, 300, '<h3 style="color:#fcd34d;text-align:center">Reference monitor</h3>', 'c d')
b += ND(456, 265, 150, 60, 'AuthN', BL, 'là ai?', '#fff') + AR(606, 270, 40, BL) + ND(646, 265, 150, 60, 'AuthZ', R, 'được làm gì?', '#fff')
b += ND(476, 380, 300, 70, 'Chính sách (policy)', TE, '', '#fff') + AR(606, 330, 40, '#fff', '↓')
b += AR(836, 255, 80, BL) + ND(926, 235, 270, 110, 'Object', TE, 'bảng điểm grades-ds') + LB(920, 360, 290, 'chỉ cho qua khi chính sách cho phép')
for i, (ti, tx, a) in enumerate([('Chống sửa đổi', 'Kẻ tấn công không thể đổi reference monitor.', R), ('Không thể bị bỏ qua', 'Mọi đường truy cập đều đi qua.', BL), ('Đủ nhỏ để kiểm chứng', 'Fail-safe default: không khớp thì từ chối.', TE)]):
    b += K(56 + i * 452, 535, 424, 175, ti, tx, a)
slides.append(S(10, '9.5 Mô hình authorization', b))

# 11 four models
b = ''
ms = [('MAC', 'Nhãn bảo mật do quản trị trung tâm đặt.', R, 'tập trung'), ('DAC', 'Chủ sở hữu tự trao quyền cho người khác.', OR, 'chủ sở hữu'),
      ('RBAC', 'Quyền gắn với vai trò, người dùng nhận vai trò.', BL, 'vai trò'), ('ABAC', 'Xét thuộc tính người dùng, tài nguyên và môi trường.', TE, 'thuộc tính')]
for i, (ti, tx, a, tg) in enumerate(ms):
    b += K(56 + i * 334, 215, 316, 290, ti, tx, a, '<div style="margin-top:14px">' + P(tg, a, TINT[a]) + '</div>')
b += B(56, 535, 1328, 70, f'<div class="hl" style="background:linear-gradient(90deg,{R},{OR},{BL},{TE});margin-top:14px"></div>', 'c')
b += LB(66, 618, 300, 'đơn giản, cứng') + LB(1074, 618, 300, 'chi tiết, linh hoạt')
b += D(56, 650, 1328, 70, 'ABAC', '')
b = b.replace('<h3>ABAC</h3><p></p>', '<p style="font-size:20px"><b style="color:#fcd34d">ABAC</b>: chi tiết hơn nhưng chính sách phức tạp, khó kiểm tra.</p>')
slides.append(S(11, 'MAC, DAC, RBAC, ABAC', b))

# 12 ABAC
b = ''
for i, (ti, tx, a) in enumerate([('Chủ thể', 'vai trò · khoa · nhãn', BL), ('Tài nguyên', 'nhãn · chủ sở hữu', TE), ('Môi trường', 'giờ truy cập · node nhận', OR)]):
    b += K(56, 205 + i * 100, 400, 90, ti, tx, a)
    b += AR(466, 222 + i * 100, 60, a)
b += ND(536, 245, 300, 180, 'Policy engine', NV, 'đối chiếu thuộc tính đã xác thực', NV, '#fff')
b += AR(846, 285, 60, BL) + ND(916, 215, 220, 70, 'Cho phép', GR, '', '#e3f5e8') + ND(916, 345, 220, 70, 'Từ chối', R, '', '#fde8e9')
for i, (ti, tx, a) in enumerate([('Alice', 'Đúng vai trò và khoa: ABAC cho đọc.', GR), ('Mallory', 'Nhãn thấp hơn bảng điểm: MAC chặn.', R), ('Tự khai admin', 'Thuộc tính tự khai bị bỏ qua.', OR)]):
    b += K(56 + i * 452, 530, 424, 180, ti, tx, a)
slides.append(S(12, 'ABAC trong TrustMesh', b))

# 13 ACL vs capability
b = B(56, 205, 600, 420, f'<h3 style="color:{R}">ACL · theo object</h3><p>Quyền lưu cùng với tài nguyên.</p>', 'c k', R)
tbl = ''
for u, o in [('Alice', 'read'), ('Bob', 'read'), ('Mallory', '—')]:
    tbl += f'<div style="display:flex;justify-content:space-between;padding:10px 14px;border:1px solid #e3e7f1;border-radius:8px;margin:8px 0;font-size:19px"><b>{u}</b><span class="mono" style="color:{R if o=="—" else GR}">{o}</span></div>'
b += B(86, 320, 540, 230, f'<div class="mono" style="font-size:17px;color:#475569;margin-bottom:6px">grades-ds</div>{tbl}', '', None, None, 'position:absolute;')
b += B(784, 205, 600, 420, f'<h3 style="color:{BL}">Capability · theo subject</h3><p>Bằng chứng quyền do subject giữ, server xác minh token.</p>', 'c k', BL)
tk = (f'<div class="mono" style="font-size:17px;line-height:1.7;color:#1e293b">holder: Bob<br>op: read · grades-ds<br>hạn: ngắn<br>chữ ký: Ed25519 ✓</div>')
b += B(814, 330, 540, 150, tk, 'c', None, None, f'border:2px dashed {BL};')
b += P('vé TrustMesh = capability có chữ ký', BL, TINT[BL]).replace('<span', '<span style="position:absolute;left:814px;top:500px"') if False else f'<div style="position:absolute;left:814px;top:500px">{P("vé TrustMesh = capability có chữ ký", BL, TINT[BL])}</div>'
b += f'<div class="cir" style="left:698px;top:395px;--a:{NV}">⇄</div>'
b += D(56, 650, 1328, 70, '', '')
b = b.replace('<h3></h3><p></p>', '<p style="font-size:19px">Capability cần chống sửa vé, dùng lại vé, vé quá hạn; thu hồi khó nên dùng hạn ngắn và danh sách thu hồi.</p>')
slides.append(S(13, 'ACL và capability', b))

# 14 delegation
b = ND(56, 215, 300, 110, 'node-a / Alice', BL, 'quyền gốc: read + write')
b += AR(366, 235, 70, BL) + LB(360, 285, 80, 'ký vé') + ND(446, 215, 300, 110, 'Bob', TE, 'read · hạn 1 giờ')
b += AR(756, 235, 70, TE) + LB(750, 285, 80, 'ủy lại') + ND(836, 215, 300, 110, 'Carol', OR, 'read · hạn 15 phút')
b += B(1166, 215, 218, 110, f'<p style="font-size:17px"><b style="color:{R}">Không mở rộng</b><br>quyền chỉ thu hẹp hoặc giữ nguyên</p>', 'c k', R)
b += B(56, 360, 620, 140, f'<h3 style="color:{BL}">Delegation</h3><p>Cho bên khác hành động thay mình mà không đưa mật khẩu.</p>', 'c k', BL)
b += B(706, 360, 678, 140, f'<h3 style="color:{OR}">OAuth</h3><p>Token có scope và thời hạn thay cho mật khẩu của người dùng.</p>', 'c k', OR)
b += K(56, 530, 620, 180, 'Trong TrustMesh', 'node-a ký vé cho Bob; Bob ủy lại cho Carol với quyền hẹp hơn. node-b, node-c tự kiểm chữ ký.', TE)
b += K(706, 530, 678, 180, 'Rủi ro cần chặn', 'Vé bị đánh cắp · vé quá hạn · mở rộng quyền khi ủy tiếp.', R)
slides.append(S(14, '9.5.3 Delegation và OAuth', b))

# 15 WAVE
b = ND(56, 225, 270, 100, 'trust anchor', R, 'node-a', '#fde8e9') + AR(334, 240, 60, R)
b += ND(394, 225, 270, 100, 'vé 1', BL, 'node-a → Bob: read') + AR(672, 240, 60, BL)
b += ND(732, 225, 270, 100, 'vé 2', TE, 'Bob → Carol: read (hẹp hơn)') + AR(1010, 240, 60, TE)
b += ND(1070, 225, 314, 100, 'Carol đọc ở node-c', OR, 'node-c verify chuỗi')
b += B(56, 360, 1328, 90, f'<p style="font-size:20px;text-align:center;margin-top:8px">Verifier duyệt <b>ngược</b> chuỗi attestation từ vé 2 về trust anchor, kiểm từng chữ ký và từng bước thu hẹp quyền.</p>', 'c')
for i, (ti, tx, a) in enumerate([('WAVE', 'Biểu diễn ủy quyền bằng đồ thị attestation.', BL), ('Mỗi mắt xích', 'Thu hẹp quyền của mắt trước, không mở rộng.', TE), ('Không hỏi lại', 'node-b, node-c không gọi lại node cấp vé.', OR)]):
    b += K(56 + i * 452, 480, 424, 230, ti, tx, a)
slides.append(S(15, 'WAVE và chuỗi delegation', b))

# 16 firewall
b = ND(56, 245, 200, 100, 'Internet', '#475569', 'người dùng · kẻ tấn công') + AR(262, 255, 70, R)
b += ND(338, 215, 170, 160, 'Firewall', R, 'lọc ở biên', '#fde8e9')
b += AR(514, 255, 70, R)
b += B(594, 205, 790, 200, '', 'c', None, None, 'border:2px dashed #94a3b8;')
for i, nm in enumerate(['node-a', 'node-b', 'node-c']):
    b += ND(624 + i * 250, 240, 220, 80, nm, BL, 'audit · IDS')
b += LB(594, 340, 790, 'bên trong: mỗi node tự audit và phát hiện')
b += f'<div style="position:absolute;left:56px;top:414px;width:1328px;text-align:center;font-size:21px;font-weight:700;color:{R}">Tài khoản hợp lệ bị chiếm vẫn đi qua firewall như lưu lượng bình thường</div>'
for i, (ti, tx, a) in enumerate([('Chặn', 'Cổng, địa chỉ, giao thức không hợp lệ.', TE), ('Bỏ sót', 'Lưu lượng bình thường nhưng ý đồ xấu.', R), ('Cần thêm', 'Audit và phát hiện xâm nhập bên trong.', BL)]):
    b += K(56 + i * 452, 455, 424, 170, ti, tx, a)
b += D(56, 645, 1328, 70, '', '')
b = b.replace('<h3></h3><p></p>', '<p style="font-size:20px"><b style="color:#fcd34d">Firewall không thay thế authorization.</b></p>')
slides.append(S(16, '9.6 Firewall và giám sát', b))

# 17 SIDS vs AIDS
b = B(56, 205, 640, 320, f'<h3 style="color:{BL}">SIDS · theo chữ ký</h3><p>Khớp mẫu tấn công đã biết, dễ giải thích.</p>', 'c k', BL)
b += ND(86, 320, 150, 60, 'Gói tin', BL) + AR(236, 328, 50, BL) + ND(286, 320, 170, 60, 'Khớp mẫu?', BL) + AR(456, 328, 50, BL) + ND(506, 320, 160, 60, 'Cảnh báo', R, '', '#fde8e9')
b += f'<div style="position:absolute;left:86px;top:410px">{P("dễ giải thích", GR, TINT[GR])}{P("yếu với zero-day", R, TINT[R])}</div>'
b += B(744, 205, 640, 320, f'<h3 style="color:{TE}">AIDS · theo bất thường</h3><p>Học hành vi bình thường, tìm điều lệch chuẩn.</p>', 'c k', TE)
b += ND(774, 320, 150, 60, 'Hành vi', TE) + AR(924, 328, 50, TE) + ND(974, 320, 170, 60, 'Lệch chuẩn?', TE) + AR(1144, 328, 50, TE) + ND(1194, 320, 160, 60, 'Cảnh báo', R, '', '#fde8e9')
b += f'<div style="position:absolute;left:774px;top:410px">{P("bắt được tấn công mới", GR, TINT[GR])}{P("dễ báo nhầm", R, TINT[R])}</div>'
b += K(56, 555, 424, 155, 'SIDS ở node-b', 'Nhận ra path traversal bằng mẫu đã biết.', BL)
b += K(508, 555, 424, 155, 'AIDS ở node-a, node-c', 'Ba lần bị từ chối liên tiếp là bất thường.', TE)
b += D(960, 555, 424, 155, 'Một cảnh báo', 'chưa là sự cố; cần quorum nhiều reporter.')
slides.append(S(17, 'SIDS và AIDS', b))

# 18 CIDS
b = B(56, 205, 640, 340, f'<h3 style="color:{OR}">CIDS tập trung</h3>', 'c k', OR)
b += ND(296, 330, 160, 70, 'Trung tâm', OR, 'phân tích', '#ffeede')
for i, (x, y) in enumerate([(100, 280), (100, 400), (560, 280), (560, 400), (330, 470)]):
    b += ND(x, y, 90, 44, f's{i+1}', BL)
b += B(744, 205, 640, 340, f'<h3 style="color:{TE}">CIDS phân tán</h3>', 'c k', TE)
b += ND(790, 300, 150, 60, 'head A', TE, '', '#e0f5f1') + ND(1180, 300, 150, 60, 'head B', TE, '', '#e0f5f1') + AR(940, 305, 240, TE, '↔')
for x, y in [(790, 400), (880, 440), (1180, 400), (1270, 440)]:
    b += ND(x, y, 70, 38, 's', BL)
b += LB(790, 495, 300, 'community A') + LB(1180, 495, 200, 'community B')
b += K(56, 575, 424, 135, 'Tập trung', 'Chính xác hơn nhưng dễ nghẽn, một điểm lỗi.', OR)
b += K(508, 575, 424, 135, 'Phân tán', 'Mở rộng tốt, không có điểm lỗi duy nhất.', TE)
b += D(960, 575, 424, 135, 'TrustMesh', 'Hai reporter độc lập tạo quorum.')
slides.append(S(18, 'Collaborative IDS (CIDS)', b))

# 19 metrics
cells = [('TP', 'cảnh báo đúng', GR, '#e3f5e8'), ('FP', 'báo nhầm', R, '#fde8e9'), ('FN', 'bỏ sót tấn công', OR, '#ffeede'), ('TN', 'bỏ qua đúng', BL, '#e6efff')]
b = LB(250, 205, 200, 'thực tế: tấn công') + LB(470, 205, 200, 'thực tế: bình thường')
for i, (n, tx, a, bg) in enumerate(cells):
    x = 230 + (i % 2) * 230
    y = 235 + (i // 2) * 150
    b += B(x, y, 215, 135, f'<div style="font-size:42px;font-weight:700;color:{a}">{n}</div><p style="font-size:16px">{tx}</p>', 'c', None, None, f'background:{bg};')
b += LB(56, 280, 160, 'IDS báo<br>tấn công') + LB(56, 430, 160, 'IDS báo<br>bình thường')
b += B(720, 205, 664, 135, f'<h3 style="color:{BL}">Accuracy</h3><p class="mono" style="font-size:21px">(TP + TN) / tổng số mẫu</p>', 'c k', BL)
b += B(720, 355, 664, 135, f'<h3 style="color:{TE}">Precision</h3><p class="mono" style="font-size:21px">TP / (TP + FP)</p><p>Cảnh báo đúng bao nhiêu phần.</p>', 'c k', TE)
b += D(56, 530, 1328, 180, 'Base rate', '<span style="font-size:21px">Tấn công hiếm thì FP lấn át cảnh báo. Ví dụ minh họa: tấn công 1%, FP 5% → precision chỉ khoảng 17%. Vì vậy theo dõi precision, đừng chỉ đếm số cảnh báo.</span>')
slides.append(S(19, 'Đánh giá IDS: TP, FP, FN, TN', b))

# 20 demo
acts = [('1', 'Ai được đọc bảng điểm?', 'Alice đọc được (ABAC), Mallory bị MAC chặn, tự khai admin bị bỏ qua.', BL, '9.5.1–9.5.2'),
        ('2', 'Ủy quyền qua ba node', 'node-a ký vé cho Bob, Bob ủy Carol, Carol đọc ở node-c.', TE, '9.5.3'),
        ('3', 'Mallory đổi chiến thuật', 'Vé đánh cắp, vé giả đều bị từ chối; AIDS và SIDS đủ quorum.', OR, '9.4, 9.6'),
        ('4', 'Xóa dấu vết', 'Sửa audit log node-a, chuỗi hash đứt; node-b, c còn bằng chứng.', R, '9.4.3')]
b = ''
for i, (n, ti, tx, a, tg) in enumerate(acts):
    x = 56 + i * 334
    b += B(x, 225, 316, 330, f'<h3 style="color:{a};margin-top:34px">{ti}</h3><p>{tx}</p><div style="margin-top:12px">{P(tg, a, TINT[a])}</div>', 'c k', a) + CIR(x + 20, 205, n, a)
    if i < 3: b += AR(x + 316, 360, 18, a, '›')
b += D(56, 585, 1328, 125, 'Partial failure', 'Tắt node B, bấm R, chạy lại 1 → 4: hai node còn lại vẫn phục vụ.')
slides.append(S(20, 'Demo: Mallory muốn sửa bảng điểm', b))

# 21 conclusion
b = ''
for i, (ti, tx, a) in enumerate([('Trust', 'Không loại bỏ nhu cầu kiểm chứng.', R), ('Authorization', 'Mặc định từ chối, giới hạn delegation.', BL), ('Monitoring', 'Kết hợp nhiều điểm quan sát.', TE)]):
    b += K(56 + i * 452, 215, 424, 230, ti, tx, a)
b += K(56, 475, 650, 235, 'Partial failure', 'Một node hỏng chỉ giảm năng lực, không dừng cả hệ thống.', OR)
b += D(736, 475, 648, 235, 'Thông điệp chính', 'Một cơ chế đơn lẻ không đủ. Tin giả định về cả nhóm, và kiểm chứng từng bằng chứng.')
slides.append(S(21, 'Kết luận 9.7', b))

# 22 thanks
slides.append(
    '<section class="s w"><img class="hd" src="header_cover.png">'
    '<div style="position:absolute;left:0;top:250px;width:1440px;text-align:center">'
    f'<div style="font-size:54px;font-weight:700;color:{R}">Cảm ơn thầy và các bạn đã lắng nghe</div>'
    f'<div style="font-size:34px;font-weight:700;color:{R};margin-top:16px">Hỏi đáp</div></div>'
    f'<div style="position:absolute;left:0;top:570px;width:1440px;height:240px;background:{R}"></div>'
    '<div style="position:absolute;right:70px;top:650px;text-align:right;font:italic 700 24px/1.6 Courier New,monospace;color:#fff">'
    'Vũ Văn Hùng<br>Hoàng Văn Huynh - B23DCCC086</div></section>')

html = '<!doctype html><html lang="vi"><meta charset="utf-8"><title>TrustMesh</title><style>' + CSS + '</style><body>' + ''.join(slides) + '</body></html>'
open('trustmesh-ptit.html', 'w', encoding='utf-8').write(html)
print(len(slides), 'slides')
