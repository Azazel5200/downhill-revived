#!/usr/bin/env python3
"""Build the project's pinned SDL3 static library and run a native ARM64 SDL smoke.

The full game, SDL window/device runtime and Rust renderer are intentionally out of scope.
"""
import argparse
import os
from pathlib import Path
import subprocess

from build_host64 import windows_arm64_paths
import sdl3

ROOT = Path(__file__).resolve().parents[2]


def link_command(llvm, msvc, sdk, version, library, includes, out):
    return [str(llvm / 'clang-cl.exe'), '--target=aarch64-pc-windows-msvc',
            '-fuse-ld=lld', '/nologo', '/O2', '/MT',
            '/imsvc' + str(msvc / 'include'),
            *['/imsvc' + str(sdk / 'Include' / version / x) for x in ('ucrt', 'um', 'shared')],
            '/I' + str(includes), str(ROOT / 'port/host/selftest_win_sdl3.c'),
            '/Fe' + str(out / 'selftest_win_sdl3.exe'), '/Fo' + str(out) + os.sep,
            '/link', str(library), '/libpath:' + str(msvc / 'lib/arm64'),
            '/libpath:' + str(sdk / 'Lib' / version / 'ucrt/arm64'),
            '/libpath:' + str(sdk / 'Lib' / version / 'um/arm64'),
            *sdl3.SYSTEM_LIBS, 'onecore.lib', '/subsystem:console']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--llvm', type=Path, required=True)
    a = p.parse_args()
    if os.name != 'nt' or os.environ.get('PROCESSOR_ARCHITECTURE') != 'ARM64':
        p.error('native Windows ARM64 required; no x64 emulation')
    hosted = (os.environ.get('GITHUB_ACTIONS') == 'true' and
              os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted' and
              os.environ.get('DHD_CI_ALLOW_C_OUTPUT') == '1')
    out = ROOT / 'build/host-sdl3-winarm64'
    if out.drive.upper() == 'C:' and not hosted:
        p.error('local build output must stay off C:')
    if not (a.llvm / 'clang-cl.exe').is_file() or not (a.llvm / 'lld-link.exe').is_file():
        p.error('clang-cl.exe and lld-link.exe are required')
    try:
        msvc, sdk, version = windows_arm64_paths(os.environ)
        out.mkdir(parents=True, exist_ok=True)
        # Reuse SDL3's exact pinned release, options and SHA-256 validation; the target is new.
        library, includes = sdl3.build('aarch64-pc-windows-msvc')
        print('Built SDL3 static ARM64:', library)
        cmd = link_command(a.llvm, msvc, sdk, version, library, includes, out)
        r = subprocess.run(cmd, cwd=out, capture_output=True, text=True, timeout=300)
        if r.returncode:
            raise RuntimeError('ARM64 SDL3 link failed:\n' + r.stdout + r.stderr)
        r = subprocess.run([str(out / 'selftest_win_sdl3.exe')], cwd=out,
                           capture_output=True, text=True, timeout=30)
        print(r.stdout + r.stderr, end='')
        if r.returncode or 'PASS: native Windows ARM64 SDL3' not in r.stdout:
            raise RuntimeError('ARM64 SDL3 smoke failed: exit %d' % r.returncode)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as e:
        p.error(str(e))


if __name__ == '__main__':
    main()
