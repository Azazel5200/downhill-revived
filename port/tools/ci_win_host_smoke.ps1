# Native GitHub runner only: configure the target VS/SDK compiler and run the host OS smoke.
param([ValidateSet('arm64', 'x64')][string]$Arch, [switch]$SDL3, [switch]$RustCheck, [switch]$RustBuild, [switch]$RustAbi, [switch]$HostRouting)
$ErrorActionPreference = 'Stop'
$expected = if ($Arch -eq 'arm64') { 'ARM64' } else { 'AMD64' }
if ($env:PROCESSOR_ARCHITECTURE -ne $expected) { throw "Expected native $expected runner" }

$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
if (!(Test-Path $vswhere)) { throw 'vswhere.exe unavailable' }
$vs = & $vswhere -latest -products '*' -property installationPath
if ($LASTEXITCODE -ne 0 -or !$vs) { throw 'No Visual Studio installation' }
$dev = Join-Path $vs 'Common7/Tools/VsDevCmd.bat'
$native = if ($Arch -eq 'arm64') { 'arm64' } else { 'amd64' }
$setCmd = 'call "' + $dev + '" -no_logo -arch=' + $native + ' -host_arch=' + $native + ' >nul && set'
$rows = & $env:ComSpec /d /s /c $setCmd
if ($LASTEXITCODE -ne 0) { throw 'VS developer environment failed' }
foreach ($row in $rows) {
    if ($row -match '^([^=]+)=(.*)$') {
        Set-Item -Path ('Env:' + $Matches[1]) -Value $Matches[2]
    }
}

