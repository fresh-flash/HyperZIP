# PowerShell script to build HyperZip for Windows and macOS

Write-Host "Building HyperZip for Windows and macOS..." -ForegroundColor Cyan
Write-Host ""

Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host ""

Write-Host "Removing previous build directory..." -ForegroundColor Yellow
if (Test-Path -Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
}
Write-Host ""

Write-Host "===== Building for Windows =====" -ForegroundColor Green
Write-Host "Building executable with HyperZip.spec..." -ForegroundColor Yellow
pyinstaller --clean HyperZip.spec
Write-Host ""

if (Test-Path -Path "dist\HyperZip.exe") {
    Write-Host "Windows build successful! Executable is located at: dist\HyperZip.exe" -ForegroundColor Green
} else {
    Write-Host "Windows build failed. Please check the error messages above." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "===== Building for macOS =====" -ForegroundColor Green
Write-Host "Note: This will only work if run on a macOS system or with appropriate cross-compilation tools." -ForegroundColor Yellow
Write-Host ""

# Check if we're on macOS or have bash available
$bashAvailable = $null -ne (Get-Command "bash" -ErrorAction SilentlyContinue)
if (-not $bashAvailable) {
    Write-Host "Bash not found. Skipping macOS build as it requires a macOS system." -ForegroundColor Yellow
} else {
    Write-Host "Running macOS build script..." -ForegroundColor Yellow
    bash build_macos.sh
}

Write-Host ""
Write-Host "Build process completed." -ForegroundColor Cyan
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
