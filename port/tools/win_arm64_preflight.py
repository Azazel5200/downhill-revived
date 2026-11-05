#!/usr/bin/env python3
"""Read-only Windows ARM64 toolchain preflight; no game image or build required.

Run in a Visual Studio developer shell before attempting a native Windows ARM64
host build.  This checks *presence* of prerequisites, not their suitability:
an ARM64 object, native fiber switch, renderer and game still need real tests.

    python port/tools/win_arm64_preflight.py
    python port/tools/win_arm64_preflight.py --json

Exit 0 only when every required prerequisite was found.  The native-machine
check is informational: x64 Windows can be used for cross-compilation.
"""

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

RUST_TARGET = 'aarch64-pc-windows-msvc'
TOOLS = ('clang-cl', 'lld-link', 'llvm-lib', 'llvm-rc', 'cmake', 'ninja',
         'cargo', 'rustc', 'rustup', 'cl')


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str
    required: bool = True


def sdk_version(environ):
    """WindowsSDKVersion often has a trailing slash; never concatenate it raw."""
    return environ.get('WindowsSDKVersion', '').strip().rstrip('\\/')


def requirements(system, machine, py_version, environ, available, rust_targets, python_bits=64):
    """Pure assessment, injectable for offline tests and Windows x64 cross builds."""
    result = [Check('Windows host', system == 'Windows',
                    'Windows is required to link the MSVC/Windows SDK host.')]
    result.append(Check('ARM64 host CPU', machine.upper() in ('ARM64', 'AARCH64'),
                        'An ARM64 machine is needed for native runtime tests; cross-compilation is allowed.',
                        required=False))
    result.append(Check('Python 3.12+', tuple(py_version) >= (3, 12),
                        'Use Python 3.12 or newer.'))
    result.append(Check('64-bit Python', python_bits == 64,
                        'Use a 64-bit Python interpreter for this build.'))

    for name in TOOLS:
        result.append(Check(name, bool(available.get(name)),
                            'Available on PATH.' if available.get(name) else
                            'Missing on PATH; use a VS developer shell / install the tool.'))

    vc_text = environ.get('VCToolsInstallDir', '').strip()
    vc = Path(vc_text) if vc_text else None
    vc_ok = vc is not None and (vc / 'lib' / 'arm64').is_dir()
    result.append(Check('MSVC ARM64 libraries', vc_ok,
                        'VCToolsInstallDir must contain lib/arm64. x64 libraries are not suitable.'))

    sdk_text = environ.get('WindowsSdkDir', '').strip()
    sdk = Path(sdk_text) if sdk_text else None
    version = sdk_version(environ)
    include_ok = bool(sdk and version and all((sdk / 'Include' / version / p).is_dir()
                                               for p in ('ucrt', 'um', 'shared')))
    result.append(Check('Windows SDK headers', include_ok,
                        'WindowsSdkDir and WindowsSDKVersion must select ucrt/um/shared headers.'))
    lib_ok = bool(sdk and version and all((sdk / 'Lib' / version / p / 'arm64').is_dir()
                                           for p in ('ucrt', 'um')))
    result.append(Check('Windows SDK ARM64 libraries', lib_ok,
                        'The SDK must contain Lib/<version>/{ucrt,um}/arm64.'))

    result.append(Check('Rust Windows ARM64 target', RUST_TARGET in rust_targets,
                        'Install with: rustup target add aarch64-pc-windows-msvc.'))
    return result


def installed_rust_targets():
    if not shutil.which('rustup'):
        return set()
    try:
        r = subprocess.run(['rustup', 'target', 'list', '--installed'],
                           capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return set()
    return set(r.stdout.splitlines()) if r.returncode == 0 else set()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--json', action='store_true', help='print structured results to stdout')
    args = parser.parse_args(argv)
    checks = requirements(platform.system(), platform.machine(),
                          sys.version_info[:2], os.environ,
                          {name: shutil.which(name) for name in TOOLS}, installed_rust_targets(),
                          python_bits=64 if sys.maxsize > 2**32 else 32)
    missing = [c.name for c in checks if c.required and not c.ok]
    if args.json:
        print(json.dumps({'target': RUST_TARGET, 'ready_for_compile_attempt': not missing,
                          'checks': [asdict(c) for c in checks]}, ensure_ascii=False, indent=2))
    else:
        print('Windows ARM64 preflight (prerequisites only; no compilation or game test)')
        for check in checks:
            state = 'OK' if check.ok else 'INFO' if not check.required else 'MISSING'
            print(f'  [{state}] {check.name}: {check.detail}')
        print('Result: prerequisites found' if not missing else
              'Result: prerequisites missing: ' + ', '.join(missing))
        print('Next gates: ARM64 object / fiber test / renderer / actual device.')
    return int(bool(missing))


if __name__ == '__main__':
    sys.exit(main())
