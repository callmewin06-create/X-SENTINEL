"""Evidence-backed editorial patch; formal follow-up results remain pending."""
from pathlib import Path
import hashlib
import json
import re
from copy import deepcopy
from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'output/teacher_revision_2026_11_04/paper_m8_update/X_SENTINEL_Anonymous_Working_2026_11_04.docx'
out=ROOT/'output/jstis_revision_2026_11_09'; out.mkdir(parents=True,exist_ok=True)
doc=Document(source); original=list(doc.paragraphs); edits=[]


def replace(i,text):
    paragraph=original[i]; before=paragraph.text
    # Preserve paragraph/run styling and all non-text content elsewhere.
    if paragraph.runs:
        paragraph.runs[0].text=text
        for run in paragraph.runs[1:]: run.text=''
    else: paragraph.add_run(text)
    edits.append({'paragraph':i,'before':before,'after':text})


replace(0,'Evaluating Feature View Attribution Concentration for Backdoor Triage in LightGBM PE Classifiers')
abstract=('We evaluate feature-view attribution concentration for per-input backdoor triage in LightGBM portable executable classifiers. '
    'X-SENTINEL combines View Mass Concentration and Behavioral-Gated SHAP using small trusted benign reference and calibration pools. '
    'At thresholds fixed on benign calibration data, mean Reduced recall is 35.75% on confirmed EMBER2018 restricted attacks and 48.33% on EMBER2024 restricted attacks. '
    'These cohort-specific results do not establish general backdoor detection: distributed triggers largely evade the detector, and linear rank fusion can lose detections made by a single component. '
    'Raw-feature novelty controls, an independent public-data comparator and bounded post-training evasion reveal further limitations. '
    'A separate audit on two benign executable fixtures quantifies collateral feature and attribution changes without establishing malicious-function preservation or binary-backdoor recall. '
    'The evidence supports a conditional diagnostic role for attribution concentration under explicit attacker, defender and feature-space constraints.')
