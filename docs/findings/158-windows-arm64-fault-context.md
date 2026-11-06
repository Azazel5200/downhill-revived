# 158 — Windows ARM64 fault context: keep the native PC

Status: in progress

Branch `azazel/win-arm64-fault-context` from `main` 5a38832, started 2026-11-06.

## Goal and acceptance

Remove a known x64-only assumption from the Windows guest-memory fault reporter before a
native Windows ARM64 host is attempted. A Windows ARM64 `CONTEXT` has `Pc`, not `Rip`; the
reporter must use the correct instruction pointer for `RtlLookupFunctionEntry`,
`RtlVirtualUnwind` and the printed relative address. Keep the existing x64 report unchanged.

The source patch alone is **not** a validated Windows ARM64 port. Acceptance is compilation
of this unit with native ARM64 MSVC headers followed by the future `--target win-arm64
--fiber-test` on Windows 11 ARM64, including both fault cases. Neither the target nor a working
Windows ARM64 fiber adapter exists yet; do not claim those tests passed.

## Progress

- [x] 2026-11-06: use `CONTEXT.Pc` on `_M_ARM64`, `CONTEXT.Rip` otherwise, retaining the
  human-readable x64 `at rip` diagnostic; avoid modifying the memory mapping or fault policy.
- [ ] Compile with the Windows ARM64 SDK and link against ARM64 libraries.
- [ ] Run native guard-fault and fiber unwinding tests on Windows ARM64 hardware.

## Decisions

- Keep the architecture selection in the Win32 reporter, where `CONTEXT` is read. The shared
  `guest_memory.c` has no reason to know about the host CPU.
- Use `_M_ARM64` as the native Windows ARM64 gate. Do not treat ARM64EC as classic ARM64; its
  context and ABI differ.
- Continue using `RtlLookupFunctionEntry`/`RtlVirtualUnwind` provisionally; native failure
  tests must establish that unwinding survives the fiber stack switch before the ARM64 build
  can be considered supported.

## Surprises

- Windows ARM64 `CONTEXT` does not expose x64's `Rip` (`ARM64_NT_CONTEXT` in the Windows SDK),
  even though the POSIX and Android ARM64 host adapters already exist. Source: Microsoft Learn,
  https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-arm64_nt_context.
- `port/tools/build_host64.py` currently supports only Windows x64; its MSVC library paths,
  clang target and fiber adapter are hard-coded for x64 (preflight draft PR #2). Fixing this reporter is
  one prerequisite, not a working build target.

## Result

Pending Windows ARM64 compiler/linker and device validation. The source change is isolated to
the Windows fault report, leaving existing x64 PC extraction and label unchanged.
