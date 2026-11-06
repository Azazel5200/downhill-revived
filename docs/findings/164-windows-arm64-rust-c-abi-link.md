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
- [ ] Run and diagnose native ARM64 C/Rust link and executable in GitHub Actions.

## Decisions

- Reuse the already-validated `dhd_render.lib` from `rustgs.py`; do not modify
  the renderer ABI or the existing x64 game code.
- Use the MSVC/SDK ARM64 environment established by the same Windows host
  smoke used in findings 160–163. Never treat an x64 import library as proof
  of an ARM64 link.
- Check a pure API before creating a GPU device, since GitHub's headless runner
  cannot establish the user's Adreno performance or rendering behaviour.

## Surprises

Pending native CI evidence.

## References

- [Rust reference: linking a static library to native code](https://doc.rust-lang.org/reference/linkage.html).
- [Rust MSVC target conventions](https://doc.rust-lang.org/rustc/platform-support/windows-msvc.html).
- `port/render/include/dhd_render.h` and `port/render/src/abi.rs`, the project's frozen C ABI.

## Result

Pending native C→Rust ARM64 executable link and call. The entire game remains
unported until its host build and runtime testing pass.
