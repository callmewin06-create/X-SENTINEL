"""Experimental modern-LIEF adapter. Reads only; never invokes a binary."""
import hashlib
import struct
import numpy as np
import lief
from .vectorizer import Vectorizer,upstream_module

def verify_pe(data,max_bytes=20*1024*1024):
    if len(data)>max_bytes: raise ValueError('Upload exceeds 20 MiB')
    if len(data)<64 or data[:2]!=b'MZ': raise ValueError('Missing DOS MZ header')
    offset=struct.unpack_from('<I',data,0x3c)[0]
    if offset<64 or offset+24>len(data) or data[offset:offset+4]!=b'PE\0\0':
        raise ValueError('Invalid PE signature/header offset')

def extract_pe(data):
    verify_pe(data)
    binary=lief.PE.parse(list(data))
    if binary is None: raise ValueError('LIEF could not parse PE')
    u=upstream_module(); raw={'sha256':hashlib.sha256(data).hexdigest()}
    for cls in (u.ByteHistogram,u.ByteEntropyHistogram,u.StringExtractor,u.ImportsInfo,u.ExportsInfo,u.GeneralFileInfo,u.HeaderFileInfo,u.DataDirectories):
        obj=cls(); raw[obj.name]=obj.raw_features(data,binary)
    # Modern LIEF moved enum names, removed old exception aliases and renamed
    # characteristics_list. Map enum names to legacy EMBER CHARA_* tokens.
    def token(e):
        name=getattr(e,'name',str(e).split('.')[-1])
        return name
    header=raw['header']
    header['coff']['characteristics']=['CHARA_'+token(c) if not token(c).startswith('CHARA_') else token(c) for c in binary.header.characteristics_list]
    sections=[]; entry=''
    entry_rva=binary.entrypoint-binary.imagebase
    chosen=binary.section_from_rva(entry_rva)
    if chosen is not None: entry=chosen.name
    for s in binary.sections:
        props=[token(c) for c in s.characteristics_lists]
        sections.append({'name':s.name,'size':s.size,'entropy':s.entropy,'vsize':s.virtual_size,'props':props})
        if not entry and 'MEM_EXECUTE' in props: entry=s.name
    raw['section']={'entry':entry,'sections':sections}
    return Vectorizer().transform(raw),{'sha256':raw['sha256'],'lief_version':lief.__version__,
        'compatibility':'experimental; no identical-binary legacy LIEF 0.9 validation yet','execution':'never executed'}
