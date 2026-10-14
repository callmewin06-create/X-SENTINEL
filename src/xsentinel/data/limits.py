"""Shared upload contract for the UI, readers and input metadata."""
MAX_UPLOAD_MIB = 50
MAX_UPLOAD_BYTES = MAX_UPLOAD_MIB * 1024 * 1024


def verify_size(size):
    if size > MAX_UPLOAD_BYTES:
        raise ValueError('Upload exceeds 50 MiB')
