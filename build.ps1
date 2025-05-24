# PowerShell script to help build HyperZip
# This script detects the shell environment and provides the appropriate command

# Function to check if we're running in PowerShell
function Test-PowerShell {
    return $null -ne $PSVersionTable
}

# Function to check if we're running in Command Prompt
function Test-CommandPrompt {
    return $null -ne $env:ComSpec -and $null -eq $PSVersionTable
}

# Display header
Write-Host "HyperZip Build Helper" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""

# Detect environment
if (Test-PowerShell) {
    Write-Host "Detected environment: PowerShell" -ForegroundColor Green
    Write-Host ""
    Write-Host "To build HyperZip, run one of the following commands:" -ForegroundColor Yellow
    Write-Host "  .\build_all.ps1            # Builds for Windows and attempts macOS build if possible" -ForegroundColor White
    Write-Host "  .\build_windows.bat        # Builds for Windows only" -ForegroundColor White
    Write-Host "  .\build_all.bat            # Builds for Windows and attempts macOS build if possible" -ForegroundColor White
    Write-Host ""
    Write-Host "Would you like to run the build now? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Host "Running .\build_all.ps1..." -ForegroundColor Green
        & .\build_all.ps1
    }
} elseif (Test-CommandPrompt) {
    Write-Host "Detected environment: Command Prompt" -ForegroundColor Green
    Write-Host ""
    Write-Host "To build HyperZip, run one of the following commands:" -ForegroundColor Yellow
    Write-Host "  build_windows.bat          # Builds for Windows only" -ForegroundColor White
    Write-Host "  build_all.bat              # Builds for Windows and attempts macOS build if possible" -ForegroundColor White
    Write-Host ""
    Write-Host "Would you like to run the build now? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Host "Running build_all.bat..." -ForegroundColor Green
        & build_all.bat
    }
} else {
    Write-Host "Detected environment: Unknown" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To build HyperZip, try one of the following commands:" -ForegroundColor Yellow
    Write-Host "  In PowerShell: .\build_all.ps1" -ForegroundColor White
    Write-Host "  In Command Prompt: build_all.bat" -ForegroundColor White
    Write-Host "  In bash/sh: ./build_all.sh" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
