// Native editable English deck using bundled Artifact Tool.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const runtime='C:/Users/win9tui/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
process.env.RUNTIME_PYTHON=runtime+'/python/python.exe';
const skill='C:/Users/win9tui/.codex/plugins/cache/openai-primary-runtime/presentations/26.930.11008/skills/presentations';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'));
const {resolvePresentationFont,applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs'));
const root=process.cwd(), build=path.join(root,'tmp/slides'), output=path.join(root,'outputs/pilot_verified');
await fs.mkdir(build,{recursive:true});
const e=JSON.parse(await fs.readFile(path.join(output,'seed_17/concentrated_0.01/evaluation/evaluation.json'),'utf8'));
const family=resolvePresentationFont(); const deck=Presentation.create({slideSize:{width:1280,height:720}});
function text(slide,content,left,top,width,height,size,bold=false,color='#15263C'){
 const shape=slide.shapes.add({geometry:'textbox',position:{left,top,width,height},fill:'none',line:{fill:'none',width:0}});
 shape.text=content; shape.text.style={typeface:family,fontSize:size,bold,color,autoFit:'none'}; return shape;
}
const slides=[];
function page(title,body,notes=''){
 const slide=deck.slides.add(); slide.background.fill='#FFFFFF';
 text(slide,title,72,48,1136,100,46,true);
 if(body) text(slide,body,72,178,1110,440,28);
 slide.speakerNotes.textFrame.setText(notes); slides.push(slide); return slide;
}
page('X-SENTINEL','Cross-view backdoor suspicion at inference\n\nImplementation and pilot evidence\nGroup 4  ·  IAM302T  ·  4 October 2026',
 'Design sources: instructor PDF, baseline specification and approved handoff in project root. This deck reports a pilot, not completed final experiments.');
page('Malware classification and trigger suspicion',
 'Main classifier estimates the probability of malware.\n\nThe detector scores evidence that an input may carry a trigger.\n\nPASS means the detector did not exceed its locked threshold.\n\nFull detection requires clean-trained view classifiers.',
 'Source: docs/METHOD_SPEC.md. Clean-model controls belong to evaluation, never detector inputs.');
page('Data and blind protocol',
 'Verified official data: 600,000 labeled train and 200,000 test.\n\nNo duplicate SHA256 within or across official partitions.\n\nOfficial benign test split: 500 reference, 2,000 calibration,\n97,500 final benign. Malware final test: 100,000.\n\nTrain data alone determine trigger features and values.',
 'Source: data/ember2018_full/dataset.json and splits.json. These are full data counts, distinct from the pilot training/evaluation sizes.');
page('Baseline and cross-view scores',
 'TADR: largest absolute feature SHAP share.\nSTRIP: one minus mean binary entropy across 50 blends.\n\nM3: largest absolute attribution share of a semantic view.\nM4 reduced: benign probability × positive behavioral SHAP share.\nM4 full: benign probability × behavioral malware probability.\n\nReference ranks combine M3 and M4 with equal weights.',
 'Sources: docs/METHOD_SPEC.md; https://github.com/elastic/ember/blob/master/ember/features.py; https://arxiv.org/abs/1902.06531 .');
page('Semantic and attack limitations',
 'Limited M5 combines rare printable-distribution values with\nbenign-directed attribution dominance above 80%.\nThe group-only detector cannot confirm sensitive API/string evidence.\n\nSeveri feasible features do not cover Behavioral hashed buckets.\nA three-view vector stress test requires a distinct profile.\n\nVector interventions do not prove PE realizability.',
 'Sources: configs/semantic_rules.json, docs/upstream/severi_data_utils.py and severi_ember_feature_utils.py. Original code uses EMBER v1 and a different string-feature name order.');
page('Pilot attack remains weak',
 `Pilot training: 9,337 labeled observations.\nOne seed, concentrated trigger, 1% poisoning.\n\nAttack succeeded on ${e.attack_asr.count} of ${e.attack_asr.n} eligible malware.\nASR: ${(100*e.attack_asr.rate).toFixed(1)}%\nWilson 95% interval: ${(100*e.attack_asr.wilson95[0]).toFixed(1)}% to ${(100*e.attack_asr.wilson95[1]).toFixed(1)}%\n\nThese results establish pipeline execution. Defense efficacy\nagainst a strong backdoor remains unresolved.`,
 'Source: outputs/pilot_verified/seed_17/concentrated_0.01/evaluation/evaluation.json. Evaluation randomly selects 100 benign and 100 malware pilot observations, of which 87 are clean-model eligible.');
const chartSlide=page('Pilot AUROC across selected methods',null,
 'Source: outputs/pilot_verified/seed_17/concentrated_0.01/evaluation/evaluation.json. Trigger versus benign. Weak attack and small pilot pools prevent final defense claims.');
const methods=['TADR','STRIP','M3','M4_reduced','M4_full','X_reduced','X_full'];
const chart=chartSlide.charts.add('bar',{position:{left:80,top:165,width:1110,height:390},categories:methods,
 series:[{name:'AUROC',values:methods.map(k=>Number(e.metrics[k].auroc_trigger_vs_benign.toFixed(4))),fill:'#315F87'}],
 barOptions:{direction:'column',grouping:'clustered'},hasLegend:false,
 yAxis:{visible:true,min:0,max:1,numberFormatCode:'0.0',majorUnit:0.2,textStyle:{fontSize:18}},
 xAxis:{visible:true,textStyle:{fontSize:18}},dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:22}}});
applyPresentationChartFont(chart,{fontFamily:family});
for(let i=0;i<methods.length;i++){
 const label=chart.series.getItemAt(0).dataLabelOverrides.add(i);
 label.text=e.metrics[methods[i]].auroc_trigger_vs_benign.toFixed(4); label.position='outEnd'; label.textStyle.fontSize=22; label.textStyle.typeface=family;
}
text(chartSlide,'Trigger versus benign on a small pilot with weak attack efficacy',80,590,1110,75,26);
page('Reproduction and remaining validation',
 'Data preparation, detection, evaluation and dashboard run locally.\n13 tests pass. Locked models and thresholds support resume.\n\nThe 27-model research configuration is ready to run.\nOfficial attack viability and final detector evidence remain pending.\n\nDocker image build needs a Docker-enabled machine.\nModern LIEF extraction needs paired legacy compatibility validation.',
 'Source: docs/IMPLEMENTATION_STATUS.md and README.md. GitHub remote and Drive model-sharing URLs remain unconfigured.');
const candidate=path.join(build,'candidate.pptx'); await (await PresentationFile.exportPptx(deck)).save(candidate);
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(output,'X_SENTINEL_Pilot_v3.pptx'),
 pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',
 layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 requiredNativeChartOwnerSlides:[7],requiredNativeTableOwnerSlides:[],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[family]},
 verifyArtifactToolImport:true,receiptPath:path.join(build,'validation-v3.json')});
for(let i=0;i<slides.length;i++){
 const png=await deck.export({slide:slides[i],format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));
}
console.log('Final editable deck created:',path.join(output,'X_SENTINEL_Pilot_v3.pptx'));
