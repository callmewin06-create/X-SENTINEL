"""Exact original-vs-selected comparison and interleaved local timing."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from xsentinel.detection.detector import Detector
from xsentinel.service.scoring import score_input
from xsentinel.service.registry import BundleRegistry
from xsentinel.attacks.primary import VectorTrigger
from xsentinel.demo_provenance import demo_ground_truth
from xsentinel.result_pdf import result_pdf,history_pdf
from xsentinel.utils import read_json,sha256,write_json

OUT=Path('outputs/implementation_2026_10_20')


def stats(values):
    return {'n':len(values),'mean_ms':float(np.mean(values)),'p50_ms':float(np.quantile(values,.5)),
            'p95_ms':float(np.quantile(values,.95)),'p99_ms':float(np.quantile(values,.99))}


def main():
    source=subprocess.run(['git','show','HEAD:src/xsentinel/detection/detector.py'],check=True,capture_output=True).stdout.decode('utf8')
    legacy={};exec(compile(source,'<original detector>','exec'),legacy)
    component_source=subprocess.run(['git','show','HEAD:src/xsentinel/detection/components.py'],check=True,capture_output=True).stdout.decode('utf8')
    legacy_components={};exec(compile(component_source,'<original components>','exec'),legacy_components)
    legacy['primary_components']=legacy_components['primary_components']
    (OUT/'detector_before.py').write_text(source,encoding='utf8')
    (OUT/'components_before.py').write_text(component_source,encoding='utf8')
    registry=BundleRegistry();rows=[];samples=[]
    for dataset in ('EMBER2018','EMBER2024'):
        pool=Path('outputs/fusion_binary_latency_2026_10_20/final_pool')/dataset
        X=np.load(pool/'X.npy');y=np.load(pool/'y.npy');ids=np.load(pool/'ids.npy')
        for variant in ('reduced','full'):
            entry=next(e for e in registry.entries.values() if e['dataset']==dataset and e['variant']==variant
                and e['family']=='spread_structural' and e['rate']==.02 and e['seed']==17)
            path=Path('outputs/primary')/entry['relative_path']
            start=time.perf_counter();old=legacy['Detector'].load(path);old_cold=(time.perf_counter()-start)*1000
            start=time.perf_counter();new=Detector.load(path);new_cold=(time.perf_counter()-start)*1000
            trigger=VectorTrigger(**read_json(path.parent/'attack.json')['trigger'])
            malware=trigger.apply(X[y==1][:50],new.schema);benign=X[y==0][:50]
            vectors=np.concatenate([benign,malware]);order=np.random.default_rng(20261020).permutation(len(vectors))
            method='X_primary_'+variant
            before,after,serialize,phases=[],[],[],[]
            # Warm both paths without response caching.
            old.predict(vectors[:1]);new.predict_selected(vectors[:1],method)
            for position,j in enumerate(order):
                x=vectors[j:j+1]
                if position%2:
                    actual=new.predict_selected(x,method);expected=old.predict(x)
                else:expected=old.predict(x);actual=new.predict_selected(x,method)
                before.append(expected[3]);after.append(actual[3]);phases.append(actual[2]['phase_timings_ms'])
                for key in actual[0]:
                    np.testing.assert_allclose(actual[0][key],expected[0][key],rtol=0,atol=1e-12)
                    np.testing.assert_array_equal(actual[1][key],expected[1][key])
                np.testing.assert_array_equal(actual[2]['malware_probability'],expected[2]['malware_probability'])
                np.testing.assert_array_equal(actual[2]['phi'],expected[2]['phi'])
                start=time.perf_counter();result=score_input(new,x,method,scope='selected');serialize.append((time.perf_counter()-start)*1000)
            rows.append({'dataset':dataset,'variant':variant,'n_unique_vectors':len(vectors),'unchanged_scores_flags':True,
                'original_suite':stats(before),'selected_core':stats(after),'selected_serialized':stats(serialize),
                'cold_load_original_ms':old_cold,'cold_load_new_ms':new_cold,
                'phase_mean_ms':{key:float(np.mean([p[key] for p in phases])) if phases[0][key] is not None else None for key in phases[0]}})
            result=score_input(new,new.reference[:1],method,scope='selected')
            result.update(ground_truth=demo_ground_truth(entry['state'],new.reference[:1],True),demo_mode=True,
                input_metadata={'name':'KIỂM THỬ · Mẫu tham chiếu '+dataset+' '+variant,'kind':'demo'},
                experiment={'variant':variant},input_sha256=hashlib.sha256(new.reference[:1].astype('<f4').tobytes()).hexdigest(),
                request_id='qa-'+dataset+'-'+variant,created_at='2026-10-20T00:00:00+00:00',saved=True)
            samples.append(result)
            print(json.dumps(rows[-1],ensure_ascii=True),flush=True)
    qa=OUT/'pdf_qa';qa.mkdir(exist_ok=True)
    (qa/'detail.pdf').write_bytes(result_pdf(samples[-1]))
    history=[]
    for i in range(45):
        row=dict(samples[i%4],request_id=f'QA_{i:03}')
        row['input_metadata']={'name':f'KIỂM THỬ {i} · tên <>& '+'tệp_dài_'*7}
        row['variant']=samples[i%4]['experiment']['variant'];history.append(row)
    history[1]['main_classification']=None;history[1]['backdoor_alert']=None
    (qa/'history.pdf').write_bytes(history_pdf(history,created_at='2026-10-20T01:00:00+00:00'))
    write_json(OUT/'sample_results.json',samples)
    write_json(OUT/'latency.json',{'cases':rows,'original_source_sha256':sha256(OUT/'detector_before.py'),
        'original_components_sha256':sha256(OUT/'components_before.py'),
        'scope':'Interleaved warm exact original HEAD suite vs selected core, 100 unique same vectors per dataset/variant; serialization measured separately. Same Windows host, excludes upload/PE/API/DB/browser. Not a VM benchmark or a universal 10 ms guarantee.'})
    before=read_json(OUT/'primary_before.json')
    assert all(sha256(path)==digest for path,digest in before.items())
    write_json(OUT/'primary_unchanged.json',{'files':len(before),'unchanged':True})


if __name__=='__main__':main()
