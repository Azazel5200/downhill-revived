"""Asset-free PE header checks for the native ARM64 C -> Rust linker smoke."""
from pathlib import Path
import struct
import tempfile
import unittest

from build_win_rust_abi_smoke import cargo_windows_import_paths, windows_arm64_executable


def pe_bytes(machine):
    image = bytearray(128)
    image[:2] = b'MZ'
    struct.pack_into('<I', image, 0x3c, 64)
    image[64:68] = b'PE\0\0'
    struct.pack_into('<H', image, 68, machine)
    return bytes(image)


class WinRustAbiTest(unittest.TestCase):
    def check(self, data):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'smoke.exe'
            p.write_bytes(data)
            windows_arm64_executable(p)

    def test_arm64_pe_machine(self):
        self.check(pe_bytes(0xaa64))

    def test_reject_x64_pe(self):
        with self.assertRaisesRegex(ValueError, 'not native ARM64'):
            self.check(pe_bytes(0x8664))

    def test_reject_non_pe(self):
        with self.assertRaisesRegex(ValueError, 'not a Windows executable'):
            self.check(b'not an exe')

    def test_reject_truncated_pe(self):
        with self.assertRaisesRegex(ValueError, 'missing Windows PE header'):
            self.check(pe_bytes(0xaa64)[:65])

    def test_cargo_052_arm64_import_library_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = Path(tmp) / 'registry' / 'src' / 'index' / 'windows_aarch64_msvc-0.52.6' / 'lib' / 'windows.0.52.0.lib'
            lib.parent.mkdir(parents=True)
            obj = struct.pack('<HH', 0xaa64, 1) + bytes(16)
            hdr = b'test.obj/'.ljust(16) + b'0'.ljust(12) + b'0'.ljust(6) + b'0'.ljust(6) + (
                b'100644'.ljust(8)) + b'20'.ljust(10) + b'`\n'
            lib.write_bytes(b'!<arch>\n' + hdr + obj)
            self.assertEqual(cargo_windows_import_paths(tmp, ['windows.0.52.0.lib']),
                             ['/libpath:' + str(lib.parent)])

    def test_import_library_rejects_x64_and_unknown_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cargo_windows_import_paths(tmp, ['kernel32.lib']), [])
            with self.assertRaisesRegex(ValueError, 'unexpected Windows import'):
                cargo_windows_import_paths(tmp, ['windows.0.53.0.lib'])
            with self.assertRaisesRegex(ValueError, 'expected exactly one'):
                cargo_windows_import_paths(tmp, ['windows.0.52.0.lib'])


if __name__ == '__main__':
    unittest.main()
