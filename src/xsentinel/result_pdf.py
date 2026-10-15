"""Portable Vietnamese result PDF, built only from an existing scoring snapshot."""
from functools import lru_cache
from importlib.resources import files
from io import BytesIO
from html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xsentinel.dashboard_presentation import explain_result, feature_rows
from xsentinel.demo_provenance import demo_comparison


@lru_cache(maxsize=1)
def _fonts():
    root = files('xsentinel').joinpath('assets/fonts')
    pdfmetrics.registerFont(TTFont('XSSans', str(root.joinpath('DejaVuSans.ttf'))))
    pdfmetrics.registerFont(TTFont('XSSansBold', str(root.joinpath('DejaVuSans-Bold.ttf'))))
    pdfmetrics.registerFontFamily('XSSans', normal='XSSans', bold='XSSansBold')


def result_pdf(result):
    _fonts()
    explanation = explain_result(result)
    comparison = demo_comparison(result)
    stream = BytesIO()
    style = ParagraphStyle('body', fontName='XSSans', fontSize=9, leading=14, spaceAfter=6,
                           textColor=colors.HexColor('#172B4D'), splitLongWords=True)
    heading = ParagraphStyle('heading', parent=style, fontName='XSSansBold', fontSize=12, leading=18, spaceBefore=12)
    title = ParagraphStyle('title', parent=heading, fontSize=20, leading=26, textColor=colors.HexColor('#087F8C'))
    def p(value, selected=style):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), selected)
    story = [p('X-SENTINEL', title), p('BÁO CÁO KẾT QUẢ PHÂN TÍCH', heading)]
    metadata = result.get('input_metadata') or {}
    experiment = result.get('experiment') or {}
    for label, value in (
        ('Đầu vào', metadata.get('name', 'Chưa lưu tên đầu vào')),
        ('Thời điểm phân tích', result.get('created_at', 'Phiên local, chưa lưu thời điểm')),
        ('Mã lần phân tích', result.get('request_id', 'Phiên local')),
        ('Bộ mô hình', result.get('dataset', 'Chưa lưu')),
        ('Chế độ', experiment.get('variant', 'full' if 'full' in result['method'] else 'reduced' if 'reduced' in result['method'] else 'Chưa lưu')),
        ('Nguồn mẫu', comparison.get('source', 'Chưa có nhãn đối chiếu được xác minh')),
    ):
        story.append(p(f'{label}: {value}'))
    if comparison['known']:
        story.extend([p('Nhãn gốc theo bộ dữ liệu: ' + comparison['expected']), p('Đối chiếu: ' + comparison['text'])])
    story.extend([p('1. Phân loại file', heading), p(explanation['classification']),
                  p(explanation['classification_explanation']),
                  p('Điểm mô hình không phải mức chắc chắn thực tế đã được kiểm chứng.'),
                  p('2. Dấu hiệu trigger', heading), p(explanation['method_label'] + ': ' + explanation['alert']),
                  p(explanation['threshold_explanation']), p(explanation['interpretation']),
                  p(explanation['method_explanation']), p('3. Đặc trưng ảnh hưởng mạnh', heading),
                  p('SHAP dương đẩy về mã độc; SHAP âm đẩy về lành trong mô hình. SHAP không phải phần trăm xác suất. Bảng gồm các đặc trưng mạnh nhất, chưa phải toàn bộ đóng góp.')])
    rows = [[p(v, heading) for v in ('Đặc điểm', 'Giá trị', 'SHAP', 'Chiều ảnh hưởng')]]
    for row in feature_rows(result):
        rows.append([p(row['title'] + '\n' + row['name']), p(f"{row['value']:.6g}"),
                     p(f"{row['shap']:+.6f}"), p(row['direction'])])
    if len(rows) > 1:
        table = Table(rows, colWidths=[230, 65, 75, 141], repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EAF4F6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOX', (0, 0), (-1, -1), .5, colors.HexColor('#CFDBE6')),
            ('INNERGRID', (0, 0), (-1, -1), .3, colors.HexColor('#CFDBE6')),
            ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
    story.extend([Spacer(1, 8), p('4. Giới hạn cách đọc kết quả', heading),
                  p('File được đọc, không được thực thi. Không có cảnh báo trigger không chứng nhận file an toàn. Nhãn gốc demo chỉ đối chiếu phân loại lành/mã độc, không chấm trigger đúng/sai.'),
                  p('Đối chiếu một mẫu không thay cho đánh giá độ chính xác toàn hệ thống.'),
                  p(f"Thời gian tính toàn bộ điểm và STRIP: {result.get('elapsed_ms', 0):.2f} ms. Chưa gồm upload, đọc PE, API/lưu, hiển thị và tạo PDF."),
                  p('GitHub: https://github.com/callmewin06-create/X-SENTINEL')])
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('XSSans', 8)
        canvas.setFillColor(colors.HexColor('#52667A'))
        canvas.drawString(42, 25, 'X-SENTINEL | Kết quả tại thời điểm phân tích')
        canvas.drawRightString(A4[0] - 42, 25, f'Trang {doc.page}')
        canvas.restoreState()
    SimpleDocTemplate(stream, pagesize=A4, rightMargin=42, leftMargin=42,
                      topMargin=35, bottomMargin=40, title='X-SENTINEL - Kết quả phân tích',
                      author='X-SENTINEL').build(story, onFirstPage=footer, onLaterPages=footer)
    return stream.getvalue()
