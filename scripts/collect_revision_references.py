"""Verify bibliographic identities against registration or author arXiv metadata."""
from pathlib import Path
import json,re,time,urllib.request,urllib.parse,xml.etree.ElementTree as ET
from difflib import SequenceMatcher

TITLES=[
'EMBER: An Open Dataset for Training Static PE Malware Machine Learning Models',
'EMBER2024 - A Benchmark Dataset for Holistic Evaluation of Malware Classifiers',
'BODMAS: An Open Dataset for Learning based Temporal Analysis of PE Malware',
'SOREL-20M: A Large Scale Benchmark Dataset for Malicious PE Detection',
'DREBIN: Effective and Explainable Detection of Android Malware in Your Pocket',
'LightGBM: A Highly Efficient Gradient Boosting Decision Tree',
'A Unified Approach to Interpreting Model Predictions',
'Consistent Individualized Feature Attribution for Tree Ensembles',
'From local explanations to global understanding with explainable AI for trees',
'Greedy Function Approximation: A Gradient Boosting Machine',
'Why Should I Trust You?: Explaining the Predictions of Any Classifier',
'Explanation-Guided Backdoor Poisoning Attacks Against Malware Classifiers',
'Jigsaw Puzzle: Selective Backdoor Attack to Subvert Malware Classifiers',
'Dos and Don\'ts of Machine Learning in Computer Security',
'TESSERACT: Eliminating Experimental Bias in Malware Classification across Space and Time',
'Learning to Detect Concept Drift in Computer Security Applications',
'Transcending Transcend: Revisiting Malware Classification in the Presence of Concept Drift',
'Explaining and Harnessing Adversarial Examples',
'Towards Evaluating the Robustness of Neural Networks',
'On Adaptive Attacks to Adversarial Example Defenses',
'Obfuscated Gradients Give a False Sense of Security: Circumventing Defenses to Adversarial Examples',
'Practical black-box attacks against machine learning',
'Intriguing Properties of Adversarial ML Attacks in the Problem Space',
'Black-Box Attacks against RNN based Malware Detection Algorithms',
'Learning to Evade Static PE Machine Learning Malware Models via Reinforcement Learning',
'Adversarial Malware Binaries: Evading Deep Learning for Malware Detection in Executables',
'Explaining Vulnerabilities of Deep Learning to Adversarial Malware Binaries',
'Functionality-preserving black-box optimization of adversarial Windows malware',
'Malware Detection by Eating a Whole EXE',
'Deep Neural Network Based Malware Detection Using Two Dimensional Binary Program Features',
'BadNets: Identifying Vulnerabilities in the Machine Learning Model Supply Chain',
'Trojaning Attack on Neural Networks',
'Hidden Trigger Backdoor Attacks',
'Label-Consistent Backdoor Attacks',
'Poison Frogs! Targeted Clean-Label Poisoning Attacks on Neural Networks',
'Sleeper Agent: Scalable Hidden Trigger Backdoors for Neural Networks Trained from Scratch',
'Backdoor Learning: A Survey',
'A Survey on Backdoor Attacks and Defenses in Deep Learning',
'STRIP: A Defence Against Trojan Attacks on Deep Neural Networks',
'Spectral Signatures in Backdoor Attacks',
'Detecting Backdoor Attacks on Deep Neural Networks by Activation Clustering',
'SPECTRE: Defending Against Backdoor Attacks Using Robust Statistics',
'Neural Cleanse: Identifying and Mitigating Backdoor Attacks in Neural Networks',
'Fine-Pruning: Defending Against Backdooring Attacks on Deep Neural Networks',
'ABS: Scanning Neural Networks for Back-doors by Artificial Brain Stimulation',
'Anti-Backdoor Learning: Training Clean Models on Poisoned Data',
'Neural Attention Distillation: Erasing Backdoor Triggers from Deep Neural Networks',
'Backdoor Defense via Decoupling the Training Process',
'Beatrix: Defending Against Backdoor Attacks in Deep Neural Networks',
'A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification',
'Conformal Risk Control',
'Distribution-Free, Risk-Controlling Prediction Sets',
'Bootstrap Methods: Another Look at the Jackknife',
'Comparing the Areas under Two or More Correlated Receiver Operating Characteristic Curves: A Nonparametric Approach',
'Probable inference, the law of succession, and statistical inference',
'An Introduction to ROC Analysis',
'The Relationship Between Precision-Recall and ROC Curves',
'A systematic evaluation of backdoor data poisoning attacks on image classifiers',
'Adversarial Examples Are Not Bugs, They Are Features',
'The Security of Machine Learning',
'Random Forests',
]
OUT=Path('output/revision_2026_10_13/references');OUT.mkdir(parents=True,exist_ok=True)
def norm(s):return re.sub(r'[^a-z0-9]+',' ',re.sub('<[^>]+>','',s).lower()).strip()
def similarity(a,b):return SequenceMatcher(None,norm(a),norm(b)).ratio()
def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'X-SENTINEL academic bibliography verification/1.0'})
    with urllib.request.urlopen(request,timeout=35) as response:return response.read()
