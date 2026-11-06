# 163 — Windows ARM64 Rust/wgpu static library build and archive validation

Status: in progress

Branch `azazel/win-arm64-rust-staticlib` stacked on the green renderer compile-check
branch (`azazel/win-arm64-rust-check`, finding 162), started 2026-11-06. This is a
separate **experimental preflight**, not a release and not a full game executable.

## Goal and acceptance

Build the actual `dhd_render.lib` for `aarch64-pc-windows-msvc` with the same pinned
Rust 1.97.1 and dependency graph already checked in finding 162. Use the existing
`rustgs.py` wrapper and its version, include, dependency, provenance and native-library
gates. Verify that the output archive contains ARM64 COFF objects, no known x86/x64
objects, and matches the wrapper's reported SHA-256.

Acceptance:

1. Local asset-free `python -B -m unittest discover -s port/tools -p
   'test_arm64_coff.py' -v` and `test_win_arm64_rust_target.py` pass.
2. `python tools/check.py docs` passes.
3. On native Windows ARM64 GitHub hosted CI, `ci_win_host_smoke.ps1 -Arch arm64
   -RustBuild` first checks the Windows host services and the Rust graph, then
   executes `python -B port/tools/rustgs.py build --target aarch64-pc-windows-msvc
   --no-cache --report ...` and `check_arm64_coff.py --report ...`.
4. Preserve the verified report as a CI artifact, never copyrighted game data.

This does not yet link the C/wasm2c game host, initialize a GPU, play sounds or
measure frame rates. No user laptop or game disc is needed for this phase.

## Progress

- [x] 2026-11-06: isolate the ARM64 staticlib preflight in a new stacked branch.
- [x] 2026-11-06: extend the existing Rust wrapper's COFF CodeView path normalization
  to ARM64; use a target-specific native-library allow-list and a streamed CPU
  architecture check to reject accidental x64 archive members.
- [ ] Native CI actually builds and validates `dhd_render.lib`.

## Decisions

- `rustgs.py` remains the only Cargo build path, including its fully offline
  dependency and ABI checks. `cargo fetch --locked` happens first on the ephemeral
  runner, exactly as in finding 162.
- The provisional ARM64 allowed native system libraries mirror the known Windows
  x64 list. Only the actual ARM64 `native-static-libs` output can justify adding
  another library to this target-specific list.
- A separate COFF verifier examines member headers rather than attempting to run
  the graphics engine without a display. It checks bytes on disk and the wrapper's
  digest without loading the entire archive into memory.
- GitHub's disposable C: runner remains an opt-in exception; the user's own
  off-C: requirement is unchanged.

## Surprises

None recorded yet. Build failures and their exact evidence belong here.

## References

- [Rust linkage reference: native static libraries and `--print native-static-libs`](https://doc.rust-lang.org/reference/linkage.html).
- [Rust MSVC targets: PE/COFF and Windows ARM64](https://doc.rust-lang.org/rustc/platform-support/windows-msvc.html).
- [ring Windows ARM64 clang requirement](https://github.com/briansmith/ring/blob/main/BUILDING.md).

## Result

Pending the native Windows ARM64 static library build. Do not claim the full game
is ported until host linkage, display, input, sound, state and performance checks
run on the appropriate hardware.
