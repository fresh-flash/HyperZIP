@echo off
echo Building HyperZip for Windows...
echo.

echo Installing required packages...
pip install -r requirements.txt
echo.
echo Removing previous build directory...
if exist dist rmdir /s /q dist
echo.
echo Building executable with HyperZip.spec...
pyinstaller --clean HyperZip.spec
echo.

if exist dist\HyperZip.exe (
    echo Build successful! Executable is located at: dist\HyperZip.exe
) else (
    echo Build failed. Please check the error messages above.
)

echo Cleaning up...
REM del simple.spec - No longer needed

echo.
pause