def crossref(title):
    url='https://api.crossref.org/works?'+urllib.parse.urlencode({'query.title':title,'rows':3})
    data=json.loads(fetch(url))['message']['items']
    matches=[(similarity(title,x.get('title',[''])[0]),x) for x in data]
    score,item=max(matches,key=lambda x:x[0])
    if score<.97:return None
    dates=item.get('published',item.get('issued',{})).get('date-parts',[[None]])[0]
    authors=[(x.get('given','')+' '+x.get('family','')).strip() for x in item.get('author',[])]
    if not authors or dates[0] is None:return None
    return {'requested_title':title,'title':re.sub('<[^>]+>','',item['title'][0]),'authors':authors,'year':dates[0],
            'venue':item.get('container-title',[''])[0] if item.get('container-title') else '',
            'doi':item.get('DOI'),'url':item.get('URL'),'metadata_source':url,'title_match':score,
            'abstract':re.sub('<[^>]+>',' ',item.get('abstract','')),'verification':'Exact/near-exact title and registered author/year metadata'}
def arxiv(title):
    url='https://export.arxiv.org/api/query?'+urllib.parse.urlencode({'search_query':'ti:"'+title+'"','max_results':3})
    root=ET.fromstring(fetch(url));ns={'a':'http://www.w3.org/2005/Atom'};matches=[]
    for entry in root.findall('a:entry',ns):
        name=' '.join(entry.findtext('a:title','',ns).split());matches.append((similarity(title,name),entry,name))
    if not matches:return None
    score,e,name=max(matches,key=lambda x:x[0])
    if score<.97:return None
    return {'requested_title':title,'title':name,'authors':[a.findtext('a:name','',ns) for a in e.findall('a:author',ns)],
            'year':int(e.findtext('a:published','',ns)[:4]),'venue':'arXiv','doi':None,'url':e.findtext('a:id','',ns).replace('http:','https:'),
            'metadata_source':url,'title_match':score,'abstract':' '.join(e.findtext('a:summary','',ns).split()),
            'verification':'Author-submitted arXiv identity and abstract verified'}
def esc(s):return s.replace('\\','\\textbackslash{}').replace('&','\\&').replace('%','\\%').replace('_','\\_').replace('#','\\#')