assert 120<=len(abstract.split())<=150
replace(2,'Abstract—'+abstract)
replace(3,'Index Terms—Malware, backdoors, LightGBM, TreeSHAP, attribution, calibration.')
replace(27,original[27].text+' Spectral Signatures and Activation Clustering could be adapted to SHAP or leaf-index representations of tree ensembles. Such choices introduce a representation and validation problem distinct from their original neural activation setting. We do not report these adaptations as implemented defenses. Our training-level comparison is limited to Isolation Forest filtering and retraining; conclusions about defense superiority are correspondingly restricted.')
replace(31,'The model provider executes a fixed LightGBM training routine and may receive poisoned benign-labeled records. In the frozen benchmark, the attacker uses study-specific feature selectors and prescribed trigger geometries without altering the learner or loss. These restrictions can favor a concentration-based detector and therefore delimit the evidence; they are not assumed to describe all attackers. The defender does not select the attack domain. A separate bounded inference search evaluates post-training evasion. This setting does not grant the attacker arbitrary control over model weights or the training algorithm. Table I delineates defender resources.')
replace(122,'At thresholds fixed on the 2,000-record benign calibration pool, mean Reduced recall is 35.75% on the 12 confirmed EMBER2018 restricted configurations and 48.33% on the three confirmed EMBER2024 restricted configurations; corresponding mean final benign FPRs are 0.52% and 0.78%. These are configuration-level macro averages over recurring source records, not independent-file estimates. The secondary retrospective 1% final-FPR-cap analysis gives Reduced recall of 37.69% and 52.82%, and Full recall of 44.72% and 60.13%. At that cap, VMC alone reaches 60.36% on the EMBER2024 restricted cohort. For distributed Cross triggers, raw kNN (top-32) reaches 24.75%, LOF 20.00% and rarity 11.46%, whereas Reduced detects fewer than 0.01%. The cap operating points use final benign scores retrospectively and are not deployment thresholds.')
replace(144,'View cardinality and score fusion remain open methodological questions. VMCnorm replaces total view attribution mass with mean mass per coordinate; normalization alone does not establish improved detection. Max-rank fusion changes both attack and benign score distributions. Neither is an improvement established by the frozen primary tables. Historical MAX exploration showed different tradeoffs across cohorts. We leave these extensions to future work requiring separate calibration and held-out, matched-FPR evaluation.')
replace(145,'The evaluated training pipeline is fixed and honest, but its data may be poisoned. The frozen benchmark and bounded post-training search do not establish robustness to feedback-driven poisoning-time optimization or an unrestricted malicious supplier. Prescribed trigger geometry can structurally favor concentration-based detection; Cross-view failures are counterevidence to universal efficacy. Dataset, schema, time period and confirmed-family composition are entangled. The original EMBER2024 restricted cohort contains three seeds; repeated source IDs across models are not independent files. Supplemental comparisons reuse observed pools, and exact-SHA256 deduplication does not exclude near duplicates or shared software families. Random disjoint partitions alone do not establish temporal generalization.')
replace(146,'The frozen benchmark fixes the study-specific legacy_rare selector. A geometry-constrained signed, conditioned adaptation and a retrained four-candidate random-search pilot do not constitute a complete selector comparison or feedback-driven adaptive evaluation. Generality across original Severi strategies [6], allowed domains and poisoning-time objectives requires a separately locked follow-up; no such completed result is claimed in the primary tables.')
replace(147,'We do not report operational latency or gateway throughput from the returned five-file microbenchmark because its host, thread and execution-hash provenance is incomplete. A reproducible timing comparison must state hardware, software, batch size, input scope and whether feature extraction, TreeSHAP and auxiliary classifiers are included.')
anchor=original[140]; node=OxmlElement('w:p'); anchor._p.addnext(node); p=Paragraph(node,anchor._parent)
p.style=anchor.style
p.add_run('Using the same experimental adapter, we compared each physical combined edit with an ideal vector edit that overwrites only the two target coordinates. On the frozen poisoned classifier, the physical-minus-ideal VMC differences are +0.00241 for the native fixture and +0.00425 for the managed fixture. Relative to each original, however, the physical edits change VMC by +0.10192 and −0.09219, respectively. Thus collateral coordinates affect attribution concentration, while the direction of the total change differs between these two fixtures. This within-model diagnostic does not establish a population effect or legacy-extractor equivalence.')
edits.append({'insert_after':140,'after':p.text})
def insert_after(anchor,text):
    node=OxmlElement('w:p'); anchor._p.addnext(node); paragraph=Paragraph(node,anchor._parent)
    paragraph.style=anchor.style; paragraph.add_run(text)
    edits.append({'insert_after_text':anchor.text[:80],'after':text})

vi_abstract=('Chúng tôi đánh giá mức tập trung đóng góp đặc trưng theo view để sàng lọc backdoor trong bộ phân loại PE LightGBM. '
    'X-SENTINEL kết hợp VMC và BGS với dữ liệu lành tính tin cậy để tham chiếu và hiệu chỉnh ngưỡng. '
    'Tại ngưỡng hiệu chỉnh, recall trung bình trên các cấu hình tấn công giới hạn đặc trưng đã xác nhận đạt 35,75% với EMBER2018 và 48,33% với EMBER2024. '
    'Trigger phân tán phần lớn né được detector; hợp nhất tuyến tính đôi khi kém một thành phần. '
    'Đối chứng đặc trưng thô và thí nghiệm né tránh cho thấy thêm giới hạn. '
    'Kiểm tra hai chương trình lành tính lượng hóa thay đổi đặc trưng và VMC khi sửa binary, chưa chứng minh bảo toàn chức năng malware. '
    'Kết quả hỗ trợ vai trò chẩn đoán có điều kiện.')
assert 120<=len(vi_abstract.split())<=150
insert_after(original[2],'Tóm tắt—'+vi_abstract)
vi_paragraph=Paragraph(original[2]._p.getnext(),original[2]._parent)
if original[2].runs[0]._r.rPr is not None:
    vi_paragraph.runs[0]._r.insert(0,deepcopy(original[2].runs[0]._r.rPr))
insert_after(original[3],'Từ khóa—mã độc, cửa hậu, LightGBM, TreeSHAP, hiệu chỉnh.')

