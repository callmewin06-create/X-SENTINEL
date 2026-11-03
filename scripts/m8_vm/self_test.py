"""Standard-library self-test; generates inert header fixtures, never runs EXEs."""
import csv
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

import m8_preflight


def make_header(path):
    data = bytearray(512)
    data[:2] = b'MZ'; struct.pack_into('<I', data, 0x3c, 128)
    data[128:132] = b'PE\0\0'
    struct.pack_into('<H', data, 132, 0x8664)
    struct.pack_into('<H', data, 148, 240)
    struct.pack_into('<H', data, 152, 0x20b)
    struct.pack_into('<I', data, 260, 16)
    path.write_bytes(data)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        parent = Path(os.environ.get('M8_SELFTEST_TMPDIR') or tempfile.gettempdir()).resolve(strict=True)
        self.temp = tempfile.TemporaryDirectory(prefix='m8_selftest_', dir=str(parent))
        self.base = Path(self.temp.name).resolve()
        if self.base.parent != parent:
            raise RuntimeError('Unexpected temporary directory outside requested parent')
        self.addCleanup(self.temp.cleanup)
        self.samples = self.base/'samples'; self.samples.mkdir()
        make_header(self.samples/'inert_header.exe')

    def test_cli_unicode_path_and_report(self):
        output = self.base/'report space \u1eabu'
        result = subprocess.run([sys.executable, str(Path(m8_preflight.__file__).resolve()),
              '--samples', str(self.samples), '--output', str(output)],
              capture_output=True, encoding='utf-8', errors='strict')
        self.assertEqual(result.returncode, 0, result.stderr)
        with (output/'binary_inventory.csv').open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['architecture'], 'x64')
        self.assertEqual(rows[0]['functional_status'], 'NOT_RUN')
        self.assertEqual(rows[0]['label'], 'UNVERIFIED')
        environment = json.loads((output/'environment.json').read_text(encoding='utf-8'))
        self.assertEqual(environment['sample_execution'], 'NEVER')
        self.assertEqual(environment['os'], m8_preflight.platform.system())

    def test_corrupt_header_not_accepted(self):
        (self.samples/'broken.exe').write_bytes(b'MZ')
        row = m8_preflight.inspect_file(self.samples/'broken.exe', self.samples)
        self.assertEqual(row['static_status'], 'ERROR')
        self.assertEqual(row['functional_status'], 'NOT_RUN')

    def test_refuses_output_inside_corpus(self):
        with self.assertRaises(ValueError):
            m8_preflight.run(self.samples, self.samples/'report')
        self.assertFalse((self.samples/'report').exists())

    def test_skips_symlink(self):
        link = self.samples/'link.exe'
        try:
            link.symlink_to(self.samples/'inert_header.exe')
        except OSError:
            self.skipTest('Symlink privilege unavailable on this host')
        row = m8_preflight.inspect_file(link, self.samples)
        self.assertEqual(row['static_status'], 'SKIPPED_NONREGULAR')
        self.assertEqual(row['sha256'], '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
