"""Use bundled render_docx.py with the independently exported native Word PDF."""
import importlib.util,os,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
skill=Path('C:/Users/win9tui/.codex/plugins/cache/openai-primary-runtime/documents/26.1105.12137/skills/documents/render_docx.py')
spec=importlib.util.spec_from_file_location('render_docx',skill);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
tmp=root/'output/jstis_revision_2026_11_10/render_tmp';tmp.mkdir(exist_ok=True);tempfile.tempdir=str(tmp)
bundle=Path('C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies')
os.environ['PATH']=str(bundle/'native/poppler/Library/bin')+os.pathsep+os.environ['PATH']
mod.convert_to_pdf=lambda *args,**kwargs:(str(root/'output/jstis_revision_2026_11_10/native_preview.pdf'),'Native Microsoft Word export')
paths=mod.rasterize(str(root/'output/jstis_revision_2026_11_10/X_SENTINEL_Anonymous_Completed_M3_2026_11_10.docx'),
                    str(root/'output/jstis_revision_2026_11_10/render'),120,False,False)
print('Rendered pages',len(paths))
