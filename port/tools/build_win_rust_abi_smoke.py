"""Link and run the no-disc Windows ARM64 C -> dhd_render.lib ABI fixture on a native runner."""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

import check_arm64_coff

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'port' / 'tools' / 'selftest_win_rust_abi.c'
HEADER = ROOT / 'port' / 'render' / 'include'
WINDOWS_052_IMPORT = 'windows.0.52.0.lib'


def windows_arm64_executable(path):
    data = Path(path).read_bytes()
    if len(data) < 0x40 or data[:2] != b'MZ':
        raise ValueError('not a Windows executable')
    offset = struct.unpack_from('<I', data, 0x3c)[0]
    if offset + 6 > len(data) or data[offset:offset + 4] != b'PE\0\0':
        raise ValueError('missing Windows PE header')
    machine = struct.unpack_from('<H', data, offset + 4)[0]
    if machine != check_arm64_coff.MACHINE_ARM64:
        raise ValueError('executable machine is 0x%04x, not native ARM64' % machine)


def cargo_windows_import_paths(cargo_home, native_static_libs):
    """Find *only* the target-locked Windows ARM64 import lib in Cargo's registry.

    Rust's linker gets this -L automatically from the windows-targets crate; the
    independent C host linker needs the same directory explicitly. No x64 fallback.
    """
    windows_libs = [lib for lib in native_static_libs if re.fullmatch(r'windows\.\d+\.\d+\.\d+\.lib', lib)]
    if not windows_libs:
        return []
    if windows_libs != [WINDOWS_052_IMPORT]:
        raise ValueError('unexpected Windows import library list: %r' % windows_libs)
    root = Path(cargo_home) / 'registry' / 'src'
    found = sorted(root.glob('*/windows_aarch64_msvc-0.52.6/lib/' + WINDOWS_052_IMPORT))
    if len(found) != 1:
        raise ValueError('expected exactly one locked Windows ARM64 import library under Cargo registry, found %d' % len(found))
    # An ARM64 import archive is COFF too; do not accidentally link the x64 package.
    check_arm64_coff.archive_machine_summary(found[0])
    return ['/libpath:' + str(found[0].parent)]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--llvm', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args(argv)
    if os.name != 'nt' or os.environ.get('PROCESSOR_ARCHITECTURE') != 'ARM64':
        p.error('the C/Rust ABI smoke must run on native Windows ARM64')
    if not (os.environ.get('GITHUB_ACTIONS') == 'true' and
            os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted' and
            os.environ.get('DHD_CI_ALLOW_C_OUTPUT') == '1'):
        p.error('the C: hosted-runner build requires the explicit CI-only opt-in')
    count, _size, _sha = check_arm64_coff.verify_report(args.report)
    report = json.loads(args.report.read_text(encoding='utf-8'))
    lib = Path(report['lib'])
    clang = args.llvm / 'clang-cl.exe'
    linker = args.llvm / 'lld-link.exe'
    if not clang.is_file() or not linker.is_file():
        p.error('ARM64 clang-cl.exe and lld-link.exe are required')
    args.out.mkdir(parents=True, exist_ok=True)
    obj, exe = args.out / 'selftest_win_rust_abi.obj', args.out / 'selftest_win_rust_abi.exe'
    cc = [str(clang), '--target=aarch64-pc-windows-msvc', '/nologo', '/O2', '/MT', '/c',
          '/I' + str(HEADER), '/Fo' + str(obj), str(SOURCE)]
    link = [str(linker), '/nologo', '/machine:arm64', '/subsystem:console', '/out:' + str(exe),
            str(obj), str(lib), *report['native_static_libs']]
    # Respect the real VS ARM64 developer environment's LIB paths; do not read an x64 SDK.
    if not os.environ.get('LIB'):
        p.error('the native VS developer environment must supply ARM64 LIB paths')
    try:
        link += cargo_windows_import_paths(os.environ['CARGO_HOME'], report['native_static_libs'])
    except (OSError, ValueError, KeyError) as exc:
        p.error('locked ARM64 Rust import library unavailable: %s' % exc)
    for cmd in (cc, link):
        print('  + ' + ' '.join(cmd), flush=True)
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, errors='replace')
        if proc.returncode:
            raise SystemExit('ARM64 ABI compile/link failed (%d):\n%s' % (
                proc.returncode, (proc.stdout + proc.stderr)[-6500:]))
    windows_arm64_executable(exe)
    proc = subprocess.run([str(exe)], cwd=str(args.out), capture_output=True, text=True,
                          errors='replace', timeout=30)
    if proc.returncode or 'PASS: native ARM64 C -> Rust renderer ABI:' not in proc.stdout:
        raise SystemExit('ARM64 ABI executable failed (%d):\n%s' % (
            proc.returncode, (proc.stdout + proc.stderr)[-3500:]))
    print(proc.stdout.strip(), flush=True)
    print('PASS: linked and executed %s (source archive: %d ARM64 COFF objects)' % (exe.name, count))
    return 0


if __name__ == '__main__':
    sys.exit(main())
