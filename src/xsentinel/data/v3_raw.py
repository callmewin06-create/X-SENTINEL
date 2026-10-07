"""Pinned V3 JSON processing without importing binary-parser dependencies.

Only imports for pefile/signify are omitted. Class definitions and raw processing
methods are compiled unchanged. Binary extraction is deliberately unavailable.
"""
import ast
import hashlib
import types
from functools import lru_cache
from pathlib import Path

SOURCE_SHA256 = '58a085e9ad307aa2c52e165985ff80db8fd5b763891c0cba2d1758a4825f7273'
WARNINGS_SHA256 = 'a23a9d0a7a938b19390a75fe0eb024dbc9bad7a134bb1511a2913f365a52e5fb'
UPSTREAM_COMMIT = '0ef753e81d98bf209f71b03cd331dfc190b5b54d'


@lru_cache(maxsize=1)
def raw_module():
    source = Path(__file__).resolve().parents[1] / 'thrember_upstream.py'
    warnings = source.with_name('pefile_warnings.txt')
    for path, expected in ((source, SOURCE_SHA256), (warnings, WARNINGS_SHA256)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Pinned V3 extractor checksum mismatch: ' + path.name)
    tree = ast.parse(source.read_text(encoding='utf8'), filename=str(source))
    def parsing_import(node):
        return (isinstance(node, ast.Import) and
                any(n.name in ('pefile', 'signify') for n in node.names)) or (
                isinstance(node, ast.ImportFrom) and node.module == 'signify.authenticode')
    tree.body = [n for n in tree.body if not parsing_import(n)]
    module = types.ModuleType('_xsentinel_thrember_raw')
    module.__file__ = str(source)
    # Resolve type annotations only; no parser method is exposed by the adapter.
    module.pefile = types.SimpleNamespace(PE=object)
    exec(compile(tree, str(source), 'exec'), module.__dict__)
    return module
