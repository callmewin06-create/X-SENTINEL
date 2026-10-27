"""Bounded PE extraction in a disposable process; samples are never executed.

This is process separation and a wall-clock deadline, not a security sandbox.
One worker per parent process; concurrent callers receive an explicit busy error.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

from .limits import verify_size
from xsentinel.schema import get_schema, V2_PRIMARY, V3_PRIMARY

VERSION = 'pe-worker-v1'
_SLOT = threading.BoundedSemaphore(1)


class ExtractionError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def timeout_seconds():
    try:
        value = float(os.environ.get('XS_PE_TIMEOUT_SECONDS', '60'))
    except ValueError as exc:
        raise ValueError('XS_PE_TIMEOUT_SECONDS must be a number') from exc
    if not math.isfinite(value) or not 0 < value <= 300:
        raise ValueError('XS_PE_TIMEOUT_SECONDS must be > 0 and <= 300')
    return value


def _stop(process):
    if process.poll() is None:
        try:
            if os.name == 'nt':
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=2)


def _run_worker(data, schema_version, timeout):
    """Private process runner. Only a fixed packaged entry point is launched."""
    env = os.environ.copy()
    # Support both the source checkout and the installed Docker package.
    package_root = str(Path(__file__).resolve().parents[2])
    env['PYTHONPATH'] = package_root + os.pathsep + env.get('PYTHONPATH', '')
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    process = subprocess.Popen(
        [sys.executable, '-m', 'xsentinel.data.pe_worker', schema_version],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env=env, creationflags=flags, start_new_session=os.name != 'nt')
    try:
        try:
            output, _ = process.communicate(data, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            _stop(process)
            raise ExtractionError('timeout', f'PE extraction exceeded {timeout:g} seconds') from exc
        if process.returncode != 0:
            raise ExtractionError('worker_crashed', f'PE worker exited with code {process.returncode}')
        if len(output) > 512 * 1024:
            raise ExtractionError('invalid_output', 'PE worker response is too large')
        try:
            result = json.loads(output)
        except (ValueError, UnicodeError) as exc:
            raise ExtractionError('invalid_output', 'PE worker returned invalid JSON') from exc
        if not isinstance(result, dict) or result.get('sha256') != hashlib.sha256(data).hexdigest() or result.get('schema') != schema_version:
            raise ExtractionError('invalid_output', 'PE worker input identity mismatch')
        if result.get('status') == 'error':
            raise ExtractionError('parse_failed', str(result.get('error', 'PE extraction failed'))[:2000])
        if result.get('status') != 'ok' or not isinstance(result.get('provenance'), dict):
            raise ExtractionError('invalid_output', 'PE worker response is incomplete')
        try:
            x = get_schema(schema_version).matrix(result['vector'])
            if len(x) != 1:
                raise ValueError('Exactly one vector required')
        except (KeyError, TypeError, ValueError) as exc:
            raise ExtractionError('invalid_output', 'PE worker returned an invalid vector') from exc
        return x[0], result['provenance']
    finally:
        _stop(process)
        for pipe in (process.stdin, process.stdout):
            if pipe is not None:
                pipe.close()


def extract_pe_isolated(data, schema_version, *, timeout=None):
    verify_size(len(data))
    if schema_version not in (V2_PRIMARY, V3_PRIMARY):
        raise ValueError('Only primary V2/V3 PE schemas are supported')
    duration = timeout_seconds() if timeout is None else float(timeout)
    if not math.isfinite(duration) or not 0 < duration <= 300:
        raise ValueError('Invalid PE extraction timeout')
    # Cheap format checks before acquiring a worker. The existing guard remains.
    from .pe import verify_pe
    try:
        verify_pe(data)
    except ValueError as exc:
        raise ExtractionError('invalid_header', str(exc)) from exc
    if not _SLOT.acquire(blocking=False):
        raise ExtractionError('busy', 'Another PE extraction is running; retry after it finishes')
    start = time.perf_counter()
    try:
        vector, provenance = _run_worker(data, schema_version, duration)
        return vector, {**provenance, 'process_separation': VERSION,
                        'timeout_seconds': duration,
                        'worker_wall_ms': (time.perf_counter() - start) * 1000}
    finally:
        _SLOT.release()
