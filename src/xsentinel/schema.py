"""Dataset-specific layouts. Legacy constants remain for archived V2 workflows."""
import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
import numpy as np

DIM = 2381
GROUPS = {'histogram': (0,256), 'byteentropy': (256,512), 'strings': (512,616),
          'general': (616,626), 'header': (626,688), 'section': (688,943),
          'imports': (943,2223), 'exports': (2223,2351), 'datadirectories': (2351,2381)}
VIEW_GROUPS = {'structural': ('general','header','section','datadirectories'),
               'behavioral': ('imports','exports'), 'metadata': ('histogram','byteentropy','strings')}
VIEWS = {v: np.concatenate([np.arange(*GROUPS[g]) for g in gs]) for v,gs in VIEW_GROUPS.items()}
SCHEMA_VERSION = 'ember-v2-2381-views-v1'
assert np.array_equal(np.sort(np.concatenate(list(VIEWS.values()))), np.arange(DIM))
V2_PRIMARY = 'ember-v2-2381-views-v2'
V3_PRIMARY = 'ember-v3-2568-views-v1'
RESTRICTED_V2 = (612,613,614,615,616,626,677,678,679,680,681,682,684,689,690,691,692)
LEGACY_RESTRICTED_V2 = tuple(j for j in RESTRICTED_V2 if j != 684)
VERSION_FIELDS = ('major_image_version','minor_image_version','major_linker_version',
                  'minor_linker_version','major_operating_system_version',
                  'minor_operating_system_version','major_subsystem_version','minor_subsystem_version')
SECTION_COUNTS = ('num_sections','num_zero_size_sections','num_unnamed_sections',
                  'num_read_and_execute_sections','num_write_sections')

@dataclass(frozen=True)
class FeatureSchema:
    version: str
    dataset: str
    names: tuple
    types: tuple
    view_labels: tuple
    group_ranges: tuple
    restricted: tuple
    categorical: tuple = ()
    extractor_commit: str = ''
    extractor_sha256: str = ''
    warnings_sha256: str = ''
    restricted_status: str = 'source-derived; vector only; not binary feasibility'

    def __post_init__(self):
        if (len(self.names) != len(set(self.names)) or len(self.types) != self.dim or
                len(self.view_labels) != self.dim or set(self.view_labels) != set(VIEW_GROUPS)):
            raise ValueError('Invalid schema names/types/view coverage')
        if any(j < 0 or j >= self.dim for j in self.restricted + self.categorical):
            raise ValueError('Invalid schema feature pool')

    @property
    def dim(self):
        return len(self.names)

    @property
    def groups(self):
        return {g:(start,end) for g,start,end in self.group_ranges}

    @property
    def views(self):
        return {v:np.flatnonzero(np.asarray(self.view_labels)==v) for v in VIEW_GROUPS}

    def matrix(self,x):
        x=np.asarray(x,dtype=np.float32)
        if x.ndim==1: x=x[None,:]
        if x.ndim!=2 or x.shape[1]!=self.dim or not np.isfinite(x).all():
            raise ValueError(f'Expected finite {self.dataset} matrix for {self.version} with {self.dim} columns')
        return x

    def check_model(self,model,view=None):
        if view is not None and view not in self.views:
            raise ValueError('Unknown model view: '+str(view))
        expected=self.dim if view is None else len(self.views[view])
        if model.num_feature()!=expected:
            raise ValueError(f'Model/schema feature mismatch: {view or "main"} requires {expected}')

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)

    @property
    def fingerprint(self):
        payload=json.dumps(self.to_dict(),sort_keys=True,separators=(',',':'),ensure_ascii=True)
        return hashlib.sha256(payload.encode()).hexdigest()

def _v2(version):
    names=[f'{g}.column_{j-start}' for g,(start,end) in GROUPS.items() for j in range(start,end)]
    types=['numeric']*DIM
    def fields(start,values): names[start:start+len(values)]=values
    fields(512,['strings.numstrings','strings.avlength','strings.printables'])
    fields(515,[f'strings.printabledist_{i}' for i in range(96)])
    fields(611,['strings.entropy','strings.paths','strings.urls','strings.registry','strings.MZ'])
    fields(616,['general.'+k for k in ('size','vsize','has_debug','exports','imports','has_relocations','has_resources','has_signature','has_tls','symbols')])
    names[626]='header.coff.timestamp'
    for start,key in ((627,'machine'),(637,'characteristics'),(647,'subsystem'),(657,'dll_characteristics'),(667,'magic')):
        fields(start,[f'header.{key}_hash_{i}' for i in range(10)])
        types[start:start+10]=['hash_bucket']*10
    fields(677,['header.optional.'+k for k in VERSION_FIELDS+('sizeof_code','sizeof_headers','sizeof_heap_commit')])
    fields(688,['section.'+k for k in SECTION_COUNTS])
    for start,size,key in ((693,50,'size'),(743,50,'entropy'),(793,50,'vsize'),(843,50,'entry_name'),(893,50,'characteristics'),(943,256,'import_libraries'),(1199,1024,'import_functions'),(2223,128,'exports')):
        fields(start,[f'{key}.hash_{i}' for i in range(size)])
        types[start:start+size]=['hash_bucket']*size
    fields(2351,[f'datadirectories.{i}.{key}' for i in range(15) for key in ('size','virtual_address')])
    labels=['']*DIM
    for v,idx in VIEWS.items():
        for j in idx: labels[j]=v
    return FeatureSchema(version,'EMBER2018',tuple(names),tuple(types),tuple(labels),
        tuple((g,*r) for g,r in GROUPS.items()),LEGACY_RESTRICTED_V2 if version==SCHEMA_VERSION else RESTRICTED_V2)

