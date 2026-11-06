"""Validate that rustgs's Windows ARM64 .lib really contains ARM64 COFF objects.

This deliberately streams the archive: a release Rust staticlib may be hundreds of MB.
The existing check_rust_lib gate separately checks paths, runtime libraries and provenance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

MACHINE_ARM64 = 0xAA64
OTHER_COFF_MACHINES = {0x014C, 0x01C4, 0x8664}


def archive_machine_summary(path):
    """Return (ARM64 COFF object count, archived bytes); reject other known CPU objects."""
    arm64 = total = 0
    with Path(path).open('rb') as stream:
        if stream.read(8) != b'!<arch>\n':
            raise ValueError('not a COFF static library archive')
        while True:
            header = stream.read(60)
            if not header:
                break
            if len(header) != 60 or header[58:60] != b'`\n':
                raise ValueError('truncated or malformed archive member header')
            try:
                size = int(header[48:58].strip())
            except ValueError as exc:
                raise ValueError('bad archive member size') from exc
            start = stream.tell()
            name = header[:16].strip()
            body = stream.read(min(size, 20))
            if len(body) < min(size, 20):
                raise ValueError('truncated archive member')
            # Skip the archive linker symbol tables and longname table, not /123 longname refs.
            if name not in (b'/', b'//', b'/SYM64/') and len(body) >= 20:
                machine, sig = struct.unpack_from('<HH', body)
                if (machine, sig) == (0, 0xFFFF):
                    # Bigobj (or import-object) header: architecture is the third u16.
                    machine = struct.unpack_from('<H', body, 6)[0]
                if machine == MACHINE_ARM64:
                    arm64 += 1
                elif machine in OTHER_COFF_MACHINES:
                    raise ValueError('%s contains non-ARM64 COFF machine 0x%04x' % (name, machine))
            total += size
            stream.seek(start + size + (size & 1))
            if stream.tell() > Path(path).stat().st_size:
                raise ValueError('archive member extends past EOF')
    if not arm64:
        raise ValueError('no ARM64 COFF objects found')
    return arm64, total


def verify_report(path):
    report = json.loads(Path(path).read_text(encoding='utf-8'))
    if report.get('triple') != 'aarch64-pc-windows-msvc':
        raise ValueError('the report is not for Windows ARM64')
    lib = Path(report['lib'])
    if lib.name != 'dhd_render.lib' or not lib.is_file():
        raise ValueError('the ARM64 static library is missing')
    digest = hashlib.sha256()
    with lib.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != report['sha256']:
        raise ValueError('library differs from rustgs report SHA-256')
    count, size = archive_machine_summary(lib)
    return count, size, digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        count, total, digest = verify_report(args.report)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, 'ARM64 staticlib validation FAILED: %s\n' % exc)
    print('PASS: ARM64 staticlib: %d ARM64 COFF objects, %d archived bytes, SHA-256 %s' % (
        count, total, digest))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
