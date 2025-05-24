# PowerShell script to build HyperZip
# This script runs the build process directly without requiring the user to type any commands

Write-Host "HyperZip Build Process" -ForegroundColor Cyan
Write-Host "====================" -ForegroundColor Cyan
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
Write-Host "Build process completed." -ForegroundColor Cyan
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
