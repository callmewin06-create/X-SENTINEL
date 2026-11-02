"""Experimental modern-LIEF adapter. Reads only; never invokes a binary."""
import hashlib
import io
import struct
import numpy as np
import lief
from .vectorizer import Vectorizer,upstream_module
from .limits import MAX_UPLOAD_BYTES

def verify_pe(data,max_bytes=MAX_UPLOAD_BYTES):
    if len(data)>max_bytes: raise ValueError(f'Upload exceeds {max_bytes//(1024*1024)} MiB')
    if len(data)<64 or data[:2]!=b'MZ': raise ValueError('Missing DOS MZ header')
    offset=struct.unpack_from('<I',data,0x3c)[0]
    if offset<64 or offset+24>len(data) or data[offset:offset+4]!=b'PE\0\0':
        raise ValueError('Invalid PE signature/header offset')

def extract_pe(data):
    verify_pe(data)
    try:
        binary=lief.PE.parse(io.BytesIO(data))
    except Exception as exc:
        raise ValueError(f'LIEF could not parse PE: {exc}') from exc
    if binary is None: raise ValueError('LIEF could not parse PE')
    u=upstream_module(); raw={'sha256':hashlib.sha256(data).hexdigest()}
    try:
        for cls in (u.ByteHistogram,u.ByteEntropyHistogram,u.StringExtractor,u.ImportsInfo,u.ExportsInfo,u.GeneralFileInfo,u.HeaderFileInfo,u.DataDirectories):
            obj=cls(); raw[obj.name]=obj.raw_features(data,binary)
        def token(e):
            name=getattr(e,'name',str(e).split('.')[-1])
            return name
        header=raw['header']
        char_list = getattr(binary.header, 'characteristics_list', [])
        header['coff']['characteristics']=['CHARA_'+token(c) if not token(c).startswith('CHARA_') else token(c) for c in char_list]
        sections=[]; entry=''
        try:
            entrypoint = getattr(binary, 'entrypoint', 0) or 0
            imagebase = getattr(binary, 'imagebase', 0) or 0
            entry_rva = entrypoint - imagebase
            chosen = binary.section_from_rva(entry_rva) if entry_rva >= 0 else None
            if chosen is not None:
                entry = getattr(chosen, 'name', '') or ''
        except Exception:
            entry = ''
        for s in binary.sections:
            props=[token(c) for c in getattr(s, 'characteristics_lists', [])]
            s_name = getattr(s, 'name', '') or ''
            s_size = getattr(s, 'size', 0) or 0
            s_entropy = getattr(s, 'entropy', 0.0) or 0.0
            s_vsize = getattr(s, 'virtual_size', 0) or 0
            sections.append({'name':s_name,'size':s_size,'entropy':s_entropy,'vsize':s_vsize,'props':props})
            if not entry and 'MEM_EXECUTE' in props: entry=s_name
        raw['section']={'entry':entry,'sections':sections}
        return Vectorizer().transform(raw),{'sha256':raw['sha256'],'lief_version':lief.__version__,
            'compatibility':'experimental; no identical-binary legacy LIEF 0.9 validation yet','execution':'never executed'}
    except Exception as exc:
        raise ValueError(f'LIEF could not extract features from PE: {exc}') from exc
