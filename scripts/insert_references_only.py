"""Insert references without replacing, removing, or editing any original XML."""
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
import re
from lxml import etree as E
from add_report_references import REFERENCES, styled_segments

source = Path(r'C:\Users\win9tui\Downloads\Report (1).docx')
output = Path('output/docx/Report_1_References_Final.docx')
with ZipFile(source) as original:
    raw = original.read('word/document.xml')
    root = E.fromstring(raw)
    w = root.nsmap['w']
    paragraphs = root.xpath('//*[local-name()="body"]/*[local-name()="p"]')
    heading = next(p for p in paragraphs if ''.join(p.itertext()).strip() == 'References')
    existing = paragraphs[paragraphs.index(heading)+1]
    assert 'Phishing Email Detection' in ''.join(existing.itertext())
    match = next(m for m in re.finditer(rb'<w:p(?:\s[^>]*)?>.*?</w:p>', raw, re.S)
                 if b'Phishing Email Detection' in m.group())
    added = []
    for number, (entry, _) in enumerate(REFERENCES, 1):
        p = E.Element(f'{{{w}}}p', nsmap={'w': w})
        p.append(deepcopy(existing.find(f'{{{w}}}pPr')))
        for segment, italic in styled_segments(entry, number):
            r = E.SubElement(p, f'{{{w}}}r')
            if italic:
                pr = E.SubElement(r, f'{{{w}}}rPr')
                E.SubElement(pr, f'{{{w}}}i')
            t = E.SubElement(r, f'{{{w}}}t')
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            t.text = segment
        added.append(E.tostring(p).replace(f' xmlns:w="{w}"'.encode(), b''))
    insertion = b''.join(added)
    # The original file ends with a continuous section break into one column.
    # Insert in that existing final section, never inside the two-column article.
    final_section = root.xpath('//*[local-name()="body"]/*[local-name()="sectPr"]')[0]
    columns = final_section.find(f'{{{w}}}cols')
    assert columns is not None and columns.get(f'{{{w}}}num', '1') == '1'
    at = raw.rfind(b'<w:sectPr ')
    assert at > match.end()
    assert raw[at:].endswith(b'</w:sectPr></w:body></w:document>')
    revised = raw[:at] + insertion + raw[at:]
    # Removing just the newly inserted block must reproduce the original exactly.
    assert revised[:at] + revised[at+len(insertion):] == raw
    E.fromstring(revised)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w') as result:
        for info in original.infolist():
            result.writestr(info, revised if info.filename=='word/document.xml' else original.read(info.filename))
with ZipFile(source) as a, ZipFile(output) as b:
    assert a.namelist() == b.namelist()
    for name in a.namelist():
        if name != 'word/document.xml':
            assert a.read(name) == b.read(name), name
    final = b.read('word/document.xml')
    assert final[:at] + final[at+len(insertion):] == a.read('word/document.xml')
print('Verified: insertion only; every original XML byte and every other ZIP member retained.')
