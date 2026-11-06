"""Offline command-routing tests; no installed Windows compiler or game data required."""
import os
from pathlib import Path
import tempfile
import unittest

from build_win_host_smoke import command


class WindowsHostSmokeCommandTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.msvc = self.root / 'msvc'
        self.sdk = self.root / 'sdk'
        self.llvm = self.root / 'llvm'
        self.llvm.mkdir()
        for executable in ('clang-cl.exe', 'lld-link.exe'):
            (self.llvm / executable).touch()
        for dirname in ('include', 'lib/arm64', 'lib/x64'):
            (self.msvc / dirname).mkdir(parents=True)
        for dirname in ('ucrt', 'shared', 'um'):
            (self.sdk / 'Include/10.0.99999.0' / dirname).mkdir(parents=True)
        for dirname in ('ucrt/arm64', 'um/arm64', 'ucrt/x64', 'um/x64'):
            (self.sdk / 'Lib/10.0.99999.0' / dirname).mkdir(parents=True)
        self.env = {'VCToolsInstallDir': str(self.msvc),
                    'WindowsSdkDir': str(self.sdk),
                    'WindowsSDKVersion': '10.0.99999.0' + os.sep}

    def test_arm64_uses_only_arm64_libraries_and_target(self):
        cmd = command('arm64', self.llvm, self.root / 'out', self.env)
        self.assertIn('--target=aarch64-pc-windows-msvc', cmd)
        libs = [x for x in cmd if x.startswith('/libpath:')]
        self.assertEqual(len(libs), 3)
        self.assertTrue(all(x.endswith('/arm64') or x.endswith('\\arm64') for x in libs))
        self.assertNotIn('x86_64-pc-windows-msvc', ' '.join(cmd))
        self.assertIn('advapi32.lib', cmd)
        self.assertIn('selftest_win_host.c', ' '.join(cmd))

    def test_x64_uses_only_x64_libraries_and_target(self):
        cmd = command('x64', self.llvm, self.root / 'out', self.env)
        self.assertIn('--target=x86_64-pc-windows-msvc', cmd)
        libs = [x for x in cmd if x.startswith('/libpath:')]
        self.assertEqual(len(libs), 3)
        self.assertTrue(all(x.endswith('/x64') or x.endswith('\\x64') for x in libs))
        self.assertNotIn('aarch64-pc-windows-msvc', ' '.join(cmd))

    def test_reject_missing_sdk_arm64_dirs_even_when_x64_exists(self):
        import shutil
        shutil.rmtree(self.sdk / 'Lib/10.0.99999.0/um/arm64')
        with self.assertRaisesRegex(RuntimeError, 'missing .*compiler/SDK paths'):
            command('arm64', self.llvm, self.root / 'out', self.env)

    def test_reject_missing_llvm_linker(self):
        (self.llvm / 'lld-link.exe').unlink()
        with self.assertRaisesRegex(RuntimeError, 'lld-link.exe'):
            command('arm64', self.llvm, self.root / 'out', self.env)

    def test_developer_paths_accept_mixed_case_env_keys(self):
        mixed = {key.upper(): value for key, value in self.env.items()}
        cmd = command('arm64', self.llvm, self.root / 'out', mixed)
        self.assertIn('--target=aarch64-pc-windows-msvc', cmd)


if __name__ == '__main__':
    unittest.main()
