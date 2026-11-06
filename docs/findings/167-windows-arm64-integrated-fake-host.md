# 167 — Exercise the integrated Windows ARM64 host with a synthetic guest

Status: in progress

Branch `azazel/win-arm64-fake-host`, stacked on the European-disc preflight
lane (finding 166), started 2026-11-06.

## Motivation

Findings 159-165 independently verified ARM64 fiber/guard switching, Win32
host services, SDL3, Rust/wgpu native library, the C/Rust ABI and architecture
routing. They **did not** compile the entire shared C host and link the real
SDL3/Rust libraries into one executable for native Windows ARM64. Doing so
may reveal incompatible intrinsics, ABI calls or missing imports before the
user's original Spanish PS2 ISO and ARM64 laptop are available.

## Deliberate scope

`build_host64.py --target win-arm64 --fake --run` generates its existing
synthetic, independent WASM fixture instead of consuming a retail executable
or any proprietary game data. `--fake` does not compile the game's VU1
microcode or produce a playable build. The normal game build remains blocked
by the original release's unsupported European executable (finding 100).

One Windows ARM64 GitHub Actions job starts with the already passing native
host-OS smoke and then installs, by version:

- WABT 1.0.42, fetched with its official SHA-256 (Windows x64 tool uses the
  operating system's x64 application compatibility); the native C runtime
  sources are compiled by ARM64 clang.
- wasi-sdk 34.0 native Windows ARM64, verified against the upstream release
  SHA-256, only for the synthetic WASM guest.
- SIMDe 0.8.2 headers, SDL3 3.4.18 pinned by `sdl3.py` and Rust 1.97.1,
  with the same locked Rust dependency graph as the proven native ABI lane.

The full host's C source list, Rust library and linker are unchanged from
the unified `build_host64.py`. The output PE machine architecture is checked
explicitly. A green result proves an integrated *test fixture*, **not** that
the actual game compiles, boots, runs at 60 fps or supports Spanish.

## Gates

1. `python -B tools/check.py docs` and synthetic disc tests remain green.
2. Native hosted Windows ARM64 CI builds/links all included C host objects,
   SDL3 and Rust, without a disc or third-party game data.
3. `--run` synthetic fixture and its 11 negative bounds/control cases exit
   successfully, then `windows_arm64_executable` confirms ARM64 PE machine.

## Progress

- [x] Add branch-scoped CI orchestration, with checked upstream tool archives.
- [ ] Hosted full synthetic ARM64 build succeeds.
- [ ] Hosted headless synthetic/negative tests pass.
- [ ] Real, unmodified European game core compiled and played on hardware
  (separate long-running release-support work, requiring the owner's ISO).
