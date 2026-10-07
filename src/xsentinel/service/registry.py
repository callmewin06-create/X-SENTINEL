"""Only catalogued primary bundles can be requested through the API."""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import threading
from xsentinel.dashboard_catalog import primary_catalog
from xsentinel.detection.detector import Detector


class BundleRegistry:
    def __init__(self, root='outputs/primary'):
        self.root = Path(root).resolve()
        self.entries = {}
        for dataset in ('EMBER2018','EMBER2024'):
            for (family,seed,rate),variants in primary_catalog(dataset,self.root).items():
                for variant,path in variants.items():
                    path = Path(path).resolve()
                    relative = path.relative_to(self.root).as_posix()
                    manifest = (path/'bundle.json').read_bytes()
                    identity = hashlib.sha256(relative.encode()+b'\0'+manifest).hexdigest()
                    state = json.loads(manifest)
                    self.entries[identity] = {'id':identity,'dataset':dataset,'family':family,
                        'seed':seed,'rate':rate,'variant':variant,'relative_path':relative,
                        'path':path,'state':state}

    def listing(self):
        return [{k:v for k,v in e.items() if k not in ('path','state')} for e in self.entries.values()]

    def entry(self, identity):
        if identity not in self.entries:
            raise KeyError('Unknown primary bundle')
        return self.entries[identity]

    @lru_cache(maxsize=4)
    def loaded(self, identity):
        entry = self.entry(identity)
        # Windows LightGBM's native file loader cannot open an absolute Unicode
        # workspace path. Relative ASCII bundle paths preserve the same bytes.
        load_path=Path(os.path.relpath(entry['path'])) if os.name=='nt' else entry['path']
        detector = Detector.load(load_path,expected_dataset=entry['dataset'])
        if detector.protocol!='xsentinel-primary-v2' or detector.enable_m5:
            raise ValueError('API requires primary protocol with M5 disabled')
        return detector,threading.Lock()
