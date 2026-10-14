"""Build and execute only this script's reviewed benign fixtures; never corpus samples."""
import sys,struct,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from xsentinel.data.pe import extract_pe
from xsentinel.data.pe_v3 import extract_pe_v3
from xsentinel.schema import get_schema,V2_PRIMARY,V3_PRIMARY
from xsentinel.utils import sha256,write_json

SOURCE='''using System;
public class RevisionFixture {
 public static int Main(string[] args) {
   int n=0; if(args.Length>0 && !Int32.TryParse(args[0],out n)) return 2;
   Console.WriteLine("X_SENTINEL_BENIGN_FIXTURE:"+(n*n+7)); return 0;
 }
}'''


def run_owned(path,argument):
    return subprocess.run([str(path.resolve()),argument],capture_output=True,text=True,timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    root=Path('outputs/revision_2026_10_13/binary_validation');root.mkdir(parents=True,exist_ok=True)
    source=root/'ReviewedBenignFixture.cs';source.write_text(SOURCE,encoding='ascii')
    compiler=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe')
    original=root/'ReviewedBenignFixture.exe'
    result=subprocess.run([str(compiler),'/nologo','/target:exe','/platform:x86','/optimize+',f'/out:{original}',str(source)],capture_output=True,text=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    data=original.read_bytes();offset=struct.unpack_from('<I',data,0x3c)[0]
    variants={'coff_timestamp_0':bytearray(data),'coff_timestamp_2024':bytearray(data),
        'benign_overlay':bytearray(data+b'\nX_SENTINEL_REVIEWED_BENIGN_OVERLAY\n')}
    struct.pack_into('<I',variants['coff_timestamp_0'],offset+8,0)
    struct.pack_into('<I',variants['coff_timestamp_2024'],offset+8,1704067200)
    expected={arg:run_owned(original,arg) for arg in ('0','3','-4','invalid')}
    originals={};errors=[]
    for version,extract in ((V2_PRIMARY,extract_pe),(V3_PRIMARY,extract_pe_v3)):
        try:originals[version]=extract(data)
        except Exception as error:errors.append({'schema':version,'error':repr(error)})
    rows=[]
    for name,modified in variants.items():
        path=root/(name+'.exe');path.write_bytes(modified)
        checks=[]
        for arg,baseline in expected.items():
            after=run_owned(path,arg);same=(after.returncode,after.stdout,after.stderr)==(baseline.returncode,baseline.stdout,baseline.stderr)
            checks.append({'input':arg,'identical':same,'exit_before':baseline.returncode,'exit_after':after.returncode,'stdout':after.stdout.strip()})
            if not same:raise ValueError('Fixture functionality regression')
        differences={}
        for version,extract in ((V2_PRIMARY,extract_pe),(V3_PRIMARY,extract_pe_v3)):
            if version not in originals:continue
            x,info=extract(bytes(modified));base,_=originals[version];schema=get_schema(version);diff=np.flatnonzero(x!=base)
            differences[version]={'changed_n':len(diff),'changed_indices':diff.tolist(),
                'changed_by_view':{v:int(sum(schema.view_labels[j]==v for j in diff)) for v in schema.views},
                'diff':[{'index':int(j),'before':float(base[j]),'after':float(x[j])} for j in diff],
                'outside_restricted':[int(j) for j in sorted(set(diff)-set(schema.restricted))],'extractor':info}
        rows.append({'variant':name,'sha256':sha256(path),'bytes':len(modified),'function_checks':checks,'feature_differences':differences})
    write_json(root/'validation.json',{'scope':'One self-built unsigned .NET PE; 3 byte-level edits; 4 functional cases each',
        'source_sha256':sha256(source),'original_sha256':sha256(original),'compiler':str(compiler),
        'original_extractors':{v:i for v,(x,i) in originals.items()},'errors':errors,'variants':rows,
        'limitations':'Benign prototype only; does not realize original vector triggers or validate malware/backdoor functionality; V2 legacy parser equivalence untested'})
    print('Benign fixture validation complete;',len(rows),'variants;',len(originals),'extractors;',errors,flush=True)


if __name__=='__main__':main()
