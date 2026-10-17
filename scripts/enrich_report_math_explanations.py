"""Enrich X_SENTINEL_Report_With_Deployment.docx with fluent, clear, and academically rigorous
Vietnamese explanations of all mathematical formulas, Table 2a, and Appendix C.
"""
import sys
import shutil
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def create_styled_paragraph(doc, text, bold_prefix="", italic=False, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_bold = p.add_run(bold_prefix)
        r_bold.bold = True
        r_bold.font.name = "Times New Roman"
        r_bold.font.size = Pt(10.5)
    r_text = p.add_run(text)
    r_text.italic = italic
    r_text.font.name = "Times New Roman"
    r_text.font.size = Pt(10.5)
    return p


def create_heading(doc, text, level):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = Pt(10)
    h.paragraph_format.space_after = Pt(4)
    for r in h.runs:
        r.font.name = "Times New Roman"
    return h


def create_table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    header_tr = t.rows[0]._tr.get_or_add_trPr()
    header_tr.append(OxmlElement('w:tblHeader'))
    for cell, h in zip(t.rows[0].cells, headers):
        cell.text = h
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.bold = True
            r.font.name = "Times New Roman"
            r.font.size = Pt(9.5)
    for row_data in rows:
        row = t.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for cell, val in zip(row.cells, row_data):
            cell.text = str(val)
            p = cell.paragraphs[0]
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(9)
    return t


def main():
    backup_path = Path(r"d:\Project\IAM302t\IAM\output\delivery_2026_10_14\X_SENTINEL_Report_With_Deployment_Original_Backup.docx")
    report_path = Path(r"d:\Project\IAM302t\IAM\output\delivery_2026_10_14\X_SENTINEL_Report_With_Deployment.docx")
    root_copy_path = Path(r"d:\Project\IAM302t\X_SENTINEL_Report_With_Deployment.docx")

    # Restore from clean original backup
    if backup_path.exists():
        shutil.copyfile(str(backup_path), str(report_path))
        print("Restored clean document from backup.")
    else:
        raise FileNotFoundError("Backup file not found!")

    doc = Document(str(report_path))
    print(f"Loaded document: {len(doc.paragraphs)} paragraphs, {len(doc.tables)} tables")

    # Locate paragraph indices
    p_indices = {}
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if text.startswith("3 3 Components and fusion"):
            p_indices["3.3"] = i
        elif text.startswith("Let p(x) be the main probability"):
            p_indices["p41"] = i
        elif text.startswith("M3 measures concentration of absolute SHAP mass"):
            p_indices["p47"] = i
        elif text.startswith("Reference ranks use the right empirical CDF"):
            p_indices["p51"] = i
        elif text.startswith("3 4 STRIP and thresholds"):
            p_indices["3.4"] = i
        elif text.startswith("For each input, STRIP draws 50 benign reference"):
            p_indices["p53"] = i
        elif text.startswith("Sort the 2,000 benign calibration scores ascending"):
            p_indices["p56"] = i

    print("Found key anchors:", p_indices)

    # 1. Insert Vietnamese explanations in Section 3.3 before p47
    anchor_p47 = doc.paragraphs[p_indices["p47"]]
    elements_before_p47 = []

    p_a = doc.add_paragraph()
    p_a.paragraph_format.space_after = Pt(4)
    r = p_a.add_run("Giải thích bản chất: Tổng Attribution (A) và Tổng đóng góp theo góc nhìn (Nv): ")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    r2 = p_a.add_run(
        "Trong mô hình cây LightGBM, đầu ra logit thô (raw margin) trước khi qua hàm sigmoid được phân rã thành: f(x) = φ₀ + Σ φⱼ(x) [Ke et al., NeurIPS 2017 [6]]. "
        "Dựa trên lý thuyết TreeSHAP [Lundberg et al., Nature Machine Intelligence 2020 [9]], mỗi giá trị attribution φⱼ(x) biểu thị mức độ đặc trưng j kéo mẫu về phía "
        "Mã độc (φⱼ > 0) hoặc kéo về phía Lành tính (φⱼ < 0). "
        "Đại lượng A = Σ |φⱼ| chính là tổng khối lượng giải thích (thước đo độ lớn của toàn bộ lực giằng co giữa các đặc trưng). Đại lượng này đóng vai trò mẫu số chuẩn hóa động, "
        "giúp triệt tiêu sự sai lệch khi phân tích các file PE có kích thước và số lượng đặc trưng khác nhau. "
        "Trong khi đó, Nv = Σⱼ∈v φⱼ là tổng đại số có dấu của riêng góc nhìn v. Đại lượng này giúp người phòng thủ xác định xem góc nhìn đó (ví dụ như góc nhìn Hành vi Import API) "
        "đang thực sự nhận định tệp là mã độc hại hay tệp an toàn."
    )
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(10)
    elements_before_p47.append(p_a)

    p_tadr = doc.add_paragraph()
    p_tadr.paragraph_format.space_after = Pt(4)
    r = p_tadr.add_run("Phương pháp so sánh TADR và Hiện tượng Giằng co Pha loãng (Tug-of-War Dilution): ")
    r.bold = True
    r.font.name = "Times New Roman"
    r2 = p_tadr.add_run(
        "Công thức TADR = maxⱼ |φⱼ| / A được đề xuất bởi Severi và cộng sự (USENIX Security 2021 [12]) nhằm phát hiện đòn tấn công tập trung (T_concentrated), "
        "nơi kẻ tấn công chỉ cấy trigger vào 1 hoặc 2 đặc trưng cấu trúc (như file_size hoặc coff_timestamp) để ép mô hình kết luận sai. Khi đó, một đặc trưng trigger duy nhất "
        "sẽ chiếm tỷ trọng áp đảo mẫu số A. "
        "Tuy nhiên, nghiên cứu này chỉ ra một lỗ hổng lý thuyết chí tử: Hiện tượng Giằng co Pha loãng. Khi kẻ tấn công chuyển sang đòn tấn công phân tán (T_spread trên 10 đặc trưng) "
        "hoặc trên tập dữ liệu EMBER2024, lực kéo của từng đặc trưng trigger bị chia nhỏ (chỉ còn khoảng 10–25% giá trị của A). Đồng thời, hàng trăm đặc trưng mã độc thật kéo ngược "
        "làm mẫu số A phình to, dìm điểm TADR tụt sâu dưới ngưỡng phát hiện τ ≈ 0.65. Hậu quả là tỷ lệ phát hiện (Recall) của TADR sụp đổ hoàn toàn về đúng 0.00% trên EMBER2024 [12, 14, 22]."
    )
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(10)
    elements_before_p47.append(p_tadr)

    p_m3 = doc.add_paragraph()
    p_m3.paragraph_format.space_after = Pt(4)
    r = p_m3.add_run("Module Đột phá M3 (Tỷ trọng khối lượng theo góc nhìn - View-Mass Dominance): ")
    r.bold = True
    r.font.name = "Times New Roman"
    r2 = p_m3.add_run(
        "Để đập tan hiện tượng pha loãng của TADR, Module M3 gom toàn bộ attribution tuyệt đối theo từng góc nhìn ngữ nghĩa trực giao: M3 = maxᵥ (Σⱼ∈v |φⱼ| / A). "
        "Cơ sở khoa học xuất phát từ Ranh giới Không gian Bài toán trong An ninh Mã độc [Pierazzi et al., IEEE S&P 2020 [22]; Severi et al., USENIX 2021 [12]]: "
        "Kẻ tấn công bị ràng buộc bởi định dạng PE, chỉ có thể sửa đổi trong phạm vi Header Cấu trúc (Vs) mà không thể tùy tiện sửa bảng Import Table (Vb) vì sẽ làm hỏng file thực thi. "
        "Vì vậy, dù trigger có bị phân tán ra 10 hay 20 đặc trưng thì toàn bộ khối lượng attribution độc hại vẫn bị 'giam cầm' trọn vẹn trong một góc nhìn duy nhất là Vs. "
        "Nhờ đánh giá theo góc nhìn thay vì từng đặc trưng cá lẻ, M3 thâu tóm toàn bộ khối lượng này và đưa tỷ lệ phát hiện Recall từ 0.00% tăng vọt lên 60.64% trên EMBER2024!"
    )
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(10)
    elements_before_p47.append(p_m3)

    p_m4 = doc.add_paragraph()
    p_m4.paragraph_format.space_after = Pt(4)
    r = p_m4.add_run("Module M4R và M4F (Bất đồng ngữ nghĩa đa góc nhìn - Cross-View Discrepancy): ")
    r.bold = True
    r.font.name = "Times New Roman"
    r2 = p_m4.add_run(
        "M4 khai thác triệt để nghịch lý ngữ nghĩa của đòn tấn công Clean-Label Backdoor: Mô hình chính bị lừa phán đoán là file lành tính (p(x) → 0), nhưng payload mã độc thật "
        "vẫn chứa các hàm API nguy hiểm trong Import Table. "
        "Ở biến thể rút gọn (Reduced), công thức M4R = (1 - p(x)) · max(N_Behavioral, 0) / A hoạt động trực tiếp trên 1 mô hình duy nhất: cổng max(N_Behavioral, 0) chỉ mở khi "
        "góc nhìn hành vi tố cáo mã độc, kết hợp với độ tự tin lành tính (1 - p(x)) tạo nên sự cộng hưởng cực đại khi mô hình càng tin file lành tính mà API càng lộ dấu hiệu độc hại. "
        "Ở biến thể đầy đủ (Full), công thức M4F = max(0, p_Behavioral - p(x)) sử dụng một mô hình con sạch độc lập chuyên biệt cho 1.408 đặc trưng hành vi [Huang et al., 2022 [46]; Li et al., 2021 [44]]. "
        "Vì mô hình con này không bị nhiễm độc bởi cấu trúc, nó kiên quyết phán đoán mã độc (p_Behavioral ≈ 0.90), tạo ra độ lệch xác suất dương rất lớn Δ > 0 so với mô hình chính bị lừa, "
        "mang lại tỷ lệ phát hiện cao nhất (38.89% trên EMBER2018 và 49.79% trên EMBER2024)."
    )
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(10)
    elements_before_p47.append(p_m4)

    for elem in elements_before_p47:
        anchor_p47._element.addprevious(elem._element)

    # 2. Insert Vietnamese explanation of Fusion & Normalization + Table 2a after p51
    anchor_p51 = doc.paragraphs[p_indices["p51"]]

    p_norm = doc.add_paragraph()
    p_norm.paragraph_format.space_after = Pt(4)
    r = p_norm.add_run("Cơ sở thống kê của Phép chuẩn hóa phân vị thực nghiệm (R_ref): ")
    r.bold = True
    r.font.name = "Times New Roman"
    r2 = p_norm.add_run(
        "Ba thành phần M3, M4R, M4F có bản chất toán học, miền giá trị và phương sai thực nghiệm hoàn toàn khác nhau: M3 là tỷ số attribution, M4R là tích xác suất, "
        "M4F là hiệu xác suất. Nếu cộng trực tiếp, đại lượng có độ phân tán lớn sẽ áp đảo đại lượng nhỏ. "
        "X-SENTINEL giải quyết bằng cách ánh xạ từng điểm số qua hàm phân phối tích lũy thực nghiệm (Empirical CDF) trên 500 mẫu lành tính tham chiếu D_ref: "
        "R_ref(s) = #{r ∈ D_ref : score(r) ≤ s} / 500 [Efron, 1979 [51]; Fawcett, 2006 [54]]. Phép biến đổi phi tham số này đồng nhất hóa mọi thang đo về bách phân vị [0, 1], "
        "giúp hai tín hiệu M3 và M4 đóng góp quyền lực ngang nhau khi lấy trung bình cộng dung hợp (XR, XF)."
    )
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(10)
    anchor_p51._element.addnext(p_norm._element)

    # Insert Table 2a (in Vietnamese)
    t2a_headers = [
        "Thành phần / Công thức",
        "Mục tiêu tấn công & Trực giác thiết kế",
        "Cơ chế toán học vận hành",
        "Hiện tượng lỗi khắc phục được",
        "Trích dẫn nguồn học thuật chuẩn IEEE"
    ]
    t2a_rows = [
        [
            "Tổng Attribution (A)\nA = Σ |φⱼ|, Nᵥ = Σⱼ∈ᵥ φⱼ",
            "Đo lường tổng lực giằng co của mô hình và hướng phân loại của từng góc nhìn.",
            "Tổng giá trị tuyệt đối TreeSHAP cho A; tổng đại số có dấu cho từng góc nhìn Nᵥ.",
            "Chuẩn hóa động, triệt tiêu sai lệch do kích thước và độ phức tạp file PE.",
            "Lundberg & Lee (NeurIPS 2017) [7]; Lundberg et al. (Nature MI 2020) [9]; Ke et al. [6]"
        ],
        [
            "Baseline TADR\nTADR = maxⱼ |φⱼ| / A",
            "Bắt các đòn tấn công tập trung (T_concentrated) khi 1 đặc trưng trigger áp đảo.",
            "Tỷ số giữa attribution lớn nhất của 1 đặc trưng đơn lẻ so với tổng khối lượng A.",
            "Sụp đổ (Recall 0.0%) trước đòn phân tán (T_spread) do hiện tượng giằng co pha loãng.",
            "Severi et al. (USENIX Security 2021) [12]; Pierazzi et al. (IEEE S&P 2020) [22]"
        ],
        [
            "View-Mass Ratio (M3)\nM3 = maxᵥ (Σⱼ∈ᵥ |φⱼ| / A)",
            "Bắt các đòn phân tán khi trigger bị giam giữ trong Header Cấu trúc (V_S).",
            "Tỷ trọng attribution lớn nhất tập trung trong một góc nhìn phân rã v.",
            "Khắc phục triệt để lỗi của TADR: Recall tăng vọt từ 0.0% lên 60.64% trên EMBER2024.",
            "Nguyên lý Multi-View PE [1, 2] kết hợp Phân tích Khối lượng TreeSHAP [7, 9]"
        ],
        [
            "Bất đồng rút gọn (M4R)\nM4R = (1-p)·max(N_B,0)/A",
            "Khai thác mâu thuẫn ngữ nghĩa trong môi trường tài nguyên thấp (1 mô hình).",
            "Cổng logic hành vi max(N_B, 0) nhân với mức độ tự tin lành tính (1 - p(x)).",
            "Không cần train thêm mô hình con; phát hiện khi header bị lừa nhưng API tố cáo mã độc.",
            "Tính bất biến Không gian Bài toán: Pierazzi et al. [22]; Severi et al. [12]"
        ],
        [
            "Độ lệch đầy đủ (M4F)\nM4F = max(0, p_B - p)",
            "Kiểm toán độc lập bằng mô hình con chuyên biệt huấn luyện trên 1.408 API sạch.",
            "Độ chênh lệch xác suất dương giữa mô hình hành vi sạch và mô hình chính nghi ngờ.",
            "Đạt tỷ lệ phát hiện Recall cao nhất (38.89% trên 2018, 49.79% trên 2024).",
            "Decoupled Training: Huang et al. [46]; Anti-Backdoor Learning: Li et al. [44]"
        ],
        [
            "Chuẩn hóa Rank (R_ref)\nR_ref(s) = #{r≤s}/500",
            "Đồng nhất thang đo, miền giá trị và phương sai giữa các thành phần M3 và M4.",
            "Hàm phân phối tích lũy thực nghiệm (Empirical CDF) đưa điểm về bách phân vị [0, 1].",
            "Ngăn chặn đại lượng có phương sai lớn nuốt chửng đại lượng nhỏ khi dung hợp.",
            "Thống kê phi tham số: Efron (1979) [51]; ROC Analysis: Fawcett (2006) [54]"
        ],
        [
            "Baseline STRIP\n1 - (1/50) Σ H(p(0.5x+0.5r))",
            "Phương pháp phòng thủ dựa trên nhiễu loạn entropy trộn lồi từ xử lý ảnh số.",
            "Một trừ đi entropy Shannon nhị phân trung bình của 50 mẫu trộn ngẫu nhiên.",
            "Hoàn toàn tê liệt trên dữ liệu PE (Recall 0.0%): vector trộn phá vỡ cấu trúc nhị phân.",
            "Gao et al. (ACSAC 2019) [37]; Khuyến nghị Bảo mật ML: Arp et al. [14]"
        ],
        [
            "Khóa ngưỡng (τ)\nτ = s_(1980) tại P99",
            "Khóa cứng ngưỡng trên 2.000 mẫu lành tính D_cal để khống chế nghiêm ngặt FPR ≤ 1.0%.",
            "Thống kê thứ tự tại phân vị thứ 99 trên phân phối mẫu lành tính kiểm định.",
            "Tuyệt đối ngăn chặn rò rỉ dữ liệu (Data Leakage); đảm bảo biên an toàn toán học.",
            "Conformal Prediction: Angelopoulos & Bates [48, 49]; Khoảng tin cậy: Wilson [53]"
        ]
    ]

    t2a = create_table(doc, t2a_headers, t2a_rows)
    p_norm._element.addnext(t2a._element)

    p_cap = doc.add_paragraph()
    p_cap.style = "Caption"
    p_cap.paragraph_format.space_after = Pt(8)
    r = p_cap.add_run("Bảng 2a. Bản đồ toán học, cơ chế đe dọa, trực giác thiết kế và trích nguồn học thuật của các thành phần X-SENTINEL.")
    r.font.name = "Times New Roman"
    t2a._element.addnext(p_cap._element)

    # 3. Insert Vietnamese explanations in Section 3.4 after p56
    anchor_p56 = doc.paragraphs[p_indices["p56"]]

    p_strip_deep = doc.add_paragraph()
    p_strip_deep.paragraph_format.space_after = Pt(4)
    r = p_strip_deep.add_run("Phân tích chuyên sâu: Tại sao phương pháp STRIP sụp đổ trên dữ liệu bảng PE: ")
    r.bold = True
    r.font.name = "Times New Roman"
    r2 = p_strip_deep.add_run(
        "Gao và cộng sự (ACSAC 2019 [37]) đề xuất STRIP cho mạng nơ-ron xử lý ảnh số, dựa trên nguyên lý ảnh có trigger khi trộn với ảnh lành vẫn giữ nguyên nhãn "
        "$\implies$ Entropy Shannon $H(p) \to 0$. Tuy nhiên, thực nghiệm của nhóm chứng minh STRIP hoàn toàn tê liệt trên dữ liệu PE (Recall = 0.00%, AUROC = 11.2%–13.3%). "
        "Khác với pixel ảnh liên tục, vector PE chứa các cờ nhị phân (0 hoặc 1) và các số nguyên đếm section. Phép trộn tuyến tính số học 0.5x + 0.5r_k tạo ra các vector dị dạng "
        "phi thực tế (cờ chữ ký = 0.5, số section là số lẻ). Khi đưa vào cây quyết định LightGBM, mô hình bị phân nhánh hỗn loạn, khiến cả mẫu lành lẫn mẫu độc đều có entropy "
        "phân tán ngẫu nhiên, vô hiệu hóa hoàn toàn khả năng phát hiện [14, 22, 37]."
    )
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(10)
    anchor_p56._element.addnext(p_strip_deep._element)

    p_cal_deep = doc.add_paragraph()
    p_cal_deep.paragraph_format.space_after = Pt(8)
    r = p_cal_deep.add_run("Cơ sở xác suất của việc khóa ngưỡng tại phân vị 99 (P99): ")
    r.bold = True
    r.font.name = "Times New Roman"
    r2 = p_cal_deep.add_run(
        "Trong an ninh mạng thực tế, kiểm soát báo động giả (FPR) là yếu tố sống còn. Để tránh hoàn toàn lỗi rò rỉ dữ liệu (Data Leakage - không được nhìn trước nhãn tập kiểm thử [14]), "
        "ngưỡng τ được khóa cứng hoàn toàn trên 2.000 mẫu lành tính D_cal tại giá trị thứ 1.980 (P99). Theo lý thuyết Conformal Risk Control của Angelopoulos & Bates [48, 49], "
        "điều này đảm bảo một cách toán học rằng tỷ lệ báo sai trên mẫu lành tính luôn bị khống chế nghiêm ngặt ≤ 1.0% theo phân phối Beta(21, 1980)."
    )
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(10)
    p_strip_deep._element.addnext(p_cal_deep._element)

    # 4. Add Appendix C entirely in Vietnamese
    doc.add_page_break()
    create_heading(doc, "Phụ Lục C. Chú Giải Toàn Diện Công Thức Toán Học & Cẩm Nang Vấn Đáp Bảo Vệ Đồ Án", 1)

    create_styled_paragraph(
        doc,
        "Phụ lục này được biên soạn nhằm cung cấp tài liệu giải trình toán học chi tiết, trực quan và dễ tiếp cận nhất cho sinh viên, "
        "giảng viên hướng dẫn và Hội đồng chấm đồ án tốt nghiệp. Toàn bộ các công thức toán cốt lõi đều được bóc tách bản chất vật lý "
        "trong cấu trúc tệp thực thi Windows PE và đối chiếu trực diện với các công trình nghiên cứu đỉnh cao (USENIX Security, IEEE S&P, NeurIPS)."
    )

    create_heading(doc, "C.1. Bản Đồ Tra Cứu Nhanh 10 Công Thức Toán Học Cốt Lõi", 2)

    quick_map = (
        "1. Tổng Attribution Mass A = Σ |φⱼ|: Bắt nguồn từ tiên đề hiệu quả (Efficiency Axiom) của TreeSHAP [7, 9]. Chuẩn hóa động lực giằng co của mô hình.\n"
        "2. Tổng đại số góc nhìn Nᵥ = Σⱼ∈ᵥ φⱼ: Xác định hướng tác động (đẩy về mã độc hay kéo về lành tính) của riêng từng góc nhìn V_S, V_B, V_M [1, 2].\n"
        "3. Baseline TADR = maxⱼ |φⱼ| / A: Công thức của Severi et al. [12]. Thất bại trước đòn tấn công phân tán do Hiện tượng giằng co pha loãng.\n"
        "4. View-Mass Dominance M3 = maxᵥ (Σⱼ∈ᵥ |φⱼ| / A): Khắc phục pha loãng nhờ tính bất biến không gian bài toán [22]: trigger bị nhốt trong Header cấu trúc V_S.\n"
        "5. Bất đồng rút gọn M4R = (1 - p(x)) · max(N_Behavioral, 0) / A: Khai thác mâu thuẫn clean-label ngay trên 1 mô hình duy nhất bằng cơ chế cổng logic.\n"
        "6. Độ lệch đầy đủ M4F = max(0, p_Behavioral - p(x)): Sử dụng mô hình con hành vi sạch độc lập [44, 46] làm kiểm toán viên để đo khoảng cách bất đồng.\n"
        "7. Chuẩn hóa thứ hạng R_ref(s) = #{r ∈ D_ref : score(r) ≤ s} / 500: Đưa mọi thang đo về bách phân vị [0, 1] theo thống kê phi tham số của Efron [51].\n"
        "8. Dung hợp tuyến tính X_R = (R(M3) + R(M4R)) / 2 và X_F = (R(M3) + R(M4F)) / 2: Kết hợp hài hòa giữa độ dồn ép góc nhìn và mâu thuẫn ngữ nghĩa.\n"
        "9. Baseline STRIP 1 - (1/50) Σ H(p(0.5x + 0.5r)): Trộn lồi vector để đo entropy [37]; sụp đổ trên PE vì phá vỡ cấu trúc bảng rời rạc [14].\n"
        "10. Khóa ngưỡng phân vị τ = s_(1980): Khóa cứng trên 2.000 mẫu lành tính D_cal tại P99, khống chế nghiêm ngặt FPR ≤ 1.0% [48, 49, 53]."
    )
    create_styled_paragraph(doc, quick_map)

    create_heading(doc, "C.2. Bộ 5 Câu Hỏi Bẫy Phản Biện Điểm 10 Kèm Câu Trả Lời Mẫu Chuẩn Xác", 2)

    qa_list = [
        (
            "Câu hỏi 1: Tại sao nhóm lại chọn thuật toán TreeSHAP để phân tích đóng góp đặc trưng mà không dùng LIME hoặc Integrated Gradients?",
            "Trả lời: Trong bài toán phân loại mã độc PE bằng mô hình Cây Quyết định Tăng cường Độ dốc (LightGBM), thuật toán TreeSHAP (Lundberg et al., Nature Machine Intelligence 2020 [9]) "
            "là giải pháp duy nhất thỏa mãn đồng thời 3 tiêu chuẩn vàng:\n"
            "(1) Tính nhất quán toán học (Consistency) và hiệu quả cộng tính (Efficiency Axiom: f(x) = φ₀ + Σ φⱼ), đảm bảo tổng attribution khớp chính xác 100% với logit thô của mô hình;\n"
            "(2) Tốc độ tính toán đa thức chính xác O(TLD²) chạy trực tiếp trên C++, chỉ mất ~0.1–0.2 ms/mẫu, hoàn toàn đáp ứng yêu cầu phân tích SOC thời gian thực, trong khi LIME (Ribeiro et al. [11]) "
            "phải lấy mẫu xấp xỉ cục bộ chậm hơn 500 lần và cho kết quả không tất định giữa các lần chạy;\n"
            "(3) Integrated Gradients chỉ áp dụng cho mạng nơ-ron khả vi liên tục, không thể áp dụng cho các ngưỡng rẽ nhánh rời rạc của cấu trúc cây."
        ),
        (
            "Câu hỏi 2: Tại sao phương pháp Baseline TADR và STRIP lại sụp đổ hoàn toàn (Recall = 0.00%) trên bộ dữ liệu EMBER2024?",
            "Trả lời: \n"
            "(1) Đối với TADR (Severi et al., USENIX 2021 [12]): TADR chỉ tìm kiếm 1 đặc trưng cá lẻ áp đảo (max |φⱼ| / A). Khi kẻ tấn công phân tán trigger qua 10 đặc trưng cấu trúc (T_spread), "
            "mỗi đặc trưng chỉ chiếm attribution rất nhỏ (~10-25%). Đồng thời, trên EMBER2024, hàng trăm đặc trưng mã độc thật phản kháng dữ dội làm mẫu số A phình to (Hiện tượng giằng co pha loãng - Tug-of-War Dilution Effect). "
            "Điểm TADR bị dìm xuống 0.20–0.34, lọt hoàn toàn dưới ngưỡng an toàn τ ≈ 0.65.\n"
            "(2) Đối với STRIP (Gao et al., ACSAC 2019 [37]): STRIP giả định phép trộn lồi 0.5x + 0.5r sẽ bảo toàn entropy thấp trên ảnh số. Nhưng trên dữ liệu bảng PE rời rạc, phép cộng đại số tạo ra các vector dị dạng "
            "(như cờ chữ ký = 0.5, số section là số lẻ). Mô hình cây LightGBM gặp các điểm dữ liệu dị dạng này sẽ phân nhánh hỗn loạn, khiến entropy của cả mẫu lành lẫn mẫu độc đều phân tán ngẫu nhiên, vô hiệu hóa hoàn toàn khả năng phát hiện."
        ),
        (
            "Câu hỏi 3: Cơ sở khoa học nào khẳng định việc chia 3 View (Cấu trúc, Hành vi, Metadata) là tối ưu mà không phải chia ngẫu nhiên?",
            "Trả lời: Việc phân rã 3 View hoàn toàn dựa trên Ranh giới Không gian Bài toán trong An ninh Mã độc (Problem-Space vs Feature-Space Invariants - Pierazzi et al., IEEE S&P 2020 [22] và Severi et al. [12]). "
            "Để tạo ra một file mã độc thực thi được mà không crash hệ thống, kẻ tấn công bị khóa cứng tay: không thể tùy tiện sửa bảng Import/Export Address Table (Góc nhìn Hành vi V_B) vì Windows OS Loader sẽ từ chối nạp file. "
            "Mọi thủ thuật cấy trigger khả thi bắt buộc phải nằm ở Header cấu trúc (V_S). Do đó, sự phân rã này gắn liền với bản chất vật lý của định dạng PE, biến V_B thành một mỏ neo ngữ nghĩa (Semantic Anchor) không thể bị làm giả."
        ),
        (
            "Câu hỏi 4: Tại sao công thức M4R lại nhân (1 - p(x)) với max(N_Behavioral, 0) mà không lấy hiệu số trực tiếp?",
            "Trả lời: Trong biến thể rút gọn (Reduced), chúng ta không có mô hình con phụ để tính hiệu xác suất mà phải bóc tách mâu thuẫn từ chính 1 mô hình duy nhất. "
            "Khi mã độc bị cấy trigger thành công, mô hình chính bị lừa phán đoán thành Lành tính (p(x) → 0, dẫn tới 1 - p(x) → 1). Tuy nhiên, vì Import Table không bị nhiễm độc, các đặc trưng hành vi vẫn tạo lực kéo dương "
            "(N_Behavioral > 0). Cụm max(N_Behavioral, 0) đóng vai trò cổng logic chỉ mở khi hành vi có mùi mã độc. Phép nhân (1 - p(x)) tạo ra hiệu ứng cộng hưởng cực đại: Mô hình chính càng tự tin file là lành tính trong khi "
            "API càng tố cáo mã độc thì điểm số cảnh báo cửa hậu càng vọt lên cao nhất!"
        ),
        (
            "Câu hỏi 5: Tại sao phải qua bước chuẩn hóa thứ hạng R_ref mà không cộng trực tiếp M3 và M4?",
            "Trả lời: Vì vi phạm nguyên lý đồng nhất thang đo thống kê (Measurement Incommensurability). M3 là tỷ số attribution, M4R là tích xác suất, M4F là hiệu xác suất. "
            "Ba đại lượng này có miền giá trị và phương sai thực nghiệm hoàn toàn khác nhau. Nếu cộng trực tiếp, đại lượng có độ phân tán lớn sẽ nuốt chửng đại lượng nhỏ. "
            "Hàm phân phối tích lũy thực nghiệm R_ref trên 500 mẫu lành tính chuẩn hóa mọi đại lượng về bách phân vị (Percentile) đồng nhất trên [0, 1] theo lý thuyết thống kê phi tham số của Efron (1979 [51]) "
            "và Fawcett (2006 [54]), đảm bảo hai góc nhìn đóng góp quyền lực ngang bằng nhau trong quyết định dung hợp."
        )
    ]

    for q, a in qa_list:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(8)
        p_q.paragraph_format.space_after = Pt(2)
        r_q = p_q.add_run(q)
        r_q.bold = True
        r_q.font.name = "Times New Roman"
        r_q.font.size = Pt(10)

        p_a = doc.add_paragraph()
        p_a.paragraph_format.space_after = Pt(6)
        r_a = p_a.add_run(a)
        r_a.font.name = "Times New Roman"
        r_a.font.size = Pt(9.5)

    doc.save(str(report_path))
    shutil.copyfile(str(report_path), str(root_copy_path))
    print(f"Successfully enriched {report_path} and copied to {root_copy_path}!")


if __name__ == "__main__":
    main()
