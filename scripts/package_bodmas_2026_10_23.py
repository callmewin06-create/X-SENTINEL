"""Package reviewed BODMAS results and presentation notes, never raw samples."""
import csv
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'outputs/bodmas_2026_10_23'
OUT = ROOT / 'output/bodmas_2026_10_23'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(name):
    with (DATA / name).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    audit = json.loads((DATA / 'audit.json').read_text(encoding='utf8'))
    proof = json.loads((DATA / 'document_preservation.json').read_text(encoding='utf8'))
    checks = json.loads((DATA / 'validation.json').read_text(encoding='utf8'))
    assert checks['primary_hashes_and_paths_unchanged']
    assert sha(Path(proof['source'])) == proof['source_sha256']
    assert sha(Path(proof['output'])) == proof['output_sha256']
    assert sha(ROOT / 'BODMAS_RESULTS.zip') == audit['archive_sha256']
    main_records, benign = read_csv('main_records.csv'), read_csv('benign_control.csv')
    paired = read_csv('paired_main_results.csv')
    examples = [
        ('A', 'Malware khai báo, bốn cấu hình gọi MALWARE', next(r['file_sha256'] for r in paired
             if all(r[a + '_main_classification'] == 'MALWARE' and r[a + '_trigger_alert'] == 'False'
                    for a in ('2018_reduced', '2018_full', '2024_reduced', '2024_full')))),
        ('B', '2018 gọi BENIGN và có cảnh báo nghi trigger', next(r['file_sha256'] for r in paired
             if r['2018_reduced_trigger_alert'] == 'True')),
        ('C', 'File khai báo lành, 2024 gọi MALWARE', benign[0]['file_sha256']),
        ('D', 'File không qua kiểm tra header PE', next(r['file_sha256'] for r in paired
             if r['2018_reduced_scan_status'] != 'ok')),
    ]
    demo_rows, lines = [], [
        '# Hướng dẫn trình bày phần BODMAS', '',
        'Đây là minh họa bằng kết quả lưu sẵn do thành viên bàn giao từ lượt ngày 22/10/2026. '
        'Gói này không có binary malware để upload vào ứng dụng. Nhãn nguồn do người chạy khai báo; '
        'không biến chúng thành nhãn đã được xác minh độc lập.', '',
        '## Trình tự trình bày', '',
        '1. Mở bản Word có BODMAS, tới Appendix C ở trang 19–20.',
        '2. Nói rõ 200 file được dùng chung cho bốn cấu hình; 175 chấm được, 25 lỗi.',
        '3. Dùng các trường hợp dưới để giải thích hai kết luận: phân loại file và nghi ngờ trigger.',
        '4. Kết lại bằng giới hạn: chưa cấy trigger vào malware binary và chưa kiểm tra chức năng malware sau sửa.', '',
        'Các ví dụ được chọn có chủ đích sau khi có kết quả, chỉ dùng minh họa. '
        'Các bảng nghiên cứu vẫn giữ đủ 200 mẫu và mọi lỗi.', '',
    ]
    fields = ('dataset', 'variant', 'scan_status', 'main_classification', 'malware_probability',
              'score', 'threshold', 'trigger_alert', 'error_code', 'error')
    for case, purpose, file_hash in examples:
        records = [r for r in main_records + benign if r['file_sha256'] == file_hash]
        assert len(records) == 4
        lines.extend([f'## Trường hợp {case}', '', purpose + '.', '', f'SHA-256: `{file_hash}`', '',
                      '| Bộ model | Chế độ | Trạng thái | Phân loại | p malware | Cảnh báo trigger |',
                      '|---|---|---|---|---:|---|'])
        for r in records:
            demo_rows.append({'case': case, 'purpose': purpose, 'file_sha256': file_hash,
                              'relative_path': r['relative_path'], 'declared_label': r['declared_label'],
                              **{k: r[k] for k in fields}})
            probability = f"{float(r['malware_probability']):.6f}" if r['malware_probability'] else 'Chưa chấm'
            trigger = {'True': 'Có', 'False': 'Chưa', '': 'Chưa chấm'}[r['trigger_alert']]
            lines.append(f"| {r['dataset']} | {r['variant']} | {r['scan_status']} | {r['main_classification'] or 'Chưa chấm'} | {probability} | {trigger} |")
        explanation = {
            'A': 'Cách nói: Mô hình gọi file là mã độc nhưng chưa cảnh báo trigger. Hai đầu ra trả lời hai câu hỏi khác nhau.',
            'B': 'Cách nói: Với model 2018, dự đoán file lành và cảnh báo nghi trigger có thể xuất hiện cùng lúc. Chưa có nhãn trigger nên chưa thể kết luận file này thực sự chứa backdoor.',
            'C': 'Cách nói: File được khai báo lành này bị 2024 gọi mã độc. Đây là trường hợp báo nhầm so với nhãn khai báo; một file không cho biết tỷ lệ báo nhầm chung. Source/build của đúng hash này còn chưa được đối chiếu.',
            'D': 'Cách nói: File không qua kiểm tra chữ ký hoặc vị trí header PE. Hệ thống chưa đưa ra phân loại hay cảnh báo; file lỗi không được coi là file lành hoặc không có trigger.',
        }[case]
        lines.extend(['', explanation, ''])
    (OUT / 'HUONG_DAN_TRINH_BAY_BODMAS.md').write_text('\n'.join(lines), encoding='utf8')
    with (DATA / 'demo_cases.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(demo_rows[0]))
        writer.writeheader()
        writer.writerows(demo_rows)
    (OUT / 'README.md').write_text(
        '# BODMAS bàn giao ngày 23 tháng 10 năm 2026\n\n'
        'Bản Word đã có Appendix C trang 19–20. File gốc được giữ nguyên. '
        'Phần mới tổng hợp kết quả do thành viên cung cấp; không chấm lại binary.\n\n'
        'Trong gói ZIP: report/ có bản Word và nội dung tiếng Anh; data/ có CSV/JSON; '
        'HUONG_DAN_TRINH_BAY_BODMAS.md giải thích các ví dụ; input/ giữ ZIP kết quả gốc; '
        'reproduction/ chứa source các công cụ tổng hợp. Không có raw malware hoặc model weights.\n\n'
        'main_summary.csv có bốn cấu hình; main_records.csv có 800 dòng tương ứng 200 file × 4; '
        'paired_main_results.csv có 200 file; unique_errors.csv có 25 file lỗi duy nhất; '
        'alerts_by_configuration.csv có 4 dòng từ 2 file cảnh báo × 2 biến thể 2018; '
        'benign_control.csv có bốn dòng từ cùng một file lành; timing.csv dùng 175 file chấm được mỗi lượt.\n\n'
        'Tỷ lệ chấm được là 175/200 = 87,5%. 2018 gọi MALWARE 162/175, 2024 gọi MALWARE 175/175. '
        'Không dùng các số này để khẳng định độ chính xác hệ thống 100% hay recall phát hiện backdoor. '
        'Các lỗi, file lành bị báo nhầm và xung đột log đều được ghi trong báo cáo và audit.json.\n\n'
        'Tái tạo trong repository gốc: chạy scripts/summarize_bodmas_results.py rồi '
        'scripts/build_bodmas_report_2026_10_23.py bằng Python có python-docx/lxml. '
        'Công cụ tổng hợp chỉ đọc JSON/CSV, đối chiếu metadata của kit và tạo bảng; không gọi detector. '
        'Các file reproduction/ là source lưu kèm, cần đặt lại vào đúng repository để chạy; '
        'gói này không cung cấp một môi trường huấn luyện hay chạy malware.\n\n'
        'Bằng chứng QA: 16 lượt được đối chiếu, 4 dữ liệu lỗi giả lập bị từ chối; '
        '752 file primary giữ nguyên hash; 20 trang Word đã render và xem ảnh. '
        'Giới hạn nguồn nhãn, mô hình thực chạy trên VM, một file lành và chức năng trigger vẫn giữ.\n',
        encoding='utf8')
    visual = {'document_sha256': proof['output_sha256'], 'pages': 20,
              'all_pages_visually_reviewed': list(range(1, 21)), 'appendix_pages': [19, 20],
              'no_new_clipping_or_overlap': True, 'timing_table_intact': True,
              'unrelated_original_layout_retained': True}
    (DATA / 'visual_verification.json').write_text(json.dumps(visual, indent=2) + '\n', encoding='utf8')
    files = [(OUT / 'README.md', 'README.md'),
             (OUT / 'HUONG_DAN_TRINH_BAY_BODMAS.md', 'HUONG_DAN_TRINH_BAY_BODMAS.md'),
             (Path(proof['output']), 'report/' + Path(proof['output']).name),
             (OUT / 'BODMAS_REPORT_SECTION_EN.md', 'report/BODMAS_REPORT_SECTION_EN.md'),
             (ROOT / 'docs/BODMAS_RESULTS_2026_10_23.md', 'BODMAS_RESULTS_2026_10_23.md'),
             (ROOT / 'BODMAS_RESULTS.zip', 'input/BODMAS_RESULTS.zip')]
    files += [(p, 'data/' + p.name) for p in sorted(DATA.iterdir()) if p.suffix in ('.csv', '.json')]
    names = ('summarize_bodmas_results.py', 'build_bodmas_report_2026_10_23.py',
             'render_bodmas_report_2026_10_23.ps1', 'render_bodmas_pages_2026_10_23.py',
             'package_bodmas_2026_10_23.py')
    files += [(ROOT / 'scripts' / n, 'reproduction/' + n) for n in names]
    sums = '\n'.join(f'{sha(path)}  {name}' for path, name in files) + '\n'
    package = OUT / 'BODMAS_DELIVERY_2026_10_23.zip'
    with ZipFile(package, 'w', ZIP_DEFLATED) as dest:
        for path, name in files:
            dest.write(path, name)
        dest.writestr('SHA256SUMS.txt', sums)
    with ZipFile(package) as archive:
        assert archive.testzip() is None
        for line in sums.splitlines():
            checksum, name = line.split('  ', 1)
            assert hashlib.sha256(archive.read(name)).hexdigest() == checksum
        assert not any(Path(name).suffix.lower() in ('.exe', '.dll', '.sys') for name in archive.namelist())
    print(json.dumps({'package': str(package), 'bytes': package.stat().st_size,
                      'sha256': sha(package), 'entries': len(files) + 1,
                      'demo_cases': len(examples), 'new_inference': False}, indent=2))


if __name__ == '__main__':
    main()
