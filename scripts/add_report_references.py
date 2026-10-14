"""Add verified X-SENTINEL references while preserving strict OOXML content."""
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import hashlib
import json

SOURCE = Path(r'C:\Users\win9tui\Downloads\Report.docx')
OUTPUT = Path('output/docx/Report_IEEE_References.docx')
QA = Path('tmp/report_ieee_references')

REFERENCES = [
 ('H. S. Anderson and P. Roth, “EMBER: An open dataset for training static PE malware machine learning models,” 2018, arXiv:1804.04637.', 'https://arxiv.org/abs/1804.04637'),
 ('G. Severi, J. Meyer, S. Coull, and A. Oprea, “Explanation-guided backdoor poisoning attacks against malware classifiers,” in Proc. 30th USENIX Secur. Symp., 2021, pp. 1487–1504.', 'https://www.usenix.org/conference/usenixsecurity21/presentation/severi'),
 ('D. Zhan, K. Xu, X. Liu, T. Han, Z. Pan, and S. Guo, “Practical clean-label backdoor attack against static malware detection,” Comput. Secur., vol. 150, Mar. 2025, Art. no. 104280, doi: 10.1016/j.cose.2024.104280.', 'https://doi.org/10.1016/j.cose.2024.104280'),
 ('D. T. Nguyen, N. N. Tran, T. T. Johnson, and K. Leach, “PBP: Post-training backdoor purification for malware classifiers,” in Proc. Netw. Distrib. Syst. Secur. Symp. (NDSS), 2025, doi: 10.14722/ndss.2025.240603.', 'https://doi.org/10.14722/ndss.2025.240603'),
 ('G. Ke et al., “LightGBM: A highly efficient gradient boosting decision tree,” in Advances in Neural Information Processing Systems, vol. 30, 2017, pp. 3146–3154.', 'https://papers.nips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html'),
 ('S. M. Lundberg and S.-I. Lee, “A unified approach to interpreting model predictions,” in Advances in Neural Information Processing Systems, vol. 30, 2017, pp. 4768–4777.', 'https://papers.nips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html'),
 ('S. M. Lundberg et al., “From local explanations to global understanding with explainable AI for trees,” Nat. Mach. Intell., vol. 2, no. 1, pp. 56–67, Jan. 2020, doi: 10.1038/s42256-019-0138-9.', 'https://doi.org/10.1038/s42256-019-0138-9'),
 ('Y. Gao, C. Xu, D. Wang, S. Chen, D. C. Ranasinghe, and S. Nepal, “STRIP: A defence against trojan attacks on deep neural networks,” in Proc. 35th Annu. Comput. Secur. Appl. Conf. (ACSAC), 2019, pp. 113–125, doi: 10.1145/3359789.3359790.', 'https://doi.org/10.1145/3359789.3359790'),
 ('L. Yang et al., “Jigsaw puzzle: Selective backdoor attack to subvert malware classifiers,” 2022, arXiv:2202.05470.', 'https://arxiv.org/abs/2202.05470'),
 ('R. J. Joyce et al., “EMBER2024—A benchmark dataset for holistic evaluation of malware classifiers,” in Proc. 31st ACM SIGKDD Conf. Knowl. Discov. Data Mining, 2025, doi: 10.1145/3711896.3737431.', 'https://doi.org/10.1145/3711896.3737431'),
 ('E. B. Wilson, “Probable inference, the law of succession, and statistical inference,” J. Amer. Statist. Assoc., vol. 22, no. 158, pp. 209–212, 1927, doi: 10.1080/01621459.1927.10502953.', 'https://doi.org/10.1080/01621459.1927.10502953'),
 ('B. Efron and R. J. Tibshirani, An Introduction to the Bootstrap. New York, NY, USA: Chapman & Hall, 1993.', 'https://link.springer.com/book/10.1007/978-1-4899-4541-9'),
]

# IEEE italicizes publication titles and the author abbreviation "et al.".
ITALIC_PHRASES = {
    2: ['Proc. 30th USENIX Secur. Symp.'],
    3: ['Comput. Secur.'],
    4: ['Proc. Netw. Distrib. Syst. Secur. Symp. (NDSS)'],
    5: ['et al.', 'Advances in Neural Information Processing Systems'],
    6: ['Advances in Neural Information Processing Systems'],
    7: ['et al.', 'Nat. Mach. Intell.'],
    8: ['Proc. 35th Annu. Comput. Secur. Appl. Conf. (ACSAC)'],
    9: ['et al.'],
    10: ['et al.', 'Proc. 31st ACM SIGKDD Conf. Knowl. Discov. Data Mining'],
    11: ['J. Amer. Statist. Assoc.'],
    12: ['An Introduction to the Bootstrap'],
}

