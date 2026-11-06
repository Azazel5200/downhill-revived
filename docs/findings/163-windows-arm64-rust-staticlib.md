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
- [x] 2026-11-06: native [CI run 42172540886](https://github.com/Azazel5200/downhill-revived/actions/runs/42172540886)
  built `dhd_render.lib` and passed the full wrapper, dependency, provenance,
  archive-machine and SHA-256 gates; report uploaded as a short-lived CI artifact.

## Decisions

- `rustgs.py` remains the only Cargo build path, including its fully offline
  dependency and ABI checks. `cargo fetch --locked` happens first on the ephemeral
  runner, exactly as in finding 162.
- The ARM64 allowed native library list began with the known Windows x64 system
  libraries. The first native build emitted one additional name,
  `windows.0.52.0.lib`, from the locked Windows crate graph. This exact name is
  allowed **only** for ARM64; no blanket relaxation of the gate.
- A separate COFF verifier examines member headers rather than attempting to run
  the graphics engine without a display. It checks bytes on disk and the wrapper's
  digest without loading the entire archive into memory.
- GitHub's disposable C: runner remains an opt-in exception; the user's own
  off-C: requirement is unchanged.

## Surprises

- First native [CI run 42171855946](https://github.com/Azazel5200/downhill-revived/actions/runs/42171855946):
  the host service smoke and full `cargo check` passed. `cargo rustc --crate-type
  staticlib` then finished, and `rustgs` normalized **60** COFF `S_OBJNAME` records.
  Its post-build gate refused exactly one new `native-static-libs` entry:
  `windows.0.52.0.lib`. No compiler or CPU-architecture error was reported.
  Add that exact, observed library to the target-specific allow-list and rerun;
  the validator and final report were not reached on this attempt.
- Second native [CI run 42172540886](https://github.com/Azazel5200/downhill-revived/actions/runs/42172540886)
  passed all jobs. It compiled in release profile with Rust 1.97.1, normalized the
  same 60 `S_OBJNAME` records, and the streamed archive validator found **2,427 ARM64
  COFF objects** (no recognized x86/x64 objects) in **19,746,805** archived bytes.
  The library's SHA-256 was
  `1df5c1613e33738a2353bc411bc8b1739194f85ec83659d399243f8947ed0268`.
  The run uploaded a `rustgs` JSON report, **not** the compiled library itself.

## References

- [Rust linkage reference: native static libraries and `--print native-static-libs`](https://doc.rust-lang.org/reference/linkage.html).
- [Rust MSVC targets: PE/COFF and Windows ARM64](https://doc.rust-lang.org/rustc/platform-support/windows-msvc.html).
- [ring Windows ARM64 clang requirement](https://github.com/briansmith/ring/blob/main/BUILDING.md).

## Result

**The native Windows ARM64 Rust/wgpu static library build and validation passed.**
Do not claim the full game is ported until the C host can link this library and
the game's display, input, sound, state and performance run on appropriate hardware.
The compiled `.lib` existed on the ephemeral CI runner; it was not published as a
downloadable binary. Keep this finding `in progress` until the draft lane is integrated.
