# Adds a "sync2canvas" function to your PowerShell profile.
# Usage: powershell -ExecutionPolicy Bypass -File install_shortcut.ps1

$VENV_DIR = Join-Path $env:USERPROFILE "venvs\canvas_quarto_env"
$PYTHON   = Join-Path $VENV_DIR "Scripts\python.exe"
$SCRIPT   = Join-Path $VENV_DIR "CanvasQuartoSync\sync_to_canvas.py"

if (-not (Test-Path $PYTHON)) {
    Write-Host "Python not found at $PYTHON - run install.ps1 first." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $SCRIPT)) {
    Write-Host "sync_to_canvas.py not found at $SCRIPT - run install.ps1 first." -ForegroundColor Red
    exit 1
}

# Build the block to add to $PROFILE
$funcBlock = @()
$funcBlock += ""
$funcBlock += "# --- sync2canvas (added by CanvasQuartoSync) ---"
$funcBlock += "function sync2canvas { if (`$args.Count -eq 0) { & `"$PYTHON`" `"$SCRIPT`" . } else { & `"$PYTHON`" `"$SCRIPT`" @args } }"
$funcBlock += "# --- end sync2canvas ---"

# Create profile if needed
if (-not (Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force | Out-Null
    Write-Host "Created profile: $PROFILE" -ForegroundColor Cyan
}

# Skip if already there
$existing = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ($existing -and $existing.Contains("# --- sync2canvas")) {
    Write-Host "sync2canvas already in profile. Nothing to do." -ForegroundColor Green
    exit 0
}

# Append
Add-Content -Path $PROFILE -Value ($funcBlock -join "`r`n")
Write-Host "Added sync2canvas to $PROFILE" -ForegroundColor Green
Write-Host ""
Write-Host "Activate now:  . `$PROFILE" -ForegroundColor Cyan
Write-Host "Or open a new terminal, then:" -ForegroundColor Cyan
Write-Host "  cd YourCourseFolder" -ForegroundColor Gray
Write-Host "  sync2canvas" -ForegroundColor Gray
