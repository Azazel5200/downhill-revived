# 157 — Identificación de recursos españoles en el disco europeo

Status: in progress

Branch `azazel/es-disc-inventory` from `main` 5a38832, started 2026-11-05.

## Goal and acceptance

The user's requested port must be playable with Spanish menus and text. The
upstream `100-other-releases.md` documents that Europe's `SLES-52202` disc has
Spanish menu and bike-shop resource variants, plus five language tables in
the European ELF. The current native port accepts **USA only**.

This lane makes a small, **read-only** check of the local European disc's
filenames. It does not extract or upload assets, translate the game, or imply
that a European disc is supported as the game's boot image.

    python port/tools/spanish_disc_inventory.py /path/to/own-europe.iso --json
    python -m unittest discover -s port/tools -p test_spanish_disc_inventory.py -v

The inventory succeeds only if `SYSTEM.CNF` boots `SLES_522.02` and both the
`SHELL/UIS.*` and `SHELL/BIKESHPS.*` families are present. The ISO 9660 reader
is reused from `release_compare.py`; tests generate synthetic ISO data only.

## Progress

- [x] 2026-11-05: minimal inventory and synthetic ISO 9660 tests written.
- [x] 2026-11-06: three tests passed (European image, USA region and missing
  bike-shop resource); `python tools/check.py docs` passed both checks.
- [ ] Verify a genuine user-provided European ISO locally (no upload).
- [ ] Determine how the localization is integrated with the USA game core or
  whether a European core is unavoidable, then test the game menus.

## Decisions

- Check file names and region only, not copyrighted file contents.
- Print only counts and availability; do not copy, hash or print game data.
- Separate graphics resources from the European ELF's five-language text
  tables. Passing this check is **not** Spanish-language gameplay.
- Movies and loading screens may contain other localized resources not covered
  by this quick gate; their filenames are only informational.

## Surprises

Awaiting tests on an actual European ISO. Our synthetic fixtures validate the
reader and gating, not the documented content of the retail disc.

The broader `python tools/check.py port` check reached `build_wasm` but could
not compile because this environment has no `clang` binary (and no personal
game image). No game build or gameplay localization is claimed.

## Result

Pending integration with the game and on-device testing.
