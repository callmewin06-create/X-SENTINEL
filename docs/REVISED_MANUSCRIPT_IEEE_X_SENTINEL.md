# Feature-View Attribution Concentration as a Per-Input Backdoor Signal for Static PE Classifiers

**Đặng Lý Quân, Trần Đặng Hữu Thắng, Lại Vĩnh Phú, Phạm Nguyễn Hoàng Phúc**  
*Department of Information Assurance, FPT University, Ho Chi Minh City, Vietnam*  
`{danglyquan, callmewin06, vinhphu2020, tqtphamnguyenhoangphuc}@gmail.com`

---

### Abstract
We investigate per-input backdoor suspicion in static PE malware classifiers using feature-view attribution and prediction signals. X-SENTINEL combines the maximum view share of absolute SHAP contributions—termed View Mass Concentration (VMC)—with either a Behavioral-Gated SHAP signal (BGS) under restricted access, or the positive Behavioral Probability Gap (BPG) between an auxiliary clean Behavioral classifier and a suspicious main classifier. All backdoor poisoning and evasion experiments in this benchmark operate strictly in feature space. In physical executable tests, an empirical audit demonstrates that isolated PE binary modifications do not realize multi-coordinate triggers without inducing substantial collateral feature drift. 

We evaluate frozen LightGBM classifiers across 54 model/attack configurations on EMBER2018 and the Win32, Win64, and .NET subsets of EMBER2024. In the primary restricted-access setting (Reduced), the defender holds only the suspicious model, 500 trusted benign reference samples, and 2,000 calibration samples. In the supplemental resource-rich setting (Full), the defender additionally leverages a clean Behavioral classifier. In the confirmed restricted cohort, Reduced detects 35.75% of successful-eligible attacks on EMBER2018 and 48.33% on EMBER2024 at calibrated 1% false-positive rates; Full achieves 42.94% and 59.75% recall. Retrospective low-FPR comparisons, signed-SHAP Isolation Forest baselines, and clean-data budget sweeps demonstrate that while Full outperforms Reduced, an auxiliary clean full-feature Shadow classifier substantially outperforms both whenever 200,000 trusted labeled training records are accessible. Furthermore, distributed cross-view triggers and bounded multiview adaptive optimization undermine view-concentration signals, increasing joint evasion by up to 15.25 percentage points. These findings establish attribution concentration as a measurable heuristic under restricted defender access rather than a universal defense against adaptive backdoors.

**Keywords**: PE malware classification; backdoor poisoning; LightGBM; TreeSHAP; attribution views; inference-time suspicion; calibration; problem-space feasibility.

---

## I. INTRODUCTION

Static machine learning classifiers summarize portable executable (PE) files into numerical feature vectors to predict malicious intent without dynamic execution. Public benchmark datasets, including EMBER [1] and EMBER2024 [2], standardise feature representations across Windows executables, while large-scale corpora such as BODMAS [3] and SOREL-20M [4] examine temporal distribution shifts. In production environments, gradient-boosted decision trees—specifically LightGBM [5]—are widely adopted due to their low inference latency, sub-millisecond evaluation, and tabular parsing efficiency.

Data poisoning attacks subvert machine learning classifiers by manipulating training samples. In a backdoor attack, an adversary injects a trigger pattern into training inputs while assigning a benign label, causing the trained model to misclassify triggered malware as benign at test time while maintaining standard accuracy on clean inputs [6], [7]. In static malware classification, prior research has explored explanation-guided backdoors [6] and selective triggering mechanisms [7]. However, feature-vector perturbations cannot be assumed to translate directly into valid, functioning executable files without breaking binary execution semantics [8].

When an enterprise defender receives an externally supplied, pre-trained malware classifier that may be trojaned, retraining from scratch is often impossible due to the lack of massive, trusted, clean training corpora. This motivates *inference-time suspicion scoring*: analyzing individual predictions to flag potentially poisoned inputs alongside the standard classification probability. Rather than seeking universal model auditing, we investigate whether feature-view attribution concentration and cross-view prediction disagreement provide measurable signals of backdoor manipulation.

We present an exhaustive evaluation of view-attribution signals under two distinct defender threat models:
1. **Reduced Resource Setting**: The defender possesses only the suspicious deployed model, 500 trusted benign reference samples, and 2,000 benign calibration samples.
2. **Full Resource Setting**: The defender additionally possesses an auxiliary clean Behavioral classifier trained on 200,000 clean labeled records.

Across 54 frozen poisoning configurations, we compare these signals against local maximum attribution (TADR) [6], randomized feature perturbation (STRIP) [9], a signed-SHAP novelty detection baseline (Isolation Forest) [10], and an unpoisoned full-feature Shadow model [6].

### Scientific Contributions
This study establishes four concrete contributions:
1. **Attribution and Discrepancy Formulations**: We formalize View Mass Concentration (VMC) and Behavioral-Gated SHAP (BGS) for tree-based PE classifiers, mapping native TreeSHAP attributions across disjoint structural, behavioral, and metadata views, paired with non-parametric empirical rank fusion.
2. **Standardized 54-Configuration Benchmark**: We present a complete, calibrated evaluation across 54 frozen attack configurations on EMBER2018 and EMBER2024, providing retrospective low-FPR comparisons, empirical FPR ceilings, and a signed-SHAP Isolation Forest novelty baseline.
3. **Identification of Fundamental Failure Modes**: We provide empirical evidence that distributed cross-view triggers and bounded multiview adaptive optimization defeat view-concentration heuristics, increasing joint evasion by up to 15.25 percentage points.
4. **Access-Cost and Binary-Feasibility Boundaries**: We quantify the performance gap relative to a clean Shadow model across five clean-data budget tiers (1,000 to 200,000 samples), and establish through physical binary compilation and modification of native C and .NET fixtures that feature-space triggers induce substantial collateral feature drift when applied to real PE files.

---

## II. RELATED WORK & THREAT MODEL

### A. PE Representations and Tree-Based Explanations
Feature-based static malware detection relies on parsing header structures, section characteristics, imported/exported dynamic-link libraries, byte histograms, and string statistics [1], [2]. Alternative paradigms include raw byte modeling via convolutional networks (MalConv) [11] and learned 2D binary representations [12]. 

For tabular feature vectors, LightGBM ensembles [5] dominate competitive static analysis. Feature attribution via TreeSHAP [13], [14] computes exact Shapley values in polynomial time $\mathcal{O}(TLD^2)$, decomposing the raw logit margin $f(x) = \phi_0 + \sum_{j=1}^M \phi_j(x)$ into additive local contributions. While SHAP attributions reflect internal model mechanics, they do not verify runtime executable behavior or causal compromise [14], [15].

Security evaluations in machine learning often suffer from experimental bias, temporal confounding, and improper claim boundaries [16], [17], [18]. TESSERACT [17] demonstrated that temporal drift significantly degrades malware classifiers over time. Consequently, baseline comparisons must condition strictly on identical data provenance, partition roles, and threshold-setting conventions.

### B. Poisoning, Evasion, and Problem-Space Constraints
Backdoor attacks inject covert triggers into models during training [6], [19], [20], [21]. Clean-label poisoning modifies training instances without altering their declared target label [22], [23]. In malware classification, Severi et al. [6] introduced explanation-guided backdoors, selecting trigger coordinates with high baseline Shapley attributions. 

