"""Integrate BODMAS and verified maintenance findings into the IEEE body.

Preserve the original title, equations, images, styles and frozen research data.
"""
from copy import deepcopy
import json
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from docx.oxml.ns import qn
from build_bodmas_report_2026_10_23 import NS, text, sha, replace_span, build_appendix

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'outputs/repair_2026_10_23'
OUT = ROOT / 'output/repair_2026_10_23'
SOURCE = ROOT / 'output/ieee_2026_10_16/X_SENTINEL_IEEE_1col.docx'
TARGET = OUT / 'X_SENTINEL_IEEE_1col_REVISED_2026_10_23.docx'


def p(value):
    return {'kind':'p','text':value}


def h(value):
    return {'kind':'heading2','text':value}


def cap(value):
    return {'kind':'caption','text':value}


def table(rows, widths):
    return {'kind':'table','rows':rows,'widths':widths}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    benign=json.loads((QA/'benign_summary.json').read_text())
    cross=json.loads((QA/'cross_diagnosis.json').read_text())
    tests=etree.parse(str(QA/'pytest_verified.xml')).find('testsuite')
    assert int(tests.get('failures'))==0 and int(tests.get('errors'))==0
    passed=int(tests.get('tests'))-int(tests.get('skipped'))
    runtime=json.loads((QA/'linux_acceptance/verification.json').read_text())
    assert runtime['recovery_ok'] and len(runtime['cases'])==4
    source_sha=sha(SOURCE.read_bytes())
    setup=[h('E. Supplementary static binary checks and maintenance diagnostics'),
        p('A member supplied a BODMAS disarmed-results archive from a Kali Linux VM. The main check used the same 200 selected byte hashes for EMBER2018 and EMBER2024, each in Reduced and Full modes, with frozen spread-Structural models at seed 17 and 2% poisoning. The 20-file pilot is a subset of these 200 inputs. The archive reports sorted-path sampling with seed 17; the complete candidate population was not supplied, so selection cannot be independently reconstructed. Labels are member-declared, and no verified trigger labels are available. We audited the manifests, structured records and reported bundle settings without executing or independently rescoring the malware binaries.'),
        p('A separate local diagnostic check, dated 23 October 2026, froze a manifest before scoring 50 installed PE files: 30 System32 executables, 10 System32 DLLs and 10 .NET Framework executables. Sorted candidates were permuted with seed 23 and selected by unique byte hash. Installed origin supplies a declared benign label, not independently established ground truth; signature inspection returned Valid for 19 and NotSigned for 31. Three previously observed source-built C# fixtures were analyzed as a separate cohort. Each extracted vector was evaluated by the paired clean and poisoned main models at the same 0.5 classification threshold, while the original Reduced/Full detector thresholds were retained. Clean main models are diagnostic controls and are not additional resources supplied to Reduced.'),
        p('We also reexamined the previously observed 20 October fusion-validation pool, which is distinct from the earlier fresh pool in Section IV-D. No new method was selected in this maintenance pass. We checked all 108 metric rows for the nine confirmed EMBER2024 Cross runs, their rank transforms and fusion arithmetic, and replayed raw component scores on the first 32 triggered inputs per run. Source-paired bootstrap contrasts resample the shared source IDs together across the nine fixed models; they do not estimate uncertainty over future models or seeds.')]
    main_rows=[['Model','Mode','Selected','Scored','Errors','MALWARE','Alerts'],
               ['2018','Reduced','200','175','25','162','2'],['2018','Full','200','175','25','162','2'],
               ['2024','Reduced','200','175','25','175','0'],['2024','Full','200','175','25','175','0']]
    benign_rows=[['Cohort','Model','Scored','Clean M','Poisoned M','Alerts R','Alerts F']]
    for row in [r for r in benign if r['variant']=='reduced']:
        full=next(r for r in benign if r['cohort']==row['cohort'] and r['dataset']==row['dataset'] and r['variant']=='full')
        assert all(full[k]==row[k] for k in ('scored','clean_called_malware','poisoned_called_malware'))
        benign_rows.append(['Installed 50' if row['cohort']=='installed50' else 'Owned 3',row['dataset'].replace('EMBER',''),str(row['scored']),str(row['clean_called_malware']),str(row['poisoned_called_malware']),str(row['trigger_alerts']),str(full['trigger_alerts'])])
    low,high=cross['full_W25_minus_W50']['source_paired_bootstrap_percentile95']
    results=[h('I. BODMAS static binary results'),
        cap('TABLE XVII\nBODMAS STATIC CHECK WITH FIXED MODELS AND THRESHOLDS'),
        table(main_rows,[.65,.85,.7,.65,.65,.85,.65]),
        p('Table XVII describes 200 unique files, not 800 independent samples. All four configurations processed the same 175 files and rejected the same 25 files, giving 87.5% processing coverage. All failures reported Invalid PE signature/header offset at the format guard before LIEF. Their cause has not been established from the results archive. Failed files have no classification or trigger decision; they are not counted as benign or as negative detector predictions.'),
        p('The 2018 main model called 162/175 scored files MALWARE and 13 BENIGN. The 2024 main model called 175/175 scored files MALWARE. These observations do not establish 100% system accuracy: 25 selected inputs were unavailable and this cohort has no representative benign comparison. Reduced and Full share the main classifier, so matching classification counts are expected. The two 2018 alerts concern the same two hashes in both modes; both were classified BENIGN. Without verified trigger labels, neither alert confirms a backdoor or proves that a classification error was corrected. Alert rates are 2/175 among scored files or 2/200 among all selected files, with the denominator stated explicitly.'),
        h('J. Benign input diagnostics'),
        cap('TABLE XVIII\nLOCAL DIAGNOSTICS WITH CLEAN AND POISONED MAIN MODELS'),
        table(benign_rows,[1.05,.6,.6,.7,.85,.7,.7]),
        p('In Table XVIII, Clean M and Poisoned M count files called MALWARE by the two main models; Alerts R and Alerts F count the Reduced and Full detector flags. All 50 installed inputs were processed for both schemas, and both main models called all 50 BENIGN. There was one detector alert for 2018 Reduced and one for 2024 Full. The other two configurations produced no alerts on these 50 files. Thus classifier errors and detector alerts must be reported separately. This convenience sample and its declared labels do not establish a population false-positive rate or a future 1% guarantee.'),
        p('Both the clean and poisoned 2024 main models called all three source-built C# fixtures MALWARE; the 2018 main models called all three BENIGN. No trigger alerts occurred on these fixtures. The 2024 failures therefore also occur without the poisoned main model, so this check does not support attributing them solely to poisoning or to M3/M4 fusion. Extractor compatibility and the classifiers\' behavior on this small .NET cohort remain possible contributors. No threshold, main model or fixture label was changed to improve the displayed result.'),
        h('K. Cross diagnostics and operational repairs'),
        p(f'The Cross cache audit and replayed subset showed no discrepancy in the checked component scores, reference ranks, strict-threshold counts or W50/W25 arithmetic. On the observed 20 October pool, W50 mean recall was 0.00% for Reduced and 5.73% for Full; W25 Full reached 10.84%, versus 13.29% for raw M4-F. The W25-minus-W50 Full contrast was 5.11 percentage points with a source-paired bootstrap percentile interval of {100*low:.2f} to {100*high:.2f} points over these fixed models. This diagnostic contrast is not a new independent validation. Modest improvement in one cohort does not resolve poor Cross coverage or justify replacing the locked W50 method.'),
        p(f'PE extraction now runs in a disposable child process with a configurable 60-second default deadline and one concurrent worker per parent process. Timeout, child failure, invalid output and invalid headers return an unavailable result. A failed retry clears the prior displayed result. Controlled sleeping/crashing workers were terminated and subsequent valid extraction succeeded on Windows and Linux Docker on the same physical host. The current regression run passed {passed} tests with one Windows symlink test skipped. Four Linux API cases verified direct-score agreement, retry/readback behavior and PDF generation; this is integration evidence, not a detector-efficacy benchmark. Process separation is not a complete security sandbox. A Dockerfile line-ending defect that prevented a Linux image build was corrected; the API and dashboard remain bound to localhost.')]
    # The raw reduced component is commonly exactly zero; weight changes cannot
    # create a missing positive Behavioral signal. Keep this measured limitation.
    zero=[r['successful_m4_zero_fraction'] for r in cross['details'] if r['variant']=='reduced']
    results[-2]['text'] += f' Across the nine runs, reduced M4 was exactly zero on {100*min(zero):.2f}% to {100*max(zero):.2f}% of successful eligible attacks; its positive and benign median reference ranks were identical within every run. This ties the reduced failure to weak component separation in this cohort rather than an observed arithmetic error.'
    results[-1]['text'] += ' Worker startup is included in extraction wall time, approximately 1.6 to 2.0 seconds in the four Linux fixture smoke checks; this containment change does not claim an end-to-end speedup.'
    discussion=[p('The binary checks add evidence about input handling and predictions under fixed models, while leaving the principal binary-backdoor claim unresolved. BODMAS has no verified labels for the study\'s trigger and the returned archive does not contain binaries or vectors for independent rescoring. Disarmed bytes also do not establish preserved malware functionality. The 25 rejected inputs remain a coverage limitation with an unresolved cause, not evidence that removing the format guard would be correct.'),
        p('The installed-file diagnostic cohort is small, selected from one machine and not established as disjoint from all model training data. Its favorable classification counts do not erase the three owned-fixture errors, and its trigger alerts are a separate outcome. BODMAS labels and VM provenance remain partly unverified; mismatched smoke/benign text logs and the rebuilt benign fixture require member follow-up. These checks support narrower, traceable claims rather than a general statement that the system is now reliable on arbitrary executables.')]
    appendix=[{'kind':'heading1','text':'APPENDIX C. BINARY AUDIT AND MAINTENANCE EVIDENCE'},
        h('A. Provenance and unresolved discrepancies'),
        p('The received archive contains 16 runs covering smoke, benign, pilot and main checks across four model configurations. CSV records, summary records and canonical manifests were cross-checked. Bundle IDs, schema identifiers, method names and thresholds match the distributed kit. These checks establish internal consistency of the structured results, not the exact model/code bytes or isolation settings actually used in the VM.'),
        p('Smoke and benign checks refer to one unique member-declared benign hash, not two controls. The CSV/JSON probabilities are approximately 0.044262 for 2018 and 0.957886 for 2024, whereas the corresponding text logs state 0.169 and 0.748. The main tables use the consistent structured records; the log discrepancy remains unresolved. The member\'s benign hash also differs from the distributed fixture hash, and its exact source/build has not been reconciled. No original-to-disarmed mapping or complete candidate population was available to establish label lineage and overlap with training/calibration data.'),
        p('A read-only follow-up utility was prepared to inspect the existing 25 failed hashes on the member\'s VM. It records file size, MZ marker, PE header offset, signature and agreement with the original byte hash. No follow-up output was available for this revision. The utility neither repairs headers nor executes samples; absence of that evidence is retained as pending rather than claimed as a parser fix.'),
        h('B. Timing boundaries'),
        p('The member\'s original kit used the suite path including STRIP. Table C-I summarizes only the 175 scored inputs per configuration and excludes model loading and manifest construction. Prediction time is not end-to-end upload time. These VM observations cannot measure the speedup of the selected-method path on a different Windows host. One 2024 input took approximately 21.6 seconds; the new process deadline was not retroactively applied to these historical runs.'),
        cap('TABLE C-I\nMEMBER VM TIMING IN MILLISECONDS AMONG SCORED FILES'),
        table([['Model','Mode','Prediction median','Extraction median','Total median','Total P95'],
               ['2018','Reduced','15.48','32.31','59.64','564.44'],['2018','Full','15.55','38.43','61.75','573.94'],
               ['2024','Reduced','13.93','182.14','197.86','3853.45'],['2024','Full','14.07','176.38','193.35','3818.21']],
               [.65,.85,1,1,1,1]),
        h('C. Reproduction and current deployment scope'),
        p('The dated maintenance outputs retain the frozen diagnostic selection, per-file predictions, extracted vectors, signature observations, Cross cache audit, regression report and Linux integration evidence. The 50 installed files were not executed or bundled for redistribution. Original primary models, triggers and thresholds remain unchanged. Unit and integration tests do not replace independent evaluation of malware detection, realistic triggered binaries, hostile-parser security or deployment on a second physical computer.'),
        p('Authentication remains intentionally deferred for the local shared-history demonstration. A public or multiuser deployment would require a separate access-control design. Appendix B preserves the earlier deployment record; its historical test counts and timing figures are not the current maintenance acceptance results.')]
    with ZipFile(SOURCE) as source:
        root=etree.fromstring(source.read('word/document.xml')); body=root.find('w:body',NS)
        original=list(body); before=[deepcopy(el) for el in body]
        replace_span(original[8], 'This study trains and evaluates only LightGBM models; these other datasets are background references and are not additional experiments',
            'This study trains and evaluates only LightGBM models; SOREL-20M is background, while Sections IV-E and V-I add a supplementary static BODMAS check using frozen EMBER-trained models')
        # Preserve abstract results; add the binary scope rather than replacing them.
        previous=original[5].findall(qn('w:r'))[-1]
        run=etree.SubElement(original[5],qn('w:r'))
        if previous.find(qn('w:rPr')) is not None:run.append(deepcopy(previous.find(qn('w:rPr'))))
        t=etree.SubElement(run,qn('w:t'));t.set(qn('xml:space'),'preserve')
        t.text=' A supplementary static BODMAS check processes 175 of 200 selected files; separate benign diagnostics and operational repairs expose remaining coverage and classification limitations.'
        replace_span(original[150],'no weights are optimized using final outcomes.',
            'its weights are not changed using final outcomes. The separately dated fusion supplement used previously observed data for development and a distinct local validation pool; W25 remains supplementary.')
        replace_span(original[154], text(original[154]),
            f'The software includes a Vietnamese Streamlit demonstration, a vector API adapter and stored analysis history. Read-only V2/V3 PE uploads up to 50 MiB now use a disposable extraction process and explicit failure states. The 23 October regression run passed {passed} tests with one Windows symlink test skipped. Windows checks and Linux Docker integration ran on the same physical computer, including worker termination/recovery and four marked API/history/PDF cases. Appendix B retains the historical deployment evidence; Appendix C records the new binary audit and its limitations. Authentication is deferred for the localhost-only shared-history demo. Deployment on a second physical computer and end-to-end scanning efficacy remain unverified; runtime integration does not establish original-dataset binary parity or a realizable malware attack.')
        replace_span(original[224],'APPENDIX B. DEPLOYMENT AND DEMONSTRATION VERIFICATION',
                     'APPENDIX B. HISTORICAL DEPLOYMENT AND DEMONSTRATION VERIFICATION')
        # The old Appendix A table follows the two new body tables.
        # Keep the number inside its SEQ field; replacing across the field
        # boundary duplicates the numeral when Word refreshes the field.
        caption = original[219]
        replace_span(caption, 'XVII', 'XIX')
        instructions = caption.xpath('.//w:instrText', namespaces=NS)
        assert len(instructions) == 1 and 'SEQ Table' in instructions[0].text
        instructions[0].text = r' SEQ Table \r 19 \* ROMAN '
        for node in build_appendix(setup): original[82].addprevious(node)
        for node in build_appendix(results): original[147].addprevious(node)
        for node in build_appendix(discussion): original[152].addprevious(node)
        section=body.find('w:sectPr',NS)
        for node in build_appendix(appendix):section.addprevious(node)
        changed=[i for i,(a,b) in enumerate(zip(before,original)) if etree.tostring(a,method='c14n',exclusive=True)!=etree.tostring(b,method='c14n',exclusive=True)]
        assert changed==[5,8,150,154,219,224],changed
        assert etree.tostring(before[0],method='c14n',exclusive=True)==etree.tostring(original[0],method='c14n',exclusive=True),'Title must be unchanged'
        with ZipFile(TARGET,'w') as dest:
            for item in source.infolist():dest.writestr(item,etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True) if item.filename=='word/document.xml' else source.read(item.filename))
    assert sha(SOURCE.read_bytes())==source_sha
    with ZipFile(SOURCE) as a,ZipFile(TARGET) as b:
        changes=[name for name in a.namelist() if a.read(name)!=b.read(name)]
        assert changes==['word/document.xml']
    report={'source_sha256':source_sha,'output_sha256':sha(TARGET.read_bytes()),'title_preserved':True,
        'changed_original_body_indices':changed,'changed_parts':changes,'original_source_preserved':True,
        'new_body_sections':['IV-E','V-I','V-J','V-K','VI additional discussion'],
        'new_tables':['XVII BODMAS','XVIII benign diagnostics','C-I timing'], 'renumbered_table':'old XVII -> XIX in Appendix A',
        'passed_tests':passed,'output':str(TARGET)}
    (QA/'report_preservation.json').write_text(json.dumps(report,indent=2)+'\n')
    (QA/'report_blocks.json').write_text(json.dumps({'setup':setup,'results':results,'discussion':discussion,'appendix':appendix},indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
