"""Offline routing/safety checks for the isolated native Windows ARM64 renderer preflight."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import rustgs
import check_rust_lib


class WinArm64RustTargetTest(unittest.TestCase):
    def test_target_is_registered_as_native_windows_staticlib(self):
        self.assertEqual(rustgs.WIN_ARM64, 'aarch64-pc-windows-msvc')
        self.assertIn(rustgs.WIN_ARM64, rustgs.TARGETS)
        self.assertIn(rustgs.WIN_ARM64, rustgs.CHECK_TARGETS)
        self.assertNotIn(rustgs.WIN_ARM64, rustgs.ARCHIVE_TARGETS)
        self.assertEqual(rustgs.feature_args(rustgs.WIN_ARM64, []), ['--features', 'native'])
        self.assertIn('--target', rustgs.cargo_args(rustgs.WIN_ARM64, 'release'))
        self.assertEqual(check_rust_lib.allowed_libs_file(rustgs.WIN_ARM64).name,
                         'native-static-libs-aarch64-pc-windows-msvc.txt')

    def test_windows_arm64_ring_c_uses_clang_not_x64_msbuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / 'clang.exe'
            exe.touch()
            with patch('rustgs.shutil.which', return_value=str(exe)):
                config = rustgs.c_tools(rustgs.WIN_ARM64)
        self.assertEqual(config['CC_aarch64_pc_windows_msvc'], str(exe))
        self.assertIn('--target=aarch64-pc-windows-msvc', config['CFLAGS_aarch64_pc_windows_msvc'])
        self.assertNotIn('x86_64', ' '.join(config.values()))

    def test_missing_clang_is_an_explicit_stop(self):
        with patch('rustgs.shutil.which', return_value=None):
            with self.assertRaisesRegex(rustgs.Refused, 'no LLVM clang'):
                rustgs.c_tools(rustgs.WIN_ARM64)

    def test_local_build_cannot_claim_ci_exception(self):
        for values in ({}, {'GITHUB_ACTIONS': 'true'},
                       {'GITHUB_ACTIONS': 'true', 'DHD_CI_ALLOW_C_OUTPUT': '1'}):
            with self.subTest(values=values), patch.dict(os.environ, values, clear=True):
                self.assertFalse(rustgs.hosted_ci_workspace())
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true',
                                     'RUNNER_ENVIRONMENT': 'github-hosted',
                                     'DHD_CI_ALLOW_C_OUTPUT': '1'}, clear=True):
            self.assertTrue(rustgs.hosted_ci_workspace())


if __name__ == '__main__':
    unittest.main()
