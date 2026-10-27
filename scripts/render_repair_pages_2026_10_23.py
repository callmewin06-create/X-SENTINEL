"""Rasterize the read-only Word PDF and locate the revised sections for QA."""
import argparse
import json
from pathlib import Path
from pypdf import PdfReader
import pypdfium2 as pdfium

parser=argparse.ArgumentParser();parser.add_argument('--iteration',type=int,default=1);args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
folder=root/f'outputs/repair_2026_10_23/render-{args.iteration}'
reader=PdfReader(folder/'report.pdf');texts=[page.extract_text() or '' for page in reader.pages]
terms=['E. Supplementary static binary checks','I. BODMAS static binary results',
       'J. Benign input diagnostics','K. Cross diagnostics','TABLE XVII','TABLE XVIII','TABLE XIX',
       'APPENDIX C.', '113 tests','175/175','87.5%']
locations={term:[i+1 for i,t in enumerate(texts) if term in t] for term in terms}
assert all(locations.values()),locations
assert 'TABLE XIXXVII' not in '\n'.join(texts)
assert any(line.strip() == 'TABLE XIX' for line in texts[17].splitlines())
(folder/'extracted.txt').write_text('\n\n'.join(f'PAGE {i+1}\n'+t for i,t in enumerate(texts)),encoding='utf8')
doc=pdfium.PdfDocument(str(folder/'report.pdf'))
for i,page in enumerate(doc):
    bitmap=page.render(scale=2);bitmap.to_pil().save(folder/f'page-{i+1}.png');bitmap.close();page.close()
doc.close()
proof={'pages':len(texts),'section_pages':locations,'renderer':'Word read-only PDF + pypdfium2 144 dpi',
       'visual_review':'pending; text checks alone do not certify layout'}
(folder/'text_checks.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
