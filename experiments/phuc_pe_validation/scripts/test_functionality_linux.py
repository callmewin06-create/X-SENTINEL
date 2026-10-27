import csv
import os
from pathlib import Path
import subprocess
import sys

def run_test_cases():
    manifest_path = Path("outputs/phuc_pe_trigger_2026_10_27/manifest.csv")
    if not manifest_path.exists():
        raise FileNotFoundError("manifest.csv not found")
        
    with open(manifest_path, "r", encoding="utf8") as f:
        variants = list(csv.DictReader(f))
        
    test_cases = [
        {"case_id": "TC1_no_args", "args": [], "expected_exit": 0, "expected_stdout": "X_SENTINEL_BENIGN_FIXTURE:7"},
        {"case_id": "TC2_pos_5", "args": ["5"], "expected_exit": 0, "expected_stdout": "X_SENTINEL_BENIGN_FIXTURE:32"},
        {"case_id": "TC3_neg_3", "args": ["-3"], "expected_exit": 0, "expected_stdout": "X_SENTINEL_BENIGN_FIXTURE:16"},
        {"case_id": "TC4_invalid_abc", "args": ["abc"], "expected_exit": 2, "expected_stdout": ""}
    ]
    
    results = []
    
    for v in variants:
        v_id = v["variant_id"]
        bin_path = Path(v["file_path"])
        ftype = v["fixture_type"]
        
        for tc in test_cases:
            if ftype == "native":
                cmd = ["wine", str(bin_path.resolve())] + tc["args"]
                env = os.environ.copy()
                env["WINEDEBUG"] = "-all"
                try:
                    proc = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        env=env,
                        timeout=5
                    )
                    stdout = proc.stdout.strip()
                    stderr = proc.stderr.strip()
                    exit_code = proc.returncode
                    
                    exit_ok = (exit_code == tc["expected_exit"])
                    if tc["expected_exit"] == 0:
                        stdout_ok = (tc["expected_stdout"] in stdout)
                    else:
                        stdout_ok = True
                    status = "PASS" if (exit_ok and stdout_ok) else "FAIL"
                except Exception as e:
                    stdout = ""
                    stderr = str(e)
                    exit_code = -1
                    status = "ERROR"
                results.append({
                    "variant_id": v_id,
                    "fixture_type": ftype,
                    "edit_type": v["edit_type"],
                    "file_sha256": v["sha256"],
                    "test_case": tc["case_id"],
                    "input_args": " ".join(tc["args"]) if tc["args"] else "(none)",
                    "expected_exit": tc["expected_exit"],
                    "actual_exit": exit_code,
                    "expected_stdout": tc["expected_stdout"],
                    "actual_stdout": stdout,
                    "actual_stderr": stderr[:200],
                    "status": status,
                    "environment": "Kali_Wine_x86_64"
                })
            else:
                # Dotnet on Linux without mono
                results.append({
                    "variant_id": v_id,
                    "fixture_type": ftype,
                    "edit_type": v["edit_type"],
                    "file_sha256": v["sha256"],
                    "test_case": tc["case_id"],
                    "input_args": " ".join(tc["args"]) if tc["args"] else "(none)",
                    "expected_exit": tc["expected_exit"],
                    "actual_exit": "N/A",
                    "expected_stdout": tc["expected_stdout"],
                    "actual_stdout": "",
                    "actual_stderr": "FUNCTIONALITY NOT VERIFIED on Linux (Mono not installed; verified on Windows host)",
                    "status": "NOT_RUN_LINUX",
                    "environment": "Kali_Linux_Host"
                })
            
    out_csv = Path("outputs/phuc_pe_trigger_2026_10_27/functionality_results_linux.csv")
    fieldnames = list(results[0].keys())
    with open(out_csv, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(results)
        
    print(f"Executed Linux test cases. Total rows: {len(results)}")
    native_passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"Native in Wine passed: {native_passed}/20")

if __name__ == "__main__":
    run_test_cases()
