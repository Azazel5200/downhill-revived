"""No toolchains, ISO, network or Windows device required for these tests."""

from pathlib import Path
import tempfile
import unittest

from win_arm64_preflight import RUST_TARGET, TOOLS, requirements, sdk_version


class PreflightTests(unittest.TestCase):
    def test_complete_arm64_toolchain(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            vc, sdk, version = base / 'MSVC', base / 'SDK', '10.0.26100.0'
            (vc / 'lib' / 'arm64').mkdir(parents=True)
            for part in ('ucrt', 'um', 'shared'):
                (sdk / 'Include' / version / part).mkdir(parents=True)
            for part in ('ucrt', 'um'):
                (sdk / 'Lib' / version / part / 'arm64').mkdir(parents=True)
            env = {'VCToolsInstallDir': str(vc), 'WindowsSdkDir': str(sdk),
                   'WindowsSDKVersion': version + '\\'}
            found = {name: '/tools/' + name for name in TOOLS}
            checks = requirements('Windows', 'ARM64', (3, 13), env, found, {RUST_TARGET})
            self.assertTrue(all(c.ok for c in checks))
            self.assertEqual(sdk_version(env), version)

    def test_cross_compile_does_not_require_arm64_host(self):
        checks = requirements('Windows', 'AMD64', (3, 13), {}, {}, set())
        arm = next(c for c in checks if c.name == 'ARM64 host CPU')
        self.assertFalse(arm.ok)
        self.assertFalse(arm.required)
        self.assertIn('MSVC ARM64 libraries', [c.name for c in checks if not c.ok and c.required])

    def test_x64_libraries_do_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'lib' / 'x64').mkdir(parents=True)
            checks = requirements('Windows', 'ARM64', (3, 13),
                                  {'VCToolsInstallDir': str(base)}, {}, set())
            self.assertFalse(next(c.ok for c in checks if c.name == 'MSVC ARM64 libraries'))

    def test_non_windows_and_old_python_fail_closed(self):
        checks = requirements('Linux', 'aarch64', (3, 11), {}, {}, set(), python_bits=32)
        self.assertFalse(next(c.ok for c in checks if c.name == 'Windows host'))
        self.assertFalse(next(c.ok for c in checks if c.name == 'Python 3.12+'))
        self.assertFalse(next(c.ok for c in checks if c.name == '64-bit Python'))
        self.assertFalse(next(c.ok for c in checks if c.name == 'Rust Windows ARM64 target'))


if __name__ == '__main__':
    unittest.main()
