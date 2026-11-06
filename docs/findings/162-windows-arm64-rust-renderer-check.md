# 162 — Windows ARM64 Rust/wgpu renderer compile preflight

Status: in progress

Branch `azazel/win-arm64-rust-check` from `azazel/win-arm64-sdl3-smoke` (finding 161),
started 2026-11-06. This experimental lane stacks after the ARM64 fault context, fibers,
Windows host OS services and SDL3 startup checks. It does **not** build the full game.

## Goal and acceptance

Check the actual `dhd_render` native dependency graph (wgpu DX12/Vulkan, network, settings,
disc and presence) with `cargo check` under the **native Windows ARM64 MSVC target**. This is the
next blocker after the already-green SDL3 startup test, before producing a game executable.

Acceptance:

1. `python -B -m unittest discover -s port/tools -p test_win_arm64_rust_target.py -v`
   passes, including architecture routing and local C: safety.
2. Native hosted Windows 11 ARM64 runner installs the project-pinned Rust 1.97.1 toolchain
   with `aarch64-pc-windows-msvc`, fetches the locked dependency graph, then runs
   `python -B port/tools/rustgs.py check --target aarch64-pc-windows-msvc`: **passed**.
3. The existing Windows host OS smoke runs first in the same runner without regression:
   **passed**.
4. Repository docs and never-commit checks pass: **passed**.

This is **only `cargo check`**. It does not produce the static library, link the executable,
initialize a GPU device or validate game state, controller, audio or frame rates.

## Progress

- [x] 2026-11-06: register the native Windows ARM64 Rust target in the existing renderer
  wrapper and Rust toolchain manifest (x64, other platforms and pin versions unchanged).
- [x] 2026-11-06: let ring's C build use LLVM clang with the ARM64 MSVC target, and add offline
  checks that reject x64-specific compiler selection.
- [x] 2026-11-06: permit C: Rust cache/output only on GitHub-hosted disposable runners with
  explicit CI opt-in; preserve the off-C: rule for the user's machine.
- [x] 2026-11-06: four ARM64 routing/safety tests and the docs/tree tier pass locally.
- [x] 2026-11-06: native hosted Windows ARM64
  [CI run 42170091082](https://github.com/Azazel5200/downhill-revived/actions/runs/42170091082)
  checked the locked native feature graph with Rust 1.97.1. The log shows `wgpu-types 29.0.3`,
  `wgpu-naga-bridge 29.0.3`, `wgpu-core-deps-windows-linux-android 29.0.3` and `dhd_render`
  all checked; `Finished release profile [optimized] target(s) in 1m 17s`.
- [ ] Decide separately whether/how to build, validate and link the actual ARM64 static library.

## Decisions

- Reuse `port/tools/rustgs.py` (the one wrapper with version and dependency gates), not a
  second Cargo pipeline. Before its offline gate, CI fetches the locked target dependencies.
- The `-msvc` ARM64 Rust target is a Tier-1 target with native host tools; the project keeps
  using **classic AArch64**, not ARM64EC or x64 emulation.
- `ring` requires clang for native Windows ARM64; locate it in the real VS/LLVM developer shell
  and set the per-target C compiler. Unavailability is a hard failure, not an x64 fallback.
- The trusted GitHub hosted runner uses an ephemeral C: workspace. The original rule against
  C: builds remains for local user laptops; no new paths or secrets are committed.

## Surprises

- `rustgs.py` previously recognized Android/macOS ARM64, but only the Windows x64 MSVC Rust
  target. The native Windows ARM64 Rust triple and Rustup manifest were not registered.
- The project requires fully offline Cargo verification. An ephemeral CI runner must fetch
  the *locked* dependency graph before it can exercise that gate.
- First hosted attempt [CI run 42169848988](https://github.com/Azazel5200/downhill-revived/actions/runs/42169848988)
  stopped at `cargo fetch`: its initial download inherited the project's enforced
  `[net] offline = true`, and could not find the locked `log` crate in a fresh cache.
  The native host OS smoke had already passed. Limit the online override to `cargo fetch`;
  do not weaken the subsequent offline renderer check.
- After fixing the initial fetch, the target-locked dependency graph and actual native renderer
  `cargo check` passed on a real Windows ARM64 runner. This does not imply the staticlib linker
  will work: link/archive output and asset-free library calls remain separate tests.
- The wider `rustgs_selftest.py` cannot finish on the current Linux scratch executor: its
  existing x64 Windows release-build step refuses without the LLVM `llvm-ar` executable.
  This is not evidence of a Rust ARM64 compile failure; the native runner is required.

## References

- Rust project, [MSVC Windows target support](https://doc.rust-lang.org/stable/rustc/platform-support/windows-msvc.html).
- ring project, [Windows ARM64 build requirements](https://github.com/briansmith/ring/blob/main/BUILDING.md).
- wgpu project, [CI target coverage](https://github.com/gfx-rs/wgpu/blob/trunk/.github/workflows/ci.yml).

## Result

The native ARM64 Rust/wgpu renderer's compile check passed. Keep this finding `in progress`
until its stacked dependencies are integrated, and investigate the next stage (staticlib
generation/validation and full game linkage) separately. No user laptop was required.