However, modifying an executable binary is fundamentally constrained by the *problem space* [8]. Binary modifications must preserve executable file integrity, valid PE headers, and malicious payloads. In contrast, feature-space perturbations directly modify floating-point vector coordinates. Adversarial evasion attacks in PE classification [8], [24], [25], [26] highlight that arbitrary vector edits cannot simply be inverted into functional binaries without causing parse errors or loader rejections.

### C. Detection Baselines and Calibration
Existing backdoor defenses operate either at training time or inference time. Training-time defenses include data sanitization via Spectral Signatures [27], Activation Clustering [28], and model pruning [29]. Inference-time defenses include STRIP [9], which injects convex input perturbations to measure prediction entropy. However, blending continuous image pixels does not translate cleanly to discrete PE feature spaces where binary indicators and section counts lose structural semantics [9], [16].

Calibration under distribution-free risk regimes [30], [31] establishes that empirical order statistics on calibration sets control false positives up to finite-sample variation. Our thresholding enforces a strict order-statistic cutoff on dedicated benign calibration pools.

---

## III. METHODOLOGY AND FORMULATION

### A. Defender Access and Threat Model
We distinguish four levels of defender resource access, summarized in Table I:

**TABLE I: Defender Resource Access Settings During Scoring**
| Setting | Suspicious Main Model | Benign Calibration Data | Clean Labeled Data | Auxiliary Models |
|---|---|---|---|---|
| **Reduced** | Suspicious LightGBM | 500 Ref + 2,000 Cal | None | None |
| **Full** | Suspicious LightGBM | 500 Ref + 2,000 Cal | 200,000 Clean Fit | Clean Behavioral Model (150 rounds) |
| **Shadow** | Suspicious LightGBM | 500 Ref + 2,000 Cal | 200,000 Clean Fit | Clean Full Model (500 rounds) |
| **Sanitization** | Retrained LightGBM | 500 Ref | Full Poisoned Fit | Top-32 SHAP Isolation Forest Filter |

Under **Reduced**, the defender receives a frozen, suspicious LightGBM model $f(x)$ and holds only 500 trusted benign reference samples $\mathcal{D}_{\text{ref}}$ and 2,000 disjoint benign calibration samples $\mathcal{D}_{\text{cal}}$. Under **Full**, the defender possesses 200,000 clean labeled training records and trains a dedicated Behavioral LightGBM model $f_{\text{Beh}}(x_{\text{Beh}})$. Under **Shadow**, the defender trains an unpoisoned 500-round full-feature LightGBM model $f_{\text{clean}}(x)$ on the same 200,000 records.

### B. Disjoint Feature-View Partitioning
We partition static PE feature vectors into three disjoint semantic views based on file structural specifications:
- **Structural View ($V_S$)**: Header fields, COFF characteristics, section counts, data directories, and PE dimensions.
- **Behavioral View ($V_B$)**: Imported functions, imported DLLs, exported symbols, and API hash buckets.
- **Metadata View ($V_M$)**: File size, byte entropy histograms, string statistics, and section hash tails.

**TABLE II: Versioned Feature-View Coordinate Partitions**
| Dataset Schema | Total Dim ($M$) | Structural ($V_S$) | Behavioral ($V_B$) | Metadata ($V_M$) | Behavioral Interval |
|---|---|---|---|---|---|
| **EMBER2018 (V2)** | 2,381 | 357 | 1,408 | 616 | $[943, 2351)$ |
| **EMBER2024 (V3)** | 2,568 | 467 | 1,411 | 690 | $[994, 2405)$ |

### C. Mathematical Formulation of Suspicion Signals
Let $p(x) = \sigma(f(x))$ denote the predicted malware probability of the main model, and let $\phi_j(x)$ denote the TreeSHAP attribution of feature $j$ to the raw margin $f(x)$, excluding the bias term $\phi_0$. 

The total absolute attribution mass $A(x)$ and the signed view attribution sum $N_v(x)$ are defined as:
$$A(x) = \sum_{j=1}^M |\phi_j(x)|, \quad N_v(x) = \sum_{j \in V_v} \phi_j(x), \quad v \in \{S, B, M\}$$
To prevent division by zero, if $A(x) \le \epsilon = 10^{-9}$, attribution ratios return zero.

#### 1. Baseline Comparator: Top Attribution Deficit Ratio (TADR)
Severi et al. [6] define TADR as the maximum attribution share of a single individual feature:
$$\text{TADR}(x) = \frac{\max_{1 \le j \le M} |\phi_j(x)|}{A(x)}$$

#### 2. View Mass Concentration (VMC)
When an attacker distributes a trigger across multiple features within a single view (e.g., 10 structural features), individual feature attributions are diluted, causing TADR to collapse. VMC measures the maximum attribution share concentrated within any single view:
$$\text{VMC}(x) = \max_{v \in \{S, B, M\}} \left( \frac{\sum_{j \in V_v} |\phi_j(x)|}{A(x)} \right)$$

#### 3. Behavioral-Gated SHAP (BGS - Reduced M4)
In clean-label backdoor attacks, the classifier is manipulated into predicting benign ($p(x) \to 0$), yet the malicious payload retains its imported API capabilities in $V_B$. BGS exploits this tension on a single model without requiring auxiliary training:
$$\text{BGS}(x) = (1 - p(x)) \cdot \frac{\max(N_B(x), 0)}{A(x)}$$
The gating operator $\max(N_B(x), 0)$ activates strictly when behavioral features vote toward malware, while $(1 - p(x))$ amplifies suspicion when the main classifier strongly predicts benign.

#### 4. Behavioral Probability Gap (BPG - Full M4)
Under Full access, an auxiliary classifier $f_{\text{Beh}}$ is trained exclusively on the 1,408 behavioral features of clean training data. BPG measures the positive probability discrepancy between the clean behavioral classifier and the suspicious main model:
$$\text{BPG}(x) = \max\left(0, p_{\text{Beh}}(x_{\text{Beh}}) - p(x)\right)$$

### D. Rank Transformation, Fusion, and Calibration
Because VMC, BGS, and BPG occupy disparate mathematical domains, direct summation is uncalibrated. We apply a non-parametric empirical rank transformation using the right empirical cumulative distribution function (ECDF) over the 500 trusted benign reference samples $\mathcal{D}_{\text{ref}}$:
$$R_{\text{ref}}(s) = \frac{1}{500} \sum_{r \in \mathcal{D}_{\text{ref}}} \mathbb{I}(\text{score}(r) \le s)$$
Ties are preserved using standard right-rank conventions.

The fused suspicion scores are defined as:
$$X_R(x) = \frac{1}{2} \left[ R_{\text{ref}}(\text{VMC}(x)) + R_{\text{ref}}(\text{BGS}(x)) \right]$$
$$X_F(x) = \frac{1}{2} \left[ R_{\text{ref}}(\text{VMC}(x)) + R_{\text{ref}}(\text{BPG}(x)) \right]$$