insert_after(next(p for p in original if p.text.startswith('For EMBER2018 Cross')),
    'A separate Development-only diagnostic fixes 100 malware source IDs per dataset in lexical order before querying models. Across nine Cross configurations, mean clean-model triggered evasion is 93.88% on EMBER2018 and 18.37% on EMBER2024. Restoring the originally observed values of the triggered Structural coordinates lowers clean-model evasion by 83.33 and 18.37 percentage points, respectively, and poisoned-model evasion by 73.47 and 97.28 points. Coordinate and view restoration results identify strong sensitivity to the selected Structural values in this subset. These controlled vector interventions neither establish binary feasibility nor estimate population-level causal effects; source IDs recur across models.')
insert_after(next(p for p in original if p.text.startswith('The values 0.999')),
    'The 500-record reference pool limits component ranks to 501 possible levels, while 2,000 separate calibration records determine the alert threshold. Across all 54 configurations, BGS occupies a mean of 93.37 distinct calibration ranks and 110.69 final-benign ranks; its largest tied groups contain means of 1,525.04 of 2,000 and 7,280.56 of 10,000 records, respectively. Thus the available rank grid is sparsely occupied. Paired tail summaries describe saturation and ties but do not establish that ties cause calibration-to-final FPR differences.')
# Relocate both unvalidated extensions out of Methods, retaining native math.
equations={int(t.cell(0,-1).text.strip('()')):t for t in doc.tables
           if t._tbl.xpath('.//m:oMath') and re.fullmatch(r'\(\d+\)',t.cell(0,-1).text)}
cursor=original[144]._p
for block in [original[46]._p,equations[5]._tbl,original[47]._p,original[48]._p,
              original[60]._p,equations[11]._tbl,original[61]._p,original[62]._p]:
    cursor.addnext(block); cursor=block
mapping={5:12,6:5,7:6,8:7,9:8,10:9,11:13,12:10,13:11}
for number,table in equations.items():
    if number in mapping:
        for run in table.cell(0,-1).paragraphs[0].runs:
            run.text=run.text.replace(f'({number})',f'({mapping[number]})')
for paragraph in doc.paragraphs:
    text=paragraph.text
    if not re.search(r'Eq(?:s)?\.|Equation',text): continue
    def convert(match):
        return re.sub(r'\((\d+)\)',lambda m:f'({mapping.get(int(m[1]),int(m[1]))})',match[0])
    revised=re.sub(r'(?:Eqs?\.|Equation)\s+\(\d+\)(?:(?:–| and |, )\(\d+\))*',convert,text)
    revised=re.sub(r'Eq\. (\d+)',lambda m:f'Eq. {mapping.get(int(m[1]),int(m[1]))}',revised)
    if revised!=text:
        paragraph.runs[0].text=revised
        for run in paragraph.runs[1:]: run.text=''
edits.append({'action':'Moved VMCnorm and MAX native equations to future-work discussion; renumbered equations and text references'})
resources=doc.tables[0]
for row in resources.rows:
    if row.cells[0].text=='Raw rarity and\npooled-view IF' or row.cells[0].text.replace('\n',' ')=='Raw rarity and pooled-view IF':
        row.cells[0].paragraphs[0].runs[0].text='Raw novelty / rarity and pooled-view IF'
        for paragraph in row.cells[0].paragraphs[1:]:
            paragraph._p.getparent().remove(paragraph._p)
        edits.append({'table':'I','action':'Explicitly included raw novelty controls in access row'})
destination=out/'X_SENTINEL_Anonymous_Working_2026_11_09.docx'; doc.save(destination)
assert len(doc.tables)==32
(out/'EDITORIAL_CHANGELOG.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'output':str(destination),'output_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
    'abstract_word_count':len(abstract.split()),'vietnamese_abstract_word_count':len(vi_abstract.split()),
    'edits':edits,'formal_M3_results':'NOT_YET_AVAILABLE',
    'submission_status':'WORKING_DRAFT_NOT_SUBMISSION_READY'},ensure_ascii=False,indent=2),encoding='utf8')
print('Working draft saved; abstract words',len(abstract.split()))
