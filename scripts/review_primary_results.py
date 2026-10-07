"""Read-only audit of locked primary results; writes a separate review namespace."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.detection.detector import Detector
from xsentinel.evaluation.primary import outcome_metrics
from xsentinel.primary_workflow import lock_primary_selector
from xsentinel.primary_reporting import report_primary

METHODS=('TADR','STRIP','X_primary_reduced','X_primary_full')
FIELDS=('benign_fpr','recall_successful_eligible','post_defense_asr','auroc_trigger_vs_benign')


def describe(rows):
    summary={}
    for method in METHODS:
        selected=[r for r in rows if r['method']==method]
        summary[method]={'runs':len(selected),**{key:{'mean':statistics.mean(r[key] for r in selected if r[key] is not None),
            'min':min(r[key] for r in selected if r[key] is not None),
            'max':max(r[key] for r in selected if r[key] is not None)} for key in FIELDS}} if selected else None
    return summary


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='outputs/primary_review/review_2026_10_07')
    args=parser.parse_args(); out=Path(args.out)
    if out.exists() and any(out.iterdir()): raise FileExistsError('Existing review preserved; choose fresh --out')
    out.mkdir(parents=True,exist_ok=True)
    protocol=Path('configs/primary_protocol.json')
    datasets=('EMBER2018','EMBER2024')
    finals=[Path('outputs/primary')/d/'protocol_v2' for d in datasets]
    published=Path('outputs/primary_reports/report_2026_10_06')
    report_primary(finals,protocol,out/'reconstructed_report')
    rebuilt=read_json(out/'reconstructed_report/report.json'); original=read_json(published/'report.json')
    if rebuilt!=original: raise ValueError('Published report differs from locked final cell evidence')
    if sha256(out/'reconstructed_report/results.csv')!=sha256(published/'results.csv'):
        raise ValueError('Published CSV differs from reconstructed evidence')
    locks={d:read_json(p/'run.lock.json') for d,p in zip(datasets,finals)}
    wanted={v['selector_lock_sha256'] for v in locks.values()}
    if len(wanted)!=1: raise ValueError('Datasets do not share selector lock')
    selectors=[p for p in Path('outputs/primary_pipeline').glob('*/selector.lock.json') if sha256(p) in wanted]
    if not selectors: raise ValueError('Frozen selector proof missing')
    original_selector=read_json(selectors[0])
    lock_primary_selector([Path('outputs/primary_development')/d/'round_1' for d in datasets],protocol,out/'selector_rechecked.json')
    if read_json(out/'selector_rechecked.json')!=original_selector:
        raise ValueError('Common selector no longer matches independent development proof')
    audited=[]; resources=[]
    for dataset,directory in zip(datasets,finals):
        rows=read_json(directory/'results.json')['rows']
        role_state=read_json(Path('data/primary')/dataset/'protocol_v2/roles.json')
        expected_ids=set(role_state['ids']['final'])
        for index,row in enumerate(rows,1):
            if row['status']!='complete': raise ValueError('Unexpected incomplete final cell')
            cell=directory/f'seed_{row["seed"]}'/row['family']/f'rate_{row["rate"]:g}'
            confirmation=Path('outputs/primary_confirmation')/dataset/'round_1'/f'seed_{row["seed"]}'/row['family']/f'rate_{row["rate"]:g}/result.json'
            if sha256(confirmation)!=row['confirmation_result_sha256']: raise ValueError('Confirmation proof changed')
            if read_json(confirmation)['independently_confirmed_strong_and_stealth']!=row['independently_confirmed_strong_and_stealth']:
                raise ValueError('Final viability label differs from confirmation')
            prediction_names=[n for n in row['artifact_sha256'] if n.startswith('paired_predictions') and n.endswith('.npz')]
            if len(prediction_names)!=1: raise ValueError('Ambiguous paired predictions')
            with np.load(cell/prediction_names[0],allow_pickle=False) as predictions:
                bi=predictions['benign_ids'].astype(str); mi=predictions['malware_ids'].astype(str)
                if len(bi)!=10000 or len(mi)!=10000 or len(set(bi)|set(mi))!=20000 or set(bi)|set(mi)!=expected_ids:
                    raise ValueError('Final source IDs differ from frozen role')
                for variant in ('reduced','full'):
                    bundle=cell/f'bundle_{variant}'
                    if sha256(bundle/'bundle.json')!=row['bundle_manifest_sha256'][variant]: raise ValueError('Bundle manifest changed')
                    detector=Detector.load(bundle,expected_dataset=dataset)
                    if detector.enable_m5 or bool(detector.views)!=(variant=='full'): raise ValueError('Bundle resource/protocol mismatch')
                    if hashlib.sha256(detector.model.model_to_string().encode()).hexdigest()!=row['evaluation']['main_model_sha256']:
                        raise ValueError('Bundle main differs from evaluated model')
                    metrics=row['evaluation']['results'][variant]
                    scores={k:predictions[f'{variant}_trigger_{k}'] for k in metrics['methods']}
                    benign={k:predictions[f'{variant}_benign_{k}'] for k in metrics['methods']}
                    result=outcome_metrics(scores,detector.thresholds,benign,predictions['clean_malware_p'],
                        predictions['triggered_main_p'],predictions['clean_trigger_p'],detector.config['malware_threshold'])
                    if result!=metrics: raise ValueError('Saved final counts/metrics differ from paired predictions')
                    del detector
            resources.append({'dataset':dataset,'family':row['family'],'rate':row['rate'],'seed':row['seed'],
                **row['resources'],'paired_comparison':row['evaluation']['paired_comparison']})
            audited.append({'dataset':dataset,'family':row['family'],'rate':row['rate'],'seed':row['seed'],
                'result_sha256':sha256(cell/'result.json'),'prediction_sha256':sha256(cell/prediction_names[0]),
                'confirmed':row['independently_confirmed_strong_and_stealth']})
            print(f'Audit {dataset}: {index}/{len(rows)} cells, both bundles and prediction metrics verified',flush=True)
    table=original['table']; summaries={}
    for dataset in datasets:
        selected=[r for r in table if r['dataset']==dataset]
        confirmed=[r for r in selected if r['confirmed_strong_and_stealth']]
        summaries[dataset]={'confirmed_cells':len(confirmed)//4,'all_runs':describe(selected),'confirmed_only':describe(confirmed),
            'families':{family:{'confirmed_cells':sum(r['method']=='TADR' and r['confirmed_strong_and_stealth'] for r in selected if r['family']==family),
                'all_runs':describe([r for r in selected if r['family']==family]),
                'confirmed_only':describe([r for r in confirmed if r['family']==family])} for family in read_json(protocol)['family_geometry']}}
    review={'audit':'54 final cells; 108 real bundles loaded; final IDs and metrics recomputed from saved paired predictions',
        'source_report_sha256':sha256(published/'report.json'),'source_csv_sha256':sha256(published/'results.csv'),
        'selector':original_selector,'cells':audited,'summaries':summaries,'resources':resources,
        'aggregation':'Equal-weight descriptive per-run means and ranges. No pooled confidence intervals or independence claims across reused IDs.',
        'original_artifacts_modified':False}
    write_json(out/'review.json',review)
    lines=['# Đọc và đối chiếu kết quả primary — 07/10/2026','',
        'Đây là bản review mới, không sửa model, ngưỡng, dữ liệu, kết quả hoặc báo cáo đã khóa.','',
        '## Kiểm tra bằng chứng','',
        '- 54/54 final cells complete; cả 108 bundle reduced/full được nạp và kiểm tra checksum/schema.',
        '- 20.000 final source IDs mỗi run khớp roles đã khóa; metrics/counts tái tính từ paired_predictions khớp kết quả lưu.',
        '- CSV và JSON báo cáo tái dựng khớp bản đã xuất. Selector khóa được kiểm tra lại chỉ từ development.',
        f'- Selector chung: **{original_selector["chosen_selector"]}**. Legacy có {original_selector["summaries"]["legacy_rare"]["strong_and_stealth_count"]}/54 development runs đạt; signed conditioned có {original_selector["summaries"]["signed_shap_conditioned"]["strong_and_stealth_count"]}/54.','',
        '## Attack đủ mạnh và kín theo heuristic','']
    for dataset in datasets:
        lines.append(f'- {dataset}: {summaries[dataset]["confirmed_cells"]}/27 run đạt cả development và confirmation. Các run còn lại vẫn được giữ.')
    lines+=['','## Detector trên các run đã đạt confirmation','',
        'Bảng dưới lấy trung bình đều theo run đã đạt cả hai screen. Đơn vị là %, không gộp sample qua seeds. Đây là thống kê mô tả, không phải CI hoặc kiểm định thắng/thua chung. Recall tính trên attack thành công trong tập malware eligible.','',
        '| Dataset | Method | Runs | Benign FPR | Recall successful eligible | Post-defense ASR | AUROC |',
        '|---|---|---:|---:|---:|---:|---:|']
    for dataset in datasets:
        for method,value in summaries[dataset]['confirmed_only'].items():
            lines.append(f'| {dataset} | {method} | {value["runs"]} | '+ ' | '.join(f'{100*value[k]["mean"]:.2f}' for k in FIELDS)+' |')
    lines+=['','## Diễn giải','',
        'Full/reduced được so trên cùng main, mẫu, reference và calibration. Full có thêm ba clean view models. Kết quả cần đọc theo family/rate/seed và paired CI từng run; không dùng bảng trung bình để nói mọi tình huống full tốt hơn.',
        '', 'FPR calibration mục tiêu 1% không đảm bảo FPR final. AUROC đo phân biệt triggered malware và benign, không đồng nghĩa recall tốt ở ngưỡng đã khóa.',
        '', 'M3 vẫn là view_mass; M5 và Metadata-only stress không nằm trong phần chính. Behavioral là imports/exports tĩnh; trigger là sửa vector, chưa chứng minh khả thi trên binary PE.',
        '', 'Whole-process peak RAM không tách được RAM riêng từng variant. Latency là warmed single-input, có STRIP, cùng mẫu và thứ tự alternating; không phải đo end-to-end upload/extraction.',
        '', 'Chi tiết family, mọi run yếu, ranges, paired CI và resource nằm trong review.json và artifacts gốc. Không retune dựa vào final.']
    (out/'review.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({'output':str(out.resolve()),'confirmed':{d:summaries[d]['confirmed_cells'] for d in datasets}},ensure_ascii=True),flush=True)


if __name__=='__main__': main()
