"""Evidence-bound primary tables; shared source IDs are not pooled across seeds."""
import csv
from pathlib import Path
from xsentinel.utils import read_json,write_json,sha256
from xsentinel.primary_workflow import expected_cells


def report_primary(directories, protocol_path, output):
    protocol=read_json(protocol_path); out=Path(output)
    if out.exists() and any(out.iterdir()): raise FileExistsError('Use a fresh report directory')
    rows={}; proofs={}
    for directory in directories:
        directory=Path(directory); state=read_json(directory/'results.json')
        lock=read_json(directory/'run.lock.json')
        if state['phase']!='final' or lock['protocol_sha256']!=sha256(protocol_path):
            raise ValueError('Matching final-phase evidence required')
        proofs[str(directory.resolve())]=sha256(directory/'results.json')
        for row in state['rows']:
            key=(row['dataset'],row['family'],row['rate'],row['seed'])
            if key in rows: raise ValueError('Duplicate final cell')
            if key not in expected_cells(protocol): raise ValueError('Undeclared final cell')
            dest=directory/f'seed_{row["seed"]}'/row['family']/f'rate_{row["rate"]:g}'
            if read_json(dest/'result.json')!=row: raise ValueError('Aggregate differs from final cell')
            for name,expected in row.get('artifact_sha256',{}).items():
                if sha256(dest/name)!=expected: raise ValueError('Final artifact changed')
            rows[key]=row
    table=[]
    for dataset,family,rate,seed in expected_cells(protocol):
        row=rows.get((dataset,family,rate,seed))
        base={'dataset':dataset,'family':family,'rate':rate,'seed':seed,
              'status':row['status'] if row else 'not_run',
              'confirmed_strong_and_stealth':row.get('independently_confirmed_strong_and_stealth',False) if row else False}
        if row is None or row['status']!='complete':
            table.append({**base,'method':'','error':row.get('error','') if row else ''}); continue
        for variant,result in row['evaluation']['results'].items():
            methods=('TADR','STRIP','X_primary_'+variant) if variant=='reduced' else ('X_primary_full',)
            for method in methods:
                metric=result['methods'][method]
                table.append({**base,'method':method,'n_eligible':result['n_eligible'],
                    'asr_eligible':result['asr_eligible']['rate'],
                    'clean_trigger_asr_eligible':result['clean_trigger_asr_eligible']['rate'],
                    'paired_gain':result['asr_eligible']['rate']-result['clean_trigger_asr_eligible']['rate']
                        if result['n_eligible'] else None,
                    'benign_fpr':metric['benign_fpr']['rate'],
                    'recall_successful_eligible':metric['recall_successful_eligible']['rate'],
                    'post_defense_asr':metric['post_defense_asr']['rate'],
                    'auroc_trigger_vs_benign':metric['auroc_trigger_vs_benign'],
                    'threshold':metric['threshold']})
    out.mkdir(parents=True,exist_ok=True)
    columns=['dataset','family','rate','seed','status','confirmed_strong_and_stealth','method','n_eligible',
        'asr_eligible','clean_trigger_asr_eligible','paired_gain','benign_fpr','recall_successful_eligible',
        'post_defense_asr','auroc_trigger_vs_benign','threshold','error']
    with (out/'results.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns); writer.writeheader(); writer.writerows(table)
    counts={dataset:{status:sum(1 for cell in expected_cells(protocol,[dataset])
        if (rows[cell]['status'] if cell in rows else 'not_run')==status)
        for status in ('complete','unsupported','failed','not_run')} for dataset in protocol['datasets']}
    write_json(out/'report.json',{'protocol_sha256':sha256(protocol_path),'source_results_sha256':proofs,
        'counts':counts,'table':table,'pooling':'No pooling source IDs across seeds/datasets',
        'interpretation':'Retain weak/unconfirmed attacks. Defense-efficacy claims require independently confirmed attacks.'})
    lines=['# X-SENTINEL primary comparison','',
        'Primary M3 is view mass. M5 and Metadata-only stress are outside this primary matrix.','',
        '| Dataset | Complete | Unsupported | Failed | Not run |','|---|---:|---:|---:|---:|']
    for dataset,count in counts.items():
        lines.append('| '+dataset+' | '+' | '.join(str(count[k]) for k in ('complete','unsupported','failed','not_run'))+' |')
    lines+=['','Per-run metrics are in [results.csv](results.csv). Counts and uncertainty are retained in the underlying final cell artifacts.',
        '', 'The same held-out source IDs are reused across seeds within each dataset. These are paired within-run comparisons; do not treat repeated IDs as independent observations or pool datasets into one confidence interval.',
        '', 'Weak, failed and unsupported cells remain explicit. Low ASR or unconfirmed attack viability does not establish detector efficacy.',
        '', 'Full uses three additional clean view models. Calibration times, model bytes and alternating-order warmed-up latency are recorded per completed cell. Shared-process peak memory does not establish an isolated full-versus-reduced RAM difference.']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return {'output':str(out.resolve()),'counts':counts}
