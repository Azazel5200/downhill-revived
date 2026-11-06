"""Asset-free SDL3 link-command checks; compiler and source archive not required."""
from pathlib import Path
import tempfile
import unittest

from build_win_sdl_smoke import link_command
import sdl3


class WinArm64SDL3CommandTest(unittest.TestCase):
    def test_pinned_sdl3_uses_distinct_architecture_cache(self):
        self.assertEqual(sdl3.X64_TARGET, 'x86_64-pc-windows-msvc')
        self.assertEqual(sdl3.VERSION, '3.4.18')
        self.assertEqual(len(sdl3.SHA256), 64)
        arm_dir = '%s-%s' % (sdl3.VERSION, 'aarch64')
        x64_dir = '%s-%s' % (sdl3.VERSION, 'x86_64')
        self.assertNotEqual(arm_dir, x64_dir)

    def test_arm64_link_never_uses_x64_libraries(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            cmd = link_command(p / 'llvm', p / 'msvc', p / 'sdk', '10.0.1',
                               p / 'SDL3-static.lib', p / 'SDL3/include', p / 'out')
        self.assertIn('--target=aarch64-pc-windows-msvc', cmd)
        paths = [x for x in cmd if x.startswith('/libpath:')]
        self.assertEqual(len(paths), 3)
        self.assertTrue(all(x.replace('\\', '/').endswith('/arm64') for x in paths))
        self.assertNotIn('x64', ' '.join(paths))
        self.assertIn('SDL3-static.lib', ' '.join(cmd))
        self.assertIn('onecore.lib', cmd)
        self.assertTrue(set(sdl3.SYSTEM_LIBS).issubset(set(cmd)))


if __name__ == '__main__':
    unittest.main()
