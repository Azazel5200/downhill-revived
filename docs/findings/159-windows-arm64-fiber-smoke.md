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

Items 2–3 now pass on a native GitHub-hosted Windows 11 ARM64 runner. Item 4 and a repeat of
items 2–3 on the user's own Windows 11 ARM64 laptop are still pending. Do not merge this lane
or claim full ARM64 game portability based on this isolated selftest.

## Progress

- [x] 2026-11-06: introduce a dedicated classic ARM64 (not ARM64EC) Windows assembly fiber
  adapter, preserving the Windows TEB stack bounds during context switches.
- [x] 2026-11-06: route only `--fiber-test` through `--target win-arm64`; fail closed for the
  game/renderer; select ARM64 MSVC/Windows SDK library directories from the VS developer shell;
  add offline command-routing and x64-library rejection tests.
- [x] 2026-11-06: add an opt-in `windows-11-vs2026-arm` GitHub Actions job for this draft PR
  only. It provisions WABT headers in its ephemeral workspace, discovers LLVM and Visual Studio
  ARM64, then attempts the real 150-switch and two guard-fault runs without the user's laptop.
- [x] Collect the hosted ARM64 job's results: core switching and guard faults pass; the
  backtrace remains too short, so the job remains red.
- [x] Compile/link the new adapter with native Windows ARM64 clang-cl on a hosted machine.
- [x] Run the 150-switch core checks and both deliberate guard-fault cases on hosted ARM64.
- [x] Exercise native ARM64 unwind metadata and obtain bounded backtraces from both root and
  switched fiber contexts on the hosted runner.
- [x] Confirm the normal selftest exits with its intended diagnostic code (`3`) and not an
  unexpected access violation after returning from the fiber stack.
- [ ] Resolve Windows ARM64 stack-walk depth, or independently establish an appropriate
  diagnostic alternative with equivalent stack-boundary safety.