#### Locked Empirical Threshold Selection
For each detector, threshold $\tau$ is locked using the 2,000 benign calibration samples $\mathcal{D}_{\text{cal}}$. Scores are sorted in ascending order, and $\tau$ is set to the 1,980th value (the 99th empirical percentile):
$$\tau = s_{(1980)}, \quad s \in \mathcal{D}_{\text{cal}}$$
An alert is raised strictly if $\text{score}(x) > \tau$, guaranteeing at most 20 false positives on $\mathcal{D}_{\text{cal}}$ ($\le 1.0\%$).

### E. Comparative Baselines: Shadow and Novelty Detection
- **Shadow Comparator**: Evaluates the probability discrepancy against the clean 500-round full model:
  $$\text{Shadow}(x) = \max(0, p_{\text{clean}}(x) - p(x))$$
  Thresholded at the 99th percentile of $\mathcal{D}_{\text{cal}}$.
- **Signed-SHAP Isolation Forest (SHAP-IF)**: We fit an Isolation Forest [10] (200 trees, 256 samples per tree) on signed native SHAP vectors from $\mathcal{D}_{\text{ref}}$, excluding bias. Anomaly scores are negated so that higher values denote greater anomaly, thresholded at the 99th percentile of $\mathcal{D}_{\text{cal}}$.

---

## IV. EXPERIMENTAL PROTOCOL

### A. Dataset Provenance and Partition Roles
We evaluate on EMBER2018 [1] and the PE subset of EMBER2024 [2] (pinned to HuggingFace commit `3d23efe`). Data partitions are strictly disjoint across roles:
- **Fit Pool**: 200,000 records (100,000 benign, 100,000 malware).
- **Selection / Development / Confirmation Pools**: 10,000 balanced records each.
- **Reference Pool ($\mathcal{D}_{\text{ref}}$)**: 500 benign records.
- **Calibration Pool ($\mathcal{D}_{\text{cal}}$)**: 2,000 benign records.
- **Final Evaluation Pool**: 20,000 balanced records (10,000 benign, 10,000 malware).

**TABLE III: Dataset Provenance and Parse Success by Partition Role**
| Role | Total ($n$) | Win32 | Win64 | .NET | Parse Flag `is_pe=0` | Benign / Malware in `is_pe=0` |
|---|---|---|---|---|---|---|
| **Fit** | 200,000 | 133,316 | 44,520 | 22,164 | 69 | 34 / 35 |
| **Selection** | 10,000 | 6,641 | 2,238 | 1,121 | 5 | 3 / 2 |
| **Development** | 10,000 | 6,653 | 2,237 | 1,110 | 7 | 3 / 4 |
| **Confirmation** | 10,000 | 6,656 | 2,233 | 1,111 | 4 | 2 / 2 |
| **Reference** | 500 | 331 | 126 | 43 | 0 | 0 / 0 |
| **Calibration** | 2,000 | 1,319 | 456 | 225 | 2 | 2 / 0 |
| **Final** | 20,000 | 13,313 | 4,470 | 2,217 | 3 | 3 / 0 |

Across all roles, EMBER2024 contains 90 records where `is_pe=0`. Feature inspection reveals that these entries contain zero feature tails from index 696 onward. In sensitivity testing, removing these entries shifted thresholds by less than $0.006$ and recall by less than $3.12\%$, establishing that parse failures do not drive detector performance.

### B. Attack Configurations and Screening
We evaluate 27 configurations per dataset across three model seeds (17, 29, 43), three poisoning rates ($0.5\%, 1.0\%, 2.0\%$ of all fit records, corresponding to 1,000, 2,000, and 4,000 poisons), and three attack geometries:
- **Concentrated Structural ($C$)**: 2 Structural columns.
- **Spread Structural ($S$)**: 10 Structural columns.
- **Cross-View Stress ($X$)**: 24 columns (8 Structural + 8 Behavioral + 8 Metadata).

**TABLE IV: Locked Training and Attack Parameters**
| Parameter | Setting |
|---|---|
| **Main & Clean Models** | LightGBM, 500 rounds, 64 leaves, learning rate 0.05, feature/bagging fraction 0.9 |
| **Clean View Models** | LightGBM, 150 rounds, same 200,000 clean fit records |
| **Poisoning Rates** | 1,000 (0.5%), 2,000 (1.0%), 4,000 (2.0%) of 200,000 total fit records |
| **Feature Selector** | `legacy_rare` (locked across all runs) |
| **Confirmation Cutoffs** | $\ge 1,000$ eligible malware, $\text{ASR} \ge 50\%$, Net Paired Gain $\ge 20\%$, Clean Loss $< 0.5\%$ |

An attack configuration is confirmed only if it satisfies all screening thresholds on both development and confirmation pools.

### C. Evaluation Metrics and Denominators
We define attack evaluation groups explicitly:
- **Eligible Malware**: Final malware correctly classified as malware by the clean model ($p_{\text{clean}}(x) \ge 0.5$).
- **Successful-Eligible**: Eligible malware classified as benign by the poisoned model after trigger insertion ($p(x_{\text{trig}}) < 0.5$).
- **Attack Success Rate (ASR)**: Ratio of successful-eligible attacks to eligible malware.
- **Detection Recall**: Percentage of successful-eligible attacks flagged by the detector ($\text{score} > \tau$).
- **Post-Defense ASR**: Percentage of eligible malware that successfully evades the classifier and avoids detection.
- **Benign FPR**: Percentage of 10,000 unpoisoned final benign inputs flagged by the detector.

---

## V. EMPIRICAL RESULTS

### A. Attack Family Confirmation Status
Table V reports the confirmation outcome across all 54 attack configurations:

**TABLE V: Attack Confirmation Status by Family**
| Dataset | Concentrated ($C$) | Spread Structural ($S$) | Cross-View Stress ($X$) | Total Confirmed |
|---|---|---|---|---|
| **EMBER2018** | 3 / 9 | 9 / 9 | 0 / 9 | **12 / 27** |
| **EMBER2024** | 0 / 9 | 3 / 9 | 9 / 9 | **12 / 27** |

On EMBER2018, all 9 spread configurations and 3 concentrated configurations (at 2% rate) passed confirmation; cross-view attacks failed because their net paired gain was below 20%. On EMBER2024, the restricted confirmed cohort consists solely of 3 spread runs at 2% rate, while all 9 cross-view runs passed confirmation.

### B. Detection Performance at Calibrated Thresholds
Table VI summarizes performance on the confirmed restricted cohorts under original calibration thresholds:

