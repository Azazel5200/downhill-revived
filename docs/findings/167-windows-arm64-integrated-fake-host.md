# 167 — Exercise the integrated Windows ARM64 host with a synthetic guest

Status: current

Synthetic ARM64 host integration **verified**; real European game core remains
pending under finding 100.

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
- [x] First integrated attempt, run 42210359542: WABT 1.0.42 and native wasi-sdk
  34.0 were fetched and SHA-256 verified; SDL3 compiled in 112.9 s and the
  actual native ARM64 Rust renderer staticlib compiled in 181.8 s; synthetic
  wasm2c preparation also succeeded. Compilation then exposed 20 x64-only
  Windows CONTEXT register references in port/hle/host.c, starting with
  Rsp and Rip, plus x64 hardware debug-register assumptions.
- [x] Select Pc/Sp and X[0..30] on Windows ARM64 for diagnostics, capture
  ARM64 backtraces with RtlCaptureContext, retain x64's existing fields and
  debug-watchpoint path unchanged. On Windows ARM64, report unsupported
  hardware watchpoints and direct the user to portable DHD_STATE_WATCH.
  The next hosted compilation must verify these changes.
- [x] Second integrated attempt, run 42213666366: SDL3 compiled in 126.1 s,
  Rust staticlib compiled in 182.0 s, and the synthetic guest converted. The
  ARM64-specific CONTEXT errors were gone; the next compiler error identified
  one remaining registration of the x64-only watchpoint handler in host_init.
  Gate its registration alongside its x64-only definition. Also explicitly
  route ARM64 SIMD audio/VIF through SIMDe and ARM64 graphics-queue FP control
  through its native FPCR path, preserving all x64 branches.
- [x] Third integrated attempt, run 42214851075: SDL3 compiled in 114.4 s,
  Rust staticlib in 175.3 s; neither CONTEXT registers nor x64 watchpoint
  registration failed again. The next compiler error was SIMDe 0.8.2's
  `atomic_thread_fence` / `memory_order_seq_cst` undeclared in the Windows
  ARM64 VIF compile. Include the C11 atomic definitions explicitly ahead of
  SIMDe on the ARM64 VIF and VU paths. The next hosted build must verify it.
- [x] Fourth integrated attempt, run 42215985852: SDL3 compiled in 107.2 s,
  Rust staticlib in 180.3 s. The SIMDe atomic-fence error disappeared, and
  `vu0_interp.c` reached its next native ARM64 compile error: Windows SDK
  `rpcndr.h` defines `small` as a macro, colliding with two local vector-mask
  variables. Rename only those locals to `subnormal_mask` with unchanged math.
  For synthetic CI retries, compile the C fixture before the costly Rust
  staticlib; real game builds retain their existing Rust-first ordering.
- [x] Fifth integrated attempt, run 42217102692: **success**. The complete
  Windows ARM64 host compiled 40 C host objects and 35 generated WASM imports,
  linked SDL3 3.4.18 and the Rust renderer (wgpu 29.0.3) into an ARM64 PE
  executable (3.1 MiB), exited normally (`host64 module exit: 0`) and passed
  all 11 out-of-bounds/invalid indirect-call negative fixture tests. The PE
  machine check confirmed the executable is native ARM64. C finished in 4.9 s
  before Rust was built, validating the fake-C-first ordering. No retail ISO,
  actual game executable, or GPU-based graphics benchmark was used.
- [x] Hosted full synthetic ARM64 build succeeds.
- [x] Hosted headless synthetic/negative tests pass.
- [ ] Real, unmodified European game core compiled and played on hardware
  (separate long-running release-support work, requiring the owner's ISO).
