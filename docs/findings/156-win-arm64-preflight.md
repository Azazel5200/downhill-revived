# 156 — Windows ARM64: auditable first gate

Status: in progress

Branch `azazel/win-arm64-preflight` from `main` 5a38832, started 2026-11-05.

## Goal and acceptance

Identify the prerequisites of a future **native Windows ARM64** host without
requiring the user's laptop or game assets. `port/tools/win_arm64_preflight.py`
checks the MSVC ARM64 and Windows SDK library layouts, required commands and
Rust target. Run it in a Visual Studio developer shell:

    python port/tools/win_arm64_preflight.py --json

Offline unit tests must pass with:

    python -m unittest discover -s port/tools -p test_win_arm64_preflight.py -v

This is only an A0 environment gate. Do **not** claim that Windows ARM64 can
compile, link or run the game until `build_host64.py --fiber-test`, the renderer
and a real device pass. The tool never installs anything or inspects game data.

## Progress

- [x] 2026-11-05: isolated dependency audit written; unit cases simulate
  ARM64 Windows, x64 Windows cross-build, missing paths and older Python.
- [x] 2026-11-05: four offline Python unit tests passed; `python tools/check.py docs`
  passed (`check_docs`, `check_tree`). `--json` returns a failure on this Linux
  host as expected: it is not a Windows ARM64 build machine.
- [ ] Run the preflight on the user's Windows 11 ARM64 laptop.
- [ ] Add and test the Windows ARM64 compiler/SDK target, native fiber ABI and
  context unwinding, SDL3, Rust/wgpu and linker in the appropriate next lane.
- [ ] Validate memory guard faults, native graphics, game startup and state
  traces on ARM64 hardware.

## Decisions

- Read-only diagnostic with JSON output; no hardcoded personal paths, no
  downloads, no privileged actions and no game assets.
- Native CPU check is informational because cross-compilation on x64 Windows
  remains valid. The ARM64 MSVC and SDK libraries are mandatory.
- Keep this gate separate from a build target. Adding an untested `win-arm64`
  option to the production builder would incorrectly suggest it already works.

## Surprises

- Existing `build_host64.py` hardcodes `win-x64`, x64 clang flags and `lib/x64`.
- The existing AAPCS64 fiber adapter is not a verified Windows ARM64 ABI
  implementation. `guest_memory_win32.c` uses x64 `CONTEXT.Rip` in its fault
  reporter. These are real follow-up changes, not covered by this gate.
- The full `python tools/check.py port` check reached `build_wasm` but could
  not run it: `clang` is not installed in this environment. No runtime or game
  build is claimed. This gate requires the actual toolchain and game inputs.

## Result

Pending a native Windows ARM64 machine and integration checks.
