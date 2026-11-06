# Hosted native Windows ARM64 only: build/run the real host C, SDL3 and Rust
# against a deliberately synthetic guest. This is NOT the actual game.
param([Parameter(Mandatory)][string]$LLVM)
$ErrorActionPreference = 'Stop'
if ($env:PROCESSOR_ARCHITECTURE -ne 'ARM64' -or $env:GITHUB_ACTIONS -ne 'true' -or
    $env:RUNNER_ENVIRONMENT -ne 'github-hosted' -or $env:DHD_CI_ALLOW_C_OUTPUT -ne '1') {
    throw 'Synthetic host build requires an explicitly opted-in native ARM64 GitHub runner'
}

$workspace = $env:GITHUB_WORKSPACE
$cache = Join-Path $workspace 'build/development-cache'
$download = Join-Path $workspace 'build/ci-downloads'
New-Item -ItemType Directory -Force -Path @($cache, $download) | Out-Null
$env:DHD_DEVCACHES = $cache
$env:CARGO_HOME = Join-Path $workspace 'build/cargo'
$env:RUSTUP_HOME = Join-Path $workspace 'build/rustup'
$env:PATH = $LLVM + [IO.Path]::PathSeparator + $env:PATH

function Download-CheckedTar([string]$Url, [string]$ExpectedSha, [string]$Name) {
    $archive = Join-Path $download $Name
    Write-Host "Downloading pinned tool: $Name"
    Invoke-WebRequest -Uri $Url -OutFile $archive
    $actual = (Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $ExpectedSha) { throw "SHA-256 mismatch in $Name; expected $ExpectedSha, got $actual" }
    $target = Join-Path $download ($Name + '-unpacked')
    New-Item -ItemType Directory -Force $target | Out-Null
    & tar -xzf $archive -C $target
    if ($LASTEXITCODE -ne 0) { throw "Cannot extract $Name" }
    return $target
}

# WABT has native runtime headers/C and a Windows x64 wasm2c tool; x64 tools
# execute under Windows on ARM64, but all produced game host objects are ARM64.
$wabtArchive = Download-CheckedTar `
    'https://github.com/WebAssembly/wabt/releases/download/1.0.42/wabt-1.0.42-windows-x64.tar.gz' `
    '62f1eb2b51aa57cf0f0b8ba333bf2c72a049930aa9c5de01dcad271c4fe48c88' `
    'wabt-1.0.42-windows-x64.tar.gz'
$wabtExe = Get-ChildItem -Path $wabtArchive -Filter wasm2c.exe -File -Recurse |
    Select-Object -First 1
if (!$wabtExe -or $wabtExe.Directory.Name -ne 'bin') { throw 'WABT archive lacks bin/wasm2c.exe' }
$wabt = $wabtExe.Directory.Parent.FullName
if (!(Test-Path (Join-Path $wabt 'include/wasm-rt.h')) -or
    !(Test-Path (Join-Path $wabt 'share/wabt/wasm2c/wasm-rt-impl.c'))) {
    $src = Join-Path $download 'wabt-source'
    git clone --depth 1 --branch 1.0.42 https://github.com/WebAssembly/wabt.git $src
    if ($LASTEXITCODE -ne 0) { throw 'WABT source checkout failed' }
    New-Item -ItemType Directory -Force -Path @(
        (Join-Path $wabt 'include'), (Join-Path $wabt 'share/wabt/wasm2c')
    ) | Out-Null
    Copy-Item (Join-Path $src 'wasm2c/*.h') -Destination (Join-Path $wabt 'include') -Force
    Copy-Item (Join-Path $src 'wasm2c/*.c') -Destination (Join-Path $wabt 'share/wabt/wasm2c') -Force
}
if (!(Test-Path (Join-Path $wabt 'include/wasm-rt.h')) -or
    !(Test-Path (Join-Path $wabt 'share/wabt/wasm2c/wasm-rt-impl.c'))) {
    throw 'WABT wasm2c runtime headers/sources unavailable'
}

# wasi-sdk compiles only the tiny synthetic WASM guest. Its own compiler is
# ARM64-hosted, while its target is WASM32; it is not the native game compiler.
$wasiArchive = Download-CheckedTar `
    'https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-34/wasi-sdk-34.0-arm64-windows.tar.gz' `
    '45e1c71f3e965621e7b98ebe1d37b0e4b1f77f3e8072113ffb4534e67b1a4b7c' `
    'wasi-sdk-34.0-arm64-windows.tar.gz'
$wasiExe = Get-ChildItem -Path $wasiArchive -Filter clang.exe -File -Recurse |
    Where-Object { $_.Directory.Name -eq 'bin' } | Select-Object -First 1
if (!$wasiExe) { throw 'wasi-sdk archive lacks bin/clang.exe' }
$wasi = $wasiExe.Directory.Parent.FullName

$simde = Join-Path $download 'simde-src'
git clone --depth 1 --branch v0.8.2 https://github.com/simd-everywhere/simde.git $simde
if ($LASTEXITCODE -ne 0 -or !(Test-Path (Join-Path $simde 'simde/x86/sse2.h'))) {
    throw 'SIMDe 0.8.2 headers unavailable'
}

python -m pip install --disable-pip-version-check ninja
if ($LASTEXITCODE -ne 0) { throw 'Ninja install failed' }
rustup toolchain install 1.97.1 --profile minimal --target aarch64-pc-windows-msvc
if ($LASTEXITCODE -ne 0) { throw 'Rust 1.97.1 ARM64 toolchain unavailable' }
Push-Location port/render
try {
    cargo +1.97.1 --config net.offline=false fetch --locked --target aarch64-pc-windows-msvc
    if ($LASTEXITCODE -ne 0) { throw 'Rust lockfile dependencies unavailable' }
} finally { Pop-Location }

Write-Host 'Compiling full native ARM64 Windows host against synthetic, no-disc WASM fixture'
python -B port/tools/build_host64.py --target win-arm64 --fake --run --jobs 4 `
    --llvm $LLVM --wabt $wabt --wasi $wasi --simde $simde
if ($LASTEXITCODE -ne 0) { throw 'ARM64 integrated synthetic host compile/run failed' }

$exe = Join-Path $workspace 'build/host64-winarm64/dhd64.exe'
python -B -c "import sys; sys.path.insert(0,'port/tools'); from build_win_rust_abi_smoke import windows_arm64_executable; windows_arm64_executable(sys.argv[1]); print('PASS: synthetic native ARM64 host executable, not the game')" $exe
if ($LASTEXITCODE -ne 0) { throw 'Produced executable is not native ARM64' }
