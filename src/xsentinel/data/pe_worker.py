"""Fixed child entry point. Read PE bytes from stdin, emit one bounded JSON result."""
import hashlib
import json
import os
import sys


def main():
    from .limits import MAX_UPLOAD_BYTES
    from xsentinel.schema import V2_PRIMARY, V3_PRIMARY
    schema = sys.argv[1]
    data = sys.stdin.buffer.read(MAX_UPLOAD_BYTES + 1)
    result = {'sha256': hashlib.sha256(data).hexdigest(), 'schema': schema}
    # Native parsers can write directly to stdout/stderr. Keep the protocol clean
    # and avoid accumulating unbounded warnings in memory or temporary log files.
    saved_stdout = os.dup(1)
    null = os.open(os.devnull, os.O_WRONLY)
    os.dup2(null, 1)
    os.dup2(null, 2)
    os.close(null)
    try:
        if schema == V3_PRIMARY:
            from .pe_v3 import extract_pe_v3 as extract
        elif schema == V2_PRIMARY:
            from .pe import extract_pe as extract
        else:
            raise ValueError('Unsupported schema')
        vector, provenance = extract(data)
        result.update(status='ok', vector=vector.tolist(), provenance=provenance)
    except Exception as error:
        result.update(status='error', error=f'{type(error).__name__}: {error}'[:2000])
    finally:
        sys.stdout.flush()
        os.dup2(saved_stdout, 1)
        os.close(saved_stdout)
    sys.stdout.buffer.write(json.dumps(result, allow_nan=False).encode('utf8'))
    sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
