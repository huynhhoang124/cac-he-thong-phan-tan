from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = PROJECT_ROOT / "screenshots"
OUTPUT = PROJECT_ROOT / "Bao_cao_thuc_hanh_02.docx"

DARK_BLUE = "17365D"
PALE_BLUE = "EAF2F8"
LIGHT_GRAY = "D9D9D9"
BLACK = RGBColor(0, 0, 0)
WHITE = RGBColor(255, 255, 255)


def set_font(run, name: str = "Times New Roman", size: float = 12, bold=False):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = BLACK


def shade_cell(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_borders(cell, color: str = LIGHT_GRAY, size: str = "8") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:color"), color)


def set_cell_margins(cell, top=100, start=120, bottom=100, end=120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def style_table(table, header=True, center_columns: set[int] | None = None) -> None:
    center_columns = center_columns or set()
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for row_index, row in enumerate(table.rows):
        for col_index, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_borders(cell)
            set_cell_margins(cell)
            if header and row_index == 0:
                shade_cell(cell, DARK_BLUE)
            elif row_index % 2 == 0:
                shade_cell(cell, PALE_BLUE)
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.alignment = (
                    WD_ALIGN_PARAGRAPH.CENTER
                    if col_index in center_columns
                    else WD_ALIGN_PARAGRAPH.LEFT
                )
                for run in paragraph.runs:
                    set_font(run, size=10.5, bold=header and row_index == 0)
                    if header and row_index == 0:
                        run.font.color.rgb = WHITE


def set_repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def suppress_paragraph_borders(paragraph) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    existing = p_pr.find(qn("w:pBdr"))
    if existing is not None:
        p_pr.remove(existing)
    borders = OxmlElement("w:pBdr")
    for edge in ("top", "left", "bottom", "right", "between", "bar"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "nil")
        borders.append(element)
    p_pr.append(borders)


def add_body(doc: Document, text: str, bold_lead: str | None = None):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.line_spacing = 1.15
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if bold_lead and text.startswith(bold_lead):
        lead = paragraph.add_run(bold_lead)
        set_font(lead, bold=True)
        rest = paragraph.add_run(text[len(bold_lead) :])
        set_font(rest)
    else:
        run = paragraph.add_run(text)
        set_font(run)
    return paragraph


def add_bullet(doc: Document, text: str):
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(3)
    for run in paragraph.runs:
        set_font(run)
    if not paragraph.runs:
        set_font(paragraph.add_run(text))
    else:
        paragraph.runs[0].text = text
    return paragraph


def add_figure(doc: Document, filename: str, caption: str, width=6.7):
    image_path = SCREENSHOTS / filename
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.add_run().add_picture(str(image_path), width=Inches(width))
    caption_paragraph = doc.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.paragraph_format.space_after = Pt(8)
    caption_run = caption_paragraph.add_run(caption)
    set_font(caption_run, size=10)
    caption_run.font.italic = True


def add_heading(doc: Document, text: str, level: int):
    paragraph = doc.add_heading(text, level=level)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_before = Pt(10 if level == 1 else 7)
    paragraph.paragraph_format.space_after = Pt(4)
    for run in paragraph.runs:
        set_font(run, size=15 if level == 1 else 13, bold=True)
    return paragraph


def add_command(doc: Document, command: str):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.25)
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(command)
    set_font(run, name="Consolas", size=9.5)


def configure_styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(12)
    normal.font.color.rgb = BLACK

    title = doc.styles["Title"]
    title.font.name = "Times New Roman"
    title._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    title._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    title._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    title.font.size = Pt(22)
    title.font.bold = True
    title.font.color.rgb = BLACK

    for style_name, size in (("Heading 1", 15), ("Heading 2", 13), ("Heading 3", 12)):
        style = doc.styles[style_name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = BLACK


def build_report() -> Path:
    doc = Document()
    configure_styles(doc)
    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    doc.core_properties.title = "Báo cáo bài thực hành số 02"
    doc.core_properties.subject = "RabbitMQ và UDP multicast trong hệ thống phân tán"
    doc.core_properties.author = "Sinh viên"

    # Trang bìa
    doc.add_paragraph("\n\n")
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    suppress_paragraph_borders(title)
    title.add_run("BÁO CÁO BÀI THỰC HÀNH SỐ 02")

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_before = Pt(10)
    subtitle.paragraph_format.space_after = Pt(30)
    run = subtitle.add_run("TRUYỀN THÔNG HƯỚNG THÔNG ĐIỆP VÀ TRUYỀN THÔNG THEO NHÓM TRONG HỆ THỐNG PHÂN TÁN")
    set_font(run, size=15, bold=True)

    student_info = (
        ("Họ và tên", "Hoàng Văn Huynh"),
        ("Mã số sinh viên", "B23DCCC086"),
    )
    for label, student_value in student_info:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(1.25)
        paragraph.paragraph_format.space_after = Pt(10)
        lead = paragraph.add_run(f"{label}: ")
        set_font(lead, bold=True)
        value = paragraph.add_run(student_value)
        set_font(value)

    date_paragraph = doc.add_paragraph()
    date_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    date_paragraph.paragraph_format.space_before = Pt(115)
    set_font(date_paragraph.add_run("Tháng 9 năm 2026"), size=12)

    doc.add_page_break()

    add_heading(doc, "Tóm tắt kết quả", 1)
    add_body(
        doc,
        "Bài thực hành đã cài đặt và kiểm thử hai cơ chế truyền thông trong hệ thống phân tán. Phần RabbitMQ chứng minh thông điệp persistent tồn tại sau khi broker khởi động lại, thông điệp transient bị mất, producer hoạt động bất đồng bộ và ba consumer cùng chia tải. Phần UDP multicast chứng minh một gói gửi có thể được nhiều receiver nhận, receiver tham gia muộn không nhận lại bản tin cũ và Wireshark quan sát đúng năm datagram trên giao diện Wi-Fi.",
    )

    summary = doc.add_table(rows=1, cols=3)
    summary.rows[0].cells[0].text = "Kịch bản"
    summary.rows[0].cells[1].text = "Kết quả đo"
    summary.rows[0].cells[2].text = "Đánh giá"
    summary_data = [
        ("RabbitMQ persistent", "5/5 tin còn sau restart", "Đạt"),
        ("RabbitMQ transient", "0/5 tin còn sau restart", "Đạt"),
        ("RabbitMQ bất đồng bộ", "0,127 giây gửi; 42,860 giây xử lý", "Đạt"),
        ("Cân bằng tải", "5 - 5 - 5 đơn", "Đạt"),
        ("Multicast nhiều receiver", "Mỗi receiver nhận 5/5 gói", "Đạt"),
        ("Receiver tham gia muộn", "Bắt đầu từ seq 5", "Đạt"),
        ("Wireshark multicast", "5 gói tới 224.1.1.1:5007", "Đạt"),
    ]
    for row_data in summary_data:
        cells = summary.add_row().cells
        for index, value in enumerate(row_data):
            cells[index].text = value
    summary.columns[0].width = Inches(2.25)
    summary.columns[1].width = Inches(3.45)
    summary.columns[2].width = Inches(1.0)
    style_table(summary, center_columns={2})
    set_repeat_header(summary.rows[0])

    add_heading(doc, "1 Mục tiêu", 1)
    add_bullet(doc, "Cài đặt mô hình Producer - Queue - Consumer bằng RabbitMQ.")
    add_bullet(doc, "Phân biệt thông điệp persistent và transient bằng kiểm thử restart broker.")
    add_bullet(doc, "Quan sát tính bất đồng bộ và cơ chế phân phối tải giữa nhiều consumer.")
    add_bullet(doc, "Cài đặt UDP multicast và kiểm chứng nhiều receiver cùng nhận một bản tin.")
    add_bullet(doc, "Dùng Wireshark bắt và phân tích lưu lượng UDP multicast trên giao diện Wi-Fi.")

    add_heading(doc, "2 Môi trường thực hiện", 1)
    environment = doc.add_table(rows=1, cols=2)
    environment.rows[0].cells[0].text = "Thành phần"
    environment.rows[0].cells[1].text = "Cấu hình"
    for item, value in (
        ("Hệ điều hành", "Windows"),
        ("Python", "3.10.11"),
        ("RabbitMQ", "3.13 Management chạy bằng Docker Compose"),
        ("Thư viện", "pika 1.3.2"),
        ("Queue", "don_hang"),
        ("Multicast", "224.1.1.1:5007"),
        ("Wireshark", "4.6.8 với Npcap"),
    ):
        row = environment.add_row().cells
        row[0].text = item
        row[1].text = value
    environment.columns[0].width = Inches(2.1)
    environment.columns[1].width = Inches(4.6)
    style_table(environment)
    set_repeat_header(environment.rows[0])
    add_figure(
        doc,
        "01-rabbitmq-service.png",
        "Hình 1  RabbitMQ 3.13 đang chạy ở trạng thái healthy",
    )

    add_heading(doc, "3 Truyền thông hướng thông điệp với RabbitMQ", 1)
    add_heading(doc, "3.1 Thiết kế chương trình", 2)
    add_body(
        doc,
        "Producer tạo thông điệp JSON gồm mã đơn hàng, danh sách sản phẩm, tổng tiền và thời điểm gửi. Queue được khai báo theo chế độ persistent hoặc transient. Consumer nhận thông điệp, mô phỏng xử lý trong 1-3 giây, ghi log thời điểm nhận và chỉ gửi manual acknowledgement sau khi xử lý xong.",
    )
    add_bullet(doc, "Persistent: durable=True và delivery_mode=2.")
    add_bullet(doc, "Transient: durable=False và delivery_mode=1.")
    add_bullet(doc, "Cân bằng tải: manual ack kết hợp prefetch_count=1.")

    add_heading(doc, "3.2 KB1 Truyền tin bền bỉ", 2)
    add_body(doc, "Cách thực hiện: dừng consumer, gửi 5 thông điệp persistent, restart RabbitMQ rồi mới khởi động consumer.")
    add_command(doc, "python -m rabbitmq.producer --mode persistent --count 5")
    add_body(
        doc,
        "Kết quả: queue có 5 thông điệp trước restart và vẫn có đủ 5 thông điệp sau restart. Consumer nhận đủ DH001-DH005 và gửi manual ack cho từng thông điệp.",
        bold_lead="Kết quả:",
    )
    add_figure(
        doc,
        "02-kb1-persistent.png",
        "Hình 2  Năm thông điệp persistent được nhận đủ sau khi broker restart",
    )

    add_heading(doc, "3.3 KB2 Truyền tin nhất thời", 2)
    add_body(doc, "Cách thực hiện: tạo lại queue với durable=False, gửi 5 thông điệp transient rồi restart RabbitMQ.")
    add_command(doc, "python -m rabbitmq.producer --mode transient --count 5")
    add_body(
        doc,
        "Kết quả: producer xác nhận đã gửi 5 thông điệp, nhưng sau restart queue cũ không tồn tại. Khi tạo lại queue, message_count bằng 0. Điều này phù hợp với tính nhất thời của queue và message transient.",
        bold_lead="Kết quả:",
    )
    add_figure(
        doc,
        "03-kb2-transient.png",
        "Hình 3  Thông điệp transient không còn sau khi RabbitMQ restart",
    )

    add_heading(doc, "3.4 KB3 Truyền tin không đồng bộ", 2)
    add_body(doc, "Producer publish liên tục 20 thông điệp mà không chờ consumer xử lý từng đơn. Consumer xử lý tuần tự với thời gian ngẫu nhiên 1-3 giây mỗi đơn.")
    async_table = doc.add_table(rows=1, cols=2)
    async_table.rows[0].cells[0].text = "Đại lượng"
    async_table.rows[0].cells[1].text = "Kết quả"
    for key, value in (
        ("Số thông điệp", "20"),
        ("Thời gian producer publish", "0,127 giây"),
        ("Thời gian consumer xử lý", "42,860 giây"),
        ("Producer chờ phản hồi", "Không"),
    ):
        cells = async_table.add_row().cells
        cells[0].text = key
        cells[1].text = value
    async_table.columns[0].width = Inches(4.1)
    async_table.columns[1].width = Inches(2.6)
    style_table(async_table, center_columns={1})
    add_body(
        doc,
        "Nhận xét: thời gian publish nhỏ hơn rất nhiều thời gian xử lý toàn bộ queue, chứng minh producer và consumer hoạt động bất đồng bộ.",
        bold_lead="Nhận xét:",
    )
    add_figure(
        doc,
        "04-kb3-asynchronous.png",
        "Hình 4  So sánh thời gian gửi và thời gian xử lý 20 thông điệp",
    )

    add_heading(doc, "3.5 KB4 Cân bằng tải giữa nhiều consumer", 2)
    add_body(doc, "Ba consumer cùng lắng nghe queue don_hang. Producer gửi 15 thông điệp; mỗi consumer dùng manual ack và prefetch_count=1.")
    balance = doc.add_table(rows=1, cols=3)
    balance.rows[0].cells[0].text = "Consumer"
    balance.rows[0].cells[1].text = "Số đơn xử lý"
    balance.rows[0].cells[2].text = "Tỷ lệ"
    for name in ("consumer-1", "consumer-2", "consumer-3"):
        cells = balance.add_row().cells
        cells[0].text = name
        cells[1].text = "5"
        cells[2].text = "33,3%"
    balance.columns[0].width = Inches(3.0)
    balance.columns[1].width = Inches(2.0)
    balance.columns[2].width = Inches(1.7)
    style_table(balance, center_columns={1, 2})
    add_body(doc, "Nhận xét: cả ba consumer xử lý đúng 5 đơn, tổng cộng 15 đơn. Kết quả thể hiện RabbitMQ phân phối tải đều trong lần chạy thử.", bold_lead="Nhận xét:")
    add_figure(
        doc,
        "05-kb4-load-balancing.png",
        "Hình 5  Kết quả phân phối 15 đơn giữa ba consumer",
    )

    add_heading(doc, "4 Truyền thông theo nhóm bằng UDP multicast", 1)
    add_heading(doc, "4.1 Thiết kế chương trình", 2)
    add_body(
        doc,
        "Sender gửi gói JSON tới địa chỉ 224.1.1.1, cổng 5007. Mỗi gói chứa sequence, timestamp dạng ISO và thời gian epoch. Receiver join multicast group, ghi thời điểm nhận và tính độ trễ. Khi chạy nhiều receiver trên cùng máy, tất cả receiver bind cùng cổng 5007 và bật SO_REUSEADDR.",
    )

    add_heading(doc, "4.2 KB1 Nhiều tiến trình cùng nhận", 2)
    add_body(doc, "Ba receiver được khởi động trước sender. Sender phát một lần cho mỗi sequence từ 0 đến 4.")
    multicast_table = doc.add_table(rows=1, cols=4)
    for index, value in enumerate(("Receiver", "Số gói nhận", "Sequence đầu", "Sequence cuối")):
        multicast_table.rows[0].cells[index].text = value
    for name in ("receiver-1", "receiver-2", "receiver-3"):
        cells = multicast_table.add_row().cells
        cells[0].text = name
        cells[1].text = "5"
        cells[2].text = "0"
        cells[3].text = "4"
    multicast_table.columns[0].width = Inches(2.5)
    multicast_table.columns[1].width = Inches(1.5)
    multicast_table.columns[2].width = Inches(1.35)
    multicast_table.columns[3].width = Inches(1.35)
    style_table(multicast_table, center_columns={1, 2, 3})
    add_body(doc, "Kết quả: cả ba receiver nhận đủ 5/5 gói có nội dung giống nhau, trong khi sender chỉ phát mỗi sequence một lần.", bold_lead="Kết quả:")
    add_figure(
        doc,
        "06-multicast-three-receivers.png",
        "Hình 6  Ba receiver đều nhận đủ năm gói multicast",
        width=6.2,
    )

    add_heading(doc, "4.3 KB2 Receiver tham gia muộn", 2)
    add_body(doc, "Sender được khởi động trước. Sau khoảng một giây, receiver mới tham gia multicast group.")
    add_body(
        doc,
        "Kết quả: receiver đầu tiên nhận seq=5, sau đó nhận seq=6 và seq=7. Các sequence 0-4 đã gửi trước khi receiver join không được phát lại.",
        bold_lead="Kết quả:",
    )
    add_figure(
        doc,
        "07-multicast-late-receiver.png",
        "Hình 7  Receiver tham gia muộn bắt đầu nhận từ sequence 5",
        width=6.2,
    )

    add_heading(doc, "4.4 KB3 Quan sát lưu lượng bằng Wireshark", 2)
    add_body(
        doc,
        "TShark được dùng để ghi đồng thời giao diện loopback, Wi-Fi và Ethernet vào tệp captures/multicast-kb3.pcapng trong lúc sender phát 5 bản tin. Do cùng một gói có thể xuất hiện trên nhiều giao diện trong tệp pcapng, điều kiện frame.interface_id == 1 chọn riêng giao diện Wi-Fi để tránh đếm trùng.",
    )
    add_command(doc, "ip.dst == 224.1.1.1 && udp.dstport == 5007 && frame.interface_id == 1")
    wireshark_table = doc.add_table(rows=1, cols=5)
    for index, value in enumerate(("Frame", "Thời gian (s)", "Nguồn", "Đích", "UDP đích")):
        wireshark_table.rows[0].cells[index].text = value
    for frame, timestamp in (("22", "1,110717"), ("69", "1,612063"), ("76", "2,113411"), ("118", "2,614761"), ("179", "3,115761")):
        cells = wireshark_table.add_row().cells
        for index, value in enumerate((frame, timestamp, "172.16.9.226", "224.1.1.1", "5007")):
            cells[index].text = value
    wireshark_table.columns[0].width = Inches(0.7)
    wireshark_table.columns[1].width = Inches(1.2)
    wireshark_table.columns[2].width = Inches(1.6)
    wireshark_table.columns[3].width = Inches(1.6)
    wireshark_table.columns[4].width = Inches(1.0)
    style_table(wireshark_table, center_columns={0, 1, 2, 3, 4})
    add_body(
        doc,
        "Kết quả: Wireshark hiển thị đúng 5 gói UDP trên giao diện Wi-Fi. Tất cả gói có nguồn 172.16.9.226, đích multicast 224.1.1.1 và cổng đích 5007; phần Data chứa JSON với các trường seq, sentAt và sentEpoch. Điều này xác nhận sender chỉ tạo một luồng gói multicast, không gửi riêng một bản sao cho từng receiver.",
        bold_lead="Kết quả:",
    )
    add_figure(
        doc,
        "08-wireshark-multicast.png",
        "Hình 8  Wireshark lọc được đúng năm datagram UDP multicast trên giao diện Wi-Fi",
        width=6.55,
    )

    add_heading(doc, "5 Kết luận", 1)
    add_body(
        doc,
        "Các kiểm thử cho thấy RabbitMQ lưu giữ được thông điệp persistent qua lần restart, trong khi thông điệp transient bị mất. Producer hoạt động bất đồng bộ và ba consumer chia tải đều. UDP multicast cho phép nhiều receiver nhận cùng một lần gửi nhưng không phát lại bản tin cũ cho thành viên tham gia muộn. Capture Wireshark xác nhận 5 lần gửi tạo đúng 5 datagram tới 224.1.1.1:5007 trên giao diện Wi-Fi. Log JSON Lines và tệp pcapng xác nhận toàn bộ kịch bản đều đạt yêu cầu.",
    )

    doc.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build_report().name)

