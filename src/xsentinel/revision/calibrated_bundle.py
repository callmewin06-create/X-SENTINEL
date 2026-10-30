"""Opt-in calibration sidecars; old Detector bundles remain byte-identical."""
from pathlib import Path
import numpy as np
from xsentinel.utils import read_json, sha256
from xsentinel.detection.detector import Detector
from xsentinel.revision.calibration_v2 import POLICY


class CalibratedBundle:
    def __init__(self, bundle_directory, policy_path):
        directory=Path(bundle_directory);self.policy=read_json(policy_path)
        if self.policy.get('policy')!=POLICY or self.policy.get('operator')!='>':
            raise ValueError('Unsupported calibration sidecar')
        if sha256(directory/'bundle.json')!=self.policy['original_bundle_sha256']:
            raise ValueError('Sidecar does not match this frozen bundle')
        self.detector=Detector.load(directory)
        self.thresholds=self.policy['thresholds']
        if set(self.thresholds)!=set(self.detector.thresholds) or not all(np.isfinite(v) for v in self.thresholds.values()):
            raise ValueError('Invalid method set or thresholds')

    def predict_selected(self, x, method):
        scores,_,details,elapsed=self.detector.predict_selected(x,method)
        flags={name:values>self.thresholds[name] for name,values in scores.items()}
        details={**details,'calibration_policy':self.policy['policy'],'calibration_scope':self.policy['scope']}
        return scores,flags,details,elapsed
