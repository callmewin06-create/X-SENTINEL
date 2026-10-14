"""Replace only the References entry, preserving every other source XML byte."""
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re
from lxml import etree as E
from add_report_references import REFERENCES, styled_segments

SOURCE = Path(r'C:\Users\win9tui\Downloads\Report (1).docx')
OUTPUT = Path('output/docx/Report_1_IEEE_References.docx')
QA = Path('tmp/report_1_ieee')

def main():
    with ZipFile(SOURCE) as zin:
        raw = zin.read('word/document.xml')
        root = E.fromstring(raw)
        w = root.nsmap['w']
        body = root.find(f'{{{w}}}body')
        paragraphs = body.findall(f'{{{w}}}p')
        heading = next(p for p in paragraphs if ''.join(p.itertext()).strip() == 'References')
        template = paragraphs[paragraphs.index(heading) + 1]
        assert 'Phishing Email Detection' in ''.join(template.itertext())
        match = next(m for m in re.finditer(rb'<w:p(?:\s[^>]*)?>.*?</w:p>', raw, re.S)
                     if b'Phishing Email Detection' in m.group())
        fragments = []
        for number, (entry, _) in enumerate(REFERENCES, 1):
            p = E.Element(f'{{{w}}}p', nsmap={'w': w})
            # Use the existing reference style, numbering, indentation and spacing.
            p.append(deepcopy(template.find(f'{{{w}}}pPr')))
            for segment, italic in styled_segments(entry, number):
                r = E.SubElement(p, f'{{{w}}}r')
                pr = E.SubElement(r, f'{{{w}}}rPr')
                if italic:
                    E.SubElement(pr, f'{{{w}}}i')
                t = E.SubElement(r, f'{{{w}}}t')
                t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                t.text = segment
            fragments.append(E.tostring(p).replace(f' xmlns:w="{w}"'.encode(), b''))
        revised = raw[:match.start()] + b''.join(fragments) + raw[match.end():]
        # Ensure all content before and after the replaced reference is untouched.
        assert revised.startswith(raw[:match.start()])
        assert revised.endswith(raw[match.end():])
        E.fromstring(revised)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(OUTPUT, 'w') as zout:
            for info in zin.infolist():
                zout.writestr(info, revised if info.filename == 'word/document.xml' else zin.read(info.filename))
    with ZipFile(SOURCE) as zin, ZipFile(OUTPUT) as zout:
        for name in zin.namelist():
            if name != 'word/document.xml':
                assert zin.read(name) == zout.read(name), name
        new_body = E.fromstring(zout.read('word/document.xml')).find(f'{{{w}}}body')
        old_children = list(body)
        new_children = list(new_body)
        at = old_children.index(template)
        for old, new in zip(old_children[:at], new_children[:at]):
            assert E.tostring(old, method='c14n') == E.tostring(new, method='c14n')
        for old, new in zip(old_children[at+1:], new_children[at+12:]):
            assert E.tostring(old, method='c14n') == E.tostring(new, method='c14n')
    QA.mkdir(parents=True, exist_ok=True)
    (QA/'audit.json').write_text(json.dumps({
        'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'unchanged_body_before_references': True,
        'unchanged_styles_sections_tables_images': True,
        'reference_count': 12,
        'references': [{'number': n, 'entry': e, 'source': u} for n, (e, u) in enumerate(REFERENCES, 1)],
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Saved {OUTPUT}; only the References entry was replaced.')

if __name__ == '__main__':
    main()
