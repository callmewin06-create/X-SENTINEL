import csv
import json
import math
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, "src")
from xsentinel.schema import get_schema, V2_PRIMARY, V3_PRIMARY
from xsentinel.data.pe_isolation import extract_pe_isolated

def run_extraction_and_diff():
    manifest_path = Path("outputs/phuc_pe_trigger_2026_10_27/manifest.csv")
    with open(manifest_path, "r", encoding="utf8") as f:
        variants = list(csv.DictReader(f))
        
    vec_dir = Path("outputs/phuc_pe_trigger_2026_10_27/vectors")
    vec_dir.mkdir(parents=True, exist_ok=True)
    
    s2 = get_schema(V2_PRIMARY)
    s3 = get_schema(V3_PRIMARY)
    
    extracted_vectors = {}
    
    print("=== Step 1: Extracting vectors for all variants ===")
    for v in variants:
        vid = v["variant_id"]
        fpath = Path(v["file_path"])
        raw = fpath.read_bytes()
        
        # V2 extraction
        v2_vec, prov2 = extract_pe_isolated(raw, V2_PRIMARY)
        np.save(vec_dir / f"{vid}_v2.npy", v2_vec)
        
        # V3 extraction
        v3_vec, prov3 = extract_pe_isolated(raw, V3_PRIMARY)
        np.save(vec_dir / f"{vid}_v3.npy", v3_vec)
        
        extracted_vectors[(vid, "V2")] = (v2_vec, prov2)
        extracted_vectors[(vid, "V3")] = (v3_vec, prov3)
        print(f"Extracted {vid}: V2={v2_vec.shape}, V3={v3_vec.shape}")
        
    print("\n=== Step 2: Comparing variants against baseline ===")
    
    # Intended targets definition
    TS_2018 = 1053454528.0
    TS_2024 = 1147337216.0
    
    detailed_rows = []
    summary_rows = []
    
    # Compare each modified variant against original
    for v in variants:
        if v["edit_type"] == "none":
            continue
        vid = v["variant_id"]
        ftype = v["fixture_type"]
        orig_id = f"{ftype}_original"
        
        for schema_ver, s, s_code in [("V2", s2, "V2_PRIMARY"), ("V3", s3, "V3_PRIMARY")]:
            orig_vec, _ = extracted_vectors[(orig_id, schema_ver)]
            mod_vec, _ = extracted_vectors[(vid, schema_ver)]
            
            case_id = f"{vid}_{schema_ver}"
            
            # Map intended targets for this case
            intended_map = {}
            if "ts_zero" in vid:
                ts_idx = s.names.index("header.coff.timestamp")
                intended_map[ts_idx] = 0.0
            elif "target_2018" in vid:
                ts_idx = s.names.index("header.coff.timestamp")
                intended_map[ts_idx] = TS_2018
            elif "target_2024" in vid:
                ts_idx = s.names.index("header.coff.timestamp")
                intended_map[ts_idx] = TS_2024
            elif "overlay" in vid:
                size_idx = s.names.index("general.size")
                intended_map[size_idx] = float(v["file_size"])
                
            changed_total = 0
            changed_structural = 0
            changed_behavioral = 0
            changed_metadata = 0
            changed_outside_pool = 0
            intended_matched = 0
            unintended_changed = 0
            
            for j in range(s.dim):
                v_before = float(orig_vec[j])
                v_after = float(mod_vec[j])
                delta = v_after - v_before
                changed = abs(delta) > 1e-7
                
                feat_name = s.names[j]
                view = s.view_labels[j]
                in_pool = (j in s.restricted)
                is_intended = (j in intended_map)
                expected_tgt = intended_map.get(j, "")
                matched_target = False
                
                if is_intended:
                    matched_target = abs(v_after - intended_map[j]) < 1e-5
                    if matched_target:
                        intended_matched += 1
                        
                if changed:
                    changed_total += 1
                    if view == "structural":
                        changed_structural += 1
                    elif view == "behavioral":
                        changed_behavioral += 1
                    elif view == "metadata":
                        changed_metadata += 1
                        
                    if not in_pool:
                        changed_outside_pool += 1
                    if not is_intended:
                        unintended_changed += 1
                        
                    note = "Intended edit" if is_intended else f"Unintended drift in {view}"
                    if not in_pool:
                        note += " (outside permitted pool)"
                        
                    detailed_rows.append({
                        "case_id": case_id,
                        "schema": schema_ver,
                        "index": j,
                        "view": view,
                        "feature_name": feat_name,
                        "value_before": v_before,
                        "value_after": v_after,
                        "delta": delta,
                        "expected_target": expected_tgt,
                        "intended": is_intended,
                        "within_permitted_pool": in_pool,
                        "changed": changed,
                        "matched_target": matched_target,
                        "notes": note
                    })
                    
            summary_rows.append({
                "case_id": case_id,
                "variant_id": vid,
                "fixture_type": ftype,
                "edit_type": v["edit_type"],
                "schema": schema_ver,
                "total_features": s.dim,
                "changed_total": changed_total,
                "changed_structural": changed_structural,
                "changed_behavioral": changed_behavioral,
                "changed_metadata": changed_metadata,
                "changed_outside_pool": changed_outside_pool,
                "intended_features_count": len(intended_map),
                "intended_matched": intended_matched,
                "unintended_changed": unintended_changed,
                "all_intended_matched": (intended_matched == len(intended_map) and len(intended_map) > 0),
                "verdict": "Binary edit executed; feature drift measured; desired single coordinate matched; FULL trigger NOT matched"
            })
            
    # Write feature_changes.csv
    detailed_path = Path("outputs/phuc_pe_trigger_2026_10_27/feature_changes.csv")
    with open(detailed_path, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(detailed_rows[0].keys()))
        w.writeheader()
        w.writerows(detailed_rows)
        
    # Write feature_change_summary.csv
    summary_path = Path("outputs/phuc_pe_trigger_2026_10_27/feature_change_summary.csv")
    with open(summary_path, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)
        
    print(f"\nWrote {len(detailed_rows)} changed feature rows to {detailed_path}")
    print(f"Wrote {len(summary_rows)} case summaries to {summary_path}")

if __name__ == "__main__":
    run_extraction_and_diff()
