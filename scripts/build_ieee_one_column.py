"""Format a preserved copy of the research/deployment manuscript to the supplied PDF."""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path('tmp/ieee_2026_10_16')
OUT = Path('output/ieee_2026_10_16')
SOURCE = Path('output/delivery_2026_10_14/X_SENTINEL_Report_With_Deployment.docx')
TEMPLATE = Path('C:/Users/win9tui/Downloads/632780296-IEEE-Template-1col.pdf')
TARGET = OUT / 'X_SENTINEL_IEEE_1col.docx'
OUT.mkdir(parents=True, exist_ok=True)
catalog = json.loads(Path('output/revision_2026_10_13/references/catalog.json').read_text(encoding='utf-8'))
doc = Document(SOURCE)
source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

def roman(n):
    result = ''
    for value, token in [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
        while n >= value:
            result += token; n -= value
    return result

ref_paras = [p for p in doc.paragraphs if re.match(r'^\[\d+\]', p.text)]
assert len(ref_paras) == len(catalog) == 58
ref_elements = {p._p for p in ref_paras}
body_paras = [p for p in doc.paragraphs if p._p not in ref_elements]
old_order = []
pattern = re.compile(r'\[(\d+(?:,\s*\d+)*)\]')
for p in body_paras:
    for match in pattern.finditer(p.text):
        for n in map(int, re.findall(r'\d+', match[1])):
            assert 1 <= n <= 58
            if n not in old_order:
                old_order.append(n)
assert len(old_order) == 58
mapping = {old: new for new, old in enumerate(old_order, 1)}

def replace_span(p, start, end, replacement):
    """Replace visible Word text only; retain fields, bookmarks, math and drawings."""
    nodes = p._p.xpath('.//w:t')
    offset = 0; started = False
    for node in nodes:
        value = node.text or ''; nxt = offset + len(value)
        if nxt > start and offset < end:
            a, b = max(0, start-offset), min(len(value), end-offset)
            node.text = value[:a] + (replacement if not started else '') + value[b:]
            node.set(qn('xml:space'), 'preserve')
            started = True
        offset = nxt

for p in body_paras:
    for match in reversed(list(pattern.finditer(p.text))):
        nums = [mapping[int(n)] for n in re.findall(r'\d+', match[1])]
        replace_span(p, match.start(), match.end(), ', '.join(f'[{n}]' for n in sorted(nums)))
    # Old generated manuscript placed references after the sentence stop.
    for match in reversed(list(re.finditer(r'([.!?])\s+(\[\d+\](?:, \[\d+\])*)', p.text))):
        replace_span(p, match.start(), match.end(), ' ' + match[2] + match[1])

def initials(given):
    return ' '.join('-'.join(part[0] + '.' for part in token.split('-') if part) for token in given.replace('.', ' ').split())

def author_text(ref, meta):
    if meta.get('author'):
        people = [(a.get('given',''), a.get('family', a.get('name',''))) for a in meta['author']]
    else:
        people = [tuple(name.rsplit(' ', 1)) for name in ref['authors']]
    names = [(initials(given)+' '+family).strip() for given, family in people]
    if len(names) >= 6: # supplied template's author-list rule
        return names[0] + ' et al.'
    if len(names) == 1:
        return names[0]
    return ', '.join(names[:-1]) + (', and ' if len(names)>2 else ' and ') + names[-1]

ABBREV = {
    'Nature Machine Intelligence':'Nat. Mach. Intell.',
    'The Annals of Statistics':'Ann. Statist.',
    'IEEE Transactions on Information Forensics and Security':'IEEE Trans. Inf. Forensics Security',
    'IEEE Transactions on Neural Networks and Learning Systems':'IEEE Trans. Neural Netw. Learn. Syst.',
    'Journal of the ACM':'J. ACM',
    'Journal of the American Statistical Association':'J. Amer. Statist. Assoc.',
    'Pattern Recognition Letters':'Pattern Recognit. Lett.',
    'Machine Learning':'Mach. Learn.',
    'Proceedings of the AAAI Conference on Artificial Intelligence':'Proc. AAAI Conf. Artif. Intell.',
}
MONTHS = ['','Jan.','Feb.','Mar.','Apr.','May','Jun.','Jul.','Aug.','Sep.','Oct.','Nov.','Dec.']
ref_evidence = []

def bibliography(old):
    ref = catalog[old-1]
    path = ROOT / 'metadata' / f'{old:02d}.json'
    raw = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    meta = raw.get('metadata', {})
    dates = meta.get('published-print',meta.get('published',{})).get('date-parts', [[ref['year']]])[0]
    date = (MONTHS[dates[1]]+' ' if len(dates)>1 else '') + str(dates[0])
    title = ref['title'].rstrip('.')
    chunks = [(author_text(ref,meta)+', “'+title+',” ', False)]
    if 'arxiv.org/abs/' in ref['url']:
        ident = re.search(r'/abs/([^/]+)',ref['url'])[1]
        chunks.append((f'arXiv:{ident}, {ref["year"]}. [Online]. Available: {ref["url"]}',False))
    elif old == 6:
        chunks += [('in Advances in Neural Information Processing Systems',True),
                   (f', vol. 30, 2017. [Online]. Available: {ref["url"]}',False)]
    elif old == 47:
        chunks += [('in Proc. Network and Distributed System Security Symp. (NDSS)',True),
                   (f', 2023. [Online]. Available: {ref["url"]}',False)]
    else:
        venue = meta.get('container-title', [ref['venue']])[0]
        kind = meta.get('type','')
        if old == 42:
            venue = 'Research in Attacks, Intrusions, and Defenses'
        if kind in ('proceedings-article','book-chapter'):
            venue = re.sub(r'^Proceedings(?: of)?(?: the)? ', 'Proc. ', venue)
            if not venue.startswith('Proc.') and not venue.startswith('Advances'):
                venue = 'Proc. ' + venue
            venue = 'in ' + venue
        else:
            venue = ABBREV.get(venue,venue)
        chunks.append((venue,True))
        tail = ''
        if meta.get('volume'): tail += ', vol. '+meta['volume']
        if meta.get('issue'): tail += ', no. '+str(int(meta['issue'])) if meta['issue'].isdigit() else ', no. '+meta['issue']
        pages = {51:'1-26',52:'837-845'}.get(old,meta.get('page'))
        if pages: tail += (', pp. ' if '-' in pages else ', p. ') + pages.replace('-', '–')
        tail += ', '+date+'.'
        if ref.get('doi'): tail = tail[:-1]+', doi: '+ref['doi']+'.'
        chunks.append((tail,False))
    ref_evidence.append({'old':old,'new':mapping[old],'key':ref['key'],'title':ref['title'],
                         'source':raw.get('source_url',ref['metadata_source']),
                         'formatted':''.join(t for t,_ in chunks)})
    return chunks

for new, (p,old) in enumerate(zip(ref_paras,old_order),1):
    p.clear(); p.add_run(f'[{new}]\t')
    for text, italic in bibliography(old):
        run = p.add_run(text); run.italic = italic
    pf = p.paragraph_format
    pf.left_indent = Inches(.25); pf.first_line_indent = Inches(-.25)
    pf.tab_stops.add_tab_stop(Inches(.25)); pf.space_after = Pt(2)
    pf.keep_together = True; pf.keep_with_next = False
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for r in p.runs: r.font.size = Pt(8)

section = doc.sections[0]
section.page_width = Inches(8.5); section.page_height = Inches(11)
section.top_margin = Inches(.75); section.bottom_margin = Inches(1)
section.left_margin = section.right_margin = Inches(.625)
section.header_distance = section.footer_distance = Inches(.3)
for sec in doc.sections:
    cols = sec._sectPr.find(qn('w:cols'))
    if cols is not None: cols.set(qn('w:num'),'1')
    for hf in [sec.header,sec.footer,sec.first_page_header,sec.first_page_footer,sec.even_page_header,sec.even_page_footer]:
        for p in hf.paragraphs: p.clear()

for style in doc.styles:
    if style.type == 1:
        style.font.name = 'Times New Roman'; style.font.color.rgb = RGBColor(0,0,0)
normal = doc.styles['Normal']
normal.font.size=Pt(10); normal.font.bold=False
normal.paragraph_format.line_spacing=1
normal.paragraph_format.space_before=Pt(0); normal.paragraph_format.space_after=Pt(0)
normal.paragraph_format.first_line_indent=Inches(.14)
normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
for name,size in [('Title',24),('Heading 1',10),('Heading 2',10),('Caption',8)]:
    s=doc.styles[name];s.font.size=Pt(size);s.font.bold=False
    s.font.italic=(name=='Heading 2');s.paragraph_format.first_line_indent=Inches(0)
    s.paragraph_format.space_before=Pt(10 if name.startswith('Heading') else 0)
    s.paragraph_format.space_after=Pt(5 if name.startswith('Heading') else 3)
    s.paragraph_format.line_spacing=1
    s.paragraph_format.keep_with_next=name.startswith('Heading')
    s.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT if name=='Heading 2' else WD_ALIGN_PARAGRAPH.CENTER
doc.styles['Heading 1'].font.small_caps=True

# Remove old direct font sizes; all mathematical runs stay untouched.
for p in body_paras:
    pf=p.paragraph_format
    pf.space_before=None;pf.space_after=None;pf.line_spacing=None
    pf.first_line_indent=None;pf.left_indent=Inches(0);pf.right_indent=Inches(0)
    pf.keep_together=False;pf.keep_with_next=False;pf.widow_control=True
    for r in p.runs:
        r.font.name='Times New Roman';r.font.size=None;r.font.color.rgb=RGBColor(0,0,0)
    for br in p._p.xpath('.//w:br[@w:type="page"]'):
        br.getparent().remove(br)
    if p.style.name=='Title':
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER;pf.keep_with_next=True
        for r in p.runs:r.bold=False
        pf.space_after=Pt(10)
    elif p.style.name=='Heading 1':
        text=p.text
        if text=='Abstract': continue
        m=re.match(r'^(\d+) (.*)',text)
        if m:p.text=roman(int(m[1]))+'. '+m[2].upper()
        else:p.text=text.upper()
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER;pf.keep_with_next=True
        if text.startswith('Appendix'):pf.page_break_before=True
    elif p.style.name=='Heading 2':
        m=re.match(r'^\d+ (\d+) (.*)',p.text)
        if m:p.text=chr(64+int(m[1]))+'. '+m[2]
        elif p.text.startswith('B.'):
            m=re.match(r'B\.(\d+)\. (.*)',p.text)
            if m:p.text=chr(64+int(m[1]))+'. '+m[2]
        p.alignment=WD_ALIGN_PARAGRAPH.LEFT;pf.keep_with_next=True
        if p.text=='H. Benign executable validation':
            pf.page_break_before=True
    elif p.style.name=='Normal' and not p._p.xpath('.//w:drawing|.//m:oMath'):
        p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY

# Title block and inline abstract, retaining the actual author information.
for i,p in enumerate(doc.paragraphs[1:5]):
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Inches(0)
    p.paragraph_format.keep_with_next=True
    for r in p.runs:r.font.size=Pt(11 if i==0 else 10)
abstract_heading=next(p for p in doc.paragraphs if p.text=='Abstract')
ps=doc.paragraphs
ai=next(i for i,p in enumerate(ps) if p.text=='Abstract')
abstract=ps[ai+1];abstract.text='Abstract—'+abstract.text
abstract.paragraph_format.first_line_indent=Inches(0)
abstract.paragraph_format.space_before=Pt(12);abstract.paragraph_format.space_after=Pt(6)
for r in abstract.runs:r.bold=True;r.font.size=Pt(9)
abstract_heading._p.getparent().remove(abstract_heading._p)
keywords=next(p for p in doc.paragraphs if p.text.startswith('Keywords:'))
keywords.text=keywords.text.replace('Keywords:','Index Terms—',1)
keywords.paragraph_format.first_line_indent=Inches(0)
for r in keywords.runs:r.font.size=Pt(9);r.italic=True

# Convert all table counter fields to Roman numerals; Word updates their REF users.
for instr in doc.element.xpath('.//w:instrText'):
    if 'SEQ Table' in (instr.text or ''):
        instr.text=instr.text.replace('ARABIC','ROMAN')
    if (instr.text or '').strip().startswith('REF '):
        instr.set(qn('xml:space'),'preserve')

eq=0
for p in doc.paragraphs:
    pf=p.paragraph_format
    if p._p.xpath('.//m:oMath'):
        eq+=1
        # Inline native math between center/right tab stops, with editable number.
        for wrapper in list(p._p.xpath('./m:oMathPara')):
            index=p._p.index(wrapper)
            for child in list(wrapper):
                if child.tag==qn('m:oMath'):p._p.insert(index,child);index+=1
            p._p.remove(wrapper)
        tab=p.add_run('\t')._r;p._p.remove(tab)
        p._p.insert(1 if p._p.pPr is not None else 0,tab)
        p.add_run(f'\t({eq})')
        pf.first_line_indent=Inches(0);pf.space_before=pf.space_after=Pt(5)
        pf.tab_stops.add_tab_stop(Inches(3.625),WD_TAB_ALIGNMENT.CENTER)
        pf.tab_stops.add_tab_stop(Inches(7.25),WD_TAB_ALIGNMENT.RIGHT)
        p.alignment=WD_ALIGN_PARAGRAPH.LEFT;pf.keep_together=True
    if p._p.xpath('.//w:drawing'):
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER;pf.first_line_indent=Inches(0)
        pf.keep_with_next=True;pf.space_before=Pt(4)
    if p.style.name=='Caption':
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER;pf.first_line_indent=Inches(0)
        pf.keep_together=True;pf.space_before=Pt(4);pf.space_after=Pt(4)
        if p.text.startswith('Table '):
            pf.keep_with_next=True
            if p.text.startswith('Table B'):
                previous=p._p.getprevious()
                p.text=re.sub(r'^Table B(\d)\. ',lambda m:'TABLE B-'+roman(int(m[1]))+'\n',p.text)
                if previous.tag==qn('w:tbl'):previous.addprevious(p._p)
            else:
                for node in p._p.xpath('.//w:t'):
                    if node.text=='Table ':node.text='TABLE '
                    elif (node.text or '').startswith('  '):
                        node.text=node.text.strip().upper()
                        node.addprevious(OxmlElement('w:br'))
        else:
            pf.keep_with_next=False
            for node in p._p.xpath('.//w:t'):
                node.text=(node.text or '').replace('Figure ','Fig. ')
            following=p._p.getnext()
            if following is not None and following.xpath('.//w:drawing'):
                following.addnext(p._p)
    elif p._p not in ref_elements:
        for node in p._p.xpath('.//w:t'):
            node.text=(node.text or '').replace('Figure ','Fig. ').replace('Table B1','Table B-I').replace('Table B2','Table B-II')

for table in doc.tables:
    table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
    for cell in table.rows[0].cells:
        for p in cell.paragraphs:
            p.paragraph_format.keep_with_next=True
    # Existing widths are relative to the old 6.65-inch text block.
    widths=[int(c.width) for c in table.rows[0].cells]
    scaled=[int(Inches(7.25)*w/sum(widths)) for w in widths]
    for col,w in zip(table.columns,scaled):col.width=w
    for row in table.rows:
        for cell,w in zip(row.cells,scaled):
            cell.width=w
            for shade in cell._tc.xpath('./w:tcPr/w:shd'):shade.set(qn('w:fill'),'FFFFFF')
            for margin in cell._tc.xpath('./w:tcPr/w:tcMar/w:top|./w:tcPr/w:tcMar/w:bottom'):
                margin.set(qn('w:w'),'25')
            for border in cell._tc.xpath('./w:tcPr/w:tcBorders/*'):border.set(qn('w:color'),'000000')
            for p in cell.paragraphs:
                p.paragraph_format.first_line_indent=Inches(0)
                p.paragraph_format.space_before=p.paragraph_format.space_after=Pt(1)
                p.paragraph_format.line_spacing=1
                for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(8);r.font.color.rgb=RGBColor(0,0,0)

# Keep the final references together only within each entry, not all as one block.
for p in ref_paras:
    p.paragraph_format.first_line_indent=Inches(-.25)
    for r in p.runs:r.font.size=Pt(8)
settings=doc.settings.element
update=settings.find(qn('w:updateFields'))
if update is None:update=OxmlElement('w:updateFields');settings.append(update)
update.set(qn('w:val'),'true')
doc.core_properties.title='X-SENTINEL IEEE One-Column Manuscript'
doc.save(TARGET)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_sha
with ZipFile(SOURCE) as a,ZipFile(TARGET) as b:
    media=[n for n in a.namelist() if n.startswith('word/media/')]
    assert all(a.read(n)==b.read(n) for n in media)
new=Document(TARGET);old=Document(SOURCE)
assert len(new.tables)==len(old.tables)==19
assert [[c.text for row in t.rows for c in row.cells] for t in new.tables]==[[c.text for row in t.rows for c in row.cells] for t in old.tables]
assert new.element.xpath('.//m:t/text()')==old.element.xpath('.//m:t/text()')
assert len(new.inline_shapes)==len(old.inline_shapes)==7
audit={'source':str(SOURCE),'source_sha256':source_sha,'template_sha256':hashlib.sha256(TEMPLATE.read_bytes()).hexdigest(),
       'output':str(TARGET),'references':58,'mapping':mapping,'equations':eq,'tables':19,'images':7,
       'media_unchanged':True,'math_text_unchanged':True,'table_cell_text_unchanged':True,'references_metadata':ref_evidence,
       'metadata_supplements':{'old_51_pages':'https://blogs.helsinki.fi/bk-club/files/2012/05/Efron_Bootstrap_AS1979.pdf',
                              'old_52_pages':'https://pubmed.ncbi.nlm.nih.gov/3203132/'},
       'visual_qa':'pending'}
(OUT/'format_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('Created',TARGET,'with',len(ref_evidence),'references; preservation checks passed')
