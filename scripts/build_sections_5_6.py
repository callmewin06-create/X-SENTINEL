"""Write Sections 5/6 from preserved primary artifacts; never retrain or retune."""
from pathlib import Path
from collections import defaultdict
import json, hashlib, sys, re
from html import escape
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output/pdf"
FIG=OUT/"sections_5_6_figures"
FIG.mkdir(parents=True,exist_ok=True)
families=["concentrated_structural","spread_structural","cross_3view_stress"]
short={families[0]:"Conc.",families[1]:"Spread",families[2]:"Cross"}
datasets=["EMBER2018","EMBER2024"]
cells=[]
provenance={"inputs":{},"operation":"descriptive aggregation of locked artifacts; no model/threshold changes"}
for name in ("configs/primary_protocol.json","configs/primary_execution.json",
             "data/primary/EMBER2018/protocol_v2/roles.json","data/primary/EMBER2024/protocol_v2/roles.json",
             "outputs/primary_review/review_2026_10_07/review.json","requirements-lock.txt"):
    provenance["inputs"][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
for p in sorted((ROOT/"outputs/primary").glob("*/protocol_v2/seed_*/*/rate_*/result.json")):
    c=json.loads(p.read_text(encoding="utf-8"))
    assert c["status"]=="complete"
    c["_path"]=p
    cells.append(c)
    provenance["inputs"][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
assert len(cells)==54
review=json.loads((ROOT/"outputs/primary_review/review_2026_10_07/review.json").read_text(encoding="utf-8"))

def mdtable(headers,rows):
    return "\n".join(["| "+" | ".join(headers)+" |","|"+"---|"*len(headers)]+["| "+" | ".join(map(str,row))+" |" for row in rows])
def pct(x): return f"{100*x:.2f}"
def avg(cs,func):return float(np.mean([func(c) for c in cs]))
def ev(c):return c["evaluation"]["results"]["reduced"]
def method(c,m):return c["evaluation"]["results"]["full"]["methods"][m]
groups={(d,f):[c for c in cells if c["dataset"]==d and c["family"]==f] for d in datasets for f in families}
confirmed={key:[c for c in cs if c["independently_confirmed_strong_and_stealth"]] for key,cs in groups.items()}
tables={}
tables["POOLS"]=mdtable(["Role","Total","Benign","Malware"],[
    ["Fit","200,000","100,000","100,000"],["Selection","10,000","5,000","5,000"],
    ["Development","10,000","5,000","5,000"],["Confirmation","10,000","5,000","5,000"],
    ["Reference","500","500","0"],["Calibration","2,000","2,000","0"],
    ["Final","20,000","10,000","10,000"]])
tables["SETTINGS"]=mdtable(["Setting","Value"],[
    ["Main / view rounds","500 / 150"],["Leaves / learning rate","64 / 0.05"],
    ["Max bin","255"],["Feature / bagging fraction","0.9 / 0.9"],["Bagging frequency","1"],
    ["Threads / scoring batch","4 / 128"],["Seeds","17, 29, 43"],
    ["STRIP N / alpha","50 / 0.5"],["Malware threshold","0.5"],
    ["Calibration FPR target","1%"],["Bootstrap repeats","1,000"],["Latency samples per run","100"]])
attack=[]
for d in datasets:
    for f in families:
        cs=groups[d,f]
        attack.append([d[-4:]+" "+short[f],pct(avg(cs,lambda c:ev(c)["asr_eligible"]["rate"])),
                       pct(avg(cs,lambda c:ev(c)["clean_trigger_asr_eligible"]["rate"])),f"{len(confirmed[d,f])}/9"])
tables["ATTACK"]=mdtable(["Dataset / family","ASR %","Control %","Pass"],attack)
keys=[("EMBER2018",families[0]),("EMBER2018",families[1]),("EMBER2024",families[1]),("EMBER2024",families[2])]
methods=[("TADR","TADR"),("STRIP","STRIP"),("M3","M3_view_mass"),("M4-R","M4_shap_behavioral_conflict"),
         ("M4-F","M4_prob_gap"),("X-R","X_primary_reduced"),("X-F","X_primary_full")]
tables["FAMILY_AUC"]=mdtable(["Method","18 Conc.","18 Spread","24 Spread","24 Cross"],[
    [label]+[pct(avg(confirmed[k],lambda c:method(c,m)["auroc_trigger_vs_benign"])) for k in keys] for label,m in methods])
for d in datasets:
    cs=[c for c in cells if c["dataset"]==d and c["independently_confirmed_strong_and_stealth"]]
    rows=[]
    for label,m in [methods[i] for i in [0,1,5,6]]:
        data=review["summaries"][d]["confirmed_only"][m]
        values=[pct(avg(cs,lambda c: method(c,m)[k]["rate"] if k!="auroc_trigger_vs_benign" else method(c,m)[k]))
                for k in ("auroc_trigger_vs_benign","recall_successful_eligible","benign_fpr","post_defense_asr")]
        for k,val in zip(("auroc_trigger_vs_benign","recall_successful_eligible","benign_fpr","post_defense_asr"),values):
            actual=avg(cs,lambda c: method(c,m)[k]["rate"] if k!="auroc_trigger_vs_benign" else method(c,m)[k])
            assert abs(actual-data[k]["mean"])<1e-12
        rows.append([label]+values)
    tables[d]=mdtable(["Method","AUC %","Recall %","FPR %","Post-ASR %"],rows)

examples=[]
for d,f in [("EMBER2018",families[1]),("EMBER2024",families[2])]:
    c=next(c for c in cells if c["dataset"]==d and c["family"]==f and c["seed"]==17 and c["rate"]==.01)
    nfile=c["_path"].parent/next(k for k in c["artifact_sha256"] if k.startswith("paired_predictions"))
    assert hashlib.sha256(nfile.read_bytes()).hexdigest()==c["artifact_sha256"][nfile.name]
    n=np.load(nfile,allow_pickle=False)
    success=(n["clean_malware_p"]>=.5)&(n["triggered_main_p"]<.5)
    a=n["full_trigger_TADR"]>method(c,"TADR")["threshold"]
    b=n["full_trigger_M4_prob_gap"]>method(c,"M4_prob_gap")["threshold"]
    counts=[int(np.sum(success&mask)) for mask in (a&b,a&~b,~a&b,~a&~b)]
    assert sum(counts)==ev(c)["n_successful_eligible"]
    examples.append({"dataset":d,"family":f,"seed":17,"rate":.01,"counts":counts,"cell":c})
tables["PAIRED"]=mdtable(["Example","Both","TADR only","M4-F only","Neither"],[[e["dataset"][-4:]+" "+short[e["family"]]]+e["counts"] for e in examples])
tables["CASE_METRICS"]=mdtable(["Metric","2018 Spread","2024 Cross"],[
    ["Eligible malware"]+[ev(e["cell"])["n_eligible"] for e in examples],
    ["Successful attacks"]+[ev(e["cell"])["n_successful_eligible"] for e in examples],
    ["ASR %"]+[pct(ev(e["cell"])["asr_eligible"]["rate"]) for e in examples],
    ["Clean-trigger control %"]+[pct(ev(e["cell"])["clean_trigger_asr_eligible"]["rate"]) for e in examples],
    ["Clean / poisoned accuracy %"]+[pct(e["cell"]["clean_performance"]["accuracy"])+" / "+pct(e["cell"]["poisoned_clean_performance"]["accuracy"]) for e in examples]])
tables["ABLATION"]=mdtable(["Difference (pp)","2018 Spread","2024 Cross"],[
    [label]+[f'{100*e["cell"]["evaluation"]["paired_comparison"][key]["difference"]:+.2f} ['+
             ", ".join(f"{100*x:+.2f}" for x in e["cell"]["evaluation"]["paired_comparison"][key]["ci95"])+"]" for e in examples]
    for label,key in [("AUROC","auroc_full_minus_reduced"),("Recall","recall_successful_full_minus_reduced"),
                      ("FPR","benign_fpr_full_minus_reduced"),("Post-defense ASR","post_defense_asr_full_minus_reduced")]])
runtime=[]
for d in datasets:
    cs=[c for c in cells if c["dataset"]==d]
    for v in ("reduced","full"):
        runtime.append([d[-4:]+(" R" if v=="reduced" else " F")]+[
            f'{avg(cs,lambda c:c["resources"]["latency"][v][k]):.2f}' for k in ("mean_ms","median_ms","p95_ms")]+[
            f'{avg(cs,lambda c:c["resources"]["model_bytes"][v])/1048576:.2f}'])
tables["RUNTIME"]=mdtable(["Variant","Mean ms","Median ms","P95 ms","MiB"],runtime)

if "--plots-only" in sys.argv:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family":"DejaVu Serif","font.size":9,"axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(2,1,figsize=(3.7,4.6),sharey=True)
    for ax,d in zip(axes,datasets):
        asr=[avg(groups[d,f],lambda c:ev(c)["asr_eligible"]["rate"])*100 for f in families]
        ctrl=[avg(groups[d,f],lambda c:ev(c)["clean_trigger_asr_eligible"]["rate"])*100 for f in families]
        x=np.arange(3)
        ax.bar(x-.18,asr,.36,label="Poisoned model",color="#273f65")
        ax.bar(x+.18,ctrl,.36,label="Clean-trigger control",color="#a6b4c5")
        ax.set_xticks(x,[short[f]+f"\nPass {len(confirmed[d,f])}/9" for f in families]);ax.set_title(d);ax.set_ylim(0,110);ax.grid(axis="y",alpha=.2)
    for ax in axes: ax.set_ylabel("Eligible evasion rate (%)")
    axes[0].legend(loc="upper left",fontsize=7)
    fig.tight_layout();fig.savefig(FIG/"attack_controls.png",dpi=240);plt.close(fig)
    c=examples[0]["cell"]
    path=c["_path"].parent/"paired_predictions.npz"
    n=np.load(path,allow_pickle=False)
    fig,ax=plt.subplots(figsize=(4.0,2.7))
    ax.hist(n["full_benign_TADR"],bins=45,density=True,histtype="step",linewidth=1.3,color="#50775b",label="Benign, poisoned model")
    ax.hist(n["full_trigger_TADR"],bins=45,density=True,histtype="step",linewidth=1.3,color="#273f65",label="Triggered, poisoned model")
    ax.axvline(method(c,"TADR")["threshold"],ls="--",color="#9d362b",label="Locked threshold")
    ax.set_xlabel("TADR score");ax.set_ylabel("Density");ax.legend(fontsize=6.5);fig.tight_layout()
    fig.savefig(FIG/"tadr_partial_control.png",dpi=240);plt.close(fig)
    sys.exit(0)
else:
    import subprocess
    subprocess.run([str(ROOT/".venv/Scripts/python.exe"),str(Path(__file__).resolve()),"--plots-only"],check=True)

source=(ROOT/"scripts/sections_5_6_manuscript.md").read_text(encoding="utf-8")
for key,value in tables.items():source=source.replace("<<"+key+">>",value)
assert "<<" not in source
(OUT/"X_SENTINEL_Sections_5_6_EN.md").write_text(source,encoding="utf-8")
provenance["tables"]=tables
provenance["paired_examples"]=[{k:v for k,v in e.items() if k!="cell"} for e in examples]
provenance["aggregation"]="Equal-weight per-run means; no pooling across seeds; confirmed-only cohorts defined before final scoring"
(OUT/"X_SENTINEL_Sections_5_6_Provenance.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding="utf-8")

from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("SectionTimes","C:/Windows/Fonts/times.ttf"))
pdfmetrics.registerFont(TTFont("SectionTimesBold","C:/Windows/Fonts/timesbd.ttf"))
styles={"title":ParagraphStyle("title",fontName="SectionTimesBold",fontSize=15,leading=18,spaceAfter=9),
        "h2":ParagraphStyle("h2",fontName="SectionTimesBold",fontSize=12,leading=14,spaceBefore=9,spaceAfter=6,keepWithNext=True),
        "h3":ParagraphStyle("h3",fontName="SectionTimesBold",fontSize=10.4,leading=12.5,spaceBefore=7,spaceAfter=4,keepWithNext=True),
        "body":ParagraphStyle("body",fontName="SectionTimes",fontSize=10,leading=12.4,spaceAfter=7,allowWidows=0,allowOrphans=0),
        "caption":ParagraphStyle("caption",fontName="SectionTimes",fontSize=8.4,leading=10.3,spaceAfter=5,keepWithNext=True),
        "cell":ParagraphStyle("cell",fontName="SectionTimes",fontSize=7.7,leading=9.4),
        "head":ParagraphStyle("head",fontName="SectionTimesBold",fontSize=7.7,leading=9.4)}
W,H=A4;margin=38;gap=18;cw=(W-2*margin-gap)/2
frames=[Frame(margin,43,cw,H-81,id="left",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),
        Frame(margin+cw+gap,43,cw,H-81,id="right",leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)]
def footer(canvas,doc):
    canvas.setFont("SectionTimes",8);canvas.drawString(margin,24,"X-SENTINEL | Experimental Setup and Results")
    canvas.drawRightString(W-margin,24,str(doc.page))
def paragraph(s,kind="body"):return Paragraph(escape(s),styles[kind])
def make_table(lines):
    rows=[[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    rows=[r for r in rows if not all(re.fullmatch(r"[: -]+",c) for c in r)]
    n=len(rows[0]);weights=[.32]+[(.68)/(n-1)]*(n-1) if n>2 else [.55,.45]
    if rows[0][0]=="Difference (pp)":weights=[.30,.35,.35]
    if rows[0][0]=="Metric":weights=[.40,.30,.30]
    t=Table([[paragraph(c,"head" if i==0 else "cell") for c in r] for i,r in enumerate(rows)],
            colWidths=[cw*x for x in weights],repeatRows=1,hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eeeeee")),
                          ("LINEABOVE",(0,0),(-1,0),.6,colors.black),("LINEBELOW",(0,0),(-1,0),.5,colors.black),
                          ("LINEBELOW",(0,-1),(-1,-1),.6,colors.black),
                          ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
                          ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    return t
story=[];lines=source.splitlines();i=0
while i<len(lines):
    s=lines[i].strip();i+=1
    if not s:continue
    if s.startswith("|"):
        tab=[s]
        while i<len(lines) and lines[i].strip().startswith("|"):tab.append(lines[i].strip());i+=1
        story.extend([make_table(tab),Spacer(1,7)]);continue
    if s.startswith("!["):
        name=s.split("](",1)[1][:-1];p=OUT/name
        from PIL import Image as PILImage
        w,h=PILImage.open(p).size
        story.extend([Image(str(p),width=cw,height=cw*h/w),Spacer(1,5)]);continue
    if s.startswith("### "):story.append(paragraph(s[4:],"h3"))
    elif s.startswith("## "):story.append(paragraph(s[3:],"h2"))
    elif s.startswith("# "):story.append(paragraph(s[2:],"title"))
    elif s.startswith(("Table ","Figure ")):story.append(paragraph(s,"caption"))
    else:story.append(paragraph(s))
doc=BaseDocTemplate(str(OUT/"X_SENTINEL_Sections_5_6_EN.pdf"),pagesize=A4,title="X-SENTINEL Experimental Setup and Results",author="Group 4")
doc.addPageTemplates(PageTemplate(id="paper",frames=frames,onPage=footer))
doc.build(story)
print(OUT/"X_SENTINEL_Sections_5_6_EN.pdf")
print("PAIRED COUNTS",[{k:v for k,v in e.items() if k!="cell"} for e in examples])
