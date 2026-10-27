import hashlib
import json
import os
from pathlib import Path
import struct

def make_variants():
    base_dir = Path("experiments/phuc_pe_validation/fixtures")
    out_dir = base_dir / "variants"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    manifest_rows = []
    
    fixtures = [
        ("native", base_dir / "native_benign_fixture.exe", "experiments/phuc_pe_validation/fixtures/src/native_benign_fixture.c"),
        ("dotnet", base_dir / "dotnet_benign_fixture.exe", "experiments/phuc_pe_validation/fixtures/src/dotnet_benign_fixture.cs")
    ]
    
    # Target timestamps from frozen triggers:
    # EMBER2018 seed 17/29/43 concentrated/spread: 1053454528
    # EMBER2024 seed 17 concentrated/spread: 1147337216
    TS_2018 = 1053454528
    TS_2024 = 1147337216
    
    for ftype, orig_path, src_path in fixtures:
        raw = orig_path.read_bytes()
        pe_offset = struct.unpack_from('<I', raw, 0x3c)[0]
        machine, n_sec, orig_ts = struct.unpack_from('<HHI', raw, pe_offset + 4)
        
        # 1. Original
        var_id = f"{ftype}_original"
        out_path = out_dir / f"{var_id}.exe"
        out_path.write_bytes(raw)
        h = hashlib.sha256(raw).hexdigest()
        manifest_rows.append({
            "variant_id": var_id,
            "fixture_type": ftype,
            "edit_type": "none",
            "file_path": str(out_path).replace("\\", "/"),
            "file_size": len(raw),
            "sha256": h,
            "source_path": src_path,
            "pe_offset": hex(pe_offset),
            "machine": hex(machine),
            "num_sections": n_sec,
            "coff_timestamp": orig_ts,
            "description": "Unmodified original benign binary baseline"
        })
        
        # 2. Timestamp Zero
        var_id = f"{ftype}_coff_ts_zero"
        out_path = out_dir / f"{var_id}.exe"
        mod_ts_zero = raw[:pe_offset+8] + struct.pack('<I', 0) + raw[pe_offset+12:]
        out_path.write_bytes(mod_ts_zero)
        h = hashlib.sha256(mod_ts_zero).hexdigest()
        manifest_rows.append({
            "variant_id": var_id,
            "fixture_type": ftype,
            "edit_type": "coff_timestamp_zero",
            "file_path": str(out_path).replace("\\", "/"),
            "file_size": len(mod_ts_zero),
            "sha256": h,
            "source_path": src_path,
            "pe_offset": hex(pe_offset),
            "machine": hex(machine),
            "num_sections": n_sec,
            "coff_timestamp": 0,
            "description": "COFF TimeDateStamp patched to 0 (Unix Epoch 1970)"
        })
        
        # 3. Timestamp Target 2018 (1053454528)
        var_id = f"{ftype}_coff_ts_target_2018"
        out_path = out_dir / f"{var_id}.exe"
        mod_ts_18 = raw[:pe_offset+8] + struct.pack('<I', TS_2018) + raw[pe_offset+12:]
        out_path.write_bytes(mod_ts_18)
        h = hashlib.sha256(mod_ts_18).hexdigest()
        manifest_rows.append({
            "variant_id": var_id,
            "fixture_type": ftype,
            "edit_type": "coff_timestamp_target_2018",
            "file_path": str(out_path).replace("\\", "/"),
            "file_size": len(mod_ts_18),
            "sha256": h,
            "source_path": src_path,
            "pe_offset": hex(pe_offset),
            "machine": hex(machine),
            "num_sections": n_sec,
            "coff_timestamp": TS_2018,
            "description": "COFF TimeDateStamp patched to 1053454528 (EMBER2018 trigger target)"
        })
        
        # 4. Timestamp Target 2024 (1147337216)
        var_id = f"{ftype}_coff_ts_target_2024"
        out_path = out_dir / f"{var_id}.exe"
        mod_ts_24 = raw[:pe_offset+8] + struct.pack('<I', TS_2024) + raw[pe_offset+12:]
        out_path.write_bytes(mod_ts_24)
        h = hashlib.sha256(mod_ts_24).hexdigest()
        manifest_rows.append({
            "variant_id": var_id,
            "fixture_type": ftype,
            "edit_type": "coff_timestamp_target_2024",
            "file_path": str(out_path).replace("\\", "/"),
            "file_size": len(mod_ts_24),
            "sha256": h,
            "source_path": src_path,
            "pe_offset": hex(pe_offset),
            "machine": hex(machine),
            "num_sections": n_sec,
            "coff_timestamp": TS_2024,
            "description": "COFF TimeDateStamp patched to 1147337216 (EMBER2024 trigger target)"
        })
        
        # 5. Benign Overlay Pad (+256 bytes)
        var_id = f"{ftype}_benign_overlay"
        out_path = out_dir / f"{var_id}.exe"
        padding = (b"X_SENTINEL_BENIGN_OVERLAY_PADDING_RECORD_" * 6)[:256]
        mod_overlay = raw + padding
        out_path.write_bytes(mod_overlay)
        h = hashlib.sha256(mod_overlay).hexdigest()
        manifest_rows.append({
            "variant_id": var_id,
            "fixture_type": ftype,
            "edit_type": "benign_overlay",
            "file_path": str(out_path).replace("\\", "/"),
            "file_size": len(mod_overlay),
            "sha256": h,
            "source_path": src_path,
            "pe_offset": hex(pe_offset),
            "machine": hex(machine),
            "num_sections": n_sec,
            "coff_timestamp": orig_ts,
            "description": "Appended 256 bytes of benign ASCII overlay padding"
        })

    # Write manifest.csv
    import csv
    manifest_path = Path("outputs/phuc_pe_trigger_2026_10_27/manifest.csv")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(manifest_rows[0].keys())
    with open(manifest_path, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(manifest_rows)
    print(f"Generated {len(manifest_rows)} variants; manifest saved to {manifest_path}")

if __name__ == "__main__":
    make_variants()
