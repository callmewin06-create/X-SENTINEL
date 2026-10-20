"""Identity and export helpers for saved snapshots, without prediction or storage."""
from datetime import datetime, timezone, timedelta
import hashlib
import json

LOCAL_TZ=timezone(timedelta(hours=7),name='Asia/Bangkok')


def snapshot_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,
        allow_nan=False,separators=(',',':')).encode('utf8')).hexdigest()


def input_hash_rows(result):
    metadata=result.get('input_metadata') or {}
    missing='Không có file gốc (mẫu vector)' if metadata.get('kind')=='demo' else 'Chưa lưu'
    return [('SHA-256 file',metadata.get('file_sha256') or missing),
            ('SHA-256 vector',result.get('input_sha256') or 'Chưa lưu')]


def local_timestamp(value):
    if not value: return 'Chưa lưu'
    try:
        stamp=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        if stamp.tzinfo is None: return str(value)+' (chưa lưu múi giờ)'
        return stamp.astimezone(LOCAL_TZ).strftime('%d/%m/%Y %H:%M:%S')
    except (ValueError,TypeError):
        return str(value)


def classification_label(value):
    return {'MALWARE':'Dự đoán mã độc','BENIGN':'Dự đoán lành'}.get(value,'Chưa lưu')


def trigger_label(value):
    return 'Có cảnh báo' if value is True else 'Chưa cảnh báo' if value is False else 'Chưa lưu'


def timing_description(result):
    if result.get('computation_scope')=='selected':
        return 'Tính phương pháp đã chọn và phần giải thích; chỉ chạy STRIP khi chọn STRIP'
    return 'Tính toàn bộ điểm và STRIP'
