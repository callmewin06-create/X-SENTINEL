"""Rasterize the Word-exported QA PDF; no DOCX/source changes."""
import json
from pathlib import Path

from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / 'outputs/bodmas_2026_10_23/word-render-1'
pdf = folder / 'report.pdf'
reader = PdfReader(pdf)
texts = [page.extract_text() or '' for page in reader.pages]
full = '\n'.join(texts)
required = ['175/175', 'Invalid PE signature/header offset', '0.044262', '0.957886',
            '87.5%', '25 inputs', 'not 800', 'TABLE C-I', 'TABLE C-II']
for term in required:
    assert term in full, term
assert 'TABLE C-II' in texts[-1] and 'Prediction median' in texts[-1]
assert all(alias in texts[-1] for alias in ['2018', '2024', 'Reduced', 'Full'])
(folder / 'extracted.txt').write_text(full, encoding='utf8')
doc = pdfium.PdfDocument(str(pdf))
for i, page in enumerate(doc):
    bitmap = page.render(scale=2)
    bitmap.to_pil().save(folder / f'page-{i+1}.png')
    bitmap.close()
    page.close()
doc.close()
proof = {'pages': len(texts), 'required_terms': required, 'all_pass': True,
         'renderer': 'Microsoft Word PDF export, read-only; pypdfium2 raster at 144 dpi',
         'packaged_renderer_fallback_reason': 'Windows has no LibreOffice soffice.exe on PATH',
         'timing_table_together_on_last_page': True}
(folder / 'text_checks.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf8')
print(json.dumps(proof, indent=2))
