# Manuscript Paragraph & Integration Guide for Quan (Section V / Limitations)

**Author**: Pham Nguyen Hoang Phuc (PhucPNHSE203815)  
**Target Recipient**: Dang Ly Quan (Lead Paper Editor)  
**Purpose**: Ready-to-insert English scientific text addressing Reviewer Comment 1.3 (PE Problem-Space Realizability).

---

## 1. Suggested Abstract Addition (1–2 Sentences)
> "All poisoning triggers and evasion assessments in this study are evaluated as vector perturbations within the feature space; an empirical audit demonstrates that isolated PE binary header and overlay modifications do not realize the multi-coordinate poisoning triggers without inducing substantial collateral feature drift."

---

## 2. Core Manuscript Paragraph (Word Count: ~280 words)

### Suggested Section: Section V-H (*Benign Executable Validation and Trigger Feasibility*)

> **Empirical Validation of Physical PE Binary Modifications and Trigger Realizability.**  
> To assess whether feature-space backdoor triggers map to realizable executable files, we developed two deterministic, self-contained benign programs (a 64-bit native C console binary cross-compiled via `x86_64-w64-mingw32-gcc` and a managed .NET C# executable) evaluating the arithmetic function $f(n) = n^2 + 7$. We subjected each binary to controlled file-level transformations: substituting the COFF `TimeDateStamp` with epoch zero and the exact frozen trigger values from EMBER2018 ($1,053,454,528$) and EMBER2024 ($1,147,337,216$), as well as appending 256 bytes of benign overlay padding. Re-extracting feature vectors across all 2,381 dimensions in V2 and 2,568 dimensions in V3 revealed that while timestamp patching precisely matched the intended header coordinate, it inevitably triggered 11 to 16 unintended feature alterations within the Metadata view (principally in byte and byte-entropy histograms). Appending overlay padding altered between 232 and 353 features across views. Furthermore, synthesizing the concentrated trigger’s second coordinate (forcing 12 or 20 read-and-execute sections) or spread trigger combinations proved physically unachievable without dismantling section table alignment and corrupting header hashing. In functional testing, native variants preserved exact stdout and exit codes across four test cases under native Windows and Linux Wine; .NET variants bearing historic timestamps triggered Windows Application Control policy blocks (`WinError 4551`). Scoring all binary variants against 24 frozen primary detector bundles produced zero suspicion alerts (0 / 240 evaluations; $X_R \le \tau_{XR}$). We did not establish a realizable instance of the original poisoning trigger in a functioning PE binary. These findings demonstrate that our reported backdoor detection evaluations characterize feature-space attribution concentration rather than verified physical PE transformations.

---

## 3. Recommended Table to Accompany Paragraph

### Proposed Table Title: 
**TABLE XVI (REVISED): Full-Vector Feature Shifts Following Controlled Binary Edits to Benign PE Fixtures**

| Fixture Type | Target Edit | Schema | Cases Checked | Intended Coordinate Matched | Changed Total | Structural Changed | Behavioral Changed | Metadata Changed | Unintended Shifts |
|---|---|---|---|---|---|---|---|---|---|
| Native C (Win64) | COFF Timestamp 0 | V2 (2381) | 4 / 4 | Yes (1/1) | 11 | 1 | 0 | 10 | 10 |
| Native C (Win64) | COFF Timestamp 0 | V3 (2568) | 4 / 4 | Yes (1/1) | 12 | 1 | 0 | 11 | 11 |
| Native C (Win64) | COFF Timestamp Target | V2 (2381) | 4 / 4 | Yes (1/1) | 12 | 1 | 0 | 11 | 11 |
| Native C (Win64) | COFF Timestamp Target | V3 (2568) | 4 / 4 | Yes (1/1) | 13 | 1 | 0 | 12 | 12 |
| Native C (Win64) | Benign Overlay (+256B) | V2 (2381) | 4 / 4 | Yes (1/1) | 348 | 1 | 0 | 347 | 347 |
| Native C (Win64) | Benign Overlay (+256B) | V3 (2568) | 4 / 4 | Yes (1/1) | 353 | 5 | 0 | 348 | 352 |
| .NET C# | COFF Timestamp 0 | V2 (2381) | 4 / 4 | Yes (1/1) | 11 | 1 | 0 | 10 | 10 |
| .NET C# | COFF Timestamp 0 | V3 (2568) | 4 / 4 | Yes (1/1) | 12 | 1 | 0 | 11 | 11 |
| .NET C# | COFF Timestamp Target | V2 (2381) | 4 / 4 | Yes (1/1) | 14 | 1 | 0 | 13 | 13 |
| .NET C# | COFF Timestamp Target | V3 (2568) | 4 / 4 | Yes (1/1) | 15 | 1 | 0 | 14 | 14 |
| .NET C# | Benign Overlay (+256B) | V2 (2381) | 4 / 4 | Yes (1/1) | 232 | 1 | 0 | 231 | 231 |
| .NET C# | Benign Overlay (+256B) | V3 (2568) | 4 / 4 | Yes (1/1) | 238 | 6 | 0 | 232 | 237 |

*Note: Functional execution of Native C was verified across four test cases under Windows and Linux Wine; .NET historic timestamps were intercepted by Windows Application Control policies. Scored under frozen X-SENTINEL detector bundles (seeds 17, 29, 43; rate 0.02), yielding 0 alerts across 240 evaluations.*

---

## 4. Suggested Revision for Section VI (*Limitations*)

> *"A critical limitation is that our backdoor triggers were trained, injected, and evaluated directly in vector space. As shown in Section V-H, translating even a 2-feature concentrated trigger into executable PE bytes fails because modifying binary headers inevitably produces collateral drift in byte histogram features, while modifying section counts to match high target integers dismantles valid PE structure. Consequently, our findings establish detection characteristics for feature-space backdoor concentration, but leave the realizability of problem-space malware backdoors as an open challenge."*