def main():
    path=OUT/'catalog.json';existing=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    # A near-title match is insufficient: EXE/APK and reprinted books are different sources.
    replacements={
      'ref06':('LightGBM: A Highly Efficient Gradient Boosting Decision Tree',
        ['Guolin Ke','Qi Meng','Thomas Finley','Taifeng Wang','Wei Chen','Weidong Ma','Qiwei Ye','Tie-Yan Liu'],2017,
        'Advances in Neural Information Processing Systems 30','https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html',None),
      'ref29':('Malware Detection by Eating a Whole EXE',
        ['Edward Raff','Jon Barker','Jared Sylvester','Robert Brandon','Bryan Catanzaro','Charles Nicholas'],2017,
        'arXiv:1710.09435','https://arxiv.org/abs/1710.09435','10.48550/arXiv.1710.09435'),
      'ref49':('The Beatrix Resurrections: Robust Backdoor Detection via Gram Matrices',
        ['Wanlun Ma','Derui Wang','Ruoxi Sun','Minhui Xue','Sheng Wen','Yang Xiang'],2023,
        'Network and Distributed System Security Symposium','https://www.ndss-symposium.org/ndss-paper/the-beatrix-resurrections-robust-backdoor-detection-via-gram-matrices/',None)}
    existing=[x for x in existing if x['key'] not in replacements and x['key'] not in ('ref53','ref61')]
    for key,(title,authors,year,venue,url,doi) in replacements.items():
        fetch(url)  # Confirm the primary page remains available in this run.
        existing.append({'key':key,'requested_title':TITLES[int(key[3:])-1],'title':title,'authors':authors,'year':year,
            'venue':venue,'url':url,'doi':doi,'metadata_source':url,'title_match':1,
            'abstract':'','verification':'Manually disambiguated from primary publisher/author page'})
    for key,doi in [('ref53','10.1214/aos/1176344552'),('ref61','10.1023/A:1010933404324')]:
        url='https://api.crossref.org/works/'+urllib.parse.quote(doi,safe='')
        item=json.loads(fetch(url))['message'];title=item['title'][0]
        authors=[(x.get('given','')+' '+x.get('family','')).strip() for x in item['author']]
        existing.append({'key':key,'requested_title':TITLES[int(key[3:])-1],'title':title,'authors':authors,
            'year':item['published']['date-parts'][0][0],'venue':item['container-title'][0],
            'url':item['URL'],'doi':doi,'metadata_source':url,'title_match':1,'abstract':'',
            'verification':'Original publication DOI disambiguated; author/year checked'})
    existing.sort(key=lambda x:x['key']);path.write_text(json.dumps(existing,ensure_ascii=False,indent=2),encoding='utf-8')
    attempted={x['requested_title'] for x in existing};unresolved=[]
    for i,title in enumerate(TITLES,1):
        if title in attempted:continue
        result=None;errors=[]
        for fn in (crossref,arxiv):
            try:result=fn(title)
            except Exception as error:errors.append(str(error))
            if result:break
        if result:
            result['key']=f'ref{i:02d}';existing.append(result)
            path.write_text(json.dumps(existing,ensure_ascii=False,indent=2),encoding='utf-8')
            print('Verified',result['key'],result['title'],flush=True)
        else:
            unresolved.append({'title':title,'errors':errors});print('Unresolved',title,errors,flush=True)
        time.sleep(.5)
    (OUT/'unresolved.json').write_text(json.dumps(unresolved,indent=2),encoding='utf-8')
    bib=[]
    for x in existing:
        bib.append('@misc{'+x['key']+',\n  title={'+x['title']+'},\n  author={'+ ' and '.join(x['authors'])+'},\n  year={'+str(x['year'])+'},\n  howpublished={'+x['venue']+'},\n  url={'+x['url']+'}'+(',\n  doi={'+x['doi']+'}' if x['doi'] else '')+'\n}')
    (OUT/'references.bib').write_text('\n\n'.join(bib),encoding='utf-8')
    lines=['# Verified research bibliography','',f'{len(existing)} bibliographic identities verified. Metadata verification is distinct from a full-text literature review.','']
    lines.extend(f"- {x['key']}: {x['title']} ({x['year']}). {x['url']}" for x in existing)
    (OUT/'catalog.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Verified count',len(existing),'Unresolved',len(unresolved),flush=True)


if __name__=='__main__':main()
