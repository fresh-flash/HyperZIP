@echo off
echo Building HyperZip for Windows...
echo.

echo Installing required packages...
pip install customtkinter pillow htmlmin jsmin csscompressor tinify pyinstaller
echo.

echo Building executable...
pyinstaller --name=HyperZip --onefile --windowed --clean ^
  --hidden-import=PIL._tkinter_finder ^
  --hidden-import=customtkinter ^
  --hidden-import=tinify ^
  --hidden-import=htmlmin ^
  --hidden-import=jsmin ^
  --hidden-import=csscompressor ^
  --hidden-import=tkinter ^
  --hidden-import=tkinter.filedialog ^
  --hidden-import=tkinter.messagebox ^
  hyperzip_app.py
echo.

if exist dist\HyperZip.exe (
  echo Build successful! Executable is located at: dist\HyperZip.exe
) else (
  echo Build failed. Please check the error messages above.
)

echo.
pause
