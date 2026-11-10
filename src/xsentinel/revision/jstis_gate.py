"""Global artifact barrier for the six-cell fresh follow-up."""
from pathlib import Path
import json
import hashlib

DATASETS=('EMBER2018','EMBER2024')
SEEDS=(17,29,43)


def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def inventory(root):
    root=Path(root).resolve(); cells={}
    for dataset in DATASETS:
        for seed in SEEDS:
            cell=root/dataset/f'seed_{seed}'; receipt=cell/'ATTACKS_LOCKED.json'
            if not receipt.is_file(): raise ValueError(f'Global held-out barrier: missing {dataset}/{seed}')
            state=json.loads(receipt.read_text(encoding='utf8'))
            if state['status']!='CELL_ATTACKS_LOCKED_NOT_EVALUATED' or state['heldout_roles_opened']:
                raise ValueError('Cell not eligible for global lock')
            for name,expected in state['artifacts'].items():
                target=(cell/name).resolve()
                if not target.is_relative_to(cell.resolve()) or not target.is_file() or file_hash(target)!=expected:
                    raise ValueError('Cell artifact changed or escaped cell root')
            static=json.loads((cell/'static_attempts.json').read_text(encoding='utf8'))
            keys={(r['profile'],r['selector']) for r in static}
            expected={(p,s) for p in ('feature_restricted','vector_stress')
                      for s in ('min_population','count_abs_shap','signed_shap_conditioned')}
            if len(static)!=6 or keys!=expected: raise ValueError('Incomplete static matrix')
            for arm in ('asr_only','vmc_aware'):
                result=json.loads((cell/f'{arm}.json').read_text(encoding='utf8'))
                if result['budget_completed']!=16 or len(result['trajectory'])!=16 or result['arm']!=arm:
                    raise ValueError('Adaptive budget not complete')
                if result['status'] not in ('SELECTED_ON_SEARCH','NO_VALID_ATTACK'):
                    raise ValueError('Infrastructure failure cannot pass global barrier')
                if (result['selected'] is None)!=(result['status']=='NO_VALID_ATTACK'):
                    raise ValueError('Inconsistent search winner')
            cells[f'{dataset}/seed_{seed}']={'receipt_sha256':file_hash(receipt),
                'protocol_digest':state['protocol_digest'],'artifacts':state['artifacts']}
    return {'version':'jstis-six-cell-global-barrier-v1','status':'ALL_ATTACKS_LOCKED_BEFORE_HELDOUT',
            'static_attempts':36,'adaptive_arms':12,'cells':cells}


def verify_global_lock(root,lockpath):
    recorded=json.loads(Path(lockpath).read_text(encoding='utf8'))
    current=inventory(root)
    if recorded!=current: raise ValueError('Global locked inventory changed')
    return recorded
