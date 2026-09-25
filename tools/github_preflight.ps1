$ErrorActionPreference = "Stop"
Write-Host "CHANDRABHAR-2 GitHub preflight" -ForegroundColor Cyan

$badNames = @("mission_data", "ChandrayaanData", ".git")
$foundBad = Get-ChildItem -Recurse -Force -Directory | Where-Object { $badNames -contains $_.Name }
if ($foundBad) {
  Write-Error "Protected/local directory detected: $($foundBad.FullName -join ', ')"
}

$large = Get-ChildItem -Recurse -File | Where-Object { $_.Length -gt 90MB }
if ($large) {
  $large | ForEach-Object { Write-Host ("Large file: {0} ({1:N1} MB)" -f $_.FullName, ($_.Length/1MB)) -ForegroundColor Yellow }
  Write-Error "Remove large files before pushing. GitHub blocks individual files over 100 MiB."
}

$secretPatterns = @("ghp_", "github_pat_", "AKIA", "BEGIN RSA PRIVATE KEY", "BEGIN OPENSSH PRIVATE KEY")
$scanFiles = Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notlike "*\tools\github_preflight.ps1" }
$hits = $scanFiles | Select-String -Pattern $secretPatterns -SimpleMatch -List -ErrorAction SilentlyContinue
if ($hits) {
  $hits | ForEach-Object { Write-Host "Possible secret: $($_.Path)" -ForegroundColor Red }
  Write-Error "Possible credential/private-key material detected."
}

Write-Host "Preflight passed. Review 'git status' and 'git diff --cached' before committing." -ForegroundColor Green
