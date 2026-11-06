# 164 — Windows ARM64 C host to Rust renderer: isolated ABI link smoke

Status: in progress

Branch `azazel/win-arm64-rust-abi` stacked on the green static library branch
`azazel/win-arm64-rust-staticlib` (finding 163), started 2026-11-06. This is a
separate **experimental no-disc preflight**, not a release or full game build.

## Goal and acceptance

Compile a tiny Windows ARM64 C program that uses the frozen `dhd_render.h` ABI,
links against the **real native Rust/wgpu `dhd_render.lib`** (not a C stub
library), and runs on a hosted Windows ARM64 machine. It calls `dhdr_version()`
and verifies `dhdr_device_features()==0` before GPU initialization. Its only
C callback is an asset-free `dhd_host_log` stub. It must verify the resulting
PE machine ID is 0xAA64 and refuse to run on x64 or on an ordinary user device.

Acceptance:

1. `python -B -m unittest discover -s port/tools -p 'test_win_rust_abi.py' -v`
   and the existing ARM64 Rust/COFF routing tests pass locally.
2. `python -B tools/check.py docs` passes.
3. GitHub's native Windows 11 ARM64 runner builds the renderer with the
   validated `rustgs.py` path, runs the `check_arm64_coff` archive gate, then
   compiles the small C fixture with `clang-cl` and links it through `lld-link`
   using the actual Rust-reported native static libraries.
4. The linked ARM64 executable prints a C→Rust ABI `PASS` line and returns 0;
   publish only this standalone no-game selftest as a short-lived CI artifact.

Not in scope: `build_host64.py --target win-arm64` for the complete game, SDL3
presentation, wasm2c, GPU adapter creation, sound, input, frame rate or online
play. No original disc or user's laptop is needed.

## Progress

- [x] 2026-11-06: add a C-to-Rust version/feature call fixture with no data
  files, no GPU initialization and a self-contained log bridge.
- [x] 2026-11-06: add native ARM64 compiler/linker routing and PE header check,
  limited to GitHub's hosted disposable ARM64 runner.
- [x] 2026-11-06: native [CI run 42174405666](https://github.com/Azazel5200/downhill-revived/actions/runs/42174405666)
  passed C compilation, C→Rust linking, PE machine verification and the
  standalone ARM64 executable's two ABI checks.

## Decisions

- Reuse the already-validated `dhd_render.lib` from `rustgs.py`; do not modify
  the renderer ABI or the existing x64 game code.
- Use the MSVC/SDK ARM64 environment established by the same Windows host
  smoke used in findings 160–163. Never treat an x64 import library as proof
  of an ARM64 link.
- The Windows `windows.0.52.0.lib` from Rust's locked `windows_aarch64_msvc
  0.52.6` package resides under Cargo's registry, not the Visual Studio SDK.
  Only that exact ARM64 import archive's verified directory can be added to
  the independent C link command.
- Check a pure API before creating a GPU device, since GitHub's headless runner
  cannot establish the user's Adreno performance or rendering behaviour.

## Surprises

- First native [CI run 42173632092](https://github.com/Azazel5200/downhill-revived/actions/runs/42173632092):
  the real Rust ARM64 library built and passed all gates again (2,427 COFF ARM64
  members); `clang-cl` compiled the C fixture to ARM64, but `lld-link` stopped
  at `could not open 'windows.0.52.0.lib'`. This is a missing linker search
  directory, **not** a Rust compilation failure. Resolve the exact Cargo
  `windows_aarch64_msvc-0.52.6/lib` directory; do not copy or substitute an
  import archive from an x64 package.
- Follow-up native [CI run 42174405666](https://github.com/Azazel5200/downhill-revived/actions/runs/42174405666)
  succeeded. The exact Cargo import library path ended in
  `windows_aarch64_msvc-0.52.6/lib` and its archive passed the ARM64 machine
  check. `lld-link.exe /machine:arm64` linked the C object to the real Rust
  renderer, and the resulting PE executable ran natively with exit 0:
  `PASS: native ARM64 C -> Rust renderer ABI: dhd_render 1.0 wgpu 29.0.3
  core 29.0.3 naga 29.0.3 (GPU not initialized)`.
  The runner also confirmed **2,427** ARM64 COFF objects in the renderer
  library. GitHub uploaded the standalone executable, **not the game**.

## References

- [Rust reference: linking a static library to native code](https://doc.rust-lang.org/reference/linkage.html).
- [Rust MSVC target conventions](https://doc.rust-lang.org/rustc/platform-support/windows-msvc.html).
- `port/render/include/dhd_render.h` and `port/render/src/abi.rs`, the project's frozen C ABI.

## Result

**Native Windows ARM64 C→Rust static library linking and a real ABI call passed.**
This proves that a small C program can consume the renderer's ARM64 static
library without x64 emulation. The entire game is **not** yet ported; it still
requires the unified host build (wasm2c, SDL3, game runtime), followed by
display, input, sound, state and performance tests. Keep this finding `in
progress` while the stacked draft lane awaits integration.
