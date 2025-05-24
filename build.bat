@echo off
echo HyperZip Build Helper
echo ===================
echo.

echo To build HyperZip, run one of the following commands:
echo   build_windows.bat          # Builds for Windows only
echo   build_all.bat              # Builds for Windows and attempts macOS build if possible
echo.

set /p choice=Would you like to run the build now? (Y/N): 

if /i "%choice%"=="Y" (
    echo.
    echo Running build_all.bat...
    call build_all.bat
) else (
    echo.
    echo Build cancelled.
)

echo.
echo Press any key to exit...
pause > nul