**TABLE VI: Restricted Confirmed Cohort at Calibrated Operating Points**
| Dataset | Method | Runs | Recall (%) | Benign FPR (%) | Post-Defense ASR (%) | AUROC (Success) |
|---|---|---|---|---|---|---|
| **EMBER2018** | TADR | 12 | 37.15 | 1.92 | 43.07 | 0.884 |
| | STRIP | 12 | 0.00 | 0.61 | 69.04 | 0.112 |
| | VMC ($M3$) | 12 | 14.54 | 0.76 | 55.98 | 0.870 |
| | BGS ($M4R$) | 12 | 7.47 | 0.91 | 63.59 | 0.822 |
| | BPG ($M4F$) | 12 | 38.89 | 1.03 | 40.78 | 0.890 |
| | **X-R (Reduced)** | 12 | **35.75** | **0.52** | **39.92** | **0.895** |
| | **X-F (Full)** | 12 | **42.94** | **0.78** | **35.22** | **0.929** |
| **EMBER2024** | TADR | 3 | 0.00 | 0.65 | 56.88 | 0.238 |
| | STRIP | 3 | 0.00 | 0.75 | 56.88 | 0.133 |
| | VMC ($M3$) | 3 | 60.64 | 1.05 | 22.22 | 0.947 |
| | BGS ($M4R$) | 3 | 5.82 | 0.88 | 53.58 | 0.834 |
| | BPG ($M4F$) | 3 | 49.79 | 1.07 | 28.62 | 0.883 |
| | **X-R (Reduced)** | 3 | **48.33** | **0.78** | **29.38** | **0.954** |
| | **X-F (Full)** | 3 | **59.75** | **0.83** | **22.78** | **0.935** |

On EMBER2018, fusing VMC with BGS ($X_R$) lifts recall from 14.54% to 35.75%, while $X_F$ achieves 42.94%. On EMBER2024, TADR completely collapses to 0.00% recall because the 10-feature spread trigger dilutes single-feature attribution. In contrast, VMC captures the concentrated mass in $V_S$, attaining 60.64% recall. STRIP achieves 0.00% recall on both datasets with AUROCs below 0.15, confirming that convex vector mixing disrupts discrete PE tree logic.

### C. The Failure of View Concentration Under Cross-View Triggers
When the attacker spreads perturbations across all three views (8 Structural, 8 Behavioral, 8 Metadata), the fundamental premise of view concentration is dismantled:

**TABLE VII: EMBER2024 Confirmed Cross-View Stress Results**
| Method | Runs | Recall (%) | Benign FPR (%) | Baseline ASR (%) | Post-Defense ASR (%) |
|---|---|---|---|---|---|
| **TADR** | 9 | 0.00 | 0.75 | 99.51 | 99.51 |
| **VMC ($M3$)** | 9 | 1.84 | 1.11 | 99.51 | 97.69 |
| **BGS ($M4R$)** | 9 | 0.09 | 0.70 | 99.51 | 99.43 |
| **BPG ($M4F$)** | 9 | 12.31 | 1.02 | 99.51 | 87.24 |
| **X-R (Reduced)** | 9 | **0.00** | **0.75** | 99.51 | 99.51 |
| **X-F (Full)** | 9 | **5.56** | **0.93** | 99.51 | 94.00 |

Under cross-view attacks, VMC recall plummets to 1.84%, and Reduced fusion drops to 0.00%. Because attribution mass is distributed proportionally across $V_S$, $V_B$, and $V_M$, no single view exhibits anomalous dominance.

### D. Retrospective Low-FPR and Standardized Partial AUC Comparison
To evaluate detectors fairly without threshold bias, Table VIII reports True Positive Rate (TPR) at an empirical final-set FPR capped strictly at 1.0%, along with standardized partial AUROC ($\text{pAUC}$) integrated over $\text{FPR} \in [0, 0.01]$:

**TABLE VIII: Retrospective Low-FPR Matched Operating Point Comparison**
| Dataset | Cohort | Method | Runs | Max TPR at 1% FPR (%) | Actual FPR (%) | Standardized pAUC |
|---|---|---|---|---|---|---|
| **EMBER2018** | Restricted | SHAP-IF | 12 | 0.16 | 0.99 | 0.4978 |
| | Restricted | Shadow | 12 | **99.99** | 1.00 | **0.9995** |
| | Restricted | Full ($X_F$) | 12 | 44.72 | 0.96 | 0.6797 |
| | Restricted | Reduced ($X_R$) | 12 | 37.69 | 0.87 | 0.6713 |
| **EMBER2024** | Cross | SHAP-IF | 9 | 0.02 | 1.00 | 0.4975 |
| | Cross | Shadow | 9 | **99.60** | 1.00 | **0.9907** |
| | Cross | Full ($X_F$) | 9 | 6.01 | 0.94 | 0.5179 |
| | Cross | Reduced ($X_R$) | 9 | 0.00 | 0.98 | 0.4975 |
| **EMBER2024** | Restricted | SHAP-IF | 3 | 0.04 | 1.00 | 0.4976 |
| | Restricted | Shadow | 3 | **99.98** | 1.00 | **0.9990** |
| | Restricted | Full ($X_F$) | 3 | 60.13 | 0.95 | 0.7684 |
| | Restricted | Reduced ($X_R$) | 3 | 52.82 | 0.97 | 0.6838 |

The signed-SHAP Isolation Forest baseline fails completely (TPR $\le 0.16\%$, $\text{pAUC} \approx 0.497$), demonstrating that unsupervised density estimation on signed SHAP vectors cannot distinguish poisoned inputs from clean variance. Conversely, the Shadow model attains near-perfect detection ($>99.6\%$).

### E. Clean Data Budget Analysis: Full vs. Shadow
To evaluate the impact of defender clean-data availability, we evaluate Full and Shadow across five nested training budgets (1,000 to 200,000 clean labeled fit records):

**TABLE IX: Detection Recall (TPR % at 1% FPR) Across Clean Data Budgets**
| Dataset Cohort | Method | 1,000 Samples | 5,000 Samples | 10,000 Samples | 50,000 Samples | 200,000 Samples |
|---|---|---|---|---|---|---|
| **EMBER2018 Restricted** | Full ($X_F$) | 33.60 | 38.12 | 40.54 | 43.15 | 44.72 |
| | Shadow | 16.90 | 48.75 | 76.20 | 96.40 | **99.99** |
| **EMBER2024 Restricted** | Full ($X_F$) | 56.24 | 58.10 | 58.90 | 59.50 | 60.13 |
| | Shadow | 51.29 | 74.30 | 88.60 | 98.10 | **99.98** |

When the defender possesses only 1,000 clean samples, Full outperforms Shadow (33.60% vs 16.90% on 2018; 56.24% vs 51.29% on 2024). However, as clean data scales to 10,000+ samples, Shadow's recall surges past 76%, reaching near 100% at 200,000 records. Full's utility is thus strictly confined to low-resource settings ($<5,000$ clean samples).

### F. Bounded Multiview Adaptive Optimization
We evaluate an adaptive attacker targeting 24 confirmed models across 100 lexicographically ordered malware source IDs. The attacker queries the suspicious model and Reduced detector, retaining the fixed trigger while perturbing up to 8 additional coordinates per view using benign selection values (maximum 32 sequential queries):

**TABLE X: Bounded Multiview Adaptive Attack Progression**
| Dataset | Cohort | Evaluated Runs | Initial Joint Evasion (%) | Final Joint Evasion (%) | Evasion Increase (pp) |
|---|---|---|---|---|---|
| **EMBER2018** | Restricted | 12 | 44.25 | 59.50 | **+15.25** |
| **EMBER2024** | Cross | 9 | 100.00 | 100.00 | 0.00 |
| **EMBER2024** | Restricted | 3 | 36.77 | 45.02 | **+8.25** |

Under bounded search, adaptive evasion against Reduced increases by 15.25 percentage points on EMBER2018 and 8.25 points on EMBER2024. In the cross cohort, all inputs evaded both classifier and detector from the initial query.

