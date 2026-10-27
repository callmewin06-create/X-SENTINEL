"""Evidence-linked EN/VI handoff, generated only from complete research outputs."""
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from xsentinel.utils import read_json,write_json,sha256

ROOT=Path('outputs/teacher_revision_2026_10_27')
OUT=Path('output/teacher_revision_2026_10_27')
LABELS={'X_primary_reduced':'Reduced','X_primary_full':'Full','M4_prob_gap':'BPG','M3_view_mass':'VMC',
        'M4_shap_behavioral_conflict':'BGS','Shadow':'Shadow','SHAP-IF':'SHAP-IF'}


def markdown(df):
    def cell(x):
        if pd.isna(x):return 'N/A'
        if isinstance(x,(float,np.floating)):return f'{x:.4f}' if 0<abs(x)<.01 else f'{x:.2f}'
        return str(x).replace('|','/')
    return '| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(cell(x) for x in row)+' |' for row in df.itertuples(index=False,name=None))


def budget_figures(bs,same,figdir):
    figdir.mkdir(parents=True,exist_ok=True)
    for dataset in ('EMBER2018','EMBER2024'):
        fig,ax=plt.subplots(figsize=(7,4.6),layout='constrained')
        for method in ('M4_prob_gap','X_primary_full','Shadow'):
            q=bs[(bs.dataset==dataset)&(bs.cohort=='restricted')&(bs.method==method)].sort_values('budget')
            ax.plot(q.budget,q.low_fpr_tpr*100,marker={'M4_prob_gap':'s','X_primary_full':'o','Shadow':'^'}[method],label=LABELS[method])
        reduced=same[(same.dataset==dataset)&(same.cohort=='restricted')&(same.method=='X_primary_reduced')&(same.group=='successful_eligible')].tpr_mean.iloc[0]
        ax.axhline(reduced*100,color='gray',linestyle='--',label='Reduced (no labelled fit)')
        ax.set(xscale='log',xlabel='Trusted labelled fit samples (benign and malware)',ylabel='Mean TPR at empirical FPR <= 1% (%)',
               title=f'{dataset}: clean-data budget\nRestricted cohort, {int(same[(same.dataset==dataset)&(same.cohort=="restricted")&(same.method=="X_primary_reduced")].runs.iloc[0])} fixed models',ylim=(0,101))
        ax.grid(alpha=.2);ax.legend();fig.savefig(figdir/f'clean_budget_{dataset}.png',dpi=180)
        fig.savefig(figdir/f'clean_budget_{dataset}.pdf');plt.close(fig)


