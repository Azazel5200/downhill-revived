"""Offline routing checks for the unvalidated Windows ARM64 fiber smoke target.

These do not compile ARM64 code or substitute for a run on Windows ARM64 hardware.
"""
import os
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_host64 as builder  # noqa: E402


class WindowsArm64FiberTargetTests(unittest.TestCase):
    def test_target_uses_dedicated_winarm64_adapter(self):
        target = builder.TARGETS['win-arm64']
        self.assertTrue(target.windows)
        self.assertFalse(target.posix)
        self.assertEqual(target.rust, 'aarch64-pc-windows-msvc')
        self.assertEqual(target.fiber, 'winarm64')
        self.assertEqual(builder.glue(target)[3].name, 'fiber_winarm64.c')
        self.assertNotEqual(builder.glue(target)[3], builder.glue(builder.TARGETS['win-x64'])[3])

    def test_missing_sdk_environment_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'VCToolsInstallDir'):
            builder.windows_arm64_paths({})

    def test_x64_only_sdk_libraries_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            msvc, sdk, version = root/'msvc', root/'sdk', '10.0.99999.0'
            for path in (msvc/'include', msvc/'lib/x64',
                         *[sdk/'Include'/version/name for name in ('ucrt', 'um', 'shared')],
                         sdk/'Lib'/version/'ucrt/x64', sdk/'Lib'/version/'um/x64'):
                path.mkdir(parents=True)
            env = dict(VCToolsInstallDir=str(msvc), WindowsSdkDir=str(sdk),
                       WindowsSDKVersion=version+'\\')
            with self.assertRaisesRegex(RuntimeError, 'arm64'):
                builder.windows_arm64_paths(env)

    def test_fiber_command_links_only_arm64_and_llvm_lld(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            msvc, sdk, llvm, version = root/'msvc', root/'sdk', root/'llvm', '10.0.99999.0'
            for path in (msvc/'include', msvc/'lib/arm64',
                         *[sdk/'Include'/version/name for name in ('ucrt', 'um', 'shared')],
                         sdk/'Lib'/version/'ucrt/arm64', sdk/'Lib'/version/'um/arm64'):
                path.mkdir(parents=True)
            llvm.mkdir()
            for tool in ('clang-cl.exe', 'lld-link.exe'):
                (llvm/tool).touch()
            env = dict(VCToolsInstallDir=str(msvc), WindowsSdkDir=str(sdk), WindowsSDKVersion=version+'\\')
            target = builder.TARGETS['win-arm64']
            args = SimpleNamespace(llvm=llvm)
            cmd = builder.windows_fiber_command(target, args, root, root, root/'test.exe',
                                                [Path('selftest.c')], ['-DWASM_RT_STACK_DEPTH_COUNT=1'], env)
            # Windows pathlib renders local paths with backslashes; compare
            # portable slash-normalized command text on every CI host.
            text = ' '.join(map(str, cmd)).replace('\\', '/').lower()
            self.assertIn('--target=aarch64-pc-windows-msvc', text)
            self.assertIn('-fuse-ld=lld', text)
            self.assertIn('/lib/arm64', text)
            self.assertIn('ucrt/arm64', text)
            self.assertIn('um/arm64', text)
            self.assertNotIn('/lib/x64', text)
            self.assertNotIn('ucrt/x64', text)

            # Windows os.environ normalizes names to uppercase; a copied dict
            # must preserve case-insensitive lookup for compiler discovery.
            upper_env = {name.upper(): value for name, value in env.items()}
            self.assertEqual(builder.windows_arm64_paths(upper_env), (msvc, sdk, version))

    def test_full_game_request_fails_closed(self):
        script = Path(builder.__file__).resolve()
        result = subprocess.run([sys.executable, '-B', str(script), '--target', 'win-arm64'],
                                cwd=builder.ROOT, capture_output=True, text=True,
                                env={**os.environ, 'DHD_BUILD_SLOTS': '0'}, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('experimental --fiber-test only', result.stderr)


if __name__ == '__main__':
    unittest.main()
