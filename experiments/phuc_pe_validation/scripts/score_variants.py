import csv
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, "src")
from xsentinel.schema import get_schema, V2_PRIMARY, V3_PRIMARY
from xsentinel.detection.detector import Detector
from xsentinel.detection.calibration import rank
from xsentinel.utils import sha256

def score_all():
    manifest_path = Path("outputs/phuc_pe_trigger_2026_10_27/manifest.csv")
    with open(manifest_path, "r", encoding="utf8") as f:
        variants = list(csv.DictReader(f))
        
    vec_dir = Path("outputs/phuc_pe_trigger_2026_10_27/vectors")
    
    # Target configurations to evaluate:
    # Datasets: EMBER2018 (V2), EMBER2024 (V3)
    # Seeds: 17, 29, 43
    # Families: concentrated_structural, spread_structural
    # Rate: 0.02
    # Modes: bundle_reduced, bundle_full
    
    score_rows = []
    
    configs = []
    for ds, s_code in [("EMBER2018", "V2"), ("EMBER2024", "V3")]:
        for seed in [17, 29, 43]:
            for fam in ["concentrated_structural", "spread_structural"]:
                for mode in ["bundle_reduced", "bundle_full"]:
                    b_path = Path(f"outputs/primary/{ds}/protocol_v2/seed_{seed}/{fam}/rate_0.02/{mode}")
                    if b_path.exists():
                        configs.append({
                            "dataset": ds,
                            "schema_ver": s_code,
                            "seed": seed,
                            "family": fam,
                            "mode": mode,
                            "bundle_path": b_path
                        })
                        
    print(f"Found {len(configs)} detector configurations to score.")
    
    for cfg in configs:
        ds = cfg["dataset"]
        s_code = cfg["schema_ver"]
        seed = cfg["seed"]
        fam = cfg["family"]
        mode = cfg["mode"]
        b_path = cfg["bundle_path"]
        
        # Load detector
        detector = Detector.load(b_path)
        bundle_id = f"{ds}_seed{seed}_{fam}_{mode}"
        model_hash = sha256(b_path / "main.txt")
        tau_xr = float(detector.thresholds.get("X_primary_reduced", 0.0))
        tau_xf = float(detector.thresholds.get("X_primary_full", 0.0))
        
        for v in variants:
            vid = v["variant_id"]
            vec_path = vec_dir / f"{vid}_{s_code.lower()}.npy"
            x = np.load(vec_path)
            if x.ndim == 1:
                x = x[None, :]
                
            scores, flags, details, latency = detector.predict(x)
            
            p_main = float(details["malware_probability"][0])
            malware_label = int(p_main >= 0.5)
            
            m3 = float(scores["M3_view_mass"][0])
            m4r = float(scores["M4_shap_behavioral_conflict"][0])
            
            ref_rank_m3 = float(rank(detector.rank_reference["M3_view_mass"], scores["M3_view_mass"])[0])
            ref_rank_m4r = float(rank(detector.rank_reference["M4_shap_behavioral_conflict"], scores["M4_shap_behavioral_conflict"])[0])
            
            xr = float(scores["X_primary_reduced"][0])
            alert_xr = bool(flags["X_primary_reduced"][0])
            
            # Full mode metrics if present
            m4f = float(scores.get("M4_prob_gap", [0.0])[0]) if "M4_prob_gap" in scores else ""
            xf = float(scores.get("X_primary_full", [0.0])[0]) if "X_primary_full" in scores else ""
            alert_xf = bool(flags.get("X_primary_full", [False])[0]) if "X_primary_full" in flags else ""
            
            score_rows.append({
                "case_id": f"{vid}_{s_code}_{bundle_id}",
                "variant_id": vid,
                "fixture_type": v["fixture_type"],
                "edit_type": v["edit_type"],
                "dataset": ds,
                "model_sha256": model_hash,
                "bundle_id": bundle_id,
                "mode": "reduced" if "reduced" in mode else "full",
                "seed": seed,
                "trigger_family": fam,
                "poison_rate": 0.02,
                "extractor_version": s_code,
                "file_sha256": v["sha256"],
                "p_main": round(p_main, 6),
                "malware_label_at_0_5": malware_label,
                "M3": round(m3, 6),
                "M4R": round(m4r, 6),
                "reference_rank_M3": round(ref_rank_m3, 6),
                "reference_rank_M4R": round(ref_rank_m4r, 6),
                "X_R": round(xr, 6),
                "tau_X_R": round(tau_xr, 6),
                "trigger_alert_X_R": alert_xr,
                "M4F": round(m4f, 6) if isinstance(m4f, float) else "",
                "X_F": round(xf, 6) if isinstance(xf, float) else "",
                "tau_X_F": round(tau_xf, 6) if tau_xf else "",
                "trigger_alert_X_F": alert_xf if alert_xf != "" else "",
                "scoring_status": "SCORED_FROZEN_BUNDLE"
            })
            
    out_csv = Path("outputs/phuc_pe_trigger_2026_10_27/xsentinel_scores.csv")
    fieldnames = list(score_rows[0].keys())
    with open(out_csv, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(score_rows)
        
    print(f"Scored {len(score_rows)} variant x bundle pairs; saved to {out_csv}")

if __name__ == "__main__":
    score_all()
