"""Merge verified fresh follow-up into a new anonymous Word copy."""
from pathlib import Path
from copy import deepcopy
import json,statistics,hashlib,re
from docx import Document
from docx.shared import Pt,Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'output/jstis_revision_2026_11_09/X_SENTINEL_Anonymous_Working_2026_11_09.docx'
out=ROOT/'output/jstis_revision_2026_11_10';out.mkdir(exist_ok=True)
audit_path=ROOT/'outputs/jstis_revision_2026_11_09/completed_audit/VERIFIED_RESULTS.json'
audit=json.loads(audit_path.read_text(encoding='utf8'))
assert audit['status']=='ARITHMETIC_AND_PROVENANCE_VERIFIED'
doc=Document(source);edits=[]

def find(prefix):
    matches=[p for p in doc.paragraphs if p.text.startswith(prefix)]
    assert len(matches)==1,(prefix,len(matches))
    return matches[0]

def replace(prefix,text):
    p=find(prefix);before=p.text
    if p.runs:
        p.runs[0].text=text
        for run in p.runs[1:]:run.text=''
    else:p.add_run(text)
    edits.append({'before':before,'after':text})

def para(text,before=None,heading=False,caption=False):
    p=doc.add_paragraph()
    p.paragraph_format.space_after=Pt(6)
    p.paragraph_format.line_spacing=1
    if heading or caption:p.paragraph_format.keep_with_next=True
    if caption:p.paragraph_format.space_before=Pt(6)
    if caption:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    run=p.add_run(text);run.font.name='Times New Roman';run.font.size=Pt(11 if caption else 11.5)
    run.bold=heading or caption;run.italic=heading and not caption and not text.startswith('APPENDIX')
    if before is not None:before._p.addprevious(p._p)
    return p

