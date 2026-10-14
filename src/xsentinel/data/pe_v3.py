"""Read-only V3 binary extraction using the checksum-pinned upstream parser."""
import hashlib,importlib.util
from functools import lru_cache
from pathlib import Path
import numpy as np
from .pe import verify_pe
from .v3_raw import SOURCE_SHA256,WARNINGS_SHA256,UPSTREAM_COMMIT
from .vectorizer import Vectorizer
from xsentinel.schema import V3_PRIMARY,get_schema


@lru_cache(maxsize=1)
def binary_module():
    source=Path(__file__).resolve().parents[1]/'thrember_upstream.py'
    for path,expected in ((source,SOURCE_SHA256),(source.with_name('pefile_warnings.txt'),WARNINGS_SHA256)):
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Pinned V3 source mismatch')
    spec=importlib.util.spec_from_file_location('_xsentinel_thrember_binary',source)
    module=importlib.util.module_from_spec(spec)
    try:spec.loader.exec_module(module)
    except ImportError as error:raise ImportError('Install xsentinel[binary-v3] for V3 binary parsing') from error
    return module


def extract_pe_v3(data):
    """Return one 2568-vector and provenance; never executes the supplied bytes."""
    verify_pe(data);mod=binary_module();extractor=mod.PEFeatureExtractor()
    schema=get_schema(V3_PRIMARY);offset=0
    for f in extractor.features:
        if schema.groups[f.name]!=(offset,offset+f.dim):raise ValueError('V3 feature layout mismatch')
        offset+=f.dim
    if offset!=schema.dim:raise ValueError('V3 binary dimension mismatch')
    raw=extractor.raw_features(data);vector=extractor.process_raw_features(raw)
    if not np.array_equal(vector,Vectorizer(V3_PRIMARY).transform(raw)):raise ValueError('Binary/raw processing disagreement')
    if vector.shape!=(schema.dim,) or not np.isfinite(vector).all():raise ValueError('Invalid V3 binary features')
    if vector[2]!=1:raise ValueError('Upstream could not parse supplied PE')
    return vector,{'sha256':hashlib.sha256(data).hexdigest(),'schema_version':V3_PRIMARY,
        'schema_sha256':schema.fingerprint,'upstream_commit':UPSTREAM_COMMIT,
        'source_sha256':SOURCE_SHA256,'warnings_sha256':WARNINGS_SHA256,'execution':'never executed',
        'compatibility':'Pinned upstream binary/raw parity; benign fixture validation; no original-binary dataset parity'}