### G. Seed Variability on EMBER2024
To assess stability beyond the initial three seeds, we pre-declared seeds 59 and 71 under spread Structural 2% poisoning:

**TABLE XI: EMBER2024 Spread 2% Seed Repetitions**
| Seed | Origin | Confirmed | Confirmation ASR (%) | Reduced Recall (%) | Reduced FPR (%) | Full Recall (%) | Full FPR (%) |
|---|---|---|---|---|---|---|---|
| **17** | Original | True | 57.46 | 48.85 | 0.85 | 62.79 | 0.61 |
| **29** | Original | True | 55.81 | 48.86 | 0.81 | 63.67 | 0.71 |
| **43** | Original | True | 52.18 | 47.27 | 0.67 | 52.79 | 1.16 |
| **59** | Additional | True | 53.33 | 54.30 | 0.79 | 60.06 | 0.93 |
| **71** | Additional | False | 49.82 | 45.94 | 0.67 | 52.90 | 0.98 |

Seed 71 achieved 49.82% confirmation ASR, narrowly missing the 50% cutoff. Across the four confirmed seeds, Reduced recall averaged $49.82\% \pm 3.08\%$ (range: 47.27–54.30%), and Full recall averaged $59.83\% \pm 4.94\%$ (range: 52.79–63.67%).

### H. Training-Data Sanitization Context
Following Severi et al. [6], we test a training-time defense: selecting 32 features by mean absolute SHAP on 500 benign reference samples, fitting an Isolation Forest on benign training vectors, and discarding the top 5% suspicious samples prior to retraining:

**TABLE XII: Training-Data Sanitization vs. Random Removal Control**
| Dataset | Method | Samples Removed | Poisons Removed | Clean Removed | Pre-Defense ASR (%) | Post-Defense ASR (%) | Clean Accuracy (%) |
|---|---|---|---|---|---|---|---|
| **EMBER2018** | IF-Top32 | 5,000 | 977 | 4,023 | 97.81 | 95.75 | 95.93 |
| | Random Ctrl | 5,000 | 169 | 4,831 | 97.81 | 98.86 | 96.08 |
| **EMBER2024** | IF-Top32 | 5,000 | 1,845 | 3,155 | 59.39 | 35.84 | 97.31 |
| | Random Ctrl | 5,000 | 169 | 4,831 | 59.39 | 59.79 | 97.36 |

On EMBER2024, sanitization eliminates 1,845 of 4,000 poisons, lowering ASR from 59.39% to 35.84%. However, on EMBER2018, residual ASR remains at 95.75%, demonstrating that training sanitization leaves substantial vulnerability.

### I. Physical PE Binary Validation & Trigger Realizability
A central question in malware backdoor research is whether feature-space vector perturbations can be realized in functional executable binaries. Severi et al. [6] evaluated explanation-guided backdoors on EMBER; however, an independent audit of their public repository (`ClonedOne/MalwareBackdoors`) reveals that their code modified vector arrays in-memory (`x[idx] = val`) without providing a binary watermarking engine for PE files.

To empirically evaluate physical realizability, we developed two deterministic, self-contained benign PE fixtures:
1. **64-bit Native C Console Binary**: Cross-compiled using `x86_64-w64-mingw32-gcc -O2 -s -Wl,--build-id=none` (43,520 bytes).
2. **Managed .NET C# Executable**: Compiled targeting .NET Framework (4,096 bytes).

Both fixtures compute $f(n) = n^2 + 7$. We implemented binary-level modifications matching the study's triggers: setting the COFF `TimeDateStamp` to epoch zero, the EMBER2018 target ($1,053,454,528$), and the EMBER2024 target ($1,147,337,216$), as well as appending 256 bytes of overlay padding. We re-extracted feature vectors using the isolated extractor and scored them against 24 frozen primary detector bundles:

**TABLE XIII (REVISED TABLE XVI): Feature Shifts and Scoring of Controlled PE Binary Modifications**
| Fixture Type | Target Binary Edit | Schema | Cases Checked | Intended Coordinate Matched | Total Shifted | Structural Shifted | Behavioral Shifted | Metadata Shifted | Unintended Collateral Shifts | Detector Alerts (XR) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Native C (x64)** | Timestamp 0 | V2 | 4 / 4 | Yes (1/1) | 11 | 1 | 0 | 10 | **10** | 0 / 24 |
| **Native C (x64)** | Timestamp 0 | V3 | 4 / 4 | Yes (1/1) | 12 | 1 | 0 | 11 | **11** | 0 / 24 |
| **Native C (x64)** | Timestamp Target | V2 | 4 / 4 | Yes (1/1) | 12 | 1 | 0 | 11 | **11** | 0 / 24 |
| **Native C (x64)** | Timestamp Target | V3 | 4 / 4 | Yes (1/1) | 13 | 1 | 0 | 12 | **12** | 0 / 24 |
| **Native C (x64)** | Overlay (+256B) | V2 | 4 / 4 | Yes (1/1) | 348 | 1 | 0 | 347 | **347** | 0 / 24 |
| **Native C (x64)** | Overlay (+256B) | V3 | 4 / 4 | Yes (1/1) | 353 | 5 | 0 | 348 | **348** | 0 / 24 |
| **.NET C#** | Timestamp 0 | V2 | 4 / 4 | Yes (1/1) | 11 | 1 | 0 | 10 | **10** | 0 / 24 |
| **.NET C#** | Timestamp 0 | V3 | 4 / 4 | Yes (1/1) | 12 | 1 | 0 | 11 | **11** | 0 / 24 |
| **.NET C#** | Timestamp Target | V2 | 4 / 4 | Yes (1/1) | 14 | 1 | 0 | 13 | **13** | 0 / 24 |
| **.NET C#** | Timestamp Target | V3 | 4 / 4 | Yes (1/1) | 15 | 1 | 0 | 14 | **14** | 0 / 24 |
| **.NET C#** | Overlay (+256B) | V2 | 4 / 4 | Yes (1/1) | 232 | 1 | 0 | 231 | **231** | 0 / 24 |
| **.NET C#** | Overlay (+256B) | V3 | 4 / 4 | Yes (1/1) | 238 | 6 | 0 | 232 | **232** | 0 / 24 |

#### Experimental Observations
1. **Collateral Feature Drift Invariant**: Modifying 4 bytes of COFF timestamp inevitably alters 10 to 14 metadata features (byte entropy and byte histograms). Appending overlay padding shifts 231 to 348 features.
2. **Structural Integrity Constraints**: Forcing the concentrated trigger's second coordinate (`num_read_and_execute_sections = 12/20`) cannot be achieved in a real PE file without invalidating section headers and causing OS loader crashes.
3. **Execution Integrity**: Native C variants executed identically across all test cases on Windows and Linux Wine (20/20 test cases preserved exit code and stdout). .NET binaries with historic timestamps were intercepted by Windows Application Control policies (`WinError 4551`).
4. **Detector Alert Invariance**: All 10 modified binary variants produced **0 alerts across 240 detector evaluations** ($X_R \le \tau_{XR}$). Because isolated binary edits induce collateral drift rather than isolated trigger convergence, they do not trigger view-concentration alerts.

