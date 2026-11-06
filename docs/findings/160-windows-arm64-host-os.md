# 160 — Windows ARM64 host OS services smoke

Status: in progress

Branch `azazel/win-arm64-host-os` from `azazel/win-arm64-fiber-smoke` (finding 159),
started 2026-11-06. This is a stacked experimental lane: the ARM64 fiber and fault-context
changes must land first. It does **not** build or run the game.

## Goal and acceptance

Eliminate the x64-only intrinsics in `port/host/host_win32.c`, preserving the existing x64
behavior and testing the real Windows ARM64 OS services without a disc or renderer.

Acceptance before marking current:

1. `python -B -m unittest discover -s port/tools -p test_win_host_os_smoke.py -v`
   passes, including the rejection of x64 SDK libraries for an ARM64 target.
2. Native Windows 11 ARM64 CI compiles `host_win32.c` with `clang-cl` targeting
   `aarch64-pc-windows-msvc` and runs the standalone host OS smoke to completion.
3. Native Windows x64 CI compiles and runs the same source and smoke without regression.
4. `python -B tools/check.py docs` and the never-commit checks pass.
5. Full game, SDL3, Rust renderer, licensed game data, performance and state traces remain
   outside this lane; do not claim acceptance for them.

## Progress

- [x] 2026-11-06: move the proven AArch64 MXCSR-to-FPCR mapping into one shared header,
  removing its POSIX-only copy; use it in the native Windows ARM64 host.
- [x] 2026-11-06: add Windows ARM64-specific `CONTEXT.Pc` heartbeat sampling, a documented
  monotonic `QueryPerformanceCounter` timer and Windows processor identity without x86 CPUID.
- [x] 2026-11-06: write a self-contained native host OS test and five offline Python checks
  for target architecture selection. The Python tests pass locally.
- [ ] Hosted Windows ARM64 build and runtime verification of the C adapter.
- [ ] Hosted Windows x64 build and regression verification.
- [ ] Full game integration later, after SDL3 and Rust ARM64 prerequisites exist.

## Decisions

- Retain the one host service interface and the existing x64 implementation; only CPU-specific
  register and processor-name operations need conditional code.
- The shared FPCR helper accepts the same abstract MXCSR word on macOS/Android/Linux ARM64 and
  Windows ARM64. The Windows build uses clang-cl's AArch64 inline register instructions.
- `host_cycles` is for relative timing diagnostics, not a game clock; use Windows QPC on ARM64
  (documented to measure monotonic wall-clock time) rather than x86 `__rdtsc`.
- The test is a small isolated Windows PE executable with a stubbed `guest_base`: it exercises
  floating-point rounding/flush modes, paths, system identity, memory protection, the PE code
  section, the counter and environment variables, without spawning the game.
- Local build outputs stay off C:, except the disposable hosted GitHub CI workspace.

## Surprises

- The native fiber adapter and fault guard already pass on ARM64; the separate Windows host
  still contained unconditional x64 intrinsics, so a complete game would not compile yet.
- The full build also requires Windows ARM64 SDL3 and Rust renderer routes, which this lane
  intentionally does not enable.

## References

- Microsoft, [ARM64 intrinsics](https://learn.microsoft.com/en-us/cpp/intrinsics/arm64-intrinsics).
- Microsoft, [ARM64 ABI conventions and the cycle counter](https://learn.microsoft.com/en-us/cpp/build/arm64-windows-abi-conventions).
- Microsoft, [QueryPerformanceCounter](https://learn.microsoft.com/en-us/windows/win32/api/profileapi/nf-profileapi-queryperformancecounter).

## Result

Pending native Windows ARM64 and x64 CI runs; leave this finding `in progress`.
