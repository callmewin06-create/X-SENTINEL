"""Render an editable Vietnamese or English report outline to PDF."""
from pathlib import Path
from html import escape
import argparse
import re
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
parser = argparse.ArgumentParser()
parser.add_argument("--english", action="store_true")
parser.add_argument("--sample", action="store_true", help="Use the previous report's section structure and typography")
args = parser.parse_args()
if args.sample:
    args.english = True
    A4 = letter
STEM = "X_SENTINEL_Report_Outline_EN" if args.english else "X_SENTINEL_Khung_Bao_Cao"
if args.sample:
    STEM = "X_SENTINEL_Report_Structure_EN"
HEADER = "X-SENTINEL | RESEARCH REPORT OUTLINE" if args.english else "X-SENTINEL | KHUNG BÁO CÁO NGHIÊN CỨU"
FOOTER = "Outline draft - 8 October 2026" if args.english else "Bản đề cương - 08/10/2026"
pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("ArialBold", "C:/Windows/Fonts/arialbd.ttf"))
NAVY = colors.HexColor("#153149")
TEAL = colors.HexColor("#137C87")
styles = {
    "h1": ParagraphStyle("h1", fontName="ArialBold", fontSize=18, leading=23, textColor=NAVY, spaceAfter=12),
    "h2": ParagraphStyle("h2", fontName="ArialBold", fontSize=13, leading=18, textColor=TEAL, spaceAfter=10),
    "h3": ParagraphStyle("h3", fontName="ArialBold", fontSize=10.7, leading=15, textColor=NAVY, spaceBefore=7, spaceAfter=4, keepWithNext=True),
    "body": ParagraphStyle("body", fontName="Arial", fontSize=10, leading=14.4, textColor=colors.HexColor("#233443"), spaceAfter=7),
    "cell": ParagraphStyle("cell", fontName="Arial", fontSize=9, leading=12.5, textColor=NAVY),
    "thead": ParagraphStyle("thead", fontName="ArialBold", fontSize=9, leading=12.5, textColor=colors.white),
}
if args.english:
    styles["body"].fontSize = 9.5
    styles["body"].leading = 13.2
    styles["body"].spaceAfter = 6
    styles["body"].allowWidows = 0
    styles["body"].allowOrphans = 0
    styles["h3"].spaceBefore = 6
    styles["h3"].spaceAfter = 3
if args.sample:
    pdfmetrics.registerFont(TTFont("TimesNR", "C:/Windows/Fonts/times.ttf"))
    pdfmetrics.registerFont(TTFont("TimesNRBold", "C:/Windows/Fonts/timesbd.ttf"))
    for name, style in styles.items():
        style.fontName = "TimesNR" if name in ("body", "cell") else "TimesNRBold"
        style.textColor = colors.black
    styles["body"].fontSize = 13
    styles["body"].leading = 16.5
    styles["body"].spaceAfter = 6
    styles["h1"].fontSize = 18
    styles["h1"].leading = 22
    styles["h1"].keepWithNext = True
    styles["h2"].fontSize = 15
    styles["h3"].fontSize = 13
    styles["h3"].leading = 16
    styles["cell"].fontSize = 11
    styles["cell"].leading = 14
    styles["thead"].fontSize = 11
    styles["thead"].leading = 14

def para(text, kind="body"):
    return Paragraph(escape(text), styles[kind])

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.states = []
    def showPage(self):
        self.states.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        count = len(self.states)
        for state in self.states:
            self.__dict__.update(state)
            self.setFont("TimesNR" if args.sample else "Arial", 8)
            self.setFillColor(colors.black if args.sample else NAVY)
            if not args.sample:
                self.setStrokeColor(TEAL)
                self.setLineWidth(1)
                self.line(44, A4[1]-36, A4[0]-44, A4[1]-36)
                self.drawString(44, A4[1]-27, HEADER)
                self.drawString(44, 26, FOOTER)
            self.drawRightString(A4[0]-44, 26, f"{self._pageNumber} / {count}")
            super().showPage()
        super().save()

def table(lines):
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in lines]
    rows = [row for row in rows if not all(re.fullmatch(r"[: -]+", cell) for cell in row)]
    data = [[para(cell, "thead" if i == 0 else "cell") for cell in row] for i, row in enumerate(rows)]
    width = A4[0] - (113.4 if args.sample else 88)
    if len(rows[0]) == 4:
        widths = [width*.40, width*.20, width*.20, width*.20]
    elif rows[0][0] in ("Hạng mục", "Work area"):
        widths = [width*.32, width*.19, width*.49]
    elif rows[0][0] in ("View", "Method", "Question"):
        widths = [width*.23, width*.43, width*.34]
    else:
        widths = [width*.23, width*.57, width*.20]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F0F5F7"), colors.white]),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LINEBELOW", (0,0), (-1,0), .7, TEAL),
        ("LINEBELOW", (0,1), (-1,-1), .3, colors.HexColor("#DCE6EA")),
    ]))
    if args.sample:
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EEEEEE")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white]),
            ("GRID", (0,0), (-1,-1), .4, colors.black),
        ]))
    return t

content = (OUT / f"{STEM}.md").read_text(encoding="utf-8")
story = []
for page_index, block in enumerate(content.split("---PAGE---")):
    if page_index and not args.sample:
        story.append(PageBreak())
    lines = block.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("|"):
            tab = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tab.append(lines[i].strip())
                i += 1
            story.extend([table(tab), Spacer(1, 7)])
            continue
        if line.startswith("### "):
            story.append(para(line[4:], "h3"))
        elif line.startswith("## "):
            story.append(para(line[3:], "h2"))
        elif line.startswith("# "):
            story.append(para(line[2:], "h1"))
        else:
            story.append(para(line))
        i += 1

doc = SimpleDocTemplate(str(OUT / f"{STEM}.pdf"), pagesize=A4,
                        rightMargin=56.7 if args.sample else 44, leftMargin=56.7 if args.sample else 44,
                        topMargin=51 if args.sample else 50, bottomMargin=51 if args.sample else 45,
                        title="X-SENTINEL - Research Report Outline" if args.english else "X-SENTINEL - Khung báo cáo nghiên cứu",
                        author="Group 4" if args.english else "Nhóm 4")
doc.build(story, canvasmaker=NumberedCanvas)
print(OUT / f"{STEM}.pdf")