---

## VI. DISCUSSION & LIMITATIONS

Our empirical findings establish explicit boundary conditions for view-attribution backdoor detection:

1. **Feature Space vs. Problem Space**: All evaluated poisoning attacks operate in feature vector space. Real-world binary file manipulation induces widespread collateral feature drift, leaving problem-space backdoor realization an unresolved challenge.
2. **Vulnerability to Multi-View Dispersion**: View Mass Concentration relies on trigger confinement within a single view. Cross-view triggers and multiview adaptive optimization disperse attribution mass, reducing detection recall to near zero.
3. **Resource Regimes and the Dominance of Shadow Models**: When a defender possesses 10,000 or more clean training samples, an unpoisoned Shadow classifier outperforms attribution heuristics, achieving $>99\%$ recall. Attribution-based detection is justified strictly under restricted access ($\le 1,000$ clean samples).
4. **Data Confounding Across Benchmark Generations**: EMBER2024 features 467 structural dimensions compared to 357 in EMBER2018. The concentration of attributions in EMBER2024 reflects both schema expansion and dataset composition rather than an invariant property of PE malware.
5. **False Positives on Minimalist Binaries**: The clean EMBER2024 classifier predicted our tiny self-built benign fixtures as malware ($p > 0.5$). This reflects training set representation bias against extremely small ($<50$ KB) synthetic binaries rather than a backdoor phenomenon.

---

## VII. CONCLUSION

X-SENTINEL demonstrates that feature-view attribution concentration and behavioral discrepancy provide measurable suspicion signals for static PE malware classifiers under restricted defender access. On frozen EMBER benchmarks, combining View Mass Concentration with Behavioral-Gated SHAP achieves 35.75% to 48.33% recall at calibrated 1% false-positive rates without requiring clean training data. 

However, view concentration fails when attackers distribute triggers across multiple views or employ adaptive optimization. Furthermore, clean Shadow models dominate attribution heuristics whenever clean training data are abundant, and physical PE binary modifications do not reproduce vector triggers without significant collateral feature drift. Consequently, attribution concentration represents a calibrated triage signal under constrained defender access rather than a complete defense against backdoor attacks.

---

## REFERENCES
1. H. S. Anderson and P. Roth, "EMBER: An Open Dataset for Training Static PE Malware Machine Learning Models," *arXiv preprint arXiv:1804.04637*, 2018.
2. R. J. Joyce, G. Miller, P. Roth, R. Zak, E. Zaresky-Williams, H. Anderson, E. Raff, and J. Holt, "EMBER2024: A Benchmark Dataset for Holistic Evaluation of Malware Classifiers," in *Proc. 31st ACM SIGKDD Conf. Knowl. Discov. Data Min. (KDD)*, 2025, pp. 5516–5526.
3. L. Yang, A. Ciptadi, I. Laziuk, A. Ahmadzadeh, and G. Wang, "BODMAS: An Open Dataset for Learning based Temporal Analysis of PE Malware," in *Proc. IEEE Secur. Priv. Workshops (SPW)*, 2021, pp. 78–84.
4. R. Harang and E. M. Rudd, "SOREL-20M: A Large Scale Benchmark Dataset for Malicious PE Detection," *arXiv preprint arXiv:2012.07634*, 2020.
5. G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, and T.-Y. Liu, "LightGBM: A Highly Efficient Gradient Boosting Decision Tree," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 30, 2017, pp. 3146–3154.
6. G. Severi, J. Meyer, S. Coull, and A. Oprea, "Explanation-Guided Backdoor Poisoning Attacks Against Malware Classifiers," in *Proc. 30th USENIX Secur. Symp. (USENIX Security)*, 2021, pp. 1487–1504.
7. L. Yang, Z. Chen, J. Cortellazzi, F. Pendlebury, K. Tu, F. Pierazzi, L. Cavallaro, and G. Wang, "Jigsaw Puzzle: Selective Backdoor Attack to Subvert Malware Classifiers," in *Proc. 44th IEEE Symp. Secur. Priv. (S&P)*, 2023, pp. 719–736.
8. F. Pierazzi, F. Pendlebury, J. Cortellazzi, and L. Cavallaro, "Intriguing Properties of Adversarial ML Attacks in the Problem Space," in *Proc. 41st IEEE Symp. Secur. Priv. (S&P)*, 2020, pp. 1332–1349.
9. Y. Gao, C. Xu, D. Wang, S. Chen, D. C. Ranasinghe, and S. Nepal, "STRIP: A Defence Against Trojan Attacks on Deep Neural Networks," in *Proc. 35th Annu. Comput. Secur. Appl. Conf. (ACSAC)*, 2019, pp. 113–125.
10. F. T. Liu, K. M. Ting, and Z.-H. Zhou, "Isolation Forest," in *Proc. 8th IEEE Int. Conf. Data Min. (ICDM)*, 2008, pp. 413–422.
11. E. Raff, J. Barker, J. Sylvester, R. Brandon, B. Catanzaro, and C. Nicholas, "Malware Detection by Eating a Whole EXE," in *Proc. Workshops AAAI Conf. Artif. Intell.*, 2018.
12. J. Saxe and K. Berlin, "Deep Neural Network Based Malware Detection Using Two Dimensional Binary Program Features," in *Proc. 10th Int. Conf. Malicious Unwanted Softw. (MALWARE)*, 2015, pp. 11–20.
13. S. M. Lundberg and S.-I. Lee, "A Unified Approach to Interpreting Model Predictions," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 30, 2017, pp. 4765–4774.
14. S. M. Lundberg, G. Erion, H. Chen, A. DeGrave, J. M. Prutkin, B. Nair, R. Katz, J. Himmelfarb, N. Bansal, and S.-I. Lee, "From Local Explanations to Global Understanding with Explainable AI for Trees," *Nat. Mach. Intell.*, vol. 2, no. 1, pp. 56–67, 2020.
15. M. T. Ribeiro, S. Singh, and C. Guestrin, ""Why Should I Trust You?": Explaining the Predictions of Any Classifier," in *Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discov. Data Min. (KDD)*, 2016, pp. 1135–1144.
16. D. Arp, E. Quiring, F. Pendlebury, A. Warnecke, F. Pierazzi, C. Wressnegger, L. Cavallaro, and K. Rieck, "Dos and Don'ts of Machine Learning in Computer Security," in *Proc. 31st USENIX Secur. Symp. (USENIX Security)*, 2022, pp. 3971–3988.
17. F. Pendlebury, F. Pierazzi, R. Jordaney, J. Kinder, and L. Cavallaro, "TESSERACT: Eliminating Experimental Bias in Malware Classification Across Space and Time," in *Proc. 28th USENIX Secur. Symp. (USENIX Security)*, 2019, pp. 729–746.
18. F. Barbero, F. Pendlebury, F. Pierazzi, and L. Cavallaro, "Transcending TRANSCEND: Revisiting Malware Classification in the Presence of Concept Drift," in *Proc. 43rd IEEE Symp. Secur. Priv. (S&P)*, 2022, pp. 805–823.
19. T. Gu, B. Dolan-Gavitt, and S. Garg, "BadNets: Identifying Vulnerabilities in the Machine Learning Model Supply Chain," *IEEE Access*, vol. 7, pp. 47230–47244, 2019.
20. Y. Liu, S. Ma, Y. Aafer, W.-C. Lee, J. Zhai, W. Wang, and X. Zhang, "Trojaning Attack on Neural Networks," in *Proc. 25th Annu. Netw. Distrib. Syst. Secur. Symp. (NDSS)*, 2018.
21. Y. Li, Y. Jiang, Z. Li, and S.-T. Xia, "Backdoor Learning: A Survey," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 35, no. 1, pp. 5–22, 2024.
22. A. Turner, D. Tsipras, and A. Madry, "Label-Consistent Backdoor Attacks," *arXiv preprint arXiv:1912.02771*, 2019.
23. A. Shafahi, W. R. Huang, M. Najibi, O. Suciu, C. Studer, T. Dumitras, and T. Goldstein, "Poison Frogs! Targeted Clean-Label Poisoning Attacks on Neural Networks," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 31, 2018, pp. 6103–6113.
24. H. S. Anderson, A. Kharkar, B. Filar, D. Evans, and P. Roth, "Learning to Evade Static PE Machine Learning Malware Models via Reinforcement Learning," *arXiv preprint arXiv:1801.08917*, 2018.
25. B. Kolosnjaji, A. Demontis, B. Biggio, D. Maiorca, G. Giacinto, C. Eckert, and F. Roli, "Adversarial Malware Binaries: Evading Deep Learning for Malware Detection in Executables," in *Proc. 26th Eur. Signal Process. Conf. (EUSIPCO)*, 2018, pp. 533–537.
26. L. Demetrio, B. Biggio, G. Lagorio, F. Roli, and A. Armando, "Functionality-Preserving Black-Box Optimization of Adversarial Windows Malware," *IEEE Trans. Inf. Forensics Secur.*, vol. 16, pp. 3469–3478, 2021.
27. B. Tran, J. Li, and A. Madry, "Spectral Signatures in Backdoor Attacks," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 31, 2018, pp. 8000–8010.
28. B. Chen, W. Carvalho, N. Baracaldo, H. Ludwig, B. Edwards, T. Lee, I. Molloy, and B. Srivastava, "Detecting Backdoor Attacks on Deep Neural Networks by Activation Clustering," in *Proc. Workshops Adv. Neural Inf. Process. Syst. (NeurIPS)*, 2018.
29. K. Liu, B. Dolan-Gavitt, and S. Garg, "Fine-Pruning: Defending Against Backdooring Attacks on Deep Neural Networks," in *Proc. 21st Int. Symp. Res. Attacks, Intrusions, Def. (RAID)*, 2018, pp. 273–294.
30. A. N. Angelopoulos and S. Bates, "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification," *arXiv preprint arXiv:2107.07511*, 2021.
31. A. N. Angelopoulos, S. Bates, A. Fisch, L. Lei, and T. Schuster, "Conformal Risk Control," in *Proc. 12th Int. Conf. Learn. Represent. (ICLR)*, 2024.
32. F. Tramer, N. Carlini, W. Brendel, and A. Madry, "On Adaptive Attacks to Adversarial Example Defenses," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 1633–1645.
33. A. Athalye, N. Carlini, and D. Wagner, "Obfuscated Gradients Give a False Sense of Security: Circumventing Defenses to Adversarial Examples," in *Proc. 35th Int. Conf. Mach. Learn. (ICML)*, 2018, pp. 274–283.
34. I. J. Goodfellow, J. Shlens, and C. Szegedy, "Explaining and Harnessing Adversarial Examples," in *Proc. 3rd Int. Conf. Learn. Represent. (ICLR)*, 2015.
35. J. Hayase, W. Kong, R. Somani, and S. Oh, "SPECTRE: Defending Against Backdoor Attacks Using Robust Statistics," in *Proc. 38th Int. Conf. Mach. Learn. (ICML)*, 2021, pp. 4129–4139.
36. Y. Li, X. Lyu, N. Koren, L. Lyu, B. Li, and X. Ma, "Anti-Backdoor Learning: Training Clean Models on Poisoned Data," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 34, 2021, pp. 14900–14912.
37. K. Huang, Y. Li, B. Wu, Z. Qin, and K. Ren, "Backdoor Defense via Decoupling the Training Process," in *Proc. 10th Int. Conf. Learn. Represent. (ICLR)*, 2022.

