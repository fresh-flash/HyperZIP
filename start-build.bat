@echo off
echo HyperZip Build Process
echo ====================
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

:end
echo.
echo Build process completed.
echo Press any key to exit...
pause > nul
