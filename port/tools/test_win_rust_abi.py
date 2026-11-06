"""Asset-free PE header checks for the native ARM64 C -> Rust linker smoke."""
from pathlib import Path
import struct
import tempfile
import unittest

from build_win_rust_abi_smoke import windows_arm64_executable


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


if __name__ == '__main__':
    unittest.main()
