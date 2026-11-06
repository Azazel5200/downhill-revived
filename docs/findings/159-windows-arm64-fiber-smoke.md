# 159 — Native Windows ARM64 EE fiber smoke target

Status: in progress

Branch `azazel/win-arm64-fiber-smoke` from `azazel/win-arm64-fault-context` (finding 158),
started 2026-11-06. This is a stacked experimental lane; the earlier fault-context fix must
land before this one.

## Goal and acceptance

Make it possible to ask an actual Windows 11 ARM64 laptop to compile and run the smallest
native part of the port: guest-memory reservations and EE fiber switching, without the game
disc or the complete LLVM/Rust/SDL3 toolchain. This is **not** a complete native game port.

Acceptance before marking this finding current:

1. `python -B -m unittest discover -s port/tools -p test_win_arm64_fiber_target.py -v`
   must pass on the checkout, including refusal to use x64 libraries or invoke a full build.
2. On Windows 11 ARM64, `python -B port/tools/build_host64.py --target win-arm64 --fiber-test
   --llvm <LLVM_BIN> --wabt <WABT_ROOT>` must compile with ARM64 MSVC/Windows SDK libraries;
   both `clang-cl.exe` and `lld-link.exe` must be present.
3. The native `selftest_fiber.exe` must print its 150-switch `PASS` line, pass the stack bounds,
   FPCR, backtrace and 64-slot checks, and terminate with the expected fault codes on both
   `--guest-guard` and `--native-guard` child runs.
4. The existing Windows x64 fiber test must continue to pass unchanged.

Items 2–4 require a matching Windows installation and are **unverified** here. Do not merge
this lane or claim ARM64 portability based only on Python tests.

## Progress

- [x] 2026-11-06: introduce a dedicated classic ARM64 (not ARM64EC) Windows assembly fiber
  adapter, preserving the Windows TEB stack bounds during context switches.
- [x] 2026-11-06: route only `--fiber-test` through `--target win-arm64`; fail closed for the
  game/renderer; select ARM64 MSVC/Windows SDK library directories from the VS developer shell;
  add offline command-routing and x64-library rejection tests.
- [ ] Compile/link the new adapter with native Windows ARM64 clang-cl, and inspect its ARM64
  exception unwinding metadata.
- [ ] Run the native selftest and both deliberate guard faults on Windows 11 ARM64 hardware.
- [ ] Rerun the unchanged win-x64 fiber selftest and the full port tier in the correct environment.

## Decisions

- One target table and shared `fiber.c`; only a small CPU/ABI-specific adapter is new, not a
  parallel game implementation. The existing POSIX AArch64 assembly is not Windows COFF/SEH.
- Frame saves callee-saved x19–x30, d8–d15 and FPCR; Windows ARM64's `x18` is the TEB pointer.
  Save/restore StackBase, StackLimit and DeallocationStack together with SP, like the existing
  x64 Windows adapter. Exact TEB offsets and unwind behavior remain a hardware-test risk.
- LLVM, MSVC headers, SDK ARM64 libs and WABT are the only compiler inputs for this selftest.
  Cargo/Rust, SDL3, CMake and the game disc are not needed here.
- Do not silently select the hardcoded Windows x64 MSVC/SDK locations from the existing game
  build, even when a developer shell happens to have them installed.
- Run generated binaries, temporary files and logs under the explicit output directory; keep
  build/tool downloads off the system drive when that is the machine's policy.

## Surprises

- Microsoft's Windows ARM64 ABI reserves `x18` as the TEB pointer and requires 16-byte SP
  alignment: https://learn.microsoft.com/en-us/cpp/build/arm64-windows-abi-conventions.
- LLVM's ARM64 Windows COFF assembler has `.seh_*` directives, but generating unwind metadata
  alone does not validate a context switch across two stack regions:
  https://reviews.llvm.org/D87369.
- Visual Studio's developer environment provides `VCToolsInstallDir`, `WindowsSdkDir` and
  `WindowsSDKVersion`; it must be configured for ARM64, not its x64 defaults:
  https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line.
- No native Windows ARM64 compiler or SDK is available in the Linux editing environment;
  syntax/unit/document checks here cannot execute an ARM64 machine-code test.

## Result

Pending compiler/SDK and native-device validation. This draft only exposes an intentionally
limited standalone smoke target, not a player-ready ARM64 executable.
