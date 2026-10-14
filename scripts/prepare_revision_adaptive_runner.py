"""Preserve the first runner and correct the supplementary Structural constraint."""
from pathlib import Path
import json
p=Path('scripts/run_revision_validation.py');s=p.read_text(encoding='utf-8')
s=s.replace('outputs/revision_2026_10_13/validation_results','outputs/revision_2026_10_13/adaptive_structural')
s=s.replace('fresh-and-adaptive-v1','adaptive-structural-v2')
s=s.replace('j for j in schema.restricted if j not in trigger.indices',"j for j in schema.restricted if schema.view_labels[j]=='structural' and j not in trigger.indices")
s=s.replace('set(np.flatnonzero(changed)).issubset(schema.restricted)','set(np.flatnonzero(changed)).issubset(set(variable))')
s=s.replace('args=p.parse_args()',"args=p.parse_args(); assert args.stage=='adaptive'")
Path('scripts/run_revision_adaptive.py').write_text(s,encoding='utf-8')
Path('outputs/revision_2026_10_13/validation_results/adaptive_preliminary_invalid.json').write_text(json.dumps({
 'status':'Withdrawn preliminary implementation',
 'reason':'V2 whitelist contains 4 Metadata columns. Structural-only filter added before the final adaptive matrix. Exclude preliminary adaptive.json files.',
 'replacement':'outputs/revision_2026_10_13/adaptive_structural'},indent=2),encoding='utf-8')
