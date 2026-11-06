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
   specifically `aarch64-pc-windows-msvc`, using the same upstream source and feature options:
   **passed**.
3. The linker verifies ARM64 compatibility by producing `selftest_win_sdl3.exe`; a native
   Windows ARM64 process then initializes and shuts down SDL3 successfully: **passed**.
4. The preceding Windows ARM64 host OS smoke still passes on the same runner: **passed**.
5. Docs and repository never-commit checks pass: **passed**.

The full game's SDL window and GPU surface, audio device, controller mapping, Rust graphics,
game data and frame-time are out of scope. These require separate actual-machine checks.

## Progress

- [x] 2026-11-06: add an asset-free SDL3 ARM64 link/startup test and a hosted Windows ARM64
  build job, reusing the proven native Visual Studio compiler/SDK setup and pinned SDL3 recipe.
- [x] 2026-11-06: add offline target and dependency-command checks.
- [x] 2026-11-06: native Windows ARM64 hosted
  [CI run 42168576509](https://github.com/Azazel5200/downhill-revived/actions/runs/42168576509)
  built `build/port/sdl3/3.4.18-aarch64/build/SDL3-static.lib`, linked the PE executable and
  printed `PASS: native Windows ARM64 SDL3 3.4.18 initialized (without opening devices)`.
  The same native runner (Windows 11 25H2, Cobalt 100) also passed the host OS smoke and docs.
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
- Native SDL3 3.4.18 static build and `SDL_Init(0)` succeeded without changing the pinned
  source or feature flags; the full game cannot be inferred from this isolated result.

## References

- SDL project, [CMake build notes](https://wiki.libsdl.org/SDL3/README-cmake).
- SDL project, [Windows build notes](https://wiki.libsdl.org/SDL3/README-windows).

## Result

The native Windows ARM64 build, link and startup smoke passed. The asset-free standalone
diagnostic binary is available from the hosted CI artifact for seven days. Leave this finding
`in progress` until its stacked dependencies are integrated; it is not a playable game or a
window/audio/controller runtime validation.