---

## APPENDIX A: COMPLETE BENCHMARK OF ALL 54 ATTACK CONFIGURATIONS

Table XIV presents the complete performance record for all 54 frozen configurations. No underperforming attacks have been censored. 
- **Family**: $C$ = Concentrated Structural (2 features); $S$ = Spread Structural (10 features); $X$ = Cross-View Stress (24 features).
- **Rate**: Poisoning percentage relative to all 200,000 fit samples ($0.5\% = 1,000$, $1.0\% = 2,000$, $2.0\% = 4,000$).
- **Confirmed**: Met both development and confirmation eligibility criteria.

**TABLE XIV: Complete Performance Record Across All 54 Poisoning Configurations**
| Dataset | Seed | Family | Rate (%) | Confirmed | Baseline ASR (%) | Reduced Recall ($X_R$ %) | Full Recall ($X_F$ %) | Full FPR (%) |
|---|---|---|---|---|---|---|---|---|
| **2018** | 17 | C | 0.5 | No | 16.60 | 0.50 | 1.12 | 0.73 |
| **2018** | 17 | C | 1.0 | No | 29.32 | 1.45 | 3.29 | 0.63 |
| **2018** | 17 | C | 2.0 | **Yes** | 56.44 | 13.48 | 21.34 | 0.88 |
| **2018** | 17 | X | 0.5 | No | 99.61 | 0.05 | 0.00 | 0.59 |
| **2018** | 17 | X | 1.0 | No | 99.93 | 0.00 | 0.00 | 0.75 |
| **2018** | 17 | X | 2.0 | No | 99.98 | 0.01 | 0.00 | 0.63 |
| **2018** | 17 | S | 0.5 | **Yes** | 50.25 | 14.44 | 21.57 | 0.68 |
| **2018** | 17 | S | 1.0 | **Yes** | 69.45 | 41.23 | 47.23 | 0.74 |
| **2018** | 17 | S | 2.0 | **Yes** | 97.81 | 76.34 | 79.82 | 0.74 |
| **2018** | 29 | C | 0.5 | No | 20.94 | 0.45 | 0.99 | 0.81 |
| **2018** | 29 | C | 1.0 | No | 28.83 | 2.12 | 3.31 | 0.88 |
| **2018** | 29 | C | 2.0 | **Yes** | 55.33 | 11.14 | 18.79 | 0.86 |
| **2018** | 29 | X | 0.5 | No | 99.48 | 0.00 | 0.00 | 0.64 |
| **2018** | 29 | X | 1.0 | No | 99.96 | 0.00 | 0.00 | 0.74 |
| **2018** | 29 | X | 2.0 | No | 99.97 | 0.01 | 0.00 | 0.95 |
| **2018** | 29 | S | 0.5 | **Yes** | 55.12 | 18.79 | 25.44 | 0.66 |
| **2018** | 29 | S | 1.0 | **Yes** | 73.00 | 36.17 | 43.62 | 0.76 |
| **2018** | 29 | S | 2.0 | **Yes** | 99.42 | 77.62 | 79.31 | 0.75 |
| **2018** | 43 | C | 0.5 | No | 17.38 | 0.30 | 1.13 | 0.78 |
| **2018** | 43 | C | 1.0 | No | 27.91 | 1.33 | 2.37 | 0.91 |
| **2018** | 43 | C | 2.0 | **Yes** | 52.70 | 11.72 | 19.72 | 0.88 |
| **2018** | 43 | X | 0.5 | No | 99.51 | 0.07 | 0.00 | 0.69 |
| **2018** | 43 | X | 1.0 | No | 99.95 | 0.00 | 0.00 | 0.71 |
| **2018** | 43 | X | 2.0 | No | 100.00 | 0.00 | 0.00 | 0.97 |
| **2018** | 43 | S | 0.5 | **Yes** | 53.63 | 23.10 | 31.26 | 0.79 |
| **2018** | 43 | S | 1.0 | **Yes** | 66.97 | 33.72 | 48.83 | 0.94 |
| **2018** | 43 | S | 2.0 | **Yes** | 98.36 | 71.20 | 78.35 | 0.69 |
| **2024** | 17 | C | 0.5 | No | 14.67 | 7.98 | 7.34 | 0.91 |
| **2024** | 17 | C | 1.0 | No | 25.34 | 21.42 | 17.13 | 0.96 |
| **2024** | 17 | C | 2.0 | No | 48.86 | 45.94 | 54.93 | 0.85 |
| **2024** | 17 | X | 0.5 | **Yes** | 97.94 | 0.00 | 12.49 | 0.82 |
| **2024** | 17 | X | 1.0 | **Yes** | 99.87 | 0.00 | 8.38 | 0.51 |
| **2024** | 17 | X | 2.0 | **Yes** | 100.00 | 0.00 | 4.74 | 0.69 |
| **2024** | 17 | S | 0.5 | No | 31.51 | 22.26 | 24.20 | 1.29 |
| **2024** | 17 | S | 1.0 | No | 41.49 | 33.89 | 39.01 | 0.87 |
| **2024** | 17 | S | 2.0 | **Yes** | 59.39 | 48.85 | 62.79 | 0.61 |
| **2024** | 29 | C | 0.5 | No | 15.51 | 8.14 | 6.20 | 0.68 |
| **2024** | 29 | C | 1.0 | No | 23.14 | 16.27 | 13.86 | 0.82 |
| **2024** | 29 | C | 2.0 | No | 48.01 | 54.08 | 50.81 | 1.41 |
| **2024** | 29 | X | 0.5 | **Yes** | 99.42 | 0.00 | 1.10 | 0.83 |
| **2024** | 29 | X | 1.0 | **Yes** | 100.00 | 0.00 | 2.01 | 0.72 |
| **2024** | 29 | X | 2.0 | **Yes** | 100.00 | 0.00 | 0.03 | 2.27 |
| **2024** | 29 | S | 0.5 | No | 33.92 | 31.90 | 29.19 | 0.63 |
| **2024** | 29 | S | 1.0 | No | 44.26 | 47.04 | 46.41 | 0.75 |
| **2024** | 29 | S | 2.0 | **Yes** | 57.84 | 48.86 | 63.67 | 0.71 |
| **2024** | 43 | C | 0.5 | No | 11.02 | 4.79 | 3.57 | 0.82 |
| **2024** | 43 | C | 1.0 | No | 29.03 | 27.39 | 26.28 | 0.75 |
| **2024** | 43 | C | 2.0 | No | 44.70 | 43.58 | 53.33 | 1.12 |
| **2024** | 43 | X | 0.5 | **Yes** | 99.29 | 0.00 | 11.72 | 0.74 |
| **2024** | 43 | X | 1.0 | **Yes** | 99.41 | 0.01 | 6.68 | 0.76 |
| **2024** | 43 | X | 2.0 | **Yes** | 99.68 | 0.00 | 2.87 | 1.03 |
| **2024** | 43 | S | 0.5 | No | 28.54 | 25.10 | 22.67 | 0.84 |
| **2024** | 43 | S | 1.0 | No | 49.30 | 44.75 | 54.66 | 0.78 |
| **2024** | 43 | S | 2.0 | **Yes** | 53.42 | 47.27 | 52.79 | 1.16 |