def table(headers,rows,widths,before=None):
    t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    for i,w in enumerate(widths):t.columns[i].width=Cm(w)
    for row in [headers,*rows]:
        cells=t.rows[0].cells if row is headers else t.add_row().cells
        for i,(cell,text) in enumerate(zip(cells,row)):
            cell.width=Cm(widths[i]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.text=str(text)
            for p in cell.paragraphs:
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
                for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(9);run.bold=row is headers
            props=cell._tc.get_or_add_tcPr();borders=OxmlElement('w:tcBorders')
            for side in ('top','left','bottom','right'):
                e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
            props.append(borders)
            if row is headers:
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E7EDF3');props.append(shade)
        if row is not headers:
            no_split=OxmlElement('w:cantSplit');t.rows[-1]._tr.get_or_add_trPr().append(no_split)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    if before is not None:before._p.addprevious(t._tbl)
    return t

def mean_sd(values):
    return f'{100*statistics.mean(values):.2f} ± {100*statistics.stdev(values):.2f}' if len(values)>1 else f'{100*values[0]:.2f}'

abstract=('We evaluate feature-view attribution concentration for backdoor triage in LightGBM portable executable classifiers. '
    'X-SENTINEL combines View Mass Concentration and Behavioral-Gated SHAP with trusted benign reference and calibration data. '
    'At calibration thresholds, Reduced recall on the frozen restricted cohorts is 35.75% for EMBER2018 and 48.33% for EMBER2024. '
    'A separate fresh-data study evaluates three selector adaptations and feedback-driven poisoning-time search without view quotas. '
    'All six VMC-aware attacks pass confirmation, while VMC and Reduced detect none of their successful final inputs; mean attack success remains above 95% on both datasets. '
    'Raw-feature controls, rank-fusion diagnostics and two benign binary fixtures further delimit the evidence. '
    'The results establish sensitivity to attack construction and expose a failure of concentration-based triage under the evaluated bounded adaptation, without establishing universal evasion or functioning-malware preservation.')
assert 120<=len(abstract.split())<=150
replace('Abstract—','Abstract—'+abstract)
vi=('Nghiên cứu đánh giá mức tập trung đóng góp đặc trưng theo view để sàng lọc backdoor trong bộ phân loại PE LightGBM. '
    'X-SENTINEL kết hợp VMC và BGS, dùng dữ liệu lành tính để tham chiếu và hiệu chỉnh ngưỡng. '
    'Recall Reduced trên các nhóm giới hạn đặc trưng cũ đạt 35,75% với EMBER2018 và 48,33% với EMBER2024. '
    'Thí nghiệm riêng trên dữ liệu mới so sánh ba selector và tìm kiếm poisoning-time có phản hồi, không ép quota view. '
    'Cả sáu tấn công VMC-aware đều qua xác nhận, nhưng VMC và Reduced không phát hiện mẫu tấn công thành công nào; ASR trung bình vẫn trên 95% ở cả hai bộ dữ liệu. '
    'Kết quả cho thấy giới hạn của sàng lọc theo attribution khi attacker thích nghi, chưa chứng minh khả năng né tránh phổ quát hoặc bảo toàn chức năng malware.')
assert 120<=len(vi.split())<=150
replace('Tóm tắt—','Tóm tắt—'+vi)
replace('3) Empirical failure-mode','3) Empirical failure-mode and adaptive evaluation: We separate a frozen benchmark from a fresh-data follow-up with three selector adaptations and two feedback-driven poisoning objectives. Calibrated comparisons, common-success analysis and binary-fixture diagnostics expose limits of concentration-based triage without developing a replacement detector.')
replace('In this work, we consider an honest model provider',
    'We study an honest model provider whose training pipeline receives poisoned data. The frozen benchmark fixes feature selectors and trigger geometries, while a separate fresh follow-up permits quota-free selection and feedback-driven poisoning-time search under the same fixed learner. After training, a defender inspects individual inputs using the suspicious classifier and small trusted reference pools. We ask when concentrated feature-view attributions and static Behavioral conflicts provide useful suspicion signals, how their performance depends on attack construction, and whether a bounded adaptive objective transfers to held-out detector evasion.')
replace('The model provider executes a fixed LightGBM',
    'The model provider runs fixed LightGBM training and may receive poisoned benign-labeled records. The frozen benchmark uses prescribed feature selectors and geometries that can favor concentration-based detection. The fresh follow-up in Section IV-E removes view quotas and evaluates an attacker with fit, selection and Search access who knows the learner and VMC formula and may retrain candidates. It withholds defender reference, calibration, confirmation and final inputs from the optimizer. The training objective and algorithm remain fixed; this is not arbitrary control over a supplied model. Table I delineates defender resources.')
replace('The evaluated training pipeline is fixed and honest',
    'The fresh study covers bounded, feedback-driven poisoning-time adaptation to the VMC component under fixed honest-provider training. It does not evaluate arbitrary malicious model supply, all adaptive optimizers or an end-to-end objective against Reduced or Full. All six VMC-aware attacks pass confirmation and yield zero observed VMC/Reduced recall on final successful inputs, but each dataset has only three model/search seeds and one fresh shared split. Repeated source IDs across models are not independent files; pointwise per-model intervals must not be interpreted as pooled or simultaneous population guarantees. Exact-SHA256 exclusion does not eliminate near duplicates, family overlap or unknown external exposures, and random roles do not establish temporal generalization.')
replace('The frozen benchmark fixes the study-specific legacy_rare',
    'Selector effects are substantial: the frozen legacy_rare results and the fresh selector/domain matrix answer different conditional questions and must not be pooled. The follow-up adapts Severi configurations [6] to versioned 2,381- and 2,568-dimensional representations, mixed selection data and a declared tie policy; it is not an exact reproduction of every original implementation detail. The raw-kNN control also remains weak in several settings. A strong result on a selected restricted cohort therefore does not establish superiority across attackers, datasets or defender access budgets.')
replace('X-SENTINEL evaluates when feature-view attribution',
    'Feature-view attribution concentration can flag some frozen restricted attacks, but its utility is sensitive to selector and allowed domain. A fresh, quota-free poisoning-time study shows that adaptation to VMC transfers to complete observed evasion of Reduced across six confirmed attacks while retaining high classifier ASR. Same-access raw novelty and auxiliary-model signals exhibit their own limitations. X-SENTINEL is consequently supported as an evaluation framework for conditional diagnostics, not a generally effective backdoor defense. Improved scoring and functioning binary-backdoor validation remain open research problems.')

anchor=find('V. RESULTS')
para('E. Fresh Selector and Poisoning-Time Follow-up',before=anchor,heading=True)
para('We froze a separate seven-role split per dataset after excluding 622,688 known historical SHA256 identifiers, including earlier validation, latency and public-Shadow pools. Fit contains 200,000 balanced records; mixed Selection, Search and Confirmation each contain 10,000 balanced records; Reference and Calibration contain 500 and 2,000 benign records; Final contains 10,000 benign and 10,000 malware records. Only Final uses the official test partition. Both datasets share the new source IDs across seeds 17, 29 and 43. Metadata labels are used by the steward for stratification; optimizer inputs are limited to Fit, Selection and Search. This is known-history ID disjointness, not family or temporal independence. Original is_pe flags are retained; 80 of the 220,000 fresh EMBER2024 attacker records have is_pe=0.',before=anchor)
para('Using the same clean-model Selection SHAP, we adapt three configurations [6]: LargeAbsSHAP with independent MinPopulation values; LargeAbsSHAP with independent CountAbsSHAP values minimizing inverse count plus the sum of absolute SHAP; and signed greedy conditioned selection minimizing inverse count plus signed SHAP over the surviving rows. MinPopulation value ties retain first observation; CountAbsSHAP ties use ascending unique values; conditioned feature ties use lower coordinate index. Each selects K=10 varying coordinates without view quotas. R10 uses a versioned restricted pool: 17 varying V2 coordinates (13 Structural and four Metadata) versus 13 V3 coordinates, all Structural. A10 permits every varying coordinate. These domains do not establish valid binary edits. Three configurations, two domains, two datasets and three seeds produce 36 static attempts at 2% all-fit poisoning (4,000 benign-labeled records).',before=anchor)
para('For each dataset–seed cell, ASR-only and VMC-aware search share the A10 CountAbsSHAP initialization and each evaluate 16 logical candidates. The next proposal mutates the current feedback-selected incumbent, with equal coordinate-replacement/value-change probability and observed float32 Selection values. Poison source IDs, labels and learner remain fixed. ASR uses clean-original eligible Search malware; the VMC objective averages triggered scores over 1,000 fixed eligible original IDs. Feasibility requires at least 1,000 eligible records, ASR at least 50%, paired gain at least 20 points and accuracy loss below 0.5 points. ASR-only maximizes ASR; VMC-aware minimizes mean VMC, with declared ties and shared feasibility-violation ranking. Canonical triggers and input/model/score hashes permit exact reuse without enlarging the logical budget. Infrastructure failures are not no-valid outcomes.',before=anchor)
para('All 36 static attempts and 12 completed adaptive arms were locked globally before releasing fresh Confirmation, Reference, Calibration or Final vectors. Confirmation uses classifier/utility screening only; all completed static models are evaluated even when unconfirmed. Each suspicious model receives its own reference scores and calibration thresholds; source IDs remain paired across models. Primary comparisons are VMC, Reduced, TADR and raw-kNN-top32 with the same trusted access; Full is secondary and uses one 150-round clean Behavioral auxiliary per cell. Classifier threshold is 0.5 and detector alerts require score strictly above the calibration threshold. No held-out score is fed back to search.',before=anchor)

anchor=find('VI. DISCUSSION AND LIMITATIONS')
para('M. Fresh Selector and Adaptive Outcomes',before=anchor,heading=True)
para('All 36 static attempts completed; 28 passed the paired Search/Confirmation screen (15/18 on EMBER2018 and 13/18 on EMBER2024). All 12 adaptive arms completed their budgets and passed confirmation; no no-valid outcome occurred. The two trajectories diverged in all six cells. There were 207 unique poisoned fits rather than the 216 upper-bound projection because exact repeated triggers reused fits, plus six clean main and six Behavioral models. The poisoned training timers sum to 10.87 hours; this excludes selection, scoring, I/O, interruption time and the clean fits and is not total wall time.',before=anchor)
para('Table XX reports all adaptive arms, with three-seed means and sample SDs. Reduced recall falls from 63.10% to zero on EMBER2018 and from 40.42% to zero on EMBER2024 when the objective changes from ASR-only to VMC-aware. Mean classifier ASR remains 98.42% and 95.60%, respectively. VMC also detects none of the six VMC-aware successful pools. On source-aligned common-success intersections, Reduced recall is 62.96% versus zero on EMBER2018 and 40.15% versus zero on EMBER2024, so this contrast is not explained solely by different success denominators. The attacker optimized VMC, not a direct Reduced/Full score objective.',before=anchor)
para('TABLE XX\nFRESH ADAPTIVE OUTCOMES AT CALIBRATION THRESHOLDS',before=anchor,caption=True)
rows=[]
for ds in ('EMBER2018','EMBER2024'):
 for arm in ('asr_only','vmc_aware'):
    a=[r for r in audit['adaptive'] if r['dataset']==ds and r['label']==arm]
    rows.append([ds.replace('EMBER',''),arm.replace('_',' '),mean_sd([x['asr'] for x in a]),
        mean_sd([x['methods']['X_primary_reduced']['successful_recall']['rate'] for x in a]),
        mean_sd([x['methods']['X_primary_reduced']['benign_fpr']['rate'] for x in a]),
        mean_sd([x['methods']['X_primary_reduced']['post_defense_asr']['rate'] for x in a])])
table(['Dataset','Objective','ASR (%)','Reduced recall (%)','Reduced FPR (%)','Post-defense ASR (%)'],rows,[1.6,2.4,2.8,3.1,2.8,3.0],before=anchor)
para('All entries are means ± sample SD over three seeds. Recall conditions on final successful-eligible inputs; post-defense ASR retains the fixed clean-original eligible denominator. Zero observed recall does not prove zero population detection probability. Appendix F reports other methods and per-seed counts.',before=anchor)
para('Static results in Table XXI demonstrate selector sensitivity without an adaptive objective. For example, mean Reduced recall on V2 R10 changes from 43.83% with MinPopulation to 1.66% with CountAbsSHAP; on V3 it changes from 57.68% to 53.66%, while greedy conditioned selection gives 2.90%. These all-attempt summaries retain unconfirmed cases; they must not be substituted for the historical restricted-confirmed headline. Raw-kNN-top32 does not supply a general remedy: its VMC-aware recall is 0.45% on V2 and 10.07% on V3. Full is also nearly or completely bypassed, despite its additional clean-data access (Appendix F).',before=anchor)
para('TABLE XXI\nALL FRESH STATIC ATTEMPTS BY SELECTOR AND DOMAIN',before=anchor,caption=True)
rows=[]
for ds in ('EMBER2018','EMBER2024'):
 for profile,domain in [('feature_restricted','R10'),('vector_stress','A10')]:
  for selector,label in [('min_population','MinPopulation'),('count_abs_shap','CountAbsSHAP'),('signed_shap_conditioned','Greedy combined')]:
    a=[x for x in audit['static'] if x['dataset']==ds and x['label']==profile+'/'+selector]
    rows.append([ds.replace('EMBER',''),domain,label,f"{sum(x['confirmed'] for x in a)}/3",
        mean_sd([x['methods']['X_primary_reduced']['successful_recall']['rate'] for x in a]),
        mean_sd([x['methods']['M3_view_mass']['successful_recall']['rate'] for x in a]),
        mean_sd([x['methods']['raw_knn_top32']['successful_recall']['rate'] for x in a])])
table(['Dataset','Domain','Selector','Conf.','Reduced recall (%)','VMC recall (%)','Raw kNN recall (%)'],rows,[1.5,1.5,2.7,1.6,2.9,2.8,2.7],before=anchor)
para('Calibration targets do not ensure every empirical final FPR is below 1%. Across 48 fresh endpoints per method, Reduced exceeds 1% in 2 cases (maximum 107/10,000), Full in 10 cases (144/10,000), VMC in 20 cases (137/10,000) and TADR in 12 cases (215/10,000); raw-kNN has no exceedance (maximum 93/10,000). These counts concern fresh attempts, not the separate 54-cell frozen analysis. We report observed operating points rather than retroactively tuning thresholds to equal final FPR.',before=anchor)

para('APPENDIX F: FRESH ADAPTIVE DETAILS',heading=True)
para('The following tables retain all adaptive arms. Each method uses its own threshold fixed on the paired fresh benign calibration pool. Three-seed means/SDs summarize model/search variation on a shared source split; they do not represent independently sampled file cohorts. Zero numerators retain their nonzero denominators and pointwise Clopper–Pearson intervals.')
para('TABLE XXII\nFRESH ADAPTIVE METHOD COMPARISON',caption=True)
rows=[]
for ds in ('EMBER2018','EMBER2024'):
 for arm in ('asr_only','vmc_aware'):
  a=[x for x in audit['adaptive'] if x['dataset']==ds and x['label']==arm]
  for method,label in [('M3_view_mass','VMC'),('X_primary_reduced','Reduced'),('TADR','TADR'),('raw_knn_top32','Raw kNN top32'),('X_primary_full','Full (secondary)')]:
    rows.append([ds.replace('EMBER',''),arm.replace('_',' '),label,
        mean_sd([x['methods'][method]['successful_recall']['rate'] for x in a]),
        mean_sd([x['methods'][method]['benign_fpr']['rate'] for x in a])])
table(['Dataset','Objective','Method','Recall (%)','Final benign FPR (%)'],rows,[1.7,2.7,3.5,3.8,4.0])
para('TABLE XXIII\nPER-SEED VMC-AWARE DETECTION COUNTS',caption=True)
rows=[]
for x in audit['adaptive']:
 if x['label']!='vmc_aware':continue
 m=x['methods']['X_primary_reduced']['successful_recall']
 rows.append([x['dataset'].replace('EMBER',''),x['seed'],x['eligible_n'],x['success_n'],
     x['methods']['M3_view_mass']['successful_recall']['count'],m['count'],f"{100*m['pointwise_cp95'][1]:.4f}"])
table(['Dataset','Seed','Eligible n','Success n','VMC TP','Reduced TP','Reduced CP95 upper (%)'],rows,[1.5,1.4,2.1,2.1,2.0,2.2,4.4])
para('All lower recall bounds are zero. Source IDs recur across seeds, so the six denominators must not be pooled into an independent-binomial trial count. Success is defined on the final malware pool after the selected trigger is locked, not selected retrospectively to obtain zero recall.')

# New main-text tables precede the historical appendices. Renumber caption and
# prose references in one pass, retaining their order and avoiding cascades.
numbering={'XX':'XI','XXI':'XII','XI':'XIII','XII':'XIV','XIII':'XV','XIV':'XVI',
           'XV':'XVII','XVI':'XVIII','XVII':'XIX','XVIII':'XX','XIX':'XXI'}
for p in doc.paragraphs:
    before=p.text
    after=re.sub(r'\b([Tt][Aa][Bb][Ll][Ee][Ss]?\s+)([IVXLCDM]+)\b',
                 lambda m:m[1]+numbering.get(m[2],m[2]),before)
    if after!=before:
        p.runs[0].text=after
        for run in p.runs[1:]:run.text=''

doc.core_properties.author='Anonymous';doc.core_properties.last_modified_by=''
doc.core_properties.title=doc.paragraphs[0].text
target=out/'X_SENTINEL_Anonymous_Completed_M3_2026_11_10.docx';doc.save(target)
assert len(doc.tables)==36
(out/'CHANGELOG.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'audit_sha256':hashlib.sha256(audit_path.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'abstract_words':len(abstract.split()),'vi_abstract_words':len(vi.split()),'edits':edits,
    'new_sections':['IV-E','V-M','Appendix F'],'new_tables':['XI','XII','XXII','XXIII'],
    'historical_table_renumbering':numbering,
    'status':'CONTENT_MERGED_PENDING_RENDER_AND_JOURNAL_LAYOUT'},ensure_ascii=False,indent=2),encoding='utf8')
print('Saved new completed-M3 Word; abstract words',len(abstract.split()),len(vi.split()))
