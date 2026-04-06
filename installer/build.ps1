# Build script for QBLocalApp-Setup.exe
# Run in PowerShell from the repo root on a clean Windows VM.
#
# Prerequisites (one-time):
#   - Inno Setup 6 installed (iscc.exe on PATH)
#   - Internet access for the initial downloads
#
# Outputs:
#   dist\QBLocalApp-Setup.exe

param(
  [string]$PythonEmbedUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip",
  [string]$HtmxUrl        = "https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js",
  [string]$QbSdkPath      = "vendor\QBSDK160.exe"   # place this yourself — Intuit requires a developer account
)

$ErrorActionPreference = "Stop"
$root    = Resolve-Path "$PSScriptRoot\.."
$staging = Join-Path $root "staging"
$dist    = Join-Path $root "dist"

Write-Host "==> Cleaning staging..."
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
New-Item -ItemType Directory -Force -Path $staging | Out-Null
New-Item -ItemType Directory -Force -Path $dist    | Out-Null

Write-Host "==> Downloading embeddable Python..."
$pyZip = Join-Path $staging "python-embed.zip"
Invoke-WebRequest -Uri $PythonEmbedUrl -OutFile $pyZip
$pyDir = Join-Path $staging "python"
New-Item -ItemType Directory -Force -Path $pyDir | Out-Null
Expand-Archive -Path $pyZip -DestinationPath $pyDir -Force
Remove-Item $pyZip

Write-Host "==> Downloading htmx..."
Invoke-WebRequest -Uri $HtmxUrl -OutFile (Join-Path $staging "htmx.min.js")

Write-Host "==> Building offline wheelhouse..."
$wheels = Join-Path $staging "wheels"
New-Item -ItemType Directory -Force -Path $wheels | Out-Null
python -m pip download -r (Join-Path $root "requirements.txt") `
    -d $wheels `
    --platform win_amd64 `
    --python-version 3.11 `
    --only-binary=:all:

Write-Host "==> Copying qb_app source..."
Copy-Item -Recurse -Force (Join-Path $root "qb_app") $staging

Write-Host "==> Copying bundled QuickBooks SDK installer..."
$vendor = Join-Path $staging "vendor"
New-Item -ItemType Directory -Force -Path $vendor | Out-Null
$sdkSrc = Join-Path $root $QbSdkPath
if (-not (Test-Path $sdkSrc)) {
  throw "Place QBSDK160.exe at $sdkSrc (download from developer.intuit.com)"
}
Copy-Item $sdkSrc $vendor

Write-Host "==> Running Inno Setup..."
& iscc (Join-Path $root "installer\installer.iss")

Write-Host "==> Done. Installer at $dist\QBLocalApp-Setup.exe"