---

## APPENDIX B: TECHNICAL ARTIFACT & SYSTEM IMPLEMENTATION REPORT

*Note: In accordance with reviewer feedback, engineering architecture, containerization, and demonstration software details are preserved in this technical appendix rather than within the core research narrative.*

### B.1. Demonstration Architecture and Operational Workflow
We developed a production demonstration platform featuring a Vietnamese localization interface built in Streamlit, backed by a FastAPI scoring service and an asynchronous PostgreSQL audit database. The system provides three operational views:
1. **Analysis View**: Accepts binary PE uploads (EXE, DLL, SYS) up to 50 MiB or vector JSON payloads. It presents two orthogonal outputs: the primary classification probability ($p(x)$) and the backdoor suspicion alert ($X_R > \tau$).
2. **History View**: Retains client-declared audit metadata, file SHA-256 hashes, extractor versions, and detector execution logs.
3. **Research View**: Exposes raw feature attributions, view contributions ($V_S, V_B, V_M$), and component comparator breakdowns.

### B.2. Process Isolation and Security Sandbox
To prevent hostile binary parsing vulnerabilities from compromising the host server, feature extraction executes inside a disposable child process with an enforced 60-second deadline. If an uploaded PE file triggers an unhandled memory exception or parsing loop within LIEF/pefile, the worker process is terminated immediately via OS process groups. The server returns a clean error state without crashing the host daemon.

### B.3. Database Persistence and Snapshot Restoration
The backend logs every analysis event to PostgreSQL. To verify reproducibility and database schema integrity:
- A database backup (`xsentinel_restore_20261014_1b6c8e5f1893`) was successfully restored into an isolated test instance.
- Exact canonical table row counts and SHA-256 row hashes matched the live database across 10 tables: `model_versions` (4), `roles` (3), `analysis_jobs` (116), `audit_events` (116), `alerts` (7), `analysis_results` (116), and `detector_scores` (676).
- Database migrations are version-controlled via Alembic.

### B.4. Latency and Execution Boundaries
Timing evaluations distinguish three distinct processing stages on an AMD Ryzen 7 8745H CPU (Windows, 4 inference threads):
- **Raw Classifier Inference**: Fast LightGBM forward pass averages **0.224 to 0.268 ms** per sample.
- **Core Suspicion Scoring (TreeSHAP + Rank Fusion)**: Averages **20.90 to 30.63 ms** for Reduced, and **22.18 to 32.16 ms** for Full.
- **Physical Binary Extraction**: File I/O and LIEF parsing of real PE binaries require **50 ms to 2,000 ms**, heavily dependent on file size and section complexity.

### B.5. Automated Software Verification
The software platform passed 113 automated unit and regression tests, verifying PE parsing guards, schema version matching (V2 vs. V3), rank fusion arithmetic, database transaction consistency, and process recovery.
