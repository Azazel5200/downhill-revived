"""Asset-free disc preflight tests with synthetic ISO 9660 sectors."""

import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from disc_probe import identify, main


SECTOR = 2048


def iso_fixture(serial='SLES_522.02', boot_exists=True, system_exists=True,
                boot_line=None):
    """Construct a tiny, self-contained fake PS2 disc without copyrighted bytes."""
    cnf = (boot_line if boot_line is not None else
           f'BOOT2 = cdrom0:\\{serial};1\r\nVER = 1.01\r\nVMODE = PAL\r\n').encode('ascii')
    boot = b'\x7fELF' + bytes(range(32))
    files = []
    if system_exists:
        files.append(('SYSTEM.CNF', 20, cnf))
    if boot_exists:
        files.append((serial, 21, boot))
    img = bytearray(23 * SECTOR)
    pvd = 16 * SECTOR
    img[pvd:pvd + 6] = b'\x01CD001'
    struct.pack_into('<I', img, pvd + 158, 18)
    struct.pack_into('<I', img, pvd + 166, SECTOR)
    records = bytearray()
    for name, at, data in [('\0', 18, None), ('\1', 18, None)] + files:
        suffix = ';1' if data is not None else ''
        name_bytes = (name + suffix).encode('ascii')
        record = bytearray(33 + len(name_bytes) + (len(name_bytes) + 1) % 2)
        record[0], record[25], record[32] = len(record), int(data is None) * 2, len(name_bytes)
        struct.pack_into('<I', record, 2, at)
        struct.pack_into('<I', record, 10, SECTOR if data is None else len(data))
        record[33:33 + len(name_bytes)] = name_bytes
        records.extend(record)
        if data is not None:
            img[at * SECTOR:at * SECTOR + len(data)] = data
    img[18 * SECTOR:18 * SECTOR + len(records)] = records
    return bytes(img), hashlib.sha256(boot).hexdigest()


class DiscProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'fixture.iso'

    def set_disc(self, **kwargs):
        payload, boot_hash = iso_fixture(**kwargs)
        self.path.write_bytes(payload)
        return payload, boot_hash

    def test_spanish_pal_european_disc_requires_its_own_core(self):
        _, boot_hash = self.set_disc()
        info = identify(self.path)
        self.assertEqual(info['serial'], 'SLES_522.02')
        self.assertIn('Spanish', info['region'])
        self.assertIn('separate European game core', info['support'])
        self.assertEqual(info['boot_sha256'], boot_hash)
        self.assertEqual(info['boot_size'], 36)
        self.assertEqual(info['version'], '1.01')
        self.assertEqual(info['video_mode'], 'PAL')
        self.assertEqual(info['files'], 2)
        self.assertNotIn('iso_sha256', info)

    def test_usa_disc_recognized_without_claiming_arm64_game_support(self):
        self.set_disc(serial='SCUS_971.77')
        info = identify(self.path)
        self.assertEqual(info['serial'], 'SCUS_971.77')
        self.assertIn('Upstream USA game core', info['support'])
        self.assertIn('experimental', info['support'])

    def test_full_iso_hash_is_opt_in(self):
        payload, _ = self.set_disc()
        self.assertEqual(identify(self.path, hash_iso=True)['iso_sha256'],
                         hashlib.sha256(payload).hexdigest())

    def test_missing_boot_executable_is_reported(self):
        self.set_disc(boot_exists=False)
        with self.assertRaisesRegex(ValueError, 'missing boot executable'):
            identify(self.path)

    def test_missing_system_cnf_is_reported(self):
        self.set_disc(system_exists=False)
        with self.assertRaisesRegex(ValueError, 'SYSTEM.CNF not found'):
            identify(self.path)

    def test_bad_boot_line_is_reported(self):
        self.set_disc(boot_line='BOOT2 = unknown.exe\r\n')
        with self.assertRaisesRegex(ValueError, 'BOOT2 serial not found'):
            identify(self.path)

    def test_invalid_iso_is_rejected(self):
        self.path.write_bytes(b'not a PS2 disc')
        with self.assertRaisesRegex(ValueError, 'ISO 9660'):
            identify(self.path)

    def test_cli_reports_metadata_without_game_data(self):
        import contextlib
        from io import StringIO
        self.set_disc()
        out = StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main([str(self.path)]), 0)
        result = out.getvalue()
        self.assertIn('SLES_522.02', result)
        self.assertIn('Boot SHA-256:', result)
        self.assertNotIn('ISO SHA-256:', result)
        self.assertNotIn(str(self.path), result)


if __name__ == '__main__':
    unittest.main()
