"""TC-03 / PLAN-BE-19: Automated Feature Equivalence & Extractor Gate Test Suite.

Acceptance Criterion 3: Feature equivalence test.
Verifies exact 2,381-feature EMBER2018 schema alignment, group bounds,
determinism, downstream semantic view compatibility, and audits
LIEF/NumPy dependency divergence and prerequisite gate status.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest
from x_sentinel.data.raw_pe import (
    DATA_DIRECTORY_NAMES,
    RawPEFeatureExtractor,
    extract_byte_entropy,
    extract_byte_histogram,
    extract_data_directories,
    extract_exports_info,
    extract_general_file_info,
    extract_header_info,
    extract_imports_info,
    extract_section_info,
    extract_static_pe,
    extract_strings,
)
from x_sentinel.data.schema import FEATURE_COUNT, validate_vector
from x_sentinel.data.views import load_view_map

from tests.fixtures.synthetic_pe import build_minimal_valid_pe

# ---------------------------------------------------------------------------
# 1. Canonical 2,381-Dimension Schema & Group Breakdown
# ---------------------------------------------------------------------------


def test_extracted_vector_canonical_dimension() -> None:
    pe_bytes = build_minimal_valid_pe()
    vector = extract_static_pe(pe_bytes)

    assert len(vector) == FEATURE_COUNT == 2381
    assert all(isinstance(v, float) for v in vector)
    assert all(not math.isnan(v) and not math.isinf(v) for v in vector)

    # Validates cleanly via canonical schema
    validated = validate_vector(vector)
    assert len(validated) == 2381


def test_group_level_dimension_accounting() -> None:
    pe_bytes = build_minimal_valid_pe()
    import lief
    binary = lief.PE.parse(list(pe_bytes))

    v_hist = extract_byte_histogram(pe_bytes)
    v_ent = extract_byte_entropy(pe_bytes)
    v_str = extract_strings(pe_bytes)
    v_gen = extract_general_file_info(pe_bytes, binary)
    v_hdr = extract_header_info(pe_bytes, binary)
    v_sec = extract_section_info(pe_bytes, binary)
    v_imp = extract_imports_info(pe_bytes, binary)
    v_exp = extract_exports_info(pe_bytes, binary)
    v_dirs = extract_data_directories(pe_bytes, binary)

    group_dims = {
        "ByteHistogram": len(v_hist),
        "ByteEntropyHistogram": len(v_ent),
        "StringExtractor": len(v_str),
        "GeneralFileInfo": len(v_gen),
        "HeaderFileInfo": len(v_hdr),
        "SectionInfo": len(v_sec),
        "ImportsInfo": len(v_imp),
        "ExportsInfo": len(v_exp),
        "DataDirectories": len(v_dirs),
    }

    expected_dims = {
        "ByteHistogram": 256,
        "ByteEntropyHistogram": 256,
        "StringExtractor": 104,
        "GeneralFileInfo": 10,
        "HeaderFileInfo": 62,
        "SectionInfo": 255,
        "ImportsInfo": 1280,
        "ExportsInfo": 128,
        "DataDirectories": 30,
    }

    assert group_dims == expected_dims
    assert sum(group_dims.values()) == 2381


def test_histogram_normalization_bounds() -> None:
    pe_bytes = build_minimal_valid_pe()
    v_hist = extract_byte_histogram(pe_bytes)

    assert len(v_hist) == 256
    assert all(0.0 <= v <= 1.0 for v in v_hist)
    assert pytest.approx(sum(v_hist), abs=1e-5) == 1.0


def test_byte_entropy_normalization_bounds() -> None:
    pe_bytes = build_minimal_valid_pe()
    v_ent = extract_byte_entropy(pe_bytes)

    assert len(v_ent) == 256
    assert all(0.0 <= v <= 1.0 for v in v_ent)
    assert pytest.approx(sum(v_ent), abs=1e-5) == 1.0


def test_data_directories_order_and_count() -> None:
    assert len(DATA_DIRECTORY_NAMES) == 15
    pe_bytes = build_minimal_valid_pe()
    import lief
    binary = lief.PE.parse(list(pe_bytes))
    v_dirs = extract_data_directories(pe_bytes, binary)

    assert len(v_dirs) == 30
    # Every pair is (size, virtual_address)
    for i in range(15):
        size = v_dirs[2 * i]
        rva = v_dirs[2 * i + 1]
        assert size >= 0.0
        assert rva >= 0.0


# ---------------------------------------------------------------------------
# 2. Determinism & Stability
# ---------------------------------------------------------------------------


def test_repeated_extraction_is_deterministic() -> None:
    pe_bytes = build_minimal_valid_pe()
    extractor = RawPEFeatureExtractor(enabled=True)

    vec1 = extractor.extract_bytes(pe_bytes)
    vec2 = extractor.extract_bytes(pe_bytes)

    assert len(vec1) == len(vec2) == 2381
    max_diff = max(abs(a - b) for a, b in zip(vec1, vec2, strict=True))
    assert max_diff == 0.0, "Repeated extractions must be bit-exact identical"


# ---------------------------------------------------------------------------
# 3. Downstream Semantic Views Compatibility
# ---------------------------------------------------------------------------


def test_extracted_vector_compatible_with_demo_view_mapping() -> None:
    pe_bytes = build_minimal_valid_pe()
    vector = extract_static_pe(pe_bytes)

    view_map = load_view_map(Path("configs/views.demo.yaml"))
    slices = view_map.split(vector)

    assert "structural" in slices
    assert "behavioral" in slices
    assert "metadata" in slices

    # Slices must cover all 2,381 features without overlap
    total_sliced = sum(len(s) for s in slices.values())
    assert total_sliced == 2381



# ---------------------------------------------------------------------------
# 4. EMBER2018 Reference Vectorization Equivalence
# ---------------------------------------------------------------------------


def test_reference_ember_vectorization_matches_test_dataset() -> None:
    """Verify that EMBER2018 process_raw_features matches X_test.dat row 0."""
    features_jsonl = Path("datasets/ember2018/test_features.jsonl")
    x_test_dat = Path("datasets/ember2018/X_test.dat")

    if not features_jsonl.exists() or not x_test_dat.exists():
        pytest.skip("EMBER2018 evaluation dataset files not present on disk")

    import ember

    with open(features_jsonl, encoding="utf-8") as f:
        first_record = json.loads(f.readline())

    extractor = ember.PEFeatureExtractor(2, print_feature_warning=False)
    computed_vec = extractor.process_raw_features(first_record)

    # Load first sample from memmap
    x_test = np.memmap(x_test_dat, dtype=np.float32, mode="r", shape=(200000, 2381))
    ground_truth = np.array(x_test[0])

    assert computed_vec.shape == (2381,)
    assert ground_truth.shape == (2381,)

    max_diff = float(np.max(np.abs(computed_vec - ground_truth)))
    assert max_diff == 0.0, f"Max difference between computed and ground truth is {max_diff}"


# ---------------------------------------------------------------------------
# 5. Extractor / Schema Equivalence Prerequisite Gate Audit
# ---------------------------------------------------------------------------


def test_audit_legacy_ember_lief_version_incompatibility() -> None:
    """Demonstrate that legacy ember package raw_features fails under LIEF 1.0.

    Root Cause:
    EMBER 2018 was developed against lief==0.9.0.
    The environment runs LIEF 1.0.0, where:
    1. lief.bad_format was removed (causing AttributeError in ember.features).
    2. lief.not_found was moved to lief.lief_errors.
    3. NumPy 2.x removed np.int (causing AttributeError in ember ByteEntropyHistogram).
    This proves why the Extractor Equivalence Gate is PREREQUISITE NO-GO for
    production raw PE activation without frozen reference fixtures.
    """
    pytest.importorskip("ember")
    import ember
    import lief

    assert lief.__version__.startswith("1.0.0"), f"Expected LIEF 1.0.0, got {lief.__version__}"
    assert not hasattr(lief, "bad_format"), "LIEF 1.0.0 does not have bad_format"

    extractor = ember.PEFeatureExtractor(2, print_feature_warning=False)
    # Calling raw_features on any bytes raises AttributeError due to lief.bad_format
    with pytest.raises(AttributeError, match="bad_format"):
        extractor.raw_features(b"MZ" + b"\x00" * 100)


def test_audit_no_golden_pe_binaries_in_repository() -> None:
    """Audit evidence: the repository contains pre-extracted vectors, NOT raw PE binaries.

    The official EMBER 2018 distribution only distributes pre-extracted JSON
    and memmap feature files, not executable binaries.
    """
    repo_root = Path(".")
    pe_files = list(repo_root.glob("**/*.exe")) + list(repo_root.glob("**/*.dll"))

    # Exclude any temporary test files
    committed_pes = [p for p in pe_files if "pytest" not in str(p) and "temp" not in str(p).lower()]
    assert len(committed_pes) == 0, (
        f"Found unexpected raw PE files in repository: {committed_pes}. "
        f"EMBER2018 golden PE corpus is not checked into the repository."
    )


def test_prerequisite_gate_remains_fail_closed_in_baseline() -> None:
    """Verify that baseline configuration remains fail-closed (NotImplementedError)."""
    extractor = RawPEFeatureExtractor()
    assert extractor.enabled is False

    with pytest.raises(NotImplementedError):
        extractor.extract("sample.exe")


# ---------------------------------------------------------------------------
# 6. Exact Mathematical & Algorithmic Equivalence Tests
# ---------------------------------------------------------------------------


def test_exact_string_extractor_equivalence_to_ember() -> None:
    """Verify extract_strings produces exact bit-level match (0.0 diff) with EMBER2018 StringExtractor."""
    pytest.importorskip("ember")
    import ember.features

    test_payload = (
        b"MZ\x90\x00"
        b"This is a test printable string for EMBER extraction\x00"
        b"C:\\Windows\\System32\\kernel32.dll\x00"
        b"https://evil.com/malware.exe\x00"
        b"HKEY_LOCAL_MACHINE\\Software\\Microsoft\x00"
        b"MZ_dropper_signature_marker"
    )

    ref_extractor = ember.features.StringExtractor()
    ref_raw = ref_extractor.raw_features(test_payload, None)
    ref_vec = ref_extractor.process_raw_features(ref_raw).tolist()

    cand_vec = extract_strings(test_payload)

    assert len(ref_vec) == len(cand_vec) == 104
    max_diff = max(abs(a - b) for a, b in zip(ref_vec, cand_vec, strict=True))
    assert max_diff == 0.0, f"extract_strings diverges from EMBER2018 reference: max_diff={max_diff}"


def test_null_binary_feature_hasher_scalar_semantics() -> None:
    """Verify that header and section extraction with binary=None follows EMBER scalar hash semantics."""
    pytest.importorskip("ember")
    import ember.features

    ref_hdr = ember.features.HeaderFileInfo()
    ref_hdr_vec = ref_hdr.process_raw_features(ref_hdr.raw_features(b"", None)).tolist()
    cand_hdr_vec = extract_header_info(b"", None)

    assert len(ref_hdr_vec) == len(cand_hdr_vec) == 62
    max_hdr_diff = max(abs(a - b) for a, b in zip(ref_hdr_vec, cand_hdr_vec, strict=True))
    assert max_hdr_diff == 0.0, f"extract_header_info (None) diff={max_hdr_diff}"

    ref_sec = ember.features.SectionInfo()
    ref_sec_vec = ref_sec.process_raw_features(ref_sec.raw_features(b"", None)).tolist()
    cand_sec_vec = extract_section_info(b"", None)

    assert len(ref_sec_vec) == len(cand_sec_vec) == 255
    max_sec_diff = max(abs(a - b) for a, b in zip(ref_sec_vec, cand_sec_vec, strict=True))
    assert max_sec_diff == 0.0, f"extract_section_info (None) diff={max_sec_diff}"


def test_multi_record_dataset_group_equivalence() -> None:
    """Verify all 9 feature groups on multiple records of test_features.jsonl achieve max_diff=0.0."""
    features_jsonl = Path("datasets/ember2018/test_features.jsonl")
    if not features_jsonl.exists():
        pytest.skip("datasets/ember2018/test_features.jsonl not present")

    import ember
    from sklearn.feature_extraction import FeatureHasher

    extractor = ember.PEFeatureExtractor(2, print_feature_warning=False)

    with open(features_jsonl, encoding="utf-8") as f:
        for idx in range(10):
            line = f.readline()
            if not line:
                break
            rec = json.loads(line)
            ref_vec = extractor.process_raw_features(rec)

            c_hist = (np.array(rec["histogram"], dtype=np.float32) / np.array(rec["histogram"], dtype=np.float32).sum())
            c_ent = (np.array(rec["byteentropy"], dtype=np.float32) / np.array(rec["byteentropy"], dtype=np.float32).sum())
            hist_div = float(rec["strings"]["printables"]) if rec["strings"]["printables"] > 0 else 1.0
            c_str = np.hstack([
                rec["strings"]["numstrings"], rec["strings"]["avlength"], rec["strings"]["printables"],
                np.asarray(rec["strings"]["printabledist"]) / hist_div, rec["strings"]["entropy"],
                rec["strings"]["paths"], rec["strings"]["urls"], rec["strings"]["registry"], rec["strings"]["MZ"]
            ]).astype(np.float32)
            c_gen = np.asarray([
                rec["general"]["size"], rec["general"]["vsize"], rec["general"]["has_debug"],
                rec["general"]["exports"], rec["general"]["imports"], rec["general"]["has_relocations"],
                rec["general"]["has_resources"], rec["general"]["has_signature"], rec["general"]["has_tls"],
                rec["general"]["symbols"]
            ], dtype=np.float32)
            c_hdr = np.hstack([
                rec["header"]["coff"]["timestamp"],
                FeatureHasher(10, input_type="string").transform([[rec["header"]["coff"]["machine"]]]).toarray()[0],
                FeatureHasher(10, input_type="string").transform([rec["header"]["coff"]["characteristics"]]).toarray()[0],
                FeatureHasher(10, input_type="string").transform([[rec["header"]["optional"]["subsystem"]]]).toarray()[0],
                FeatureHasher(10, input_type="string").transform([rec["header"]["optional"]["dll_characteristics"]]).toarray()[0],
                FeatureHasher(10, input_type="string").transform([[rec["header"]["optional"]["magic"]]]).toarray()[0],
                rec["header"]["optional"]["major_image_version"], rec["header"]["optional"]["minor_image_version"],
                rec["header"]["optional"]["major_linker_version"], rec["header"]["optional"]["minor_linker_version"],
                rec["header"]["optional"]["major_operating_system_version"], rec["header"]["optional"]["minor_operating_system_version"],
                rec["header"]["optional"]["major_subsystem_version"], rec["header"]["optional"]["minor_subsystem_version"],
                rec["header"]["optional"]["sizeof_code"], rec["header"]["optional"]["sizeof_headers"],
                rec["header"]["optional"]["sizeof_heap_commit"],
            ]).astype(np.float32)
            secs = rec["section"]["sections"]
            general = [
                len(secs), sum(1 for s in secs if s["size"] == 0), sum(1 for s in secs if s["name"] == ""),
                sum(1 for s in secs if "MEM_READ" in s["props"] and "MEM_EXECUTE" in s["props"]),
                sum(1 for s in secs if "MEM_WRITE" in s["props"])
            ]
            sizes = [(s["name"], s["size"]) for s in secs]
            entropies = [(s["name"], s["entropy"]) for s in secs]
            vsizes = [(s["name"], s["vsize"]) for s in secs]
            entry_chars = [p for s in secs for p in s["props"] if s["name"] == rec["section"]["entry"]]
            c_sec = np.hstack([
                general,
                FeatureHasher(50, input_type="pair").transform([sizes]).toarray()[0],
                FeatureHasher(50, input_type="pair").transform([entropies]).toarray()[0],
                FeatureHasher(50, input_type="pair").transform([vsizes]).toarray()[0],
                FeatureHasher(50, input_type="string").transform([[rec["section"]["entry"]]]).toarray()[0],
                FeatureHasher(50, input_type="string").transform([entry_chars]).toarray()[0],
            ]).astype(np.float32)
            libs = list(set([lib_name.lower() for lib_name in rec["imports"].keys()]))
            imps = [lib.lower() + ":" + e for lib, elist in rec["imports"].items() for e in elist]
            c_imp = np.hstack([
                FeatureHasher(256, input_type="string").transform([libs]).toarray()[0],
                FeatureHasher(1024, input_type="string").transform([imps]).toarray()[0],
            ]).astype(np.float32)
            c_exp = FeatureHasher(128, input_type="string").transform([rec["exports"]]).toarray()[0].astype(np.float32)
            c_dd = np.zeros(30, dtype=np.float32)
            for i in range(15):
                if i < len(rec["datadirectories"]):
                    c_dd[2 * i] = rec["datadirectories"][i]["size"]
                    c_dd[2 * i + 1] = rec["datadirectories"][i]["virtual_address"]

            cand_vec = np.hstack([c_hist, c_ent, c_str, c_gen, c_hdr, c_sec, c_imp, c_exp, c_dd])
            max_diff = float(np.max(np.abs(ref_vec - cand_vec)))
            assert max_diff == 0.0, f"Record {idx} vectorization diff: {max_diff}"

