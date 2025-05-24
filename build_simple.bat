@echo off
echo Building HyperZip for Windows...
echo.

echo Installing required packages...
pip install customtkinter pillow htmlmin jsmin csscompressor tinify pyinstaller certifi
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

echo.
pause
