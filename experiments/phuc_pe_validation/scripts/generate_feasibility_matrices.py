import csv
from pathlib import Path
import sys

sys.path.insert(0, "src")
from xsentinel.schema import get_schema, V2_PRIMARY, V3_PRIMARY

def generate_matrices():
    out_dir = Path("outputs/phuc_pe_trigger_2026_10_27")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    s2 = get_schema(V2_PRIMARY)
    s3 = get_schema(V3_PRIMARY)
    
    # 1. severi_compatibility_matrix.csv
    # Detailed audit of Severi et al. (USENIX Security 2021) vs X-SENTINEL V2 & V3
    severi_rows = [
        {
            "aspect": "Paper Publication",
            "severi_upstream": "USENIX Security 2021 (arXiv:2003.01031v3)",
            "xsentinel_status": "Cited in [6]",
            "compatibility": "Compatible (historical reference)",
            "details": "Explanation-guided backdoor poisoning attack methodology"
        },
        {
            "aspect": "Public Codebase URL",
            "severi_upstream": "https://github.com/ClonedOne/MalwareBackdoors",
            "xsentinel_status": "Audited at commit 7e3ba27fdc1db25d68ae74da334cf3bdd9eedf71",
            "compatibility": "Available for inspection",
            "details": "Repo published April 2022; licensed under MIT"
        },
        {
            "aspect": "PE Binary Watermarking Tool",
            "severi_upstream": "MISSING / NOT PUBLIC in repo (only PDF watermarking via mimicus was released)",
            "xsentinel_status": "BLOCKER: No upstream PE binary transformation utility exists to reproduce",
            "compatibility": "INCOMPATIBLE / MISSING ARTIFACT",
            "details": "In attack_utils.py (lines 208-212), EMBER attack is executed via direct vector overwrite (x[idx]=val). No lief/pefile binary writer was published."
        },
        {
            "aspect": "Target Feature Dataset Schema",
            "severi_upstream": "EMBER-2017 (v1.0, 2351 features, feature_version=1)",
            "xsentinel_status": "EMBER-2018 (V2, 2381 features) and EMBER-2024 (V3, 2568 features)",
            "compatibility": "SCHEMA MISMATCH",
            "details": "Feature indices and names changed between EMBER 2017, 2018, and 2024. Severi indices cannot be mapped without re-alignment."
        },
        {
            "aspect": "Controllable / Feasible Pool Size",
            "severi_upstream": "17 non-hashed features (constants.py: 35 non-hashed minus 18 infeasible)",
            "xsentinel_status": "13 Structural features (schema.py: restricted structural pool)",
            "compatibility": "PARTIAL SUBSET",
            "details": "Severi included 4 string features (paths, urls, registry, MZ) which X-SENTINEL classifies as Metadata. X-SENTINEL restricts to 13 pure Structural columns."
        },
        {
            "aspect": "Behavior Preservation Verification",
            "severi_upstream": "Described in paper section 6.1 (dynamic Cuckoo sandbox run on malware)",
            "xsentinel_status": "Self-authored benign deterministic PE fixtures with automated 4-case I/O checks",
            "compatibility": "DIFFERENT METHODOLOGY",
            "details": "Severi ran opaque malware in sandbox; X-SENTINEL strictly enforces safe, deterministic, self-built benign PE execution."
        },
        {
            "aspect": "Side Effect Accounting",
            "severi_upstream": "Not measured across the entire 2351 vector in public code",
            "xsentinel_status": "Exhaustive full-vector diff (all 2381/2568 dimensions) before vs after binary edit",
            "compatibility": "X-SENTINEL MORE RIGOROUS",
            "details": "X-SENTINEL captures all unintended feature drifts in Metadata and Behavioral views caused by binary header/overlay edits."
        }
    ]
    
    with open(out_dir / "severi_compatibility_matrix.csv", "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(severi_rows[0].keys()))
        w.writeheader()
        w.writerows(severi_rows)
        
    # 2. trigger_feasibility_matrix.csv
    # Feature-by-feature feasibility audit for all 17 Severi features across V2 and V3
    features_audit = [
        {
            "feature_canonical": "header.coff.timestamp",
            "v2_idx": 626, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 696, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "PE COFF Header at pe_offset + 8 (4 bytes uint32)",
            "byte_edit_feasibility": "FEASIBLE",
            "expected_side_effects": "Modifies 4 bytes in file, causing drift in ByteHistogram (10-15 buckets), ByteEntropyHistogram, and StringExtractor.",
            "full_trigger_realizability": "PARTIAL (Matches timestamp coordinate, but fails 2-/10-feature triggers; causes 10-16 unintended drifts)",
            "status": "feasible_single_edit_with_drift"
        },
        {
            "feature_canonical": "general.size",
            "v2_idx": 616, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 0, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "Total file size in bytes (EOF offset)",
            "byte_edit_feasibility": "PARTIALLY FEASIBLE (Padding only; Truncation impossible without destroying code)",
            "expected_side_effects": "Appending overlay causes massive drift in ByteHistogram (230-350 features), ByteEntropy, overlay_size, and strings.",
            "full_trigger_realizability": "IMPOSSIBLE for small targets (e.g. 2495 bytes); SEVERELY DISRUPTIVE for large targets (80MB)",
            "status": "infeasible_as_exact_trigger"
        },
        {
            "feature_canonical": "header.optional.major_image_version",
            "v2_idx": 677, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 703, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "Optional Header MajorImageVersion (2 bytes)",
            "byte_edit_feasibility": "FEASIBLE",
            "expected_side_effects": "Alters ByteHistogram and ByteEntropyHistogram; may trigger loader heuristic warnings if out of range.",
            "full_trigger_realizability": "UNCERTAIN as part of multi-feature trigger; side effects cannot be isolated.",
            "status": "uncertain"
        },
        {
            "feature_canonical": "header.optional.minor_image_version",
            "v2_idx": 678, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 704, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "Optional Header MinorImageVersion (2 bytes)",
            "byte_edit_feasibility": "FEASIBLE",
            "expected_side_effects": "Alters ByteHistogram and ByteEntropyHistogram.",
            "full_trigger_realizability": "UNCERTAIN as part of multi-feature trigger; side effects cannot be isolated.",
            "status": "uncertain"
        },
        {
            "feature_canonical": "header.optional.major_linker_version",
            "v2_idx": 679, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 705, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "Optional Header MajorLinkerVersion (1 byte)",
            "byte_edit_feasibility": "FEASIBLE",
            "expected_side_effects": "Alters ByteHistogram and ByteEntropyHistogram. Arbitrary target values (e.g. 75) represent non-existent compilers.",
            "full_trigger_realizability": "UNCERTAIN; anomaly flag in some AV scanners.",
            "status": "uncertain"
        },
        {
            "feature_canonical": "header.optional.minor_linker_version",
            "v2_idx": 680, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 706, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "Optional Header MinorLinkerVersion (1 byte)",
            "byte_edit_feasibility": "FEASIBLE",
            "expected_side_effects": "Alters ByteHistogram and ByteEntropyHistogram.",
            "full_trigger_realizability": "UNCERTAIN.",
            "status": "uncertain"
        },
        {
            "feature_canonical": "header.optional.major_operating_system_version",
            "v2_idx": 681, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 707, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "Optional Header MajorOperatingSystemVersion (2 bytes)",
            "byte_edit_feasibility": "FEASIBLE",
            "expected_side_effects": "Alters ByteHistogram and ByteEntropyHistogram. Invalid OS versions can cause loader refusal.",
            "full_trigger_realizability": "UNCERTAIN.",
            "status": "uncertain"
        },
        {
            "feature_canonical": "header.optional.minor_operating_system_version",
            "v2_idx": 682, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 708, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "Optional Header MinorOperatingSystemVersion (2 bytes)",
            "byte_edit_feasibility": "FEASIBLE",
            "expected_side_effects": "Alters ByteHistogram and ByteEntropyHistogram.",
            "full_trigger_realizability": "UNCERTAIN.",
            "status": "uncertain"
        },
        {
            "feature_canonical": "header.optional.minor_subsystem_version",
            "v2_idx": 684, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 710, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "Optional Header MinorSubsystemVersion (2 bytes)",
            "byte_edit_feasibility": "FEASIBLE",
            "expected_side_effects": "Alters ByteHistogram and ByteEntropyHistogram.",
            "full_trigger_realizability": "UNCERTAIN.",
            "status": "uncertain"
        },
        {
            "feature_canonical": "section.num_read_and_execute_sections",
            "v2_idx": 691, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 773, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "PE Section Table headers (MEM_EXECUTE | MEM_READ flags)",
            "byte_edit_feasibility": "HIGHLY CONSTRAINED / PRACTICALLY INFEASIBLE",
            "expected_side_effects": "Target value 12 or 20 requires adding/splitting 12-20 sections! Drastically alters section table size, file alignments, section hashes (entropy_hash, size_hash, characteristics_hash), and byte distributions.",
            "full_trigger_realizability": "IMPOSSIBLE without massive collateral feature corruption.",
            "status": "impossible_isolated_edit"
        },
        {
            "feature_canonical": "section.num_write_sections",
            "v2_idx": 692, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 774, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "PE Section Table headers (MEM_WRITE flags)",
            "byte_edit_feasibility": "HIGHLY CONSTRAINED / PRACTICALLY INFEASIBLE",
            "expected_side_effects": "Target value 13 requires multiple writable sections; corrupts section counts and hashes.",
            "full_trigger_realizability": "IMPOSSIBLE without massive collateral feature corruption.",
            "status": "impossible_isolated_edit"
        },
        {
            "feature_canonical": "section.num_zero_size_sections",
            "v2_idx": 689, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 771, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "PE Section Table headers (VirtualSize / SizeOfRawData == 0)",
            "byte_edit_feasibility": "HIGHLY CONSTRAINED",
            "expected_side_effects": "Target value 82.0 zero-size sections exceeds standard PE limits and triggers severe malformation flags.",
            "full_trigger_realizability": "IMPOSSIBLE without breaking PE structural integrity.",
            "status": "impossible_isolated_edit"
        },
        {
            "feature_canonical": "section.num_unnamed_sections",
            "v2_idx": 690, "v2_view": "structural", "v2_in_pool": True,
            "v3_idx": 772, "v3_view": "structural", "v3_in_pool": True,
            "physical_location": "PE Section Table headers (Name field empty / null)",
            "byte_edit_feasibility": "FEASIBLE for individual section",
            "expected_side_effects": "Alters section name hashes and characteristics.",
            "full_trigger_realizability": "UNCERTAIN.",
            "status": "uncertain"
        },
        {
            "feature_canonical": "strings.paths",
            "v2_idx": 612, "v2_view": "metadata", "v2_in_pool": True,
            "v3_idx": "N/A", "v3_view": "metadata", "v3_in_pool": False,
            "physical_location": "Embedded printable strings matching path regex",
            "byte_edit_feasibility": "FEASIBLE (via string appending)",
            "expected_side_effects": "Drastically alters StringExtractor (numstrings, avlength, printables, string_entropy) and ByteHistogram.",
            "full_trigger_realizability": "DISQUALIFIED from Structural pool in V3; causes extensive Metadata drift in V2.",
            "status": "metadata_only_excluded_from_structural"
        },
        {
            "feature_canonical": "strings.urls",
            "v2_idx": 613, "v2_view": "metadata", "v2_in_pool": True,
            "v3_idx": "N/A", "v3_view": "metadata", "v3_in_pool": False,
            "physical_location": "Embedded printable strings matching URL regex",
            "byte_edit_feasibility": "FEASIBLE (via string appending)",
            "expected_side_effects": "Drastically alters StringExtractor and ByteHistogram.",
            "full_trigger_realizability": "DISQUALIFIED from Structural pool in V3; causes extensive Metadata drift in V2.",
            "status": "metadata_only_excluded_from_structural"
        },
        {
            "feature_canonical": "strings.registry",
            "v2_idx": 614, "v2_view": "metadata", "v2_in_pool": True,
            "v3_idx": "N/A", "v3_view": "metadata", "v3_in_pool": False,
            "physical_location": "Embedded printable strings matching Registry key regex",
            "byte_edit_feasibility": "FEASIBLE (via string appending)",
            "expected_side_effects": "Drastically alters StringExtractor and ByteHistogram.",
            "full_trigger_realizability": "DISQUALIFIED from Structural pool in V3; causes extensive Metadata drift in V2.",
            "status": "metadata_only_excluded_from_structural"
        },
        {
            "feature_canonical": "strings.MZ",
            "v2_idx": 615, "v2_view": "metadata", "v2_in_pool": True,
            "v3_idx": "N/A", "v3_view": "metadata", "v3_in_pool": False,
            "physical_location": "Occurrences of 'MZ' ASCII pattern",
            "byte_edit_feasibility": "FEASIBLE (via byte embedding)",
            "expected_side_effects": "Alters ByteHistogram and StringExtractor.",
            "full_trigger_realizability": "DISQUALIFIED from Structural pool in V3; causes extensive Metadata drift in V2.",
            "status": "metadata_only_excluded_from_structural"
        }
    ]
    
    with open(out_dir / "trigger_feasibility_matrix.csv", "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(features_audit[0].keys()))
        w.writeheader()
        w.writerows(features_audit)
        
    print(f"Generated severi_compatibility_matrix.csv and trigger_feasibility_matrix.csv in {out_dir}")

if __name__ == "__main__":
    generate_matrices()
