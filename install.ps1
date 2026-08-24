# Install gobs for the current user (Windows).
#   irm https://raw.githubusercontent.com/wisdom-km/gobs/main/install.ps1 | iex
#   or:  .\install.ps1

$ErrorActionPreference = "Stop"
python -m pip install --user --upgrade "git+https://github.com/wisdom-km/gobs.git"

$bin = Join-Path $env:USERPROFILE ".gobs\bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$cmd = Join-Path $bin "gobs.cmd"
@"
@echo off
python -m gobs %*
"@ | Set-Content -Path $cmd -Encoding ASCII

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $userPath) { $userPath = "" }
if ($userPath -notlike "*$bin*") {
    [Environment]::SetEnvironmentVariable("Path", "$bin;$userPath", "User")
}
$env:Path = "$bin;$env:Path"

Write-Host "Installed. Try:  gobs doctor"
Write-Host "First vault:     gobs init `"C:\path\to\vault`""
Write-Host "Launcher:        $cmd"