def _v3():
    from pathlib import Path
    from xsentinel.data.v3_raw import raw_module,UPSTREAM_COMMIT,SOURCE_SHA256,WARNINGS_SHA256
    mod=raw_module(); extractor=mod.PEFeatureExtractor()
    groups={}; names=[]; types=[]
    for f in extractor.features:
        start=len(names); groups[f.name]=(start,start+f.dim)
        names.extend(f'{f.name}.column_{i}' for i in range(f.dim)); types.extend(['numeric']*f.dim)
    if len(names)!=2568: raise ValueError('Pinned V3 dimension changed')
    def fields(group,offset,keys,kind='numeric'):
        start=groups[group][0]+offset
        names[start:start+len(keys)]=[group+'.'+k for k in keys]
        types[start:start+len(keys)]=[kind]*len(keys)
    fields('general',0,['size','entropy','is_pe','start_byte_0','start_byte_1','start_byte_2','start_byte_3'])
    fields('strings',0,['numstrings','avlength','printables'])
    fields('strings',3,[f'printabledist_{i}' for i in range(96)])
    fields('strings',99,['entropy'])
    fields('strings',100,['regex_count.'+k for k in mod.StringExtractor().regex_idxs])
    h=mod.HeaderFileInfo()
    fields('header',0,['coff.'+k for k in ('timestamp','number_of_sections','number_of_symbols','sizeof_optional_header','pointer_to_symbol_table','machine')])
    fields('header',6,['optional.subsystem']+['optional.'+k for k in VERSION_FIELDS+('sizeof_code','sizeof_headers','sizeof_image','sizeof_initialized_data','sizeof_uninitialized_data','sizeof_stack_reserve','sizeof_stack_commit','sizeof_heap_reserve','sizeof_heap_commit','address_of_entrypoint','base_of_code','image_base','section_alignment','checksum','number_of_rvas_and_sizes')])
    fields('header',30,['coff.characteristic.'+k for k in h._image_characteristics],'boolean')
    fields('header',46,['optional.dll_characteristic.'+k for k in h._dll_characteristics],'boolean')
    fields('header',57,['dos.'+k for k in h._dos_members])
    fields('section',0,list(SECTION_COUNTS)+['max_entropy','min_entropy','max_size_ratio','min_size_ratio','max_vsize_ratio','min_vsize_ratio'])
    for offset,size,key in ((11,50,'size'),(61,50,'vsize'),(111,50,'entropy'),(161,50,'characteristics'),(211,10,'entry_name')):
        fields('section',offset,[f'{key}_hash_{i}' for i in range(size)],'hash_bucket')
    fields('section',221,['overlay_size','overlay_size_ratio','overlay_entropy'])
    fields('imports',0,['num_imports','num_libraries'])
    fields('imports',2,[f'library_hash_{i}' for i in range(256)],'hash_bucket')
    fields('imports',258,[f'function_hash_{i}' for i in range(1024)],'hash_bucket')
    # Upstream emits len(exports_hashed), not the actual number of exports.
    fields('exports',0,['hashed_vector_length'])
    fields('exports',1,[f'hash_{i}' for i in range(128)],'hash_bucket')
    fields('datadirectories',0,[f'{key}.{field}' for key in mod.DataDirectories()._name_order for field in ('size','virtual_address')]+['has_relocs','has_dynamic_relocs'])
    fields('richheader',0,['num_pairs'])
    fields('richheader',1,[f'hash_{i}' for i in range(32)],'hash_bucket')
    fields('authenticode',0,['num_certs','self_signed','empty_program_name','no_countersigner','parse_error','chain_max_depth','latest_signing_time','signing_time_diff'])
    warnings=mod.PEFormatWarnings(Path(mod.__file__).with_name('pefile_warnings.txt'))
    fields('pefilewarnings',0,['warning.'+k for k in warnings.warning_ids],'boolean')
    fields('pefilewarnings',87,['num_warnings'])
    labels=['structural']*len(names)
    for group in ('histogram','byteentropy','strings'):
        start,end=groups[group]; labels[start:end]=['metadata']*(end-start)
    for group in ('imports','exports'):
        start,end=groups[group]; labels[start:end]=['behavioral']*(end-start)
    labels[1]='metadata'  # File entropy; size/is_pe/start bytes are Structural.
    categorical=(2,3,4,5,6,groups['header'][0]+5,groups['header'][0]+6)
    for j in categorical: types[j]='categorical'
    restricted_names=['general.size','header.coff.timestamp']+['header.optional.'+k for k in VERSION_FIELDS if k!='major_subsystem_version']+['section.'+k for k in SECTION_COUNTS[1:]]
    return FeatureSchema(V3_PRIMARY,'EMBER2024',tuple(names),tuple(types),tuple(labels),tuple((g,*r) for g,r in groups.items()),tuple(names.index(k) for k in restricted_names),categorical,UPSTREAM_COMMIT,SOURCE_SHA256,WARNINGS_SHA256,
        'semantic Structural adaptation only; real-data variation audit pending; no Metadata equivalent assumed')

@lru_cache(maxsize=3)
def get_schema(version=SCHEMA_VERSION):
    if isinstance(version,FeatureSchema): return version
    if version in (SCHEMA_VERSION,V2_PRIMARY): return _v2(version)
    if version==V3_PRIMARY: return _v3()
    raise ValueError('Unknown feature schema: '+str(version))

def matrix(x,schema=SCHEMA_VERSION):
    return get_schema(schema).matrix(x)