# The ARM64 image may not export the three VS library variables, though the tools exist.
if (!$env:VCToolsInstallDir) {
    $msvc = Get-ChildItem (Join-Path $vs 'VC/Tools/MSVC') -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName ('lib/' + $Arch)) } |
        Sort-Object Name -Descending | Select-Object -First 1
    if (!$msvc) { throw 'Target MSVC libraries unavailable' }
    $env:VCToolsInstallDir = $msvc.FullName
}
if (!$env:WindowsSdkDir) {
    $env:WindowsSdkDir = [Microsoft.Win32.Registry]::GetValue(
        'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows Kits\Installed Roots', 'KitsRoot10', $null)
    if (!$env:WindowsSdkDir) { throw 'Windows SDK unavailable' }
}
if (!$env:WindowsSDKVersion) {
    $sdk = Get-ChildItem (Join-Path $env:WindowsSdkDir 'Lib') -Directory -ErrorAction SilentlyContinue |
        Where-Object { (Test-Path (Join-Path $_.FullName ('ucrt/' + $Arch))) -and
                       (Test-Path (Join-Path $_.FullName ('um/' + $Arch))) } |
        Sort-Object Name -Descending | Select-Object -First 1
    if (!$sdk) { throw 'Target Windows SDK libraries unavailable' }
    $env:WindowsSDKVersion = $sdk.Name + '\'
}
$clang = Get-Command clang-cl.exe -ErrorAction SilentlyContinue
if ($clang) { $llvmBin = Split-Path $clang.Source }
else {
    $candidate = Get-ChildItem (Join-Path $vs 'VC/Tools/Llvm') -Filter clang-cl.exe -Recurse `
        -ErrorAction SilentlyContinue | Select-Object -First 1
    if (!$candidate) { throw 'clang-cl.exe unavailable' }
    $llvmBin = $candidate.DirectoryName
}
if (!(Test-Path (Join-Path $llvmBin 'lld-link.exe'))) { throw 'lld-link.exe unavailable' }
python -B -m unittest discover -s port/tools -p test_win_host_os_smoke.py -v
if ($LASTEXITCODE -ne 0) { throw 'Offline Windows host smoke routing failed' }
python -B port/tools/build_win_host_smoke.py --arch $Arch --llvm $llvmBin
if ($LASTEXITCODE -ne 0) { throw 'Native Windows host smoke failed' }
if ($HostRouting) {
    if ($Arch -ne 'arm64') { throw 'The native ARM64 host routing lane must use ARM64 Windows' }
    python -B -m unittest discover -s port/tools -p test_win_arm64_host_routing.py -v
    if ($LASTEXITCODE -ne 0) { throw 'Full game ARM64 host routing tests failed' }
    python -B -m unittest discover -s port/tools -p test_win_arm64_fiber_target.py -v
    if ($LASTEXITCODE -ne 0) { throw 'Native ARM64 fiber routing regression failed' }
}
if ($SDL3) {
    if ($Arch -ne 'arm64') { throw 'The SDL3 preflight is for native ARM64 only' }
    $env:DHD_DEVCACHES = Join-Path $env:GITHUB_WORKSPACE 'build/development-cache'
    python -m pip install --disable-pip-version-check ninja
    if ($LASTEXITCODE -ne 0) { throw 'Python ninja package unavailable' }
    # CMake uses clang.exe, not clang-cl.exe; both must be in the same selected toolchain.
    $env:PATH = $llvmBin + [IO.Path]::PathSeparator + $env:PATH
    python -B port/tools/build_win_sdl_smoke.py --llvm $llvmBin
    if ($LASTEXITCODE -ne 0) { throw 'Native Windows ARM64 SDL3 build or smoke failed' }
}
if ($RustCheck -or $RustBuild -or $RustAbi) {
    if ($Arch -ne 'arm64') { throw 'Rust ARM64 preflight must run natively' }
    $env:DHD_DEVCACHES = Join-Path $env:GITHUB_WORKSPACE 'build/development-cache'
    $env:CARGO_HOME = Join-Path $env:GITHUB_WORKSPACE 'build/cargo'
    $env:RUSTUP_HOME = Join-Path $env:GITHUB_WORKSPACE 'build/rustup'
    $env:PATH = $llvmBin + [IO.Path]::PathSeparator + $env:PATH
    if (!(Get-Command rustup.exe -ErrorAction SilentlyContinue)) { throw 'rustup unavailable' }
    rustup toolchain install 1.97.1 --profile minimal --target aarch64-pc-windows-msvc
    if ($LASTEXITCODE -ne 0) { throw 'Rust 1.97.1 ARM64 toolchain unavailable' }
    Push-Location port/render
    try {
        # The project's .cargo/config.toml forces offline mode. Temporarily override that
        # setting ONLY to fetch the existing lockfile; rustgs's cargo check stays offline.
        cargo +1.97.1 --config net.offline=false fetch --locked --target aarch64-pc-windows-msvc
        if ($LASTEXITCODE -ne 0) { throw 'Cargo dependencies unavailable' }
    }
    finally { Pop-Location }
    python -B -m unittest discover -s port/tools -p test_win_arm64_rust_target.py -v
    if ($LASTEXITCODE -ne 0) { throw 'Offline Windows ARM64 Rust routing tests failed' }
    if ($RustBuild -or $RustAbi) {
        python -B -m unittest discover -s port/tools -p test_arm64_coff.py -v
        if ($LASTEXITCODE -ne 0) { throw 'Offline ARM64 COFF parser tests failed' }
    }
    if ($RustAbi) {
        python -B -m unittest discover -s port/tools -p test_win_rust_abi.py -v
        if ($LASTEXITCODE -ne 0) { throw 'Offline ARM64 PE/ABI routing tests failed' }
    }
    python -B port/tools/rustgs.py check --target aarch64-pc-windows-msvc
    if ($LASTEXITCODE -ne 0) { throw 'Native Windows ARM64 Rust renderer check failed' }
    if ($RustBuild -or $RustAbi) {
        $report = Join-Path $env:GITHUB_WORKSPACE 'build/arm64-renderer-staticlib.json'
        python -B port/tools/rustgs.py build --target aarch64-pc-windows-msvc --no-cache --report $report
        if ($LASTEXITCODE -ne 0) { throw 'Native Windows ARM64 Rust staticlib build or artifact gates failed' }
        python -B port/tools/check_arm64_coff.py --report $report
        if ($LASTEXITCODE -ne 0) { throw 'Native Windows ARM64 COFF archive validation failed' }
        if ($RustAbi) {
            python -B port/tools/build_win_rust_abi_smoke.py --report $report --llvm $llvmBin `
                --out (Join-Path $env:GITHUB_WORKSPACE 'build/host-rustabi-winarm64')
            if ($LASTEXITCODE -ne 0) { throw 'Native Windows ARM64 C/Rust ABI link or runtime smoke failed' }
        }
    }
}
