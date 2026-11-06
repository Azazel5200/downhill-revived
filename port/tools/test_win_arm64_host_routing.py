"""Offline routing checks for the unified Windows ARM64 game build.

No game data, C compiler or GPU is involved: this does not claim a game build.
"""
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import build_host64 as builder
import sdl3


def sdk_paths(root, arch):
    msvc, sdk, version = root/'msvc', root/'sdk', '10.0.99999.0'
    for path in [msvc/'include', msvc/'lib'/arch,
                 *[sdk/'Include'/version/x for x in ('ucrt', 'um', 'shared')],
                 sdk/'Lib'/version/'ucrt'/arch, sdk/'Lib'/version/'um'/arch]:
        path.mkdir(parents=True, exist_ok=True)
    return {'VCToolsInstallDir': str(msvc), 'WindowsSdkDir': str(sdk),
            'WindowsSDKVersion': version+'\\'}


class WindowsArm64HostRouting(unittest.TestCase):
    def test_native_arm64_compiler_has_arm64_sdk_and_no_zen_or_x64(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = sdk_paths(root, 'arm64')
            args = SimpleNamespace(llvm=root/'llvm', debug=True)
            cmd = builder.windows_host_common(builder.TARGETS['win-arm64'], args,
                                              ['-DWASM_RT_STACK_DEPTH_COUNT=1'],
                                              ['-Ivirtual'], [], env)
            text = ' '.join(map(str, cmd)).replace('\\', '/').lower()
            self.assertIn('--target=aarch64-pc-windows-msvc', text)
            self.assertIn('/imsvc'+str(root/'msvc/include').replace('\\', '/').lower(), text)
            self.assertIn('/include/10.0.99999.0/ucrt', text)
            self.assertIn('/clang:-fno-omit-frame-pointer', text)
            self.assertIn('/mt', text)
            self.assertNotIn('x86-64', text)
            self.assertNotIn('znver', text)
            self.assertNotIn('/lib/x64', text)

    def test_arm64_requires_real_arm64_sdk(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = sdk_paths(root, 'x64')
            with self.assertRaisesRegex(RuntimeError, 'arm64'):
                builder.windows_host_common(builder.TARGETS['win-arm64'],
                                            SimpleNamespace(llvm=root/'llvm', debug=False),
                                            [], [], [], env)

    def test_arm64_link_machine_and_cargo_arm64_library(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = dict(sdk_paths(root, 'arm64'), CARGO_HOME=str(root/'cargo'))
            args = SimpleNamespace(llvm=root/'llvm', debug=True)
            with patch('build_win_rust_abi_smoke.cargo_windows_import_paths',
                       return_value=['/libpath:'+str(root/'cargo/registry/arm64')]) as resolver:
                cmd = builder.windows_host_link(builder.TARGETS['win-arm64'], args,
                                                root, root/'dhd64.exe', root/'link.rsp', env,
                                                {'native_static_libs': ['windows.0.52.0.lib']})
            resolver.assert_called_once_with(str(root/'cargo'), ['windows.0.52.0.lib'])
            text = ' '.join(map(str, cmd)).replace('\\', '/').lower()
            self.assertIn('/machine:arm64', text)
            self.assertIn('/lib/arm64', text)
            self.assertIn('/ucrt/arm64', text)
            self.assertIn('/um/arm64', text)
            self.assertNotIn('/lib/x64', text)
            self.assertIn('/subsystem:windows', text)
            self.assertIn('/debug', text)

    def test_arm64_link_missing_cargo_home_refuses(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = sdk_paths(root, 'arm64')
            with self.assertRaisesRegex(RuntimeError, 'CARGO_HOME'):
                builder.windows_host_link(builder.TARGETS['win-arm64'],
                                          SimpleNamespace(llvm=root, debug=False),
                                          root, root/'dhd64.exe', root/'link.rsp', env,
                                          {'native_static_libs': ['windows.0.52.0.lib']})

    def test_x64_compiler_and_linker_keep_original_defaults(self):
        t = builder.TARGETS['win-x64']
        args = SimpleNamespace(llvm=Path('llvm'), debug=False)
        compile = list(map(str, builder.windows_host_common(t, args, [], [], [], {})))
        link = list(map(str, builder.windows_host_link(t, args, Path('build'),
                           Path('dhd64.exe'), Path('link.rsp'), {}, {'native_static_libs': []})))
        self.assertIn('--target=x86_64-pc-windows-msvc', compile)
        self.assertIn('/clang:-march=x86-64-v2', compile)
        self.assertIn('/clang:-mtune=znver3', compile)
        self.assertTrue(any('/lib/x64' in item.replace('\\', '/') for item in link))
        self.assertFalse(any('/machine:arm64' in item for item in link))

    def test_sdl_build_chooses_native_target(self):
        args = SimpleNamespace(sdl_lib=None, sdl_include=None, sdl_libs=None)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lib, include = root/'SDL3-static.lib', root/'include'
            with patch.object(sdl3, 'build', return_value=(lib, include)) as mocked:
                got = builder.sdl(builder.TARGETS['win-arm64'], args)
            mocked.assert_called_once_with('aarch64-pc-windows-msvc')
            self.assertEqual(got[:2], (lib.resolve(), include.resolve()))
            self.assertIn('user32.lib', got[2])


if __name__ == '__main__':
    unittest.main()
