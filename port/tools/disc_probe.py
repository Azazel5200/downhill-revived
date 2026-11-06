"""Identify a player's own Downhill Domination PS2 ISO without extracting game data.

    python -B port/tools/disc_probe.py "D:/Games/Downhill.iso"
    python -B port/tools/disc_probe.py "D:/Games/Downhill.iso" --hash-iso

Only textual metadata, file counts/sizes and cryptographic hashes are printed.
No game file is written, uploaded or modified. An ISO is required only on the
player's own machine; the diagnostics can be shared without sharing its bytes.
"""

import argparse
import hashlib
from pathlib import Path
import re

from release_compare import Iso


KNOWN_RELEASES = {
    'SCUS_971.77': ('USA (NTSC)', 'Upstream USA game core; ARM64 port still experimental'),
    'SLES_522.02': ('Europe (PAL, five languages including Spanish)',
                    'Requires a separate European game core; not currently playable in this port'),
    'SCPS_150.62': ('Japan (NTSC), MT Bikers',
                    'Requires a separate Japanese game core; not currently playable in this port'),
}
BOOT = re.compile(r'^\s*BOOT2?\s*=\s*cdrom0:\\([A-Za-z]{4}_[0-9]{3}\.[0-9]{2})(?:;[0-9]+)?\s*$', re.I | re.M)
CNF_FIELD = re.compile(r'^\s*(VER|VMODE)\s*=\s*([^\r\n]+)', re.I | re.M)


def file_digest(iso, name):
    """Stream one ISO member through SHA-256; do not retain or export its bytes."""
    lsn, size = iso.files[name]
    iso.f.seek(lsn * 2048)
    h = hashlib.sha256()
    left = size
    while left:
        chunk = iso.f.read(min(left, 1 << 20))
        if not chunk:
            raise ValueError('truncated ISO while hashing the boot executable')
        h.update(chunk)
        left -= len(chunk)
    return h.hexdigest()


def identify(path, hash_iso=False):
    """Return shareable facts about a PS2 disc; never return the disc payload."""
    path = Path(path)
    if not path.is_file():
        raise ValueError('ISO does not exist or is not a regular file')
    # release_compare.Iso assumes a valid 2048-byte-sector image and leaves its
    # handle open when a short PVD raises. Validate before handing the file over.
    with path.open('rb') as source:
        source.seek(16 * 2048)
        pvd = source.read(6)
    if pvd != b'\x01CD001':
        raise ValueError('not a readable 2048-byte-sector ISO 9660 image')
    image = Iso(path)
    try:
        try:
            cnf = image.read('SYSTEM.CNF').decode('ascii', 'replace')
        except KeyError as error:
            raise ValueError('SYSTEM.CNF not found in ISO root') from error
        boot = BOOT.search(cnf)
        if not boot:
            raise ValueError('BOOT2 serial not found in SYSTEM.CNF')
        serial = boot.group(1).upper()
        if serial not in image.files:
            raise ValueError('SYSTEM.CNF points to a missing boot executable')
        fields = {m.group(1).upper(): m.group(2).strip() for m in CNF_FIELD.finditer(cnf)}
        region, support = KNOWN_RELEASES.get(serial, ('Other / unrecognized release',
                                                      'Not supported by the USA game core'))
        info = {
            'serial': serial,
            'region': region,
            'support': support,
            'version': fields.get('VER', 'not specified'),
            'video_mode': fields.get('VMODE', 'not specified'),
            'files': len(image.files),
            'boot_size': image.files[serial][1],
            'boot_sha256': file_digest(image, serial),
        }
    finally:
        image.f.close()
    if hash_iso:
        h = hashlib.sha256()
        with path.open('rb') as source:
            for chunk in iter(lambda: source.read(1 << 20), b''):
                h.update(chunk)
        info['iso_sha256'] = h.hexdigest()
    return info


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('iso', type=Path, help='local ISO image of your own PS2 disc')
    p.add_argument('--hash-iso', action='store_true', help='also stream/hash the whole ISO (slower)')
    args = p.parse_args(argv)
    try:
        info = identify(args.iso, args.hash_iso)
    except (OSError, ValueError) as error:
        p.error(str(error))
    print('Downhill PS2 disc metadata (no game data extracted)')
    print('Boot serial:   ' + info['serial'])
    print('Release:       ' + info['region'])
    print('Disc version:  ' + info['version'])
    print('Video mode:    ' + info['video_mode'])
    print('Files:         ' + str(info['files']))
    print('Boot ELF size: ' + str(info['boot_size']) + ' bytes')
    print('Boot SHA-256:  ' + info['boot_sha256'])
    if 'iso_sha256' in info:
        print('ISO SHA-256:   ' + info['iso_sha256'])
    print('Port status:   ' + info['support'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
