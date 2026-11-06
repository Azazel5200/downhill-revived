# 165 — Route the unified Windows game host build to ARM64

Status: in progress

Branch `azazel/win-arm64-host-routing` stacked on the draft ARM64 Rust C ABI lane
`azazel/win-arm64-rust-abi` (finding 164), started 2026-11-06.

## Goal and acceptance

Make `port/tools/build_host64.py` select an ARM64 Windows compiler, SDL3 static
library, MSVC/SDK paths, real Rust renderer library and final native linker via
the existing `win-arm64` target. The same host and renderer C units remain
shared with x64. Do not add a parallel host or renderer implementation.

Acceptance at this stage:

1. `python -B -m unittest discover -s port/tools -p test_win_arm64_host_routing.py -v`
   verifies the ARM64 compiler, SDK paths, SDL source target and linker flags,
   while x64 retains its previous codegen flags.
2. `python -B -m unittest discover -s port/tools -p test_win_arm64_fiber_target.py -v`
   still passes; all earlier ARM64 unit tests remain green.
3. `python -B tools/check.py docs` passes, with no retail assets in the branch.
4. Native hosted Windows ARM64 CI executes the routing checks and existing
   host OS smoke. This is deliberately not represented as a complete game build.

Out of scope: reconstructing the game's wasm module without a retail disc,
compiling all full-game C units, running the game, initializing a GPU, testing
controllers/sound or measuring frame rate. The full-host build still requires
the caller's own local game data and microcode to actually run. ARM64 game
readiness must not be inferred from a successful architecture routing check.

## Progress

- [x] 2026-11-06: select Windows ARM64 clang-cl, original shared C host, dedicated
  SDK libraries and the previously validated `aarch64-pc-windows-msvc` Rust/static
  renderer through one `build_host64.py` code path.
- [x] 2026-11-06: select pinned SDL3's architecture-specific archive, target the
  final executable with `/machine:arm64`, and resolve the exact Cargo import
  library through the same ARM64 COFF gate used in finding 164.
- [x] 2026-11-06: allow the existing Windows-only `--fake` host fixture on ARM64;
  omit retail VU1 compilation only in that independent fixture.
- [x] 2026-11-06: add no-disc architecture selection tests and CI routing gate.
- [x] 2026-11-06: hosted Windows ARM64 CI run 42208574537 passed the
  native routing and existing Windows host OS smoke. The independent tree and
  docs check passed too; no complete native game was compiled.
- [ ] Run an actual full host link and boot with a supported retail disc on a
  suitable tester machine, then its graphics, audio, frame and state gates.

## Decisions

- Preserve `win-x64`'s original MSVC/SDK defaults, target-specific optimization
  flags and host source list. ARM64 must come from a Windows developer shell that
  genuinely exposes ARM64 libraries, never from x64 substitution.
- Preserve the successful native renderer staticlib's platform-native import
  library lookup instead of copying a `.lib` between architectures.
- No game assets, modified game code, GPU or localization changes are included.

## Surprises

- The existing host build script previously rejected every ARM64 request except
  the fiber test, even though separate native CI already proved SDL3, the Rust
  staticlib and the C→Rust ABI independently.
- The local game copy is described as Spanish. The upstream port's only
  supported retail code/data image is the **USA disc**. Finding 100 establishes
  that the European multilang disc (`SLES_522.02`) has a different ELF, data
  layout and content. Making this ARM64 host buildable does **not** make the
  Spanish disc bootable; its own core/release support is an independent task.

## Result

The shared Windows host's architecture selection is now available for ARM64,
unit tested and checked on a native hosted Windows ARM64 runner.
**No complete ARM64 game compilation, runtime or
performance claim** follows from the routing tests. Retain `in progress`
until the pending hosted CI and original-disc milestones are verified.
