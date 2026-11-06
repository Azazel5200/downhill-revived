# 166 — Identify the player's own European disc without extracting anything

Status: in progress

Branch `azazel/eu-disc-preflight` stacked on the experimental Windows ARM64
host-routing lane (finding 165), started 2026-11-06.

## Problem

The original game port only supports `SCUS_971.77`, the USA disc. The
owner's legally backed-up Spanish PS2 game is likely the five-language
`SLES_522.02` European edition. Those are **not** interchangeable disc
assets: the European executable, data offsets and tracks differ (finding 100).
The ARM64 renderer, native switch, SDL3 and host routing work is independent
of this release-compatibility blocker.

The existing `release_compare.py` can compare two full locally supplied
images, but the owner has only **one** legal disc image and will not download
another region's release. The owner needs a one-disc, read-only preflight.

## Implementation

- `port/tools/disc_probe.py` reuses the repository's existing ISO 9660 walk.
- Read `SYSTEM.CNF` and validate the boot ELF exists, then report the serial,
  region, version, video mode, number of files, boot ELF size and SHA-256.
- The entire ISO SHA-256 is optional (`--hash-iso`); the default reads only
  the volume catalog, `SYSTEM.CNF` and the boot ELF. No game bytes are printed,
  exported, rewritten or uploaded.
- Recognize USA, European and Japanese PS2 boot serials. Make explicit that
  recognizing a European disc **does not** imply its native port is done.
- Test on synthetic ISO images with a fake boot header; never include a retail
  ISO or extracted executable in the test tree.

## Verification

    python -B -m unittest discover -s port/tools -p test_disc_probe.py -v
    python -B tools/check.py docs

The local tests cover European/Spanish and USA serials, optional whole-ISO
hashing, absent/malformed `SYSTEM.CNF`, absent ELF and invalid ISO descriptor,
plus metadata-only CLI output. Real-disc validation is still pending.

## Later, with the owner's laptop

    python -B port/tools/disc_probe.py "D:\\My Games\\Downhill.iso"

The example path is a placeholder, not a known location or file on the
owner's computer. Paste only the resulting text metadata. The ISO remains on
the owner's storage. The European core will still require separate development
and real on-device validation; this preflight only identifies that exact task.
