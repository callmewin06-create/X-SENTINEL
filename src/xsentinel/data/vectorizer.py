"""Upstream EMBER raw processing, without invoking legacy binary parsing."""
import importlib.util
from pathlib import Path
import numpy as np
from xsentinel.schema import DIM, GROUPS, get_schema, SCHEMA_VERSION, V3_PRIMARY

_source = Path(__file__).resolve().parents[1] / 'ember_upstream.py'

def upstream_module():
    if not _source.exists():
        raise FileNotFoundError('Vendored upstream EMBER source missing')
    import types
    module = types.ModuleType('_ember_features')
    source=_source.read_text(encoding='utf8')
    # sklearn >=1.2 forbids a bare string sample. Legacy FeatureHasher iterated
    # the characters of raw_obj['entry']; retain that historical behavior.
    source=source.replace("transform([raw_obj['entry']])", "transform([list(raw_obj['entry'])])")
    source=source.replace('dtype=np.int)', 'dtype=int)')
    exec(compile(source,str(_source),'exec'),module.__dict__)
    return module

class Vectorizer:
    def __init__(self, schema=SCHEMA_VERSION):
        self.schema = get_schema(schema)
        if self.schema.version == V3_PRIMARY:
            from .v3_raw import raw_module
            self.extractor = raw_module().PEFeatureExtractor()
        else:
            self.extractor = upstream_module().PEFeatureExtractor(2,print_feature_warning=False)
        if self.extractor.dim != self.schema.dim:
            raise ValueError('Upstream feature dimension mismatch')
        offset=0
        for f in self.extractor.features:
            if self.schema.groups[f.name] != (offset,offset+f.dim):
                raise ValueError(f'Feature layout mismatch: {f.name}')
            offset += f.dim

    def transform(self, record):
        if self.schema.version == V3_PRIMARY and 'features' in record:
            record = record['features']
        x = self.extractor.process_raw_features(record)
        if x.shape != (self.schema.dim,) or not np.isfinite(x).all():
            raise ValueError('Invalid/nonfinite raw EMBER sample')
        return x

    def transform_batch(self, records):
        """Batch FeatureHasher work across rows, preserving upstream processing."""
        if self.schema.version == V3_PRIMARY:
            return (np.stack([self.transform(r) for r in records]) if records else
                    np.empty((0,self.schema.dim),dtype=np.float32))
        from sklearn.feature_extraction import FeatureHasher
        if not records: return np.empty((0,DIM),dtype=np.float32)
        n=len(records); out=np.zeros((n,DIM),dtype=np.float32)
        def hashed(rows,dim,kind='string'):
            return FeatureHasher(dim,input_type=kind).transform(rows).toarray().astype(np.float32)
        for key in ('histogram','byteentropy'):
            a=np.asarray([r[key] for r in records],dtype=np.float32)
            out[:,slice(*GROUPS[key])]=a/a.sum(axis=1,keepdims=True)
        s=[r['strings'] for r in records]
        out[:,512:515]=[[r['numstrings'],r['avlength'],r['printables']] for r in s]
        out[:,515:611]=np.asarray([r['printabledist'] for r in s])/np.asarray([max(1,r['printables']) for r in s])[:,None]
        out[:,611:616]=[[r[k] for k in ('entropy','paths','urls','registry','MZ')] for r in s]
        out[:,616:626]=[[r['general'][k] for k in ('size','vsize','has_debug','exports','imports','has_relocations','has_resources','has_signature','has_tls','symbols')] for r in records]
        coff=[r['header']['coff'] for r in records]; opts=[r['header']['optional'] for r in records]
        out[:,626]=[r['timestamp'] for r in coff]
        out[:,627:637]=hashed([[r['machine']] for r in coff],10)
        out[:,637:647]=hashed([r['characteristics'] for r in coff],10)
        out[:,647:657]=hashed([[r['subsystem']] for r in opts],10)
        out[:,657:667]=hashed([r['dll_characteristics'] for r in opts],10)
        out[:,667:677]=hashed([[r['magic']] for r in opts],10)
        out[:,677:688]=[[r[k] for k in ('major_image_version','minor_image_version','major_linker_version','minor_linker_version','major_operating_system_version','minor_operating_system_version','major_subsystem_version','minor_subsystem_version','sizeof_code','sizeof_headers','sizeof_heap_commit')] for r in opts]
        sections=[r['section']['sections'] for r in records]; entry=[r['section']['entry'] for r in records]
        out[:,688:693]=[[len(ss),sum(s['size']==0 for s in ss),sum(s['name']=='' for s in ss),sum('MEM_READ' in s['props'] and 'MEM_EXECUTE' in s['props'] for s in ss),sum('MEM_WRITE' in s['props'] for s in ss)] for ss in sections]
        for start,key in ((693,'size'),(743,'entropy'),(793,'vsize')):
            out[:,start:start+50]=hashed([[(s['name'],s[key]) for s in ss] for ss in sections],50,'pair')
        # Upstream passes the entry string as an iterable, hashing its characters.
        out[:,843:893]=hashed([list(e) for e in entry],50)
        out[:,893:943]=hashed([[p for s in ss for p in s['props'] if s['name']==e] for ss,e in zip(sections,entry)],50)
        imports=[r['imports'] for r in records]
        out[:,943:1199]=hashed([list(set(lib.lower() for lib in r)) for r in imports],256)
        out[:,1199:2223]=hashed([[lib.lower()+':'+f for lib,fs in r.items() for f in fs] for r in imports],1024)
        out[:,2223:2351]=hashed([r['exports'] for r in records],128)
        for i,r in enumerate(records):
            dd=r['datadirectories'][:15]
            out[i,2351:2351+2*len(dd)]=[v for d in dd for v in (d['size'],d['virtual_address'])]
        if not np.isfinite(out).all(): raise ValueError('Nonfinite EMBER vectors')
        return out
