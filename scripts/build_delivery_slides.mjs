import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const root=process.cwd();
const skill='C:/Users/win9tui/.codex/plugins/cache/openai-primary-runtime/presentations/26.1011.11113/skills/presentations';
const python='C:/Users/win9tui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
process.env.RUNTIME_NODE_MODULES='C:/Users/win9tui/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const evidence=process.argv[2];
if(!evidence) throw new Error('Supply the verified evidence directory');
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const verification=await read(path.join(evidence,'verification.json'));
const restore=await read(path.join(evidence,'restore.json'));
const before=await read('outputs/delivery_2026_10_14/before/baseline.json');
const after=await read(path.join(evidence,'after/baseline.json'));
const out=path.join(root,'output/delivery_2026_10_14');
const stage=path.join(root,'tmp/delivery_slides');
await fs.mkdir(stage,{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
p.theme.defaultFont='Arial';
const teal='#087F8C', dark='#172B4D', gray='#42536A';
function text(s,t,x,y,w,h,size=30,color=dark,bold=false){
 const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=t;a.text.style={typeface:'Arial',fontSize:size,color,bold};return a;
}
function slide(title,notes){
 const s=p.slides.add();s.background.fill='#F7F9FC';
 text(s,title,64,50,1152,100,44,dark,true);
 s.speakerNotes.text=notes;
 text(s,String(p.slides.items.length),1170,664,46,32,23,gray);return s;
}
let s=p.slides.add();s.background.fill='#F7F9FC';
text(s,'X-SENTINEL',64,155,1152,110,72,dark,true);
text(s,'Demo phân tích PE',64,300,1152,80,44,teal);
text(s,'Bản triển khai ngày 14/10/2026',64,455,1152,55,30,gray);
s.speakerNotes.text='Giới thiệu giao diện và luồng triển khai hiện tại. Không trình bày demo sản phẩm như bằng chứng tăng tỷ lệ phát hiện. Báo cáo nghiên cứu vẫn dựa trên các mô hình và ngưỡng đã cố định.';
s=slide('Phân loại file và cảnh báo trigger','Nguồn: src/xsentinel/dashboard_presentation.py và kết quả Detector.predict hiện hành. Cảnh báo trigger dựa trên phương pháp đang chọn, không phải OR của tất cả phương pháp.');
text(s,'Mô hình phân loại',64,180,520,58,34,teal,true);
text(s,'Dự đoán file lành hoặc mã độc.\nĐiểm dự đoán không bảo đảm thực tế.',64,258,520,150,30);
text(s,'Dấu hiệu trigger',690,180,526,58,34,teal,true);
text(s,'Điểm vượt ngưỡng cố định thì cảnh báo.\nChưa cảnh báo vẫn cần xem xét file.',690,258,526,150,30);
text(s,'Ví dụ: dự đoán lành + có cảnh báo → xem xét cả hai kết quả.',64,510,1152,100,30,dark,true);
s=slide('Kết quả trên giao diện','Ảnh chụp trình duyệt thật từ bản triển khai ngày 14/10/2026. Dùng fixture lành do nhóm kiểm soát, chỉ đọc file và không chạy binary. V3 dự đoán mã độc cho fixture lành: đây là một ca phân loại nhầm, không phải phát hiện malware.');
s.images.add({blob:await fs.readFile(path.join(out,'ui_result.jpg')),contentType:'image/jpeg',alt:'Giao diện phân tích PE thực tế',fit:'contain',position:{left:64,top:162,width:1152,height:480}});
s=slide('Giải thích bằng kết quả đã tính','Nguồn: dashboard/app.py, dashboard_presentation.py; các bài kiểm tra xác nhận bật chi tiết không gọi predict lần nữa. Behavioral dùng đặc trưng import/export tĩnh, không phải hành vi khi chạy.');
text(s,'Điểm và ngưỡng',64,180,1120,58,34,teal,true);
text(s,'So sánh đúng phương pháp đã chọn; giữ ngưỡng đã kiểm chứng.',64,246,1120,70,30);
text(s,'SHAP và nhóm đặc trưng',64,345,1120,58,34,teal,true);
text(s,'Structural: cấu trúc PE. Behavioral: import/export.\nMetadata: byte, entropy và chuỗi trong file.',64,411,1120,105,30);
text(s,'Mở chi tiết dùng lại kết quả; không chạy mô hình thêm.',64,560,1120,70,30,dark,true);
s=slide('Thời gian tính điểm trước và sau','Nguồn: outputs/delivery_2026_10_14/before/baseline.json và thư mục evidence after/baseline.json. Mỗi cấu hình đo 11 đầu vào sau warm-up, một fixture và 10 vector reference. Không thay cho ma trận nghiên cứu, không kết luận tăng tốc từ mẫu nhỏ.');
const values=[['Cấu hình','Trước (ms)','Sau (ms)'],...before.cases.map((v,i)=>[`${v.dataset} / ${v.variant}`,v.predict_mean_ms.toFixed(2),after.cases[i].predict_mean_ms.toFixed(2)])];
const t=s.tables.add({rows:5,columns:3,left:64,top:170,width:1152,height:315,columnWidths:[632,260,260],values});
t.borders.assign({fill:'#CBD5E1',width:1});
for(let r=0;r<5;r++)for(let c=0;c<3;c++){
 const cell=t.getCell(r,c);cell.fill=r===0?teal:'#FFFFFF';cell.text.style={typeface:'Arial',fontSize:27,color:r===0?'#FFFFFF':dark,bold:r===0};
}
text(s,'44 đầu vào kiểm tra. Không gồm upload và hiển thị trình duyệt.',64,520,1152,63,27,gray);
text(s,'Mục tiêu nghiên cứu 10 ms vẫn chưa đạt.',64,600,1152,58,30,dark,true);
s=slide('Lịch sử và phục hồi dữ liệu',`Nguồn: ${evidence}/restore.json. Mọi bảng so sánh số dòng và SHA-256 của hàng canonical; API lịch sử và ${restore.api_details_checked} chi tiết khớp. Không ghi đè DB đang dùng.`);
s.images.add({blob:await fs.readFile(path.join(out,'ui_history.jpg')),contentType:'image/jpeg',alt:'Trang lịch sử thực tế',fit:'contain',position:{left:64,top:155,width:860,height:430}});
text(s,'Tên file\nDung lượng\nLoại đầu vào\nSHA-256',950,195,266,245,28,gray);
text(s,'Backup đã khôi phục khớp vào database thử riêng.',64,607,1152,56,30,dark,true);
s=slide('Phạm vi và bước nghiệm thu còn lại','Nguồn: kế hoạch chung đã duyệt và yêu cầu người dùng. Máy vật lý thứ hai được hoãn tới 15/10/2026. Authentication, M5 và thí nghiệm mới là nhánh có điều kiện. V2/V3 extraction thành công không chứng minh tấn công binary thực có tính khả thi.');
text(s,'Đã kiểm tra',64,175,520,60,34,teal,true);
text(s,`66 bài kiểm tra qua.\n${verification.frozen_primary_files_checked_unchanged} file primary giữ nguyên.\nUpload tối đa 50 MiB.`,64,255,540,185,30);
text(s,'Còn cần kiểm chứng',690,175,526,60,34,teal,true);
text(s,'Máy bạn nhóm: 15/10.\nMalware binary thật: chưa chứng minh.\nAuth / M5: cần quyết định riêng.',690,255,526,185,30);
text(s,'Giao diện rõ hơn không làm tỷ lệ phát hiện tự tăng.',64,540,1152,80,30,dark,true);
const candidate=path.join(stage,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(out,'X_SENTINEL_Demo_Reviewed.pptx'),pythonExecutable:python,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--validate-heading-punctuation','--validate-bullet-geometry','--require-native-table-slide','5'],
 requiredNativeTableOwnerSlides:[5],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
 receiptPath:path.join(stage,'validation_reviewed.json')});
for(const [i,sl] of p.slides.items.entries()){
 const blob=await p.export({slide:sl,format:'png',scale:1});await fs.writeFile(path.join(stage,`slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
}
console.log('Saved verified demo slides');
