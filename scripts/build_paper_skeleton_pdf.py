"""Build a four-page, two-column research-paper skeleton."""
from pathlib import Path
from html import escape
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, FrameBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"/"pdf"
pdfmetrics.registerFont(TTFont("PaperTimes","C:/Windows/Fonts/times.ttf"))
pdfmetrics.registerFont(TTFont("PaperTimesBold","C:/Windows/Fonts/timesbd.ttf"))
styles={
    "title":ParagraphStyle("title",fontName="PaperTimesBold",fontSize=17,leading=20,alignment=1,spaceAfter=8),
    "author":ParagraphStyle("author",fontName="PaperTimes",fontSize=10,leading=12,alignment=1,spaceAfter=10),
    "h2":ParagraphStyle("h2",fontName="PaperTimesBold",fontSize=11,leading=13,spaceBefore=8,spaceAfter=5,keepWithNext=True),
    "h3":ParagraphStyle("h3",fontName="PaperTimesBold",fontSize=10,leading=12,spaceBefore=6,spaceAfter=3,keepWithNext=True),
    "body":ParagraphStyle("body",fontName="PaperTimes",fontSize=10,leading=12.5,spaceAfter=7,allowWidows=0,allowOrphans=0),
}
W,H=A4
margin=42
gap=20
cw=(W-2*margin-gap)/2
def footer(c,doc):
    c.setFont("PaperTimes",8)
    c.drawString(margin,25,"X-SENTINEL | Paper skeleton | 8 October 2026")
    c.drawRightString(W-margin,25,str(doc.page))

first=[Frame(margin,H-220,W-2*margin,178,id="opening",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),
       Frame(margin,45,cw,H-285,id="left",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),
       Frame(margin+cw+gap,45,cw,H-285,id="right",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)]
rest=[Frame(margin,45,cw,H-87,id="left",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),
      Frame(margin+cw+gap,45,cw,H-87,id="right",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)]
doc=BaseDocTemplate(str(OUT/"X_SENTINEL_Paper_Skeleton_EN.pdf"),pagesize=A4,
                    title="X-SENTINEL Research Paper Skeleton",author="Group 4")
doc.addPageTemplates([PageTemplate(id="first",frames=first,onPage=footer,autoNextPageTemplate="body"),
                     PageTemplate(id="body",frames=rest,onPage=footer)])
text=(OUT/"X_SENTINEL_Paper_Skeleton_EN.md").read_text(encoding="utf-8")
story=[]
for i,block in enumerate(text.split("---COLUMN---")):
    if i:story.append(FrameBreak())
    for line in block.strip().splitlines():
        line=line.strip()
        if not line:continue
        if line.startswith("# "):kind="title";line=line[2:]
        elif line.startswith("## "):kind="h2";line=line[3:]
        elif line.startswith("### "):kind="h3";line=line[4:]
        elif line.startswith("Group 4"):kind="author"
        else:kind="body"
        story.append(Paragraph(escape(line),styles[kind]))
doc.build(story)
print(OUT/"X_SENTINEL_Paper_Skeleton_EN.pdf")
