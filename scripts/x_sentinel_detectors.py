# -*- coding: utf-8 -*-
"""
X-SENTINEL: Cross-View Semantic Backdoor Detection System
Đề tài: Cross-View Semantic Backdoor Detection in Malware Classifiers
Môn học: IAM302t (Fall 2026) - Lớp IA2007 - Nhóm 4 (Quân, Thắng, Phú, Phúc)

Kiến trúc giải pháp đề xuất X-SENTINEL gồm 3 module cốt lõi:
- M3: View-Contribution & Signed Polarity Conflict (Phân rã SHAP theo 3 View)
- M4: Cross-View Semantic Disagreement (Bộ phân loại View chuyên biệt dựa trên Bất biến khả thi)
- M5: Semantic Plausibility Safety Net (Kiểm định sự hợp lý ngữ nghĩa của API & Strings)
- Fusion Pipeline: Cơ chế phối hợp 2 tầng (2-Tier Real-Time Pipeline)
"""

import os
import sys
import json
import numpy as np
import lightgbm as lgb
from typing import Dict, Any, List, Tuple
from sklearn.feature_extraction import FeatureHasher

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class XSentinelDetectors:
    def __init__(
        self,
        full_model: lgb.Booster,
        view_mapping_path: str,
        d1_benign_features: np.ndarray,
        view_models: Dict[str, lgb.Booster] = None,
        seed: int = 42
    ):
        """
        Khởi tạo hệ thống phòng thủ X-SENTINEL.
        :param full_model: Mô hình LightGBM toàn cục (2.381 features) nghi vấn có backdoor.
        :param view_mapping_path: Đường dẫn file JSON cấu hình 3 View.
        :param d1_benign_features: Tập tham chiếu D1 (Benign sạch đã kiểm chứng) để khóa ngưỡng.
        :param view_models: Dictionary chứa 3 mô hình View độc lập {'struct', 'behav', 'meta'}.
        """
        self.full_model = full_model
        self.D1 = d1_benign_features
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        # Nạp cấu hình View
        with open(view_mapping_path, "r", encoding="utf-8") as f:
            self.vm = json.load(f)

        self.struct_slices = self.vm["Structural"]["slices"]
        self.behav_slices = self.vm["Behavioral/API"]["slices"]
        self.meta_slices = self.vm["Metadata/String"]["slices"]

        self.view_models = view_models or {}

        # Khởi tạo các ngưỡng khóa
        self.tau_m3_conflict = None
        self.tau_m4_behav_full = None
        self.tau_fusion = None

        # Danh sách hàm API nhạy cảm theo Manifest M5
        self.sensitive_apis = [
            "VirtualAlloc", "VirtualAllocEx", "VirtualProtect", "VirtualProtectEx",
            "WriteProcessMemory", "ReadProcessMemory", "CreateRemoteThread",
            "CreateRemoteThreadEx", "NtCreateThreadEx", "QueueUserAPC",
            "CreateProcessA", "CreateProcessW", "WinExec", "ShellExecuteA",
            "URLDownloadToFileA", "InternetOpenA", "WSAStartup", "connect",
            "IsDebuggerPresent", "RegSetValueExA", "CreateServiceA"
        ]
        self._init_m5_hasher()

    def _init_m5_hasher(self):
        """Ánh xạ các hàm API nhạy cảm sang các bin 1024 của ImportsInfo."""
        hasher = FeatureHasher(n_features=1024, input_type="string")
        # Mỗi API được đưa vào hasher như một phần tử đơn
        raw_list = [[api] for api in self.sensitive_apis]
        hashed_mat = hasher.transform(raw_list)
        # Chỉ số cột hàm import bắt đầu từ 1199 đến 2222 trong EMBER
        # (943 đến 1198 là 256 thư viện DLL, 1199 đến 2222 là 1024 hàm API)
        sensitive_cols = set()
        for row in hashed_mat:
            for col in row.indices:
                sensitive_cols.add(1199 + col)
        self.sensitive_api_indices = list(sensitive_cols)

    def extract_view(self, X: np.ndarray, view_name: str) -> np.ndarray:
        """Trích xuất ma trận đặc trưng cho từng View."""
        slices = self.vm[view_name]["slices"]
        if X.ndim == 1:
            X_2d = X.reshape(1, -1)
            parts = [X_2d[:, s:e] for s, e in slices]
            return np.hstack(parts)[0]
        else:
            parts = [X[:, s:e] for s, e in slices]
            return np.hstack(parts)

    def train_view_classifiers(self, X_train: np.ndarray, y_train: np.ndarray, params: dict = None):
        """
        Huấn luyện 3 bộ phân loại View độc lập cho Module M4.
        Đặc biệt: Behavioral View (1.408 features) hoàn toàn miễn nhiễm với backdoor
        do ràng buộc Feasibility Invariant (kẻ tấn công không thể sửa IAT trên PE thật).
        """
        if params is None:
            params = {
                "boosting_type": "gbdt",
                "objective": "binary",
                "learning_rate": 0.05,
                "num_leaves": 128,
                "feature_fraction": 0.8,
                "random_state": self.seed,
                "verbose": -1,
                "n_jobs": -1
            }

        X_struct = self.extract_view(X_train, "Structural")
        X_behav = self.extract_view(X_train, "Behavioral/API")
        X_meta = self.extract_view(X_train, "Metadata/String")

        self.view_models["struct"] = lgb.train(params, lgb.Dataset(X_struct, label=y_train), num_boost_round=100)
        self.view_models["behav"] = lgb.train(params, lgb.Dataset(X_behav, label=y_train), num_boost_round=100)
        self.view_models["meta"] = lgb.train(params, lgb.Dataset(X_meta, label=y_train), num_boost_round=100)

    # =========================================================================
    # MODULE M3: VIEW-CONTRIBUTION & SIGNED POLARITY CONFLICT
    # =========================================================================
    def compute_m3_score(self, x: np.ndarray) -> Dict[str, float]:
        """
        Tính điểm M3 dựa trên phân rã SHAP Attribution theo View:
        - Xung đột phân cực: Net_Behav (đẩy Malware) - Net_Struct (kéo Benign do Trigger).
        - Khi bị cài Backdoor trên Structural/Metadata, độ chênh lệch Net_Behav - Net_Struct tăng vọt.
        """
        contribs = self.full_model.predict(x.reshape(1, -1), pred_contrib=True)[0][:-1]

        # Tính tổng đóng góp tuyệt đối theo từng View
        s_struct = float(np.sum([np.sum(np.abs(contribs[s:e])) for s, e in self.struct_slices]))
        s_behav = float(np.sum([np.sum(np.abs(contribs[s:e])) for s, e in self.behav_slices]))
        s_meta = float(np.sum([np.sum(np.abs(contribs[s:e])) for s, e in self.meta_slices]))
        total_s = s_struct + s_behav + s_meta + 1e-12

        # Tính lực có dấu (Signed Margin Force) theo từng View
        net_struct = float(np.sum([np.sum(contribs[s:e]) for s, e in self.struct_slices]))
        net_behav = float(np.sum([np.sum(contribs[s:e]) for s, e in self.behav_slices]))
        net_meta = float(np.sum([np.sum(contribs[s:e]) for s, e in self.meta_slices]))

        # Xung đột phân cực (Polarity Conflict)
        conflict_behav_struct = net_behav - net_struct
        disagreement_std = float(np.std([net_struct, net_behav, net_meta]))

        return {
            "ratio_struct": s_struct / total_s,
            "ratio_behav": s_behav / total_s,
            "net_struct": net_struct,
            "net_behav": net_behav,
            "polarity_conflict": conflict_behav_struct,
            "disagreement_std": disagreement_std
        }

    # =========================================================================
    # MODULE M4: CROSS-VIEW SEMANTIC DISAGREEMENT
    # =========================================================================
    def compute_m4_score(self, x: np.ndarray) -> Dict[str, float]:
        """
        Tính điểm bất đồng ngữ nghĩa liên View (Cross-View Disagreement):
        - Đo độ lệch giữa mô hình Hành vi (M_behav) và mô hình Toàn cục (Full Model).
        - Nếu Full Model bị lừa (P_full ~ 0) nhưng M_behav phát hiện hành vi độc (P_behav ~ 1),
          chênh lệch p_behav - p_full sẽ đạt đỉnh ~ 1.0.
        """
        if "behav" not in self.view_models or "struct" not in self.view_models:
            raise ValueError("Chưa huấn luyện hoặc nạp mô hình View! Gọi train_view_classifiers trước.")

        x_2d = x.reshape(1, -1)
        p_full = float(self.full_model.predict(x_2d)[0])

        x_struct = self.extract_view(x_2d, "Structural")
        x_behav = self.extract_view(x_2d, "Behavioral/API")
        x_meta = self.extract_view(x_2d, "Metadata/String")

        p_struct = float(self.view_models["struct"].predict(x_struct)[0])
        p_behav = float(self.view_models["behav"].predict(x_behav)[0])
        p_meta = float(self.view_models["meta"].predict(x_meta)[0])

        # Điểm nghi ngờ chính: M_behav tố cáo mã độc trong khi Full Model bị ru ngủ
        disagreement_behav_full = max(0.0, p_behav - p_full)
        disagreement_behav_struct = max(0.0, p_behav - p_struct)
        cross_view_std = float(np.std([p_full, p_struct, p_behav, p_meta]))

        return {
            "p_full": p_full,
            "p_struct": p_struct,
            "p_behav": p_behav,
            "p_meta": p_meta,
            "m4_score": disagreement_behav_full,
            "disagreement_behav_struct": disagreement_behav_struct,
            "cross_view_std": cross_view_std
        }

    # =========================================================================
    # MODULE M5: SEMANTIC PLAUSIBILITY CHECK (HEURISTIC SAFETY NET)
    # =========================================================================
    def compute_m5_score(self, x: np.ndarray, p_full: float = None) -> Dict[str, Any]:
        """
        Kiểm định tính hợp lý ngữ nghĩa:
        Nếu mô hình dự đoán Benign (p_full < 0.5), nhưng mẫu chứa các API nhạy cảm
        (Process Injection, Network C2) hoặc chuỗi đáng ngờ (MZ dropper, registry run keys),
        M5 gióng chuông cảnh báo bất thường ngữ nghĩa (Plausibility Violation).
        """
        if p_full is None:
            p_full = float(self.full_model.predict(x.reshape(1, -1))[0])

        # Đếm số lượng API nhạy cảm xuất hiện trong mẫu
        sensitive_api_count = 0
        for idx in self.sensitive_api_indices:
            if x[idx] != 0:
                sensitive_api_count += 1

        # Kiểm tra chuỗi nhạy cảm: MZ dropper (cột 615), Registry (cột 614), URLs (cột 613)
        mz_flag = x[615] > 0
        registry_flag = x[614] > 0
        url_flag = x[613] > 0

        # Cờ vi phạm: Dự đoán Benign nhưng có API tiêm nhiễm hoặc Dropper
        is_violation = (p_full < 0.5) and (sensitive_api_count >= 2 or (sensitive_api_count >= 1 and mz_flag))

        return {
            "sensitive_api_count": sensitive_api_count,
            "mz_dropper_present": bool(mz_flag),
            "registry_key_present": bool(registry_flag),
            "url_present": bool(url_flag),
            "plausibility_violation": bool(is_violation)
        }

    # =========================================================================
    # HIỆU CHUẨN VÀ KHÓA NGƯỠNG ĐA TẦNG TRÊN D1 (FPR = 1%)
    # =========================================================================
    def calibrate_and_lock_thresholds(self, target_fpr: float = 0.01) -> Dict[str, float]:
        """
        Khóa cứng các ngưỡng phát hiện M3, M4 và Fusion tại mức FPR 1% trên tập D1.
        """
        print(f"[*] Khóa ngưỡng X-SENTINEL trên {len(self.D1)} mẫu Benign tập D1...")

        m4_scores = [self.compute_m4_score(sample)["m4_score"] for sample in self.D1]
        m3_conflicts = [self.compute_m3_score(sample)["polarity_conflict"] for sample in self.D1]

        percentile_val = (1.0 - target_fpr) * 100.0
        self.tau_m4_behav_full = float(np.percentile(m4_scores, percentile_val))
        self.tau_m3_conflict = float(np.percentile(m3_conflicts, percentile_val))

        # Ngưỡng kết hợp (Fusion): Điểm chuẩn hóa M4 + M3
        # Chuẩn hóa min-max sơ bộ trên D1
        norm_fusion = [
            (m4 / (self.tau_m4_behav_full + 1e-6)) + (m3 / (self.tau_m3_conflict + 1e-6))
            for m4, m3 in zip(m4_scores, m3_conflicts)
        ]
        self.tau_fusion = float(np.percentile(norm_fusion, percentile_val))

        locked = {
            "target_fpr": target_fpr,
            "tau_m4_behav_full": self.tau_m4_behav_full,
            "tau_m3_conflict": self.tau_m3_conflict,
            "tau_fusion": self.tau_fusion
        }
        print(f"[+] ĐÃ KHÓA NGƯỠNG X-SENTINEL: M4 (tau={self.tau_m4_behav_full:.4f}), M3 (tau={self.tau_m3_conflict:.4f})")
        return locked

    # =========================================================================
    # PIPELINE DỰ ĐOÁN THỜI GIAN THỰC (2-TIER FAST/DEEP INFERENCE)
    # =========================================================================
    def detect(self, x: np.ndarray) -> Dict[str, Any]:
        """
        Cơ chế phòng thủ thời gian thực 2 Tầng:
        - Tầng 1 (Fast-Path < 0.1ms): Chạy M4 (Behav vs Full). Nếu M4 > tau_m4 -> BLOCK lập tức!
        - Tầng 2 (Deep-Path): Nếu nghi ngờ hoặc cần phân tích giải thích, kích hoạt M3 & M5.
        """
        if self.tau_m4_behav_full is None:
            raise ValueError("Chưa khóa ngưỡng! Hãy gọi calibrate_and_lock_thresholds trước.")

        # Tầng 1: M4 Fast Forward Pass (< 0.1ms)
        m4_res = self.compute_m4_score(x)
        p_full = m4_res["p_full"]
        m4_score = m4_res["m4_score"]

        # Nếu mô hình dự đoán Malware rõ ràng (p_full >= 0.5) -> BLOCK (Mã độc thông thường)
        if p_full >= 0.5:
            return {
                "decision": "BLOCK (MALWARE)",
                "reason": "Mô hình toàn cục phát hiện mã độc",
                "p_full": round(p_full, 4),
                "is_backdoor": False,
                "m4_score": round(m4_score, 4)
            }

        # Nếu mô hình dự đoán Benign (p_full < 0.5), kiểm tra cờ Backdoor qua M4
        if m4_score > self.tau_m4_behav_full:
            return {
                "decision": "BLOCK (BACKDOOR DETECTED)",
                "reason": "M4 phát hiện bất đồng ngữ nghĩa: M_behav tố cáo mã độc",
                "p_full": round(p_full, 4),
                "is_backdoor": True,
                "m4_score": round(m4_score, 4),
                "tau_m4": round(self.tau_m4_behav_full, 4)
            }

        # Tầng 2: Kiểm tra bẫy an toàn M5 (Plausibility Safety Net)
        m5_res = self.compute_m5_score(x, p_full=p_full)
        if m5_res["plausibility_violation"]:
            return {
                "decision": "BLOCK (BACKDOOR DETECTED)",
                "reason": "M5 phát hiện vi phạm ngữ nghĩa: Dự đoán Benign nhưng có API độc hại",
                "p_full": round(p_full, 4),
                "is_backdoor": True,
                "m5_details": m5_res
            }

        # Không vi phạm -> Cho phép thực thi
        return {
            "decision": "PASS",
            "reason": "Mẫu nhất quán ngữ nghĩa liên View",
            "p_full": round(p_full, 4),
            "is_backdoor": False,
            "m4_score": round(m4_score, 4)
        }
