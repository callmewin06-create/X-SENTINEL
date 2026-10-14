"""Complete traceability and benign calibration/final score diagnostics."""
from pathlib import Path
import json,csv,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
out=Path('output/revision_2026_10_13');root=Path('outputs/revision_2026_10_13')
refs={r['key']:r for r in json.loads((out/'references/catalog.json').read_text(encoding='utf-8'))}
claims=[
 ('PE dataset representations','ref01,ref02','configs/ember2024_sources.json; data/primary/*/protocol_v2/roles.json','Dataset descriptions are background; selected local subset is audited separately'),
 ('Gradient boosted main and view models','ref06','configs/primary_protocol.json; saved model headers','LightGBM only; other classifiers in Related Work are not experiments'),
 ('SHAP attribution','ref07,ref08,ref09','src/xsentinel/baselines/scores.py','Native raw-margin contributions exclude bias; model evidence rather than executable semantics'),
 ('Clean label poisoning context','ref12,ref13,ref31','src/xsentinel/attacks/primary.py; outputs/primary/*/attack.json','Literature does not validate the current numerical trigger as a functioning binary'),
 ('Feature space versus problem space','ref23,ref28','binary_validation/validation.json','One self-built benign fixture and four functional cases per edit; no malware binary realization'),
 ('Primary M3 M4 and fusion formulas','','src/xsentinel/detection/components.py; detection/calibration.py; revision/scoring.py','These own-code formulas produced the stored primary numbers; no polarity-contrast substitution'),
 ('STRIP perturbation concept','ref39','src/xsentinel/baselines/scores.py; analysis/figures/*_strip_entropy.png','Local numerical blend adaptation; score 1-H, not binary-realized transformations'),
 ('Post review shadow and inverse comparison','','supplement/*; validation_results/fresh_summary.json','Richer clean-model access explicit; new thresholds benign-only; fresh local IDs; no tuning'),
 ('Evaluation bias and data reuse','ref14,ref15,ref17','fresh_validation/protocol.json; dataset.json','Excludes known local observation history; unknown external handover history remains'),
 ('Adaptive evaluation motivation','ref20,ref21','adaptive_structural/protocol.json; adaptive_summary.json','Own bounded 32-query Structural optimizer is not an exhaustive robustness evaluation'),
 ('Finite calibration and risk context','ref50,ref51,ref52','analysis/fpr_diagnostics.csv; supplement/calibration_scores.npz','No claim to implement conformal risk control or guarantee future FPR'),
 ('Source ID uncertainty and proportions','ref53,ref55','analysis/cluster_intervals.json; revision/analysis.py','Bootstrap is conditional on frozen models and preserves repeated source IDs; Wilson intervals per proportion'),
 ('ROC positive class definition','ref54,ref56,ref57','analysis/cell_metrics.csv; revised_metrics','Three AUROC tasks named separately; no independent DeLong hypothesis test claimed'),
 ('New measured results and timing','','summary.json; supplement/latency.json; tests.xml','Own frozen-artifact measurements, not numbers borrowed from references')]
with (out/'claim_source_map.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['claim','reference_keys','primary_source_urls','local_evidence','limit'])
 for claim,keys,evidence,limit in claims:w.writerow([claim,keys,'; '.join(refs[k]['url'] for k in keys.split(',') if k),evidence,limit])
figdir=root/'analysis/figures';curves=[];grid=np.linspace(-.06,.035,191)
methods=[('TADR','TADR'),('X_primary_reduced','X-R'),('X_primary_full','X-F')]
for dataset in ('EMBER2018','EMBER2024'):
 fig,axes=plt.subplots(1,3,figsize=(11,3.6),sharey=True)
 for ax,(method,label) in zip(axes,methods):
  cal_rows=[];final_rows=[];fprs=[[],[]]
  for cell in sorted((Path('outputs/primary')/dataset/'protocol_v2').glob('seed_*/*/rate_*')):
   r=json.loads((cell/'result.json').read_text());b=json.loads((cell/'bundle_full/bundle.json').read_text());tau=b['thresholds'][method]
   cache=root/'supplement'/dataset/f"seed_{r['seed']}"/r['family']/f"rate_{r['rate']}"/'calibration_scores.npz'
   with np.load(cache,allow_pickle=False) as z:cal=z[method].copy()-tau
   with np.load(cell/'paired_predictions.npz',allow_pickle=False) as z:final=z['full_benign_'+method].copy()-tau
   cal_rows.append(1-np.searchsorted(np.sort(cal),grid,side='right')/len(cal))
   final_rows.append(1-np.searchsorted(np.sort(final),grid,side='right')/len(final))
   fprs[0].append(float(np.mean(cal>0)));fprs[1].append(float(np.mean(final>0)))
  for values,label2,color in [(cal_rows,'Calibration (n=2,000)','#2878b5'),(final_rows,'Final benign (n=10,000)','#d97924')]:
   ax.semilogy(grid,np.maximum(np.mean(values,axis=0),1e-5),label=label2,color=color)
  ax.axvline(0,color='black',lw=.8);ax.axhline(.01,color='gray',ls=':',lw=.8)
  ax.set_ylim(.0001,1);ax.set_title(label);ax.set_xlabel('Score minus own frozen threshold')
  ax.text(.97,.96,f'FPR at 0\ncal {100*np.mean(fprs[0]):.2f}%\nfinal {100*np.mean(fprs[1]):.2f}%',transform=ax.transAxes,ha='right',va='top',fontsize=9)
  curves.append({'dataset':dataset,'method':method,'runs':27,'grid':grid.tolist(),
    'calibration_mean_exceedance_curve':np.mean(cal_rows,axis=0).tolist(),'final_mean_exceedance_curve':np.mean(final_rows,axis=0).tolist(),
    'calibration_mean_fpr':float(np.mean(fprs[0])),'final_mean_fpr':float(np.mean(fprs[1]))})
 axes[0].set_ylabel('Fraction with score above x');axes[0].legend(fontsize=8,loc='lower left')
 fig.suptitle(dataset+' benign score tails across 27 frozen models',fontsize=12)
 fig.tight_layout();fig.savefig(figdir/(dataset+'_calibration_final_tails.png'),dpi=300,bbox_inches='tight');fig.savefig(figdir/(dataset+'_calibration_final_tails.pdf'),bbox_inches='tight');plt.close(fig)
(root/'analysis/calibration_final_curves.json').write_text(json.dumps({'scope':'Descriptive equal-run means; source IDs repeated across models, no independent-count inference','curves':curves},indent=2),encoding='utf-8')
print('Claim source mapping and calibrated benign score-tail figures completed')