def styled_segments(entry, number):
    spans = []
    for phrase in ITALIC_PHRASES.get(number, []):
        assert entry.count(phrase) == 1, phrase
        at = entry.index(phrase)
        spans.append((at, at + len(phrase)))
    cursor = 0
    for begin, end in sorted(spans):
        if cursor < begin:
            yield entry[cursor:begin], False
        yield entry[begin:end], True
        cursor = end
    if cursor < len(entry):
        yield entry[cursor:], False

def text(p):
    return ''.join(p.xpath('.//*[local-name()="t"]/text()'))

def insert_after(p, anchor, citation):
    nodes = p.xpath('.//*[local-name()="t"]')
    assembled = ''.join(n.text or '' for n in nodes)
    assert assembled.count(anchor) == 1, (anchor, assembled)
    target = assembled.index(anchor) + len(anchor)
    offset = 0
    for node in nodes:
        value = node.text or ''
        if offset < target <= offset + len(value):
            at = target - offset
            node.text = value[:at] + citation + value[at:]
            node.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            return
        offset += len(value)
    raise AssertionError(anchor)

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE) as zin:
        document = E.fromstring(zin.read('word/document.xml'))
        w = document.nsmap['w']
        rns = document.nsmap['r']
        body = document.find(f'{{{w}}}body')
        paragraphs = body.findall(f'{{{w}}}p')
        refs_heading = next(p for p in paragraphs if text(p).strip() == 'References')
        start = paragraphs.index(refs_heading)
        trailing = paragraphs[start + 1:]
        old_refs = [p for p in trailing if text(p).strip()]
        assert len(old_refs) == 4 and all('Phishing' in text(p) or 'phishing' in text(p) for p in old_refs)
        template = deepcopy(old_refs[0])
        for p in trailing:
            body.remove(p)

        # Insert citations only at statements directly related to each source.
        changes = [
            (11, 'malware classifiers', ' [1]'),
            (12, 'preserving apparently normal behavior on clean inputs', ' [2]'),
            (13, 'experiments involving Windows PE files', ' [2]'),
            (13, 'original functionality of the files', ' [3]'),
            (14, 'reduce the influence of embedded backdoors', ' [4]'),
            (15, 'LightGBM malware classifiers', ' [5]'),
            (15, 'SHAP-based explanations', ' [6], [7]'),
            (15, 'STRIP baselines', ' [8]'),
            (26, 'machine learning', ' [1]'),
            (29, 'clean-label constraints', ' [2]'),
            (30, 'original files', ' [3]'),
            (31, 'malware samples', ' [9]'),
            (33, 'model output', ' [6], [7]'),
            (36, 'exact trigger', ' [4]'),
            (85, 'TreeExplainer SHAP values', ' [7]'),
            (94, 'Gao et al., ACSAC 2019', ' [8]'),
            (132, 'feature vectors from EMBER2018', ' [1]'),
            (132, 'EMBER2024 extension', ' [10]'),
            (138, 'LightGBM', ' [5]'),
            (141, 'explanation-guided attacks', ' [2]'),
            (152, '95% Wilson intervals', ' [11]'),
            (152, 'paired bootstrap resamples', ' [12]'),
            (154, 'tabular STRIP', ' [8]'),
        ]
        for index, anchor, citation in changes:
            insert_after(paragraphs[index], anchor, citation)

        # Keep the reference list on a fresh page instead of orphaning its first entry.
        heading_properties = refs_heading.find(f'{{{w}}}pPr')
        E.SubElement(heading_properties, f'{{{w}}}pageBreakBefore')

        # The source has a manual break after the small AUROC table. Reflow after
        # citation insertion would otherwise isolate its last rows on a blank page.
        auc_table = next(t for t in body.findall(f'{{{w}}}tbl')
                         if text(t).startswith('Method18 Conc.'))
        position = list(body).index(auc_table)
        caption = body[position-1]
        E.SubElement(caption.find(f'{{{w}}}pPr'), f'{{{w}}}keepNext')
        rows = auc_table.findall(f'{{{w}}}tr')
        for row_number, row in enumerate(rows):
            trpr = row.find(f'{{{w}}}trPr')
            if trpr is None:
                trpr = E.Element(f'{{{w}}}trPr')
                row.insert(0, trpr)
            E.SubElement(trpr, f'{{{w}}}cantSplit')
            for p in row.xpath('.//*[local-name()="p"]'):
                ppr = p.find(f'{{{w}}}pPr')
                if ppr is None:
                    ppr = E.Element(f'{{{w}}}pPr')
                    p.insert(0, ppr)
                E.SubElement(ppr, f'{{{w}}}keepLines')
                if row_number < len(rows)-1:
                    E.SubElement(ppr, f'{{{w}}}keepNext')
        for p in list(body)[position+1:position+4]:
            if E.QName(p).localname == 'p' and not text(p).strip():
                for br in p.xpath('.//*[local-name()="br"]'):
                    if br.get(f'{{{w}}}type') == 'page':
                        br.getparent().remove(br)

        # Keep existing table captions with their tables after citation reflow.
        children = list(body)
        for index, element in enumerate(children[:-1]):
            if E.QName(element).localname != 'p' or E.QName(children[index+1]).localname != 'tbl':
                continue
            ppr = element.find(f'{{{w}}}pPr')
            if ppr is None:
                continue
            style = ppr.find(f'{{{w}}}pStyle')
            if style is not None and style.get(f'{{{w}}}val') == 'tablehead':
                for keep in ppr.findall(f'{{{w}}}keepNext'):
                    ppr.remove(keep)
                E.SubElement(ppr, f'{{{w}}}keepNext')

        relpath = 'word/_rels/document.xml.rels'
        relations = E.fromstring(zin.read(relpath))
        rel_ns = E.QName(relations).namespace
        existing = {e.get('Id') for e in relations}
        for number, (entry, url) in enumerate(REFERENCES, 1):
            paragraph = deepcopy(template)
            for attr in list(paragraph.attrib):
                if E.QName(attr).localname in ('paraId', 'textId'):
                    del paragraph.attrib[attr]
            for child in list(paragraph):
                if E.QName(child).localname != 'pPr':
                    paragraph.remove(child)
            ppr = paragraph.find(f'{{{w}}}pPr')
            # Keep an entry together, but allow line wrapping for narrow columns.
            E.SubElement(ppr, f'{{{w}}}keepLines')
            rid = f'rIdXSentinelRef{number}'
            assert rid not in existing
            E.SubElement(relations, f'{{{rel_ns}}}Relationship', Id=rid,
                         Type=rns + '/hyperlink', Target=url, TargetMode='External')
            hyperlink = E.SubElement(paragraph, f'{{{w}}}hyperlink')
            hyperlink.set(f'{{{rns}}}id', rid)
            for segment, italic in styled_segments(entry, number):
                run = E.SubElement(hyperlink, f'{{{w}}}r')
                properties = E.SubElement(run, f'{{{w}}}rPr')
                E.SubElement(properties, f'{{{w}}}rFonts', attrib={f'{{{w}}}ascii':'Times New Roman', f'{{{w}}}hAnsi':'Times New Roman'})
                if italic:
                    E.SubElement(properties, f'{{{w}}}i')
                E.SubElement(properties, f'{{{w}}}color', attrib={f'{{{w}}}val':'000000'})
                E.SubElement(properties, f'{{{w}}}sz', attrib={f'{{{w}}}val':'16'})
                node = E.SubElement(run, f'{{{w}}}t')
                node.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                node.text = segment
            body.insert(list(body).index(body.find(f'{{{w}}}sectPr')), paragraph)

        edits = {
            'word/document.xml': E.tostring(document, encoding='UTF-8', xml_declaration=True, standalone=True),
            relpath: E.tostring(relations, encoding='UTF-8', xml_declaration=True, standalone=True),
        }
        with ZipFile(OUTPUT, 'w') as zout:
            for info in zin.infolist():
                zout.writestr(info, edits.get(info.filename, zin.read(info.filename)))
    # Check the intended scope: every untouched ZIP member is byte-identical.
    with ZipFile(SOURCE) as original, ZipFile(OUTPUT) as revised:
        assert original.namelist() == revised.namelist()
        for name in original.namelist():
            if name not in edits:
                assert original.read(name) == revised.read(name), name
        final = E.fromstring(revised.read('word/document.xml'))
        final_ps = final.xpath('//*[local-name()="body"]/*[local-name()="p"]')
        for i, before in enumerate(paragraphs[:start + 1]):
            if i not in {c[0] for c in changes}:
                assert text(before) == text(final_ps[i]), i
        assert len(final_ps[start+1:]) == 12
    (QA/'reference_sources.json').write_text(json.dumps({
        'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'references':[{'number':i,'entry':e,'url':u} for i,(e,u) in enumerate(REFERENCES,1)],
        'citation_insertions':changes,
        'preserved_unrelated_conclusion':True,
        'layout_fixes':['References starts on a fresh page', 'AUROC table kept together; trailing manual page break removed'],
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Saved {OUTPUT.name} with 12 references and {len(changes)} citation insertions')

if __name__ == '__main__':
    main()
