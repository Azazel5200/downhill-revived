"""Fast, asset-free tests for the native ARM64 Rust static-library validator."""
from pathlib import Path
import struct
import tempfile
import unittest

from check_arm64_coff import archive_machine_summary


def member(machine, *, bigobj=False):
    blob = (struct.pack('<HHHH', 0, 0xffff, 2, machine) + bytes(48)) if bigobj else (
        struct.pack('<HH', machine, 1) + bytes(16))
    length = len(blob)
    head = (b'object.o/').ljust(16) + b'0'.ljust(12) + b'0'.ljust(6) + b'0'.ljust(6) + (
        b'100644'.ljust(8)) + str(length).encode().ljust(10) + b'`\n'
    return head + blob + (b'\n' if length & 1 else b'')


class Arm64CoffTest(unittest.TestCase):
    def archive(self, *members):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.lib'
            path.write_bytes(b'!<arch>\n' + b''.join(members))
            return archive_machine_summary(path)

    def test_arm64_normal_and_bigobj(self):
        count, size = self.archive(member(0xaa64), member(0xaa64, bigobj=True))
        self.assertEqual(count, 2)
        self.assertEqual(size, 76)

    def test_x64_object_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'non-ARM64'):
            self.archive(member(0xaa64), member(0x8664))

    def test_x86_object_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'non-ARM64'):
            self.archive(member(0x014c))

    def test_non_archive_and_empty_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no ARM64'):
            self.archive()
        with self.assertRaisesRegex(ValueError, 'no ARM64'):
            self.archive(member(0x1234))

    def test_truncated_member_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'truncated'):
            self.archive(member(0xaa64)[:-1])


if __name__ == '__main__':
    unittest.main()
