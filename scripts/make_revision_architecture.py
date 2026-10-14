"""Draw the implemented score path rather than reusing the broken report image."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
out=Path('outputs/revision_2026_10_13/analysis/figures')
fig,ax=plt.subplots(figsize=(10,4.8));ax.set_xlim(0,10);ax.set_ylim(0,4.8);ax.axis('off')
def node(x,y,w,h,text,color='#eef2f6'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.06',edgecolor='#5d6977',facecolor=color,linewidth=1))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
def arrow(a,b,label=None):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,color='#3d4856',linewidth=1.2))
    if label:ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.13,label,ha='center',fontsize=8)
node(.15,2.5,1.45,.8,'Versioned\nPE feature vector')
node(2.0,2.5,1.65,.8,'Suspicious main\nprobability + SHAP')
node(4.1,3.6,1.65,.65,'M3\nabsolute view mass')
node(4.1,2.45,1.65,.7,'M4R\ngated Behavioral SHAP')
node(2.0,.7,1.65,.8,'Clean Behavioral\nmodel in full only')
node(4.1,.7,1.65,.8,'M4F\npositive probability gap')
node(6.25,2.4,1.65,.85,'Benign reference ranks\nXR: M3 and M4R\nXF: M3 and M4F')
node(8.35,2.4,1.45,.85,'Strict score > tau\nsuspicion alert')
node(6.25,.7,1.65,.8,'Separate benign\ncalibration for tau')
arrow((1.6,2.9),(2,2.9));arrow((3.65,3.1),(4.1,3.8));arrow((3.65,2.8),(4.1,2.8))
arrow((1.3,2.5),(2,.95));arrow((3.65,1.1),(4.1,1.1));arrow((3.35,2.5),(4.35,1.5))
arrow((5.75,3.85),(6.25,3.05));arrow((5.75,2.8),(6.25,2.8));arrow((5.75,1.1),(6.25,2.5))
arrow((7.9,2.8),(8.35,2.8));arrow((7.9,1.1),(8.75,2.4))
ax.text(5,.1,'Prediction and alert are separate outputs. Views are static features; alerts are suspicion signals.',ha='center',fontsize=9)
fig.tight_layout();fig.savefig(out/'implemented_score_path.png',dpi=300,bbox_inches='tight');fig.savefig(out/'implemented_score_path.pdf',bbox_inches='tight');plt.close(fig)
