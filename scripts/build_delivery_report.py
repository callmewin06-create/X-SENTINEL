"""Append measured deployment evidence to a new copy of the revised Word report."""
import argparse
import json
from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', required=True)
    parser.add_argument('--repair', action='store_true')
    args = parser.parse_args()
    evidence = Path(args.evidence)
    verified = json.loads((evidence / 'verification.json').read_text())
    restore = json.loads((evidence / 'restore.json').read_text())
    before = json.loads(Path('outputs/delivery_2026_10_14/before/baseline.json').read_text())
    after = json.loads((evidence / 'after/baseline.json').read_text())
    assert restore['all_table_snapshots_equal'] and restore['api_history_and_details_equal']
    target = Path('output/delivery_2026_10_14/X_SENTINEL_Report_With_Deployment.docx')
    if target.exists() and not args.repair:
        raise FileExistsError('Existing report is preserved')
    target.parent.mkdir(parents=True, exist_ok=True)
    doc = Document('output/revision_2026_10_13/X_SENTINEL_Report_Revised.docx')
    stale = [p for p in doc.paragraphs if p.text.startswith('The software includes a Streamlit demonstration, an API adapter')]
    assert len(stale) == 1, 'Expected one implementation-status paragraph'
    stale[0].text = ('The software includes a Vietnamese Streamlit demonstration, a vector API adapter and stored analysis history. '
                    'Read-only V2/V3 PE uploads up to 50 MiB are connected and tested on reviewed benign fixtures. '
                    'Current automated checks pass 66 tests. A PostgreSQL backup was restored into a separate test database, '
                    'and interface checks passed on Windows and Linux Docker on the current physical computer. '
                    'Appendix B records this deployment evidence and its timing boundaries. Authentication, deployment on '
                    'a second physical computer and end-to-end scanning efficacy remain unverified; runtime integration '
                    'does not establish original-dataset binary parity or a realizable malware attack.')
    def para(text):
        return doc.add_paragraph(text)
    def table(headers, rows):
        t = doc.add_table(rows=1, cols=len(headers)); t.style = 'Table Grid'
        for cell, value in zip(t.rows[0].cells, headers): cell.text = value
        repeat = OxmlElement('w:tblHeader'); t.rows[0]._tr.get_or_add_trPr().append(repeat)
        for row in rows:
            cells = t.add_row().cells
            for cell, value in zip(cells, row): cell.text = str(value)
        for row in t.rows:
            row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        return t
    doc.add_page_break()
    doc.add_heading('Appendix B. Deployment and demonstration verification', 1)
    para('This appendix records the system changes verified on 14 October 2026. The preceding research results, fixed LightGBM models and thresholds remain the basis of the scientific claims. Product verification below does not extend the attack-validity or detection-efficacy evidence.')
    doc.add_heading('B.1. Demonstration workflow', 2)
    para('The Vietnamese interface provides Analysis, History and Research views. Analysis accepts a PE file or a labelled reference-vector demo. Research retains method, experiment and reduced/full selections as well as vector/raw-JSON inputs. The upload limit is consistently 50 MiB (52,428,800 bytes), displayed as 50 MB. PE inputs are parsed without execution.')
    para('The result displays two separate decisions: the main model classification and the selected method\'s trigger alert. The explanation compares the existing score with its fixed threshold and describes available component signals. Opening SHAP/view contributions or research details reuses the saved result; it does not invoke another prediction. No alert is not an assurance that a file is safe.')
    doc.add_picture('output/delivery_2026_10_14/ui_result.jpg', width=Inches(6.5))
    para('Figure B1. Actual browser view of the revised result interface, using a reviewed benign fixture; model outputs are predictions rather than ground-truth labels.').style = 'Caption'
    para('For this benign fixture, the selected V3 model predicts malware. This is a false-positive classification in the fixture check, not evidence of malware or a successful detector attack. The screenshot establishes the operational workflow only.')
    doc.add_page_break()
    doc.add_heading('B.2. Verification and timing boundaries', 2)
    table(['Check', 'Observed outcome'], [
        ['Automated regression tests', '66 passed; the recorded run includes PE/schema, result-reuse and service checks.'],
        ['PE → API → history', f"{verified['pe_cases']} dataset/variant cases passed, including metadata, score equality and retry compatibility."],
        ['Interface runtime', 'Four demo cases on Windows and four in Linux Docker on the same physical computer.'],
        ['Above the old upload limit', 'A 21 MiB padded, reviewed PE fixture was parsed successfully by V3. Exact 50 MiB and over-limit checks validate the size guard; a 50 MiB binary integration run is not claimed.'],
        ['Scientific artifact preservation', f"{verified['frozen_primary_files_checked_unchanged']} frozen primary files retain the original SHA-256 hashes. All 44 before/after smoke input results match exactly."]])
    para('Table B1. System acceptance checks. Runtime tests are not a second-machine deployment test. V3 fixture parsing does not establish parity with original dataset binaries or preserve malware functionality under a real binary attack.').style = 'Caption'
    rows = []
    for old, new in zip(before['cases'], after['cases']):
        assert (old['dataset'], old['variant']) == (new['dataset'], new['variant'])
        rows.append([old['dataset'] + ' / ' + old['variant'], f"{old['predict_mean_ms']:.2f}", f"{new['predict_mean_ms']:.2f}"])
    table(['Smoke configuration', 'Before (ms)', 'After (ms)'], rows)
    para('Table B2. Mean warm prediction time for 11 inputs per configuration: one fixture and ten saved benign reference vectors. The operation calculates the available methods including STRIP. These 44 observations do not replace the 54-cell research latency evaluation or establish a statistically reliable speedup.').style = 'Caption'
    para('The interface separates file extraction, model prediction, the grouped API/prediction/storage round trip and application work after the click. Application timing excludes upload and browser rendering; Streamlit AppTest adds its own overhead. First-load time is separate from warm prediction. Larger files can take seconds to parse. The research target of 10 ms remains unmet; a core timing near 28 ms is not the full upload-to-screen latency.')
    doc.add_page_break()
    doc.add_heading('B.3. Persistence, restoration and remaining acceptance', 2)
    counts = ', '.join(f"{name}: {value['count']}" for name, value in restore['tables'].items())
    para('History now retains declared input metadata: display filename, size, kind, file SHA-256, schema, extractor and extraction time. The original file checksum is distinct from the vector checksum. Existing records without this metadata still display. The API receives feature vectors, so metadata is client-declared rather than independent backend verification of binary bytes.')
    para(f"A PostgreSQL dump was restored into the new isolated database {restore['restore_database']}. Every mapped table's row count and canonical-row SHA-256 match the live snapshot ({counts}). API history and {restore['api_details_checked']} result-detail responses also match. The live database was not overwritten. The backup is retained locally and is excluded from the peer deployment package.")
    doc.add_picture('output/delivery_2026_10_14/ui_history.jpg', width=Inches(6.5))
    para('Figure B2. Actual history interface. A named test input can be reopened with the explanation from its stored result.').style = 'Caption'
    para('Acceptance on another physical computer is pending. The user deferred this step to 15 October 2026, when a teammate will build and test the supplied Docker package. Windows and Linux Docker checks on the current computer must not be reported as that independent test.')
    para('The deployment remains a local shared-history demonstration without per-user authentication. M5, new attack experiments and full fit-filter/retraining runs remain conditional extensions. The dependency fixes support the existing V3 runtime and retain NumPy 1.26.4; they do not modify method formulas or detection thresholds.')
    doc.save(target)
    print(target)


if __name__ == '__main__': main()