- [ ] Repeat final verification on the user's own Windows 11 ARM64 hardware.
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
- The GitHub-hosted disposable runner has a C: checkout by default. A narrowly scoped CI-only
  opt-in (`DHD_CI_ALLOW_C_OUTPUT=1` together with GitHub's hosted-runner markers) permits this
  *fiber smoke test* to use that ephemeral system drive. Normal user builds still reject C:;
  it never writes to the user's Windows laptop.

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
- GitHub offers native Windows 11 ARM64 hosted runners for public repositories, including a
  Visual Studio 2026 image. This can catch compiler and runtime failures before involving a
  player's machine: https://github.blog/changelog/2026-08-20-windows-11-arm64-vs2026-image-generally-available/.
- First hosted native ARM64 run reached Python tests and exposed a test's Unix-only assertion
  (`/lib/arm64` against Windows backslash paths). Normalizing separators made all five tests
  pass on the next run; that run then correctly rejected the hosted runner's C: output path.
  The CI-only exception above is under test; compilation and runtime validation are still
  pending, and neither failed run is evidence that the native switch works.
- The hosted runner subsequently passed all five tests and its C: scope guard, but VsDevCmd
  appeared to lose the MSVC/SDK variables in `windows_arm64_paths`. Direct diagnostics proved
  PowerShell **and Python** both received all three variables. Root cause: Python's Windows
  `os.environ` uppercases names, while the build passed `dict(os.environ, ...)` and then used
  case-sensitive mixed-case lookups. ARM64 path discovery now handles environment variable
  names case-insensitively, with a regression test for uppercased keys.
- The next hosted run **compiled and launched the ARM64 executable successfully**, including
  stack bounds and the 256-KiB frame, but failed at `RtlCaptureStackBackTrace`'s minimum frame
  count (selftest line 83). The switch assembly initially described only its stack allocation
  in `.seh_*` unwind metadata, omitting the saved nonvolatile registers and LR. The next attempt
  gives each save a corresponding ARM64 unwind directive and logs the actual frame count on
  failure. The native switch, guard faults and full 150 rounds are **not yet validated**.
- With the additional `.seh_*` saves, the next hosted execution still returned exactly **one**
  frame from `RtlCaptureStackBackTrace`. Microsoft's ARM64 ABI recommends retaining `x29` frame
  links for reliable stack walking. The smoke compiler now explicitly uses
  `-fno-omit-frame-pointer` even under `/O2`; the subsequent native run must establish whether
  that resolves the trace or whether the synthetic fiber needs a stronger unwind boundary.
- Retaining `x29` still yielded **one frame** in the native test. A narrowly scoped ARM64 test
  probe now checks whether the ordinary root thread can produce a backtrace before switching,
  and, if not, whether `x29` and its parent point within its reported stack bounds. This
  distinguishes a general compiler/Windows tracing issue from a synthetic-fiber-only issue.
- The probe showed the **root thread also returns one frame**, before any fiber switch. Its
  current `x29` did not lie inside `GetCurrentThreadStackLimits`. The compiler option was
  placed before `/O2`, which can override frame-pointer settings. Move the explicit option
  after `/O2`, assert its order in the test, and print root `x29` and bounds on failure to
  distinguish compiler layout from an incorrect Windows stack-bounds API interpretation.
- Putting the option after `/O2` did not change the result: ordinary root-thread `x29` was
  **zero**, and `RtlCaptureStackBackTrace` returned one frame. To expose independent failures,
  the ARM64 smoke now records short backtraces without aborting immediately, attempts the
  complete switching/slot test and both deliberate guard-fault children, and **fails the job
  at the end** if the backtrace requirement is unmet. The original x64 assertions stay strict
  and unchanged. No partial PASS is a claim of overall ARM64 success.
- The native hosted run then completed **all 150 switches**, register and FP-control checks,
  module stack-pointer and call-depth checks, nested fiber, large native stack frame, 64-slot
  allocation/reuse and stack-range checks. **Both deliberate guard faults** raised the expected
  Windows access violation `0xc0000005` and printed their expected markers. The backtrace
  remained one frame both on the root thread and within fibers (3 short-trace checks), so the
  job is correctly **red**. The job initially *reported* the normal selftest return as
  `0xc0000005`, but this was a **reporting bug**: the build script reused `r` for the guard
  children and printed the *last guard child's* expected access violation instead of the
  original main process code. The report now preserves `main_code` before running guard checks.
  This is a proven **core fiber smoke**, not a fully passing Windows ARM64 port.
- A dedicated `--exit-probe` now returns status 3 before allocating guest memory or creating
  fibers. The next hosted run compares that plain Windows ARM64 CRT return to the same result
  after fiber shutdown, to separate a general runner/toolchain exit problem from corrupted
  state remaining after a context-switch sequence.
- The plain `--exit-probe` returned **3** as expected, ruling out a general CRT return-code
  failure. The next run adds a root-only backtrace exit probe and checks whether the original
  thread's TEB pointer, stack bounds, DeallocationStack and FiberData were restored exactly
  after all switches, before concluding where the normal-process access violation originates.
- The root-only trace probe also returned **3**. The full 150-switch run reached the final
  core PASS line **after** successfully checking all four original TEB/stack fields; thus the
  root context is restored in those measured respects. The apparent main-process access
  violation was the `r` reuse noted above, not evidence of corrupted CRT state. A new hosted
  run will report the correct original process exit status.
- The corrected run reported **`selftest_fiber failed (3)`** for the normal process, precisely
  the intended backtrace-diagnostic status. Both independent probe processes also returned 3,
  and both guard children still faulted as expected. **No abnormal shutdown is observed**;
  the only remaining failed selftest invariant is the short one-frame Windows ARM64 stack walk.
- Microsoft's `RtlVirtualUnwind` reconstructs the calling context using OS unwind tables,
  independently of `RtlCaptureStackBackTrace`'s fast path. The port's Windows fault reporter
  already uses `RtlLookupFunctionEntry` and `RtlVirtualUnwind` on both x64 and ARM64. Add an
  ARM64-only fallback to the fiber selftest: capture a `CONTEXT`, walk through unwind metadata,
  require at least two frames, and stop at the **current** thread/fiber stack's reported bounds
  without inventing an LR-only caller when unwind metadata is unavailable. This remains an
  experimental change pending native CI evidence; do not mark the backtrace check green merely
  because the 150 context switches passed. Reference:
  https://learn.microsoft.com/en-us/windows/win32/api/winnt/nf-winnt-rtlvirtualunwind
- Microsoft's STL maintainers separately document sporadic `RtlCaptureStackBackTrace` failures;
  the issue discusses the independently captured-context/unwind-table approach. It does not
  establish the cause of this **specific** Windows ARM64 runner's one-frame result:
  https://github.com/microsoft/STL/issues/3889.
- The subsequent native Windows ARM64 hosted job passed **both CI jobs**. The fast-path
  `RtlCaptureStackBackTrace` still returned **one frame** in each of three checks (root thread
  and two fiber contexts); the independent, stack-bounded `RtlVirtualUnwind` walk returned
  **five frames in each check**, allowing the selftest to pass without dropping the two-frame
  requirement. All 150 fiber switches and both expected guard faults (`0xc0000005`) passed
  again, with no abnormal process shutdown. CI run:
  https://github.com/Azazel5200/downhill-revived/actions/runs/42161654246.
- Preserve the small statically linked **selftest only** as a seven-day GitHub Actions artifact
  after successful native CI, so the same executable can later be run from a non-system drive
  on the user's laptop without first installing LLVM/MSVC. It contains no game binary, disc
  data or game assets, and is **not** a playable release.

## Result

ARM64 compiler/linker, the core 150-switch/guard behavior, clean shutdown and an alternative
bounded native stack walk are now validated on GitHub's native hosted hardware. The user's
on-device test and unchanged Windows x64 regression test remain pending. This draft is not a
player-ready ARM64 game executable; do not merge it yet.