def main():
    OUT.mkdir(parents=True,exist_ok=True);figdir=OUT/'figures';figdir.mkdir(exist_ok=True)
    baseline=list((ROOT/'shap_if').glob('*/seed_*/*/rate_*/result.json'))
    if len(baseline)!=54:raise RuntimeError(f'Baseline incomplete: {len(baseline)}/54')
    analysis=read_json(ROOT/'analysis/manifest.json')
    if analysis['if_cells']!=54:raise RuntimeError('Rerun analysis after all IF cells finish')
    adaptive=pd.read_csv(ROOT/'adaptive_multiview/results.csv')
    if len(adaptive)!=24:raise RuntimeError('Adaptive incomplete')
    shutil.copy2(ROOT/'adaptive_multiview/results.csv',OUT/'adaptive_per_run.csv')
    budget=pd.read_csv(ROOT/'clean_budget/results.csv')
    if len(budget)!=810:raise RuntimeError('Budget curve incomplete')
    shutil.copy2(ROOT/'clean_budget/results.csv',OUT/'clean_budget_per_run.csv')
    defense=pd.read_csv(ROOT/'training_defense_v2/results.csv')
    if len(defense)!=4:raise RuntimeError('Training defense incomplete')
    seeds=[read_json(ROOT/'ember2024_seeds_v2'/f'seed_{s}'/'result.json') for s in (59,71)]
    for path,digest in read_json(ROOT/'original_input_manifest.json')['sha256'].items():
        if sha256(path)!=digest:raise ValueError('Original asset changed: '+path)

    same=pd.read_csv(ROOT/'analysis/same_fpr_summary.csv')
    fixed=pd.read_csv(ROOT/'analysis/fixed_threshold_per_run.csv')
    compare=same[(same.group=='successful_eligible') & same.method.isin(['X_primary_reduced','X_primary_full','Shadow','SHAP-IF'])].copy()
    compare['method']=compare.method.map(LABELS)
    for key in ('tpr_mean','fpr_mean'):compare[key]*=100
    compare=compare[['dataset','cohort','method','runs','tpr_mean','fpr_mean','standardized_partial_auc_mean']]
    compare.columns=['Dataset','Cohort','Method','Runs','TPR at cap %','Actual FPR %','Standardized pAUC']
    compare.to_csv(OUT/'same_fpr_comparison.csv',index=False)
    compare['Standardized pAUC']=compare['Standardized pAUC'].map(lambda x:f'{x:.4f}')

    adaptive['cohort']=np.where(adaptive.family=='cross_3view_stress','cross','restricted')
    for field in ('start_joint_success','end_joint_success','start_main_evasion','end_main_evasion'):
        adaptive[field+'_rate']=adaptive[field]/adaptive.n_eligible
    ad=adaptive.groupby(['dataset','cohort']).agg(runs=('seed','size'),
        before=('start_joint_success_rate','mean'),after=('end_joint_success_rate','mean'),
        main_before=('start_main_evasion_rate','mean'),main_after=('end_main_evasion_rate','mean')).reset_index()
    ad['gain_pp']=(ad.after-ad.before)*100
    ad.to_csv(OUT/'adaptive_summary.csv',index=False)
    adtable=ad[['dataset','cohort','runs','before','after','gain_pp']].copy();adtable[['before','after']]*=100
    adtable.columns=['Dataset','Cohort','Runs','Joint evasion before %','Joint evasion after %','Change pp']

    old_confirm=read_json('outputs/primary_confirmation/EMBER2024/round_1/results.json')['rows']
    seed_rows=[]
    for seed in (17,29,43):
        r=read_json(Path('outputs/primary/EMBER2024/protocol_v2')/f'seed_{seed}'/'spread_structural/rate_0.02/result.json')
        e=r['evaluation']['results']['full'];c=next(x for x in old_confirm if x['seed']==seed and x['family']=='spread_structural' and x['rate']==.02)
        seed_rows.append(dict(seed=seed,origin='original',confirmed=True,confirmation_asr=c['asr']['rate'],
            confirmation_paired_gain=c['paired_gain'],asr=e['asr_eligible']['rate'],
            reduced_recall=e['methods']['X_primary_reduced']['recall_successful_eligible']['rate'],
            reduced_fpr=e['methods']['X_primary_reduced']['benign_fpr']['rate'],
            full_recall=e['methods']['X_primary_full']['recall_successful_eligible']['rate'],
            full_fpr=e['methods']['X_primary_full']['benign_fpr']['rate']))
    for r in seeds:
        m=r['metrics'];c=r['screens']['confirmation']
        seed_rows.append(dict(seed=r['seed'],origin='additional',confirmed=r['passes_original_screening_criteria'],
            confirmation_asr=c['asr']['rate'],confirmation_paired_gain=c['paired_gain'],asr=m['X_primary_reduced']['asr_before']['rate'],
            reduced_recall=m['X_primary_reduced']['recall_successful_eligible']['rate'],reduced_fpr=m['X_primary_reduced']['benign_fpr']['rate'],
            full_recall=m['X_primary_full']['recall_successful_eligible']['rate'],full_fpr=m['X_primary_full']['benign_fpr']['rate']))
    sd=pd.DataFrame(seed_rows);sd.to_csv(OUT/'ember2024_seed_runs.csv',index=False)
    st=sd[['seed','origin','confirmed','confirmation_asr','reduced_recall','reduced_fpr','full_recall','full_fpr']].copy()
    for col in st.columns[3:]:st[col]*=100
    st.columns=['Seed','Origin','Confirmed','Confirmation ASR %','Reduced recall %','Reduced FPR %','Full recall %','Full FPR %']
    variability=[]
    for label,subset in [('original_confirmed',sd[sd.origin=='original']),('all_five_attempts',sd),('all_confirmed',sd[sd.confirmed])]:
        for method in ('reduced','full'):
            v=subset[method+'_recall']
            variability.append(dict(group=label,method=method,runs=len(v),mean=float(v.mean()),minimum=float(v.min()),maximum=float(v.max()),sd=float(v.std(ddof=1))))
    vstats=pd.DataFrame(variability)
    vstats.to_csv(OUT/'ember2024_seed_variability.csv',index=False)
    def seed_stat(method,field):
        return 100*vstats[(vstats.group=='all_confirmed')&(vstats.method==method)][field].iloc[0]

    budget['cohort']=np.where(budget.family=='cross_3view_stress','cross','restricted')
    bs=budget[budget.confirmed].groupby(['dataset','cohort','budget','method']).agg(runs=('seed','size'),
        recall=('recall','mean'),fpr=('fpr','mean'),low_fpr_tpr=('low_fpr_tpr','mean'),low_fpr_fpr=('low_fpr_fpr','mean')).reset_index()
    bs.to_csv(OUT/'clean_budget_summary.csv',index=False)
    budget_figures(bs,same,figdir)
    defense.to_csv(OUT/'training_defense_results.csv',index=False)
    def budget_tpr(ds,n,method):
        return 100*bs[(bs.dataset==ds)&(bs.cohort=='restricted')&(bs.budget==n)&(bs.method==method)].low_fpr_tpr.iloc[0]
    dt=defense[['dataset','method','removed','poisons_removed','benign_unpoisoned_removed','asr_before','asr_after','accuracy_after']].copy()
    dt[['asr_before','asr_after','accuracy_after']]*=100
    dt.columns=['Dataset','Method','Removed','Poisons removed','Unpoisoned removed','ASR before %','ASR after %','Clean-test accuracy %']

    controls=[]
    for p in baseline:
        r=read_json(p)
        controls.append(dict(dataset=r['dataset'],seed=r['seed'],family=r['family'],rate=r['rate'],confirmed=r['confirmed'],
            original_malware_alerts=r['original_malware_alerts'],original_malware_n=r['original_malware_n'],
            original_malware_alert_rate=r['original_malware_alerts']/r['original_malware_n'],
            trigger_recall=r['metrics']['recall_successful_eligible']['rate'],benign_fpr=r['metrics']['benign_fpr']['rate']))
    pd.DataFrame(controls).to_csv(OUT/'shap_if_original_malware_controls.csv',index=False)
    resources=pd.DataFrame([
        ['Reduced',0,500,2000,'Suspicious model','No auxiliary clean classifier'],
        ['SHAP-IF',0,500,2000,'Suspicious model and IF fitted on reference','Same benign reference/calibration as Reduced'],
        ['Full',200000,500,2000,'Suspicious model and Behavioral classifier','Original bundle stores three view models; primary Full score consumes Behavioral only'],
        ['Shadow',200000,0,2000,'Suspicious and clean full-feature classifiers','No rank reference needed'],
        ['Training IF top32',0,500,0,'Suspicious model and entire potentially poisoned labelled fit','Access to 200000 training records and retraining; not a per-input baseline']
    ],columns=['Method','Trusted labelled fit','Benign reference','Benign calibration','Model access','Notes'])
    resources.to_csv(OUT/'resource_access_comparison.csv',index=False)
    for p in (ROOT/'analysis').glob('*.csv'):shutil.copy2(p,OUT/p.name)
    for p in (ROOT/'analysis').glob('*.png'):shutil.copy2(p,figdir/p.name)
    for p in (ROOT/'analysis').glob('*.pdf'):shutil.copy2(p,figdir/p.name)

    cross=pd.read_csv(ROOT/'analysis/cross_confirmation_diagnostics.csv')
    c18=cross[cross.dataset=='EMBER2018']
    ctable=cross.groupby('dataset').agg(runs=('seed','size'),clean_asr=('clean_trigger_asr','mean'),
        poisoned_asr=('poisoned_asr','mean'),new_evasion=('paired_new_rate','mean'),lost_evasion=('paired_lost_rate','mean'),net_gain=('paired_gain','mean')).reset_index()
    ctable.to_csv(OUT/'cross_confirmation_summary.csv',index=False)
    ctable.iloc[:,2:]*=100
    ctable.columns=['Dataset','Runs','Clean triggered ASR %','Poisoned triggered ASR %','Paired new evasion %','Paired lost evasion %','Net gain pp']
    contribution='''Our contributions are:

- A study of view attribution concentration and Behavioral-gated SHAP as per-input suspicion signals under restricted defender access.
- Calibrated evaluation across 54 frozen model/attack configurations on two EMBER schemas, supplemented by a signed-SHAP novelty baseline and low-FPR comparisons.
- Evidence that distributed and multiview adaptive vector modifications undermine these signals.
- An analysis of clean-data access, training-data sanitization, and variability across additional model seeds.'''
    en=f'''# X SENTINEL research revision content

These sections and tables are for the paper editor to integrate into the canonical manuscript. Table numbers should follow the final manuscript order. The original54 configurations remain the primary benchmark; additional seed and training-defense experiments are reported separately.

## Suggested title and abstract

Suggested title: Feature-View Attribution Concentration as a Per-Input Backdoor Signal for Static PE Classifiers.

X-SENTINEL studies per-input backdoor suspicion in LightGBM static malware classifiers using view attribution concentration and Behavioral-gated SHAP. All trigger experiments reported here operate in feature space. The primary Reduced setting requires the suspicious model and disjoint trusted benign reference and calibration pools, while a supplemental Full setting additionally uses a clean Behavioral classifier. We evaluate54 frozen model/attack configurations on two EMBER schemas and compare calibrated detection with a signed-SHAP Isolation Forest baseline and clean Shadow model. Retrospective low-FPR comparisons, two additional EMBER2024 seed attempts, clean-data budgets and a small training-data sanitization experiment clarify the effects of defender access and evaluation conditions. Cross-view triggers and bounded multiview adaptation expose substantial weaknesses in view-concentration signals. A clean Shadow model remains a strong comparator when trusted labelled training data are available. These findings support a limited interpretation of attribution signals under restricted access rather than a general claim of backdoor robustness.

## Contributions and scope

{contribution}

All experiments in this package operate in feature space. We investigate suspicion signals for a supplied LightGBM malware classifier. Reduced requires access to the suspicious model,500 trusted benign reference samples and2000 disjoint benign calibration samples. Full additionally uses a Behavioral classifier trained on trusted labelled data. A Shadow comparator uses a trusted full-feature classifier. Trusted training data contain both benign and malware examples; trusted does not mean benign-only. We position Reduced as the primary restricted-access setting and Full as a supplemental resource-rich comparison. Source IDs are reused across fixed model configurations, and each run contributes equal weight to macro summaries.

The evaluator's clean model defines clean-original eligibility but is not supplied to Reduced during inference. The Shadow comparator explicitly grants access to a clean classifier. Successful-eligible inputs are malware identified by the evaluator's clean model before modification and evaded by the suspicious classifier after modification. Shadow evaluates its clean classifier on the modified input, so its gap is closely related to this positive-group definition whenever the clean classifier resists the trigger. It is not an exact identity because eligibility uses the original input. This relationship and the extra model access must be considered when interpreting its high recall.

## Low FPR comparison

We retain the original deployment thresholds calibrated on benign calibration data. Separately, we report the highest attainable TPR at an empirical final-set FPR no greater than1%, keeping tied scores together, and standardized partial AUC over FPR0–1%. The standardized statistic uses sklearn max_fpr=0.01 and is not a raw area. These final-set operating points are retrospective comparisons, not newly validated deployment thresholds. Each method is compared on the same source IDs and attack eligibility masks within a run.

{markdown(compare)}

TPR above is measured on successful-eligible triggered malware. Actual FPR can be below1% because tied scores cannot always attain exactly1%. CSVs also contain paired-new-evasion and all-triggered groups. The clean Shadow model remains a material comparator; the original availability of200000 trusted labelled fit records must be stated when interpreting Full.

## Signed SHAP outlier baseline

For each suspicious model, we fit Isolation Forest on signed native SHAP vectors from the500 benign reference samples, excluding the bias column. We fix 200 trees, max_samples=256, max_features=1.0, no bootstrap and random_state=17. Larger anomaly scores are obtained by negating score_samples. The decision threshold is selected independently on2000 benign calibration samples with the same strict score greater than threshold convention. No hyperparameters are selected using final-set recall. We additionally score the same malware before the trigger modification; this control helps distinguish malware–benign differences from trigger-specific sensitivity. Original-malware alert rate is not benign FPR. This is a simple reference-only novelty baseline, not an exhaustive search over SHAP defenses.

## Cross and bounded multiview adaptation

For EMBER2018 Cross, confirmation clean-model triggered ASR ranges from{100*c18.clean_trigger_asr.min():.2f}% to{100*c18.clean_trigger_asr.max():.2f}%. Net paired gain ranges from{100*c18.paired_gain.min():.2f} to{100*c18.paired_gain.max():.2f} percentage points, below the prespecified20-point threshold. High poisoned-model ASR alone therefore does not establish a strong additional poisoning effect. Separate CSVs report paired new and lost evasions in confirmation and final pools.

{markdown(ctable)}

This table uses the confirmation pool. Paired new evasion counts eligible sources evaded by the poisoned classifier but not by the clean classifier after the same trigger; net gain subtracts the converse losses. Their equality in these runs reflects zero observed paired losses, not interchangeable definitions.

We also conduct bounded multiview adaptation on24 previously confirmed models. For each dataset,100 malware source IDs are selected by lexical ID order before querying outcomes. The procedure retains the original trigger and permits at most eight additional coordinates per view, with empirical values from the benign selection pool. Each input receives at most32 attacker queries, including the initial query. The objective uses only the main probability and Reduced score; Full is evaluated afterward. The source IDs are reused across runs, so the2400 model-input evaluations are not2400 independent malware samples. Joint evasion means classifier evasion and no Reduced alert among clean-original eligible samples.

{markdown(adtable)}

Cross inputs already jointly evading the model and detector are retained without additional search. Search failure under this finite budget cannot establish adaptive robustness. These outcomes motivate reporting Cross and adaptive failures in the main results.

## EMBER2024 additional seeds

We predeclare seeds59 and71, retain the original legacy_rare selector, spread Structural geometry and2% poisoning rate of all fit records, and preserve the original screening cutoffs. Both successful and unsuccessful repetitions are retained. Reference/calibration batch conventions and final batches128 match the primary implementation. No seed is substituted after inspecting outcomes.

{markdown(st)}

There are five attempted seed repetitions in this condition and{int(sd.confirmed.sum())} that satisfy the original development and confirmation criteria. Seed71 has confirmation ASR{100*sd.loc[sd.seed==71,'confirmation_asr'].iloc[0]:.2f}%, below the50% cutoff. This threshold miss is not evidence of classifier safety. The supplementary variability CSV reports all five attempts and the confirmed subset separately. Fixed-model bootstrap intervals measure source-sample uncertainty conditional on the selected models, not variability over future trained models. Additional seeds in spread2% do not broaden the evaluated trigger families.

Within the four confirmed seed attempts, Reduced recall has mean{seed_stat('reduced','mean'):.2f}%, sample SD{seed_stat('reduced','sd'):.2f} percentage points and range{seed_stat('reduced','minimum'):.2f}–{seed_stat('reduced','maximum'):.2f}%. Full recall has mean{seed_stat('full','mean'):.2f}%, sample SD{seed_stat('full','sd'):.2f} points and range{seed_stat('full','minimum'):.2f}–{seed_stat('full','maximum'):.2f}%. These use the original-style calibration thresholds, not the retrospective final-set thresholds.

## Clean data budget

We compare1000,5000,10000,50000 and200000 trusted labelled fit records. Subsets are nested, class-balanced and identical for Behavioral and Shadow training at each seed and budget. Suspicious models, reference/calibration pools, evaluation IDs and attack groups remain fixed. The200000 endpoint reuses the original models and is checked against original Full scores. For the budget experiment, only the Behavioral auxiliary model consumed by the Full formula is trained; cached view concentration is unchanged. The500 benign reference and2000 benign calibration records are outside the plotted fit budget. Shadow does not require the500 rank-reference records. Figures and the complete budget summary are supplied separately.

At the smallest tested budget of1000 labelled fit records, Full attains mean low-FPR TPR of{budget_tpr('EMBER2018',1000,'X_primary_full'):.2f}% and{budget_tpr('EMBER2024',1000,'X_primary_full'):.2f}% on the2018 and2024 restricted cohorts, compared with{budget_tpr('EMBER2018',1000,'Shadow'):.2f}% and{budget_tpr('EMBER2024',1000,'Shadow'):.2f}% for Shadow. However, Full at this budget falls below Reduced on EMBER2018. With200000 trusted fit records, Shadow dominates Full on both cohorts. The curves therefore support a conditional resource comparison, not a general advantage for Full. The original150-round Behavioral and500-round Shadow training settings are retained. Matching fit subsets does not equalize training compute or every use of trusted information: Full also consumes500 benign rank-reference records, which Shadow does not use for training.

## Training data sanitization context

Severi et al. evaluate training-data filtering in reduced feature spaces, including Isolation Forest [USENIX Security2021, Section7](https://www.usenix.org/system/files/sec21-severi.pdf). Our two-cell supplementary experiment is an adaptation, not a replication of their reported numbers. Unlike Reduced, it grants access to the potentially poisoned labelled training set and permits retraining.

We select32 features by mean absolute SHAP from the suspicious model on500 trusted benign reference records, fit Isolation Forest on benign-labelled training rows in that reduced raw-feature space, and remove the highest-scoring5% of those rows. A separate fixed RNG20261027 selects a matching random-removal control. Poison identities are used only to count removed poisons after the mask is fixed. Both classifiers are retrained with the original500-round parameters. The study fixes seed17 and spread2% on each dataset; it is not a54-cell training-defense benchmark.

{markdown(dt)}

ASR uses the same clean-original eligible malware denominator before and after retraining. Accuracy is measured on the original labelled final pool. Removal counts and residual ASR should be interpreted together with utility; a training sanitization result is not a per-input detection recall.

## Consolidated limitations and technical corrections

All new analyses reuse previously observed benchmark pools; the old fresh_validation directory is not a new unseen holdout for this revision. Cross and bounded adaptive outcomes limit the claimed robustness. Limited seed counts and a single condition for additional2024 repetitions restrict generalization. Binary-trigger feasibility and detector efficacy on executable files require separate evidence from the binary task. BODMAS classification results have no verified trigger labels. A benign fixture called malware is a classification error, not automatically a poisoning effect. Operational timing results from different input sets and execution scopes should not be presented as a measured speedup. We do not attribute calibration-to-final FPR differences solely to ties or distribution shift without further evidence.

Use descriptive component names consistently: VMC for M3 view mass concentration, BGS for M4 Reduced Behavioral-gated SHAP and BPG for M4 Full Behavioral probability gap. Historical code keys remain unchanged. Move Streamlit, database, restore, upload-limit and regression-test details to the technical appendix. Preserve the poisoning denominator as all fit records:4000/200000=2%, equivalent to4% of100000 benign fit records.
'''
    import re
    for word in ('original','evaluate','of','on','from','and','Section','seeds','seed','with','than','below','the','including','fit','by','at','to','select','uses','requires','prespecified','mean','SD','range','ASR','spread','FPR','most','not','exactly','batches'):
        en=re.sub(r'\b'+word+r'(?=\d)',lambda m:m.group()+' ',en,flags=re.I)
    en=re.sub(r',(?=\d)',', ',en)
    (OUT/'PAPER_INSERTS_EN.md').write_text(en,encoding='utf8')
    status=[
        ['1.1','Complete scoped analysis','Reduced framing, resource table and5-budget curve; no universal Full advantage claim'],
        ['1.2','Complete scoped experiment','24-cell multiview vector evaluation and separate confirmation/final Cross diagnostics'],
        ['1.3','Pending Phuc','No new binary evidence supplied; feature-space scope retained'],
        ['1.4','Complete','Original thresholds retained; retrospective low-FPR comparison added'],
        ['1.5','Complete within declared scope','54-cell reference-only SHAP-IF; two-cell training sanitization plus independent random control'],
        ['1.6','Complete scoped extension','Two additional seeds; all five attempts reported; four confirmed if original criteria pass'],
        ['2','Content supplied; integration pending Quan','Contributions, scope, names, limitations and technical-appendix guidance supplied'],
        ['3','Technical evidence supplied; Word QA pending','Counts, FPR/AUC/timing notes supplied; final formulas/captions must be checked in canonical Word'],
        ['4','Pending Phu and Quan','Primary source for sanitization supplied; complete bibliography audit remains teammate task']]
    pd.DataFrame(status,columns=['Reviewer item','Status','Evidence or remaining work']).to_csv(OUT/'review_response_status.csv',index=False)
    vi=f'''# Bàn giao phần nghiên cứu ngày27 tháng10 năm2026

Gói này dành cho bạn duyệt và Quân ghép vào bản Word chính. Các kết quả mới bổ sung bằng chứng và sửa cách so sánh; chúng không làm cho detector tự nhiên chống được Cross.

- SHAP baseline: hoàn tất54 cấu hình gốc; có đối chứng malware chưa trigger.
- Cùng mức báo nhầm: bảng so sánh có tỷ lệ thật đạt được, không tách các điểm bằng nhau để ép đủ1%.
- Adaptive nhiều view: hoàn tất24 model,100 source ID mỗi dataset. Một mẫu xuất hiện ở nhiều model; không gọi2400 lượt là2400 file độc lập.
- EMBER2024: đã chạy thêm seed59 và71. Tổng5 lượt thử ở spread2%,{int(sd.confirmed.sum())} lượt đạt tiêu chí. Giữ cả seed không đạt.
- Ngân sách sạch: đủ5 mức trên cả2 dataset và3 seed. Mẫu sạch ở đây là mẫu có nhãn đáng tin, gồm cả malware và benign; không phải toàn file lành.
- Phòng thủ tập train:2 cấu hình, có IF lọc dữ liệu và đối chứng loại ngẫu nhiên độc lập, rồi huấn luyện lại. Không suy thành đã chạy trên54 cấu hình.

## Bạn gửi cho Quân

PAPER_INSERTS_EN.md chứa nội dung tiếng Anh và bảng chính; cácCSV giữ số đầy đủ; figures/ chứa hình. Quân dùng một bản Word chính, đặt lại số bảng/hình sau khi ghép. Gói này không ghi đè bản Word nhóm đang chỉnh.

## Các điểm phải giải thích đúng

1. Full cần nhiều dữ liệu sạch hơn Reduced. Shadow vẫn phải được trình bày cùng tài nguyên và cùng mức báo nhầm, dù kết quả bất lợi cho Full.
2. Tỷ lệ phát hiện chỉ tính trên nhóm được định nghĩa rõ; không gọi recall là accuracy.
3. Thêm seed không bảo đảm thêm lượt đạt yêu cầu. Lượt không đạt vẫn là dữ liệu nghiên cứu.
4. Bộ dữ liệu final và fresh cũ đã được xem trước đây. Những phép so sánh mới là phân tích bổ sung trên benchmark cố định.
5. Kết quả mẫu BODMAS không chứng minh phát hiện backdoor thực tế khi không có nhãn trigger.

## Chỉnh sửa trong lúc triển khai

Hai thư mục cũ chỉ giữ để truy vết, không dùng làm bảng cuối: ember2024_seeds/ được thay bằng ember2024_seeds_v2/ để thống nhất cách chấm theo lô với primary; training_defense/ có đối chứng ngẫu nhiên sai do dùng chung dòng số ngẫu nhiên với bước chọn mẫu đầu độc, được thay bằng training_defense_v2/. Model và trigger của hai seed được giữ nguyên khi sửa cách chấm. Đối chứng ngẫu nhiên mới dùng seed20261027, không chọn seed theo kết quả cuối. Kiểm thử đã được bổ sung để ngăn lỗi này.

## Việc đang chờ

Phúc chưa gửi bằng chứng trigger trên file. Quân chưa gửi bản Word ghép cuối. Phú phụ trách rà toàn bộ nguồn tham khảo. Vì vậy review_response_status.csv phân biệt phần nghiên cứu đã có kết quả với các phần đang chờ tích hợp; không đánh dấu toàn bài đã sửa xong.

## Chạy lại

Chạy từ thư mục gốc project bằng môi trường .venv, với dữ liệu và các model gốc có sẵn. Thứ tự: run_shap_outlier_2026_10_27.py; run_multiview_adaptive_2026_10_27.py; run_ember2024_seeds_2026_10_27.py; run_training_defense_2026_10_27.py; run_clean_budget_2026_10_27.py; analyze_teacher_feedback_2026_10_27.py; audit_teacher_revision_2026_10_27.py; build_teacher_handoff_2026_10_27.py. Các chương trình chạy nghiên cứu nằm trong scripts/. Không đổi tham số trong thư mục kết quả đã khóa; dùng namespace mới khi đổi phương pháp.
'''
    for word in ('ngày','tháng','năm','seed','đủ'):
        vi=re.sub(r'\b'+word+r'(?=\d)',lambda m:m.group()+' ',vi)
    (OUT/'README_VI.md').write_text(vi,encoding='utf8')
    integration='''# Hướng dẫn Quân ghép bài

Không chèn nguyên gói này vào cuối bài. Thầy yêu cầu rút gọn và đổi cách trình bày; thêm liên tiếp nhiều bảng sẽ làm vấn đề dài dòng nặng hơn.

| Vị trí theo nội dung | Việc sửa | Nguồn |
|---|---|---|
| Tiêu đề và Abstract | Thống nhất tiêu đề mô tả đúng tín hiệu; Abstract nói rõ feature-space ngay đầu | PAPER_INSERTS_EN.md |
| Cuối Introduction | Dùng bốn đóng góp, gồm cả phát hiện giới hạn của phương pháp | Contributions |
| Threat Model & Scope | Đặt Reduced làm thiết lập chính; phân biệt model sạch của evaluator với quyền của defender | Scope và resource_access_comparison.csv |
| Phương pháp và protocol | Bổ sung SHAP-IF, quy tắc ngưỡng, các thí nghiệm bổ sung; giữ 54 cấu hình gốc tách khỏi hai seed mới | Methods và protocols/ |
| Kết quả chính | Giữ bảng kết quả gốc có ngưỡng calibration; thêm bảng so sánh cùng FPR, Cross/paired evasion và adaptive | same_fpr_comparison.csv, cross_confirmation_summary.csv, adaptive_summary.csv |
| Chi phí dữ liệu sạch | Đặt hai hình budget cạnh nhau hoặc thành hai panel; giải thích điểm Full tốt hơn Shadow và điểm vẫn thua Reduced | figures/clean_budget_*.pdf |
| Biến thiên kết quả | Nêu tổng 5 lượt thử, 4 đạt; đưa bảng từng seed vào phụ lục nếu thiếu chỗ | ember2024_seed_runs.csv và ember2024_seed_variability.csv |
| Bối cảnh phòng thủ tập train | Một đoạn trong thân bài; bảng 4 dòng có thể đặt phụ lục | training_defense_results.csv |
| Limitations | Gom Cross/adaptive, feature-space, giới hạn dữ liệu/seed, lỗi fixture và dữ liệu đã được quan sát | Consolidated limitations |
| Phụ lục kỹ thuật riêng | Chuyển Docker, PostgreSQL, UI, restore, upload và test phần mềm ra khỏi mạch nghiên cứu | Nội dung hệ thống cũ |

Các hình ROC chi tiết và CSV đầy đủ có thể đặt ở phụ lục/artifact. Không cần nhét tất cả vào thân bài. Chưa đánh số bảng/hình trong gói vì thứ tự còn phụ thuộc bản ghép cuối.

Đơn vị: tỷ lệ trong CSV thường ở thang 0–1; bảng Markdown có dấu % đã nhân 100. Change pp là điểm phần trăm. Standardized pAUC vẫn ở thang 0–1. Runs là số model/cấu hình, không phải số file độc lập.

Chỉ copy phần văn bản nghiên cứu phù hợp từ PAPER_INSERTS_EN.md. Dòng hướng dẫn biên tập, README, lỗi v1/v2 và trạng thái đồng đội là tài liệu nội bộ, không đưa vào narrative của bài báo.

Trước khi xuất bản cuối: kiểm lại số bảng/hình, tất cả lời dẫn trong thân bài, ký hiệu công thức trong PDF, nguồn chính thức do Phú rà và bằng chứng binary do Phúc gửi. Gói này chưa xác nhận bố cục bản Word cuối.
'''
    (OUT/'INTEGRATION_MAP_VI.md').write_text(integration,encoding='utf8')
    captions='''# Figure captions

## Low-FPR curves

Mean attainable TPR against empirical benign FPR budgets up to 1%, computed separately within each frozen model configuration and then averaged. Positives are successful-eligible triggered malware. Tied scores remain inseparable; step operating points are not interpolated. These are retrospective final-pool comparisons. The legend reports the number of original confirmed configurations: 12 for EMBER2018 restricted, 3 for EMBER2024 restricted and 9 for EMBER2024 Cross. The two additional seed attempts are reported separately. Standardized partial AUC in the tables uses its stated sklearn definition rather than the plotted step area.

## Clean-data budget curves

Mean low-FPR TPR on the original confirmed restricted cohorts as trusted labelled fit access increases. The horizontal axis is logarithmic; points are 1000, 5000, 10000, 50000 and 200000 fit records, with nested class-balanced subsets. Suspicious models and source pools are fixed. The 500 benign reference and 2000 benign calibration records are separate from this fit budget. Shadow requires no rank reference; the Reduced horizontal line requires no auxiliary labelled fit set. BPG denotes Behavioral probability gap. The original Behavioral and Shadow training-round settings differ, so this is a data-access comparison, not a compute-matched comparison.

## Same-FPR bar summary

Mean TPR at attainable empirical FPR no greater than 1%, using the same model/input groups per method. Displayed values are macro means over the original confirmed restricted configurations. The complete CSV also reports actual attained FPR, all nonconfirmed configurations and alternative positive groups. VMC is view mass concentration; BGS is Behavioral-gated SHAP; BPG is Behavioral probability gap.
'''
    (OUT/'FIGURE_CAPTIONS_EN.md').write_text(captions,encoding='utf8')
    def adaptive_rate(ds,cohort,field):
        return 100*ad[(ad.dataset==ds)&(ad.cohort==cohort)][field].iloc[0]
    briefing=f'''# Kết quả để trưởng nhóm giải thích

Không nên nói nhóm đã sửa hết điểm yếu của hệ thống. Nhóm đã bổ sung các phép đánh giá còn thiếu và có bằng chứng rõ hơn về nơi phương pháp dùng được, nơi nó thất bại. Model đang dùng trong ứng dụng không được thay bằng các model thí nghiệm mới.

## 1. Shadow và Full

Khi có 200.000 mẫu đáng tin để huấn luyện, Shadow vẫn là đối chứng rất mạnh. Vì vậy hướng đặt Reduced làm trọng tâm có cơ sở hơn việc khẳng định Full là phương án tốt nhất.

Ở mức 1.000 mẫu fit, Full đạt {budget_tpr('EMBER2018',1000,'X_primary_full'):.2f}% trên nhóm restricted2018 và {budget_tpr('EMBER2024',1000,'X_primary_full'):.2f}% trên restricted2024; Shadow tương ứng {budget_tpr('EMBER2018',1000,'Shadow'):.2f}% và {budget_tpr('EMBER2024',1000,'Shadow'):.2f}%. Đây là recall với trần báo nhầm thực nghiệm 1%, không phải accuracy. Full ở mức này vẫn thua Reduced trên2018. Full còn dùng thêm500 mẫu lành reference; không được nói toàn bộ tài nguyên thông tin và thời gian huấn luyện đã ngang nhau.

## 2. Cross và adaptive

Cross2018 làm chính model sạch bị lừa rất nhiều. So sánh cùng một mẫu trước/sau mới thấy phần sai tăng thêm do model đầu độc dưới20 điểm phần trăm, nên không đạt tiêu chí xác nhận đã khóa.

Khi cho phép sửa thêm ở nhiều view, tỷ lệ vừa qua được classifier vừa không bị Reduced cảnh báo tăng trung bình từ {adaptive_rate('EMBER2018','restricted','before'):.2f}% lên {adaptive_rate('EMBER2018','restricted','after'):.2f}% trên nhóm restricted2018; từ {adaptive_rate('EMBER2024','restricted','before'):.2f}% lên {adaptive_rate('EMBER2024','restricted','after'):.2f}% trên restricted2024. Đây là kết quả xấu đi đối với phòng thủ. Nhóm Cross2024 trong100 ID được chọn đã qua cả hai ngay từ đầu; không được gọi đó là100% thành công mới do optimizer tìm ra.

## 3. EMBER2024

Đã thêm đúng seed59 và71 theo kế hoạch. Seed71 không qua cutoff ASR50% ở confirmation. Tổng là5 lượt thử ở spread2%, trong đó{int(sd.confirmed.sum())} lượt đạt. Cùng một tập nguồn vẫn được dùng lại; không biến5 seed thành5 tập kiểm tra độc lập hoặc nói đã kiểm tra nhiều họ trigger hơn.

## 4. Hai loại Isolation Forest

SHAP-IF theo từng đầu vào dùng500 mẫu reference để học vùng thường gặp và2000 mẫu calibration để đặt ngưỡng. Đã chấm đủ54 cấu hình, gồm cả malware chưa sửa làm đối chứng. Kết quả thấp vẫn được giữ; không đổi chiều điểm theo final để làm baseline đẹp lên.

IF lọc tập train là thí nghiệm khác: có quyền xem tập huấn luyện nghi nhiễm, loại5000 mẫu rồi huấn luyện lại. Trong hai cấu hình được chọn, nó giảm ASR nhưng vẫn để lại nhiều trường hợp tấn công thành công. Không trộn ASR sau retrain với recall của bộ cảnh báo theo từng file.

## 5. Điều đã kiểm chứng và điều đang chờ

39 kiểm thử hồi quy đã qua. Kiểm toán riêng đối chiếu score, số đếm, ngưỡng, ID, các tập con dữ liệu và222 tài sản gốc trong manifest. Đây là kiểm chứng phần mềm và bằng chứng số liệu, không phải chứng nhận hiệu quả phát hiện mọi backdoor.

Phúc cần gửi kết quả trigger trên file để nhận xét phần binary. Quân cần ghép đúng một bản Word rồi xuất PDF kiểm bố cục. Phú cần hoàn tất rà tài liệu tham khảo. Trong lúc chưa có kết quả binary, Abstract phải giữ giới hạn feature-space.
'''
    briefing=re.sub(r'(?<=[^\W\d_])(?=\d)|(?<=\d)(?=[^\W\d_])',' ',briefing)
    briefing=briefing.replace('EMBER 2018','EMBER2018').replace('EMBER 2024','EMBER2024')
    (OUT/'KET_QUA_CHO_TRUONG_NHOM_VI.md').write_text(briefing,encoding='utf8')
    equations=r'''# Equations checked against the current primary code

Source: src/xsentinel/detection/components.py and src/xsentinel/detection/calibration.py. Insert in Word's equation editor using LaTeX input, convert to professional layout, then inspect the exported PDF. This file supplies notation; it does not verify Word rendering or assign final equation numbers.

Let phi_j be signed native SHAP contributions to the malware raw margin, excluding the bias column. Let D(x) be the sum of absolute contributions over all features. The three feature views form the schema's partition. p_main and p_Beh are malware probabilities, not SHAP values.

```latex
D(x)=\sum_{j=1}^{d}|\phi_j(x)|
```

For D(x)>10^{-9}:

```latex
\mathrm{VMC}(x)=\max_{v\in\mathcal{V}}\frac{\sum_{j\in v}|\phi_j(x)|}{D(x)}
```

```latex
\mathrm{BGS}(x)=(1-p_{\mathrm{main}}(x))\frac{\max(0,\sum_{j\in\mathrm{Beh}}\phi_j(x))}{D(x)}
```

Set VMC and BGS to zero when D(x)<=10^{-9}, matching the implementation. BGS takes the positive part after summing signed Behavioral contributions; it does not sum only positive individual contributions.

```latex
\mathrm{BPG}(x)=\max(0,p_{\mathrm{Beh}}(x_{\mathrm{Beh}})-p_{\mathrm{main}}(x))
```

For a component k, use its own benign reference empirical CDF. The less-than-or-equal comparison includes ties.

```latex
\widehat{F}_k(t)=\frac{1}{n_r}\sum_{i=1}^{n_r}\mathbf{1}\{S_k(x_i^{\mathrm{ref}})\le t\},\qquad n_r=500
```

```latex
X_R(x)=\frac{\widehat{F}_{\mathrm{VMC}}(\mathrm{VMC}(x))+\widehat{F}_{\mathrm{BGS}}(\mathrm{BGS}(x))}{2}
```

```latex
X_F(x)=\frac{\widehat{F}_{\mathrm{VMC}}(\mathrm{VMC}(x))+\widehat{F}_{\mathrm{BPG}}(\mathrm{BPG}(x))}{2}
```

With ascending calibration scores s_(1),...,s_(n_c), use the one-based order statistic below. It is s_(1980) when n_c=2000 and alpha=0.01.

```latex
\tau=s_{(n_c-\lfloor\alpha n_c\rfloor)},\qquad \mathrm{alert}(x)=\mathbf{1}\{S(x)>\tau\}
```

Reference ranking uses <=; alerting uses >. These operators serve different purposes and must not be made identical for visual consistency. The calibration guarantee is at most20 of2000 calibration scores strictly above the threshold; it is not a guarantee of at most1% alerts on a new final pool.
'''
    (OUT/'EQUATIONS_FOR_WORD_EN.md').write_text(equations,encoding='utf8')
    claims=[
        ['Same-FPR comparison','same_fpr_comparison.csv','Confirmed original cohorts','Retrospective final thresholds; no new holdout'],
        ['Adaptive multiview failures','adaptive_summary.csv','24 frozen models;100 unique malware IDs per dataset','Vector-only; bounded search'],
        ['Additional seed variation','ember2024_seed_runs.csv;ember2024_seed_variability.csv','Five attempts in EMBER2024 spread2%','Four confirmed; failed attempt retained'],
        ['Clean-data access tradeoff','clean_budget_summary.csv;resource_access_comparison.csv','Nested labelled fit subsets; fixed original confirmed cohorts','Reference/calibration access separate'],
        ['Training sanitization context','training_defense_results.csv','Two seed17/spread2% cells','Adaptation; not a full benchmark or per-input baseline'],
        ['Cross2018 direct-evasion effect','cross_confirmation_diagnostics.csv;final_paired_metrics.csv','Confirmation and final separately','Net paired gain differs from paired-new-evasion rate'],
        ['SHAP novelty control','shap_if_original_malware_controls.csv','54 models with matched source IDs','Original-malware alert rate is not benign FPR']]
    pd.DataFrame(claims,columns=['Claim','Evidence','Scope','Limit']).to_csv(OUT/'claim_evidence.csv',index=False)
    for name in ('audit.json','tests_final.xml'):
        shutil.copy2(ROOT/name,OUT/name)
    if (ROOT/'diagnostics').exists():
        for p in (ROOT/'diagnostics').iterdir():
            if p.is_file():shutil.copy2(p,OUT/('diagnostics_manifest.json' if p.name=='manifest.json' else p.name))
    write_json(OUT/'delivery_manifest.json',dict(original_assets_verified=len(read_json(ROOT/'original_input_manifest.json')['sha256']),
        shap_if_cells=len(baseline),adaptive_cells=len(adaptive),budget_rows=len(budget),training_defense_rows=len(defense),
        seed_attempts=len(sd),confirmed_seed_attempts=int(sd.confirmed.sum()),
        code_sha256=sha256(__file__),files={str(p.relative_to(OUT)):sha256(p) for p in OUT.rglob('*') if p.is_file() and p.name!='delivery_manifest.json'}))
    print('Built',OUT,flush=True)


if __name__=='__main__':main()
