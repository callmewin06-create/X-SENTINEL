"""Discover exported primary bundles without changing research artifacts."""
from pathlib import Path

FAMILY_NAMES = {
    'concentrated_structural': 'Concentrated Structural',
    'spread_structural': 'Spread Structural',
    'cross_3view_stress': 'Cross three-view vector stress',
}


def primary_catalog(dataset, root='outputs/primary'):
    if dataset not in ('EMBER2018', 'EMBER2024'):
        raise ValueError('Unknown dataset')
    catalog = {}
    for manifest in sorted((Path(root)/dataset/'protocol_v2').glob('seed_*/*/rate_*/bundle_*/bundle.json')):
        bundle = manifest.parent
        seed_dir = bundle.parents[2]
        family = bundle.parents[1].name
        variant = bundle.name.removeprefix('bundle_')
        if family not in FAMILY_NAMES or variant not in ('reduced', 'full'):
            continue
        seed = int(seed_dir.name.removeprefix('seed_'))
        rate = float(bundle.parent.name.removeprefix('rate_'))
        key = (family, seed, rate)
        catalog.setdefault(key, {})[variant] = str(bundle)
    return catalog


def experiment_label(key):
    family, seed, rate = key
    return f'{FAMILY_NAMES[family]} · Seed {seed} · Poison {100*rate:g}% of fit'


def preferred_method(thresholds, variant='reduced'):
    order = (['X_primary_full', 'X_full'] if variant == 'full' else ['X_primary_reduced', 'X_reduced'])
    return next((name for name in order if name in thresholds), next(iter(thresholds)))
