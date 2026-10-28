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
from xsentinel.dashboard_exports import (input_hash_rows,local_timestamp,classification_label,
    trigger_label,timing_description,LOCAL_TZ)
from datetime import datetime


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
    for label,value in input_hash_rows(result):
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
                  p('Ngưỡng được hiệu chỉnh trên tập calibration lành; mục tiêu FPR 1% không bảo đảm FPR của dữ liệu mới. Trigger phân tán hoặc thích nghi đa view vẫn có thể vượt qua các tín hiệu của detector.'),
                  p(timing_description(result)+': '+(f"{result['elapsed_ms']:.2f} ms" if result.get('elapsed_ms') is not None else 'Chưa lưu')+'. Chưa gồm upload, đọc PE, API/lưu, hiển thị và tạo PDF.'),
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


def history_pdf(records,created_at=None,limit=100):
    """Export exactly the supplied list snapshot, never query or rescore records."""
    if not records or len(records)>limit or not 1<=limit<=100:
        raise ValueError('Use 1 to 100 displayed history records')
    _fonts()
    stream=BytesIO()
    body=ParagraphStyle('history-body',fontName='XSSans',fontSize=8,leading=12,
                        textColor=colors.HexColor('#172B4D'),splitLongWords=True)
    head=ParagraphStyle('history-head',parent=body,fontName='XSSansBold')
    title=ParagraphStyle('history-title',parent=head,fontSize=17,leading=23,spaceAfter=12)
    def p(value,style=body): return Paragraph(escape(str(value)).replace('\n','<br/>'),style)
    stamp=created_at or datetime.now(LOCAL_TZ).isoformat()
    story=[p('X-SENTINEL',title),p('LỊCH SỬ PHÂN TÍCH ĐANG HIỂN THỊ',head),Spacer(1,8),
           p('Thời điểm xuất: '+local_timestamp(stamp)+' · Asia/Bangkok'),
           p(f'Phạm vi: {len(records)} bản ghi theo đúng thứ tự đang hiển thị; danh sách giới hạn {limit} bản gần nhất. Đây không phải toàn bộ database.'),
           p('Phân loại file và cảnh báo trigger là hai kết quả riêng. Thiếu dữ liệu được ghi Chưa lưu. PDF dùng dữ liệu đã lưu, không phân tích lại.'),Spacer(1,10)]
    rows=[[p(v,head) for v in ('STT','Thời gian','Đầu vào và mã lần phân tích','Bộ mô hình và chế độ','Phân loại','Trigger')]]
    for i,row in enumerate(records,1):
        metadata=row.get('input_metadata') or {}
        identity=row.get('request_id') or 'Chưa lưu'
        name=metadata.get('name') or 'Chưa lưu tên đầu vào'
        model=str(row.get('dataset') or 'Chưa lưu')+'\n'+str(row.get('variant') or 'Chưa lưu chế độ')
        rows.append([p(i),p(local_timestamp(row.get('created_at'))),p(name+'\n'+identity),p(model),
                     p(classification_label(row.get('main_classification'))),p(trigger_label(row.get('backdoor_alert')))])
    table=Table(rows,colWidths=[30,79,154,96,79,73],repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF4F6')),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D9D9D9')),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.append(table)
    def footer(canvas,doc):
        canvas.setFont('XSSans',8)
        canvas.drawString(42,24,'X-SENTINEL | Lịch sử đã lưu | Asia/Bangkok')
        canvas.drawRightString(A4[0]-42,24,f'Trang {doc.page}')
    SimpleDocTemplate(stream,pagesize=A4,leftMargin=42,rightMargin=42,topMargin=35,bottomMargin=40,
        title='X-SENTINEL - Lịch sử phân tích',author='X-SENTINEL').build(story,onFirstPage=footer,onLaterPages=footer)
    return stream.getvalue()
