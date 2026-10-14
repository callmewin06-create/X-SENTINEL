"""Read source manuscript without changing its content or package."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import hashlib,json
source=Path(r'C:\Users\win9tui\Downloads\Report 2.docx')
out=Path('output/revision_2026_10_13/source_report');out.mkdir(parents=True,exist_ok=True)
with ZipFile(source) as z:
    root=etree.fromstring(z.read('word/document.xml'))
    paragraphs=root.xpath('//*[local-name()="p"]')
    lines=[''.join(p.xpath('.//*[local-name()="t"]/text()')) for p in paragraphs]
    text='\n'.join(lines)
    (out/'source_text.txt').write_text(text,encoding='utf-8')
    (out/'provenance.json').write_text(json.dumps({'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'text_length':len(text),'media':[name for name in z.namelist() if name.startswith('word/media/')]},indent=2),encoding='utf-8')
print(text[:5500])
