# 161 — Native Windows ARM64 SDL3 static build and startup smoke

Status: in progress

Branch `azazel/win-arm64-sdl3-smoke` from `azazel/win-arm64-host-os` (finding 160),
started 2026-11-06. This is a stacked preflight lane: previous ARM64 host fault, fibers and
Windows host OS service patches must land first. This does **not** build or play the game.

## Goal and acceptance

Build the exact, SHA-256-pinned SDL3 3.4.18 source with the project's Windows options for
native Windows ARM64, link the static library to a tiny ARM64 executable and call `SDL_Init(0)`
then `SDL_Quit()`. No game disc, assets or SDL window/audio device is needed.

Acceptance:

1. `python -B -m unittest discover -s port/tools -p test_win_arm64_sdl3_target.py -v`
   passes locally, with ARM64 target and library paths separated from the x64 SDK.
2. Native hosted Windows ARM64 CI builds the static SDL3 library with CMake and Ninja,
   specifically `aarch64-pc-windows-msvc`, using the same upstream source and feature options.
3. The linker verifies ARM64 compatibility by producing `selftest_win_sdl3.exe`; a native
   Windows ARM64 process then initializes and shuts down SDL3 successfully.
4. The preceding Windows ARM64 host OS smoke still passes on the same runner.
5. Docs and repository never-commit checks pass.

The full game's SDL window and GPU surface, audio device, controller mapping, Rust graphics,
game data and frame-time are out of scope. These require separate actual-machine checks.

## Progress

- [x] 2026-11-06: add an asset-free SDL3 ARM64 link/startup test and a hosted Windows ARM64
  build job, reusing the proven native Visual Studio compiler/SDK setup and pinned SDL3 recipe.
- [x] 2026-11-06: add offline target and dependency-command checks.
- [ ] Run the native hosted SDL3 CMake build, linker and startup test.
- [ ] Inspect any Windows ARM64-specific SDL backend errors before broader integration.

## Decisions

- Continue using `port/tools/sdl3.py` and its pinned source SHA-256, CMake options and static
  library recipe. The architecture changes via its existing `build(target)` argument, not a
  parallel custom SDL build script.
- The disposable CI runner may install the Python Ninja package and cache SDL files in its own
  workspace. The user's laptop does not participate; all user-local project work stays off C:.
- A successful `SDL_Init(0)` only establishes startup/linkability, not real window/audio/input
  functionality or a playable game.

## Surprises

- `sdl3.build(target)` already accepts an explicit target triple and separates the output by
  architecture. The full host builder does not pass the Windows ARM64 target yet, and remains
  intentionally blocked. First validate the library independently.

## References

- SDL project, [CMake build notes](https://wiki.libsdl.org/SDL3/README-cmake).
- SDL project, [Windows build notes](https://wiki.libsdl.org/SDL3/README-windows).

## Result

Pending native ARM64 build and runtime verification; keep this finding `in progress`.
