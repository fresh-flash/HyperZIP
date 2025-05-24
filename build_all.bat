@echo off
echo Building HyperZip for Windows and macOS...
echo.

echo Installing required packages...
pip install -r requirements.txt
echo.

echo Removing previous build directory...
if exist dist rmdir /s /q dist
echo.

echo ===== Building for Windows =====
echo Building executable with HyperZip.spec...
pyinstaller --clean HyperZip.spec
echo.

if exist dist\HyperZip.exe (
    echo Windows build successful! Executable is located at: dist\HyperZip.exe
) else (
    echo Windows build failed. Please check the error messages above.
    goto :end
)

echo.
echo ===== Building for macOS =====
echo Note: This will only work if run on a macOS system or with appropriate cross-compilation tools.
echo.

REM Check if we're on macOS
where bash >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Bash not found. Skipping macOS build as it requires a macOS system.
    goto :end
)

echo Running macOS build script...
bash build_macos.sh

:end
echo.
echo Build process completed.
pause
