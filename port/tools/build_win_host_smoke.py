#!/usr/bin/env python3
"""Compile and run the asset-free host_win32.c adapter on native Windows ARM64 or x64.

Uses the same validated VS/Windows SDK architecture paths as build_host64.py's fiber smoke.
Does not enable or imply a full ARM64 game build.
"""
import argparse
import os
from pathlib import Path
import subprocess

from build_host64 import windows_developer_paths

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / 'port/host'


def command(arch, llvm, out, env):
    msvc, sdk, version = windows_developer_paths(env, arch)
    clang, linker = llvm / 'clang-cl.exe', llvm / 'lld-link.exe'
    if not clang.is_file() or not linker.is_file():
        raise RuntimeError('clang-cl.exe and lld-link.exe are both required under --llvm')
    triple = {'arm64': 'aarch64-pc-windows-msvc', 'x64': 'x86_64-pc-windows-msvc'}[arch]
    return [str(clang), '--target=' + triple, '-fuse-ld=lld', '/nologo', '/O2', '/MT',
            '/imsvc' + str(msvc / 'include'),
            *['/imsvc' + str(sdk / 'Include' / version / x) for x in ('ucrt', 'um', 'shared')],
            str(HOST / 'host_win32.c'), str(HOST / 'selftest_win_host.c'),
            '/Fe' + str(out / 'selftest_win_host.exe'), '/Fo' + str(out) + os.sep,
            '/link', '/libpath:' + str(msvc / 'lib' / arch),
            '/libpath:' + str(sdk / 'Lib' / version / 'ucrt' / arch),
            '/libpath:' + str(sdk / 'Lib' / version / 'um' / arch),
            'onecore.lib', 'advapi32.lib', '/subsystem:console']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--arch', choices=('arm64', 'x64'), required=True)
    p.add_argument('--llvm', type=Path, required=True, help='folder with clang-cl.exe and lld-link.exe')
    a = p.parse_args()
    if os.name != 'nt':
        p.error('this executable must compile and run on native Windows')
    expected = 'ARM64' if a.arch == 'arm64' else 'AMD64'
    if os.environ.get('PROCESSOR_ARCHITECTURE', '').upper() != expected:
        p.error('requires native Windows %s, not emulation or cross-execution' % expected)
    out = ROOT / 'build' / ('host-os-win-' + a.arch)
    # A hosted runner's system disk is disposable. Keep all local outputs off C:.
    hosted = (os.environ.get('GITHUB_ACTIONS') == 'true' and
              os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted' and
              os.environ.get('DHD_CI_ALLOW_C_OUTPUT') == '1')
    if out.drive.upper() == 'C:' and not hosted:
        p.error('build output must stay off C:')
    out.mkdir(parents=True, exist_ok=True)
    try:
        cmd = command(a.arch, a.llvm, out, os.environ)
        result = subprocess.run(cmd, cwd=out, capture_output=True, text=True, timeout=300)
        if result.returncode:
            raise RuntimeError('compiler failed:\n' + result.stdout + result.stderr)
        result = subprocess.run([str(out / 'selftest_win_host.exe')], cwd=out,
                                capture_output=True, text=True, timeout=30)
        print(result.stdout + result.stderr, end='')
        if result.returncode or 'PASS: Windows host OS:' not in result.stdout:
            raise RuntimeError('host OS smoke failed: exit %d' % result.returncode)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        p.error(str(exc))


if __name__ == '__main__':
    main()
