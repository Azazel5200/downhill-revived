"""Synthetic ISO 9660 tests: no commercial game files or network needed."""

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import struct
import tempfile
import unittest

from release_compare import Iso
from spanish_disc_inventory import inventory, main

SECTOR = 2048


def record(name, sector, size, directory=False):
    n = name.encode('ascii') if isinstance(name, str) else name
    length = 33 + len(n) + (len(n) % 2 == 0)
    out = bytearray(length)
    out[0] = length
    struct.pack_into('<I', out, 2, sector)
    struct.pack_into('>I', out, 6, sector)
    struct.pack_into('<I', out, 10, size)
    struct.pack_into('>I', out, 14, size)
    out[25] = 2 if directory else 0
    struct.pack_into('<H', out, 28, 1)
    struct.pack_into('>H', out, 30, 1)
    out[32] = len(n)
    out[33:33 + len(n)] = n
    return out


def synthetic_iso(path, region='SLES_522.02', bike_shop=True):
    """A tiny, valid-enough ISO 9660 PVD, root, shell and three dummy files."""
    raw = bytearray(26 * SECTOR)
    pvd = 16 * SECTOR
    raw[pvd] = 1
    raw[pvd + 1:pvd + 6] = b'CD001'
    raw[pvd + 6] = 1
    raw[pvd + 156:pvd + 156 + 34] = record(b'\0', 20, SECTOR, True)
    # Root directory: the writer keeps records within the first logical sector.
    root = [record(b'\0', 20, SECTOR, True), record(b'\1', 20, SECTOR, True),
            record('SYSTEM.CNF;1', 22, 70), record('SHELL', 21, SECTOR, True)]
    raw[20 * SECTOR:20 * SECTOR + len(b''.join(root))] = b''.join(root)
    shell = [record(b'\0', 21, SECTOR, True), record(b'\1', 20, SECTOR, True),
             record('UIS.RTX;1', 23, 4)]
    if bike_shop:
        shell.append(record('BIKESHPS.RTX;1', 24, 4))
    raw[21 * SECTOR:21 * SECTOR + len(b''.join(shell))] = b''.join(shell)
    cnf = f'BOOT2 = cdrom0:\\{region};1\r\nVER=1.01\r\nVMODE=PAL\r\n'.encode()
    raw[22 * SECTOR:22 * SECTOR + len(cnf)] = cnf
    raw[23 * SECTOR:23 * SECTOR + 4] = b'TEST'
    raw[24 * SECTOR:24 * SECTOR + 4] = b'TEST'
    Path(path).write_bytes(raw)


class SpanishInventoryTests(unittest.TestCase):
    @staticmethod
    def run_json(path):
        output = StringIO()
        with redirect_stdout(output):
            result = main([str(path), '--json'])
        return result, json.loads(output.getvalue())

    def test_eu_names_confirmed_from_synthetic_iso(self):
        with tempfile.TemporaryDirectory() as tmp:
            name = Path(tmp) / 'synthetic.iso'
            synthetic_iso(name)
            disc = Iso(name)
            try:
                result = inventory(disc)
                self.assertTrue(result.eu_disc)
                self.assertTrue(result.shell_names_present)
                self.assertEqual(result.localized_groups['Menu español'], 1)
                self.assertEqual(result.localized_groups['Tienda de bicicletas en español'], 1)
                self.assertFalse(any(result.legal_movies.values()))
            finally:
                disc.f.close()
            code, output = self.run_json(name)
            self.assertEqual(code, 0)
            self.assertTrue(output['shell_names_present'])
            self.assertEqual(output['boot'], 'SLES_522.02')

    def test_region_mismatch_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            name = Path(tmp) / 'us.iso'
            synthetic_iso(name, region='SCUS_971.77')
            code, output = self.run_json(name)
            self.assertEqual(code, 1)
            self.assertFalse(output['eu_disc'])

    def test_missing_shop_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            name = Path(tmp) / 'missing.iso'
            synthetic_iso(name, bike_shop=False)
            code, output = self.run_json(name)
            self.assertEqual(code, 1)
            self.assertEqual(output['localized_groups']['Tienda de bicicletas en español'], 0)


if __name__ == '__main__':
    unittest.main()
