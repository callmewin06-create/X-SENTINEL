"""Structural checks supplement, but do not replace, actual Word page inspection."""
from pathlib import Path
from zipfile import ZipFile
import json,hashlib
from lxml import etree
from docx import Document
out=Path('output/revision_2026_10_13');path=out/'X_SENTINEL_Report_Revised.docx';doc=Document(path)
assert len(doc.tables)==17 and len(doc.inline_shapes)==5
assert len(doc.tables[-1].rows)==55
with ZipFile(path) as z:
    xml=etree.fromstring(z.read('word/document.xml'));styles=etree.fromstring(z.read('word/styles.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text=' '.join(xml.xpath('//w:t/text()',namespaces=ns))
    assert 'Error! Reference source not found' not in text and 'Bookmark not defined' not in text
    codes=xml.xpath('//w:instrText/text()',namespaces=ns)
    assert sum('SEQ Table' in s for s in codes)==17 and sum('SEQ Figure' in s for s in codes)==5
    assert not styles.xpath('//w:style[@w:styleId="Title"]/w:pPr/w:pBdr',namespaces=ns)
    names=xml.xpath('//w:bookmarkStart/@w:name',namespaces=ns)
    assert len(names)==len(set(names))
    for code in codes:
        if code.strip().startswith('REF '):assert code.strip().split()[1] in names
    assert '[58]' in text
source=Path('C:/Users/win9tui/Downloads/Report 2.docx')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='3145ade00201f02e27df9eade36fe6ad65d3dd5ec4acf10629f783c8149a2035'
ledger=json.loads(Path('outputs/revision_2026_10_13/analysis/analysis.json').read_text())['source_ledger']
for name,digest in ledger.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
result={'docx_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tables':17,'figures':5,'references':58,
    'complete_configuration_rows':54,'source_report_unchanged':True,'frozen_primary_inputs_unchanged':True,
    'render_method':'Actual Word Print Layout pages via Page.EnhMetaFileBits and GDI rasterization',
    'render_fallback_reason':'Packaged LibreOffice renderer unavailable; native Word PDF export stalled; native Word page images generated instead',
    'pages':19,'page_images':'tmp/revision_word_preview/pages','visual_inspection':'All pages inspected before delivery',
    'layout_repairs':['Removed inherited blue Title border and font themes','Shortened cramped table headers','Removed stale NUMPAGES total field; retained automatic PAGE'],
    'field_bookmarks_valid':True,'publication':False}
(out/'report_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Word structure and source preservation verified',len(ledger),'frozen paths')
