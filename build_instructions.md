# Building HyperZip as a Standalone Application

This document provides instructions for compiling HyperZip into a standalone executable for Windows (.exe) or macOS application bundle (.app).

## Prerequisites

Before building, ensure you have all required dependencies installed:

```bash
pip install customtkinter tkinter pillow htmlmin jsmin csscompressor tinify pyinstaller
```

## Building for Windows (.exe)

1. **Install PyInstaller** (if not already installed):
   ```bash
   pip install pyinstaller
   ```

2. **Create a spec file** (optional but recommended):
   ```bash
   pyi-makespec --onefile --windowed --name HyperZip --icon=app_icon.ico hyperzip_app.py
   ```
   Note: Replace `app_icon.ico` with your icon file if you have one.

3. **Edit the spec file** (HyperZip.spec) to include all necessary modules:
   ```python
   # Add this to the Analysis section
   hiddenimports=['PIL._tkinter_finder', 'customtkinter', 'tinify'],
   ```

4. **Build the executable**:
   ```bash
   pyinstaller HyperZip.spec
   ```
   
   Or if you skipped creating a spec file:
   ```bash
   pyinstaller --onefile --windowed --name HyperZip --icon=app_icon.ico hyperzip_app.py
   ```

5. **Locate the executable** in the `dist` folder.

## Building for macOS (.app)

1. **Install PyInstaller** (if not already installed):
   ```bash
   pip install pyinstaller
   ```

2. **Create a spec file** (optional but recommended):
   ```bash
   pyi-makespec --onefile --windowed --name HyperZip --icon=app_icon.icns hyperzip_app.py
   ```
   Note: Replace `app_icon.icns` with your icon file if you have one. macOS requires the .icns format.

3. **Edit the spec file** (HyperZip.spec) to include all necessary modules:
   ```python
   # Add this to the Analysis section
   hiddenimports=['PIL._tkinter_finder', 'customtkinter', 'tinify'],
   ```

4. **Build the application bundle**:
   ```bash
   pyinstaller HyperZip.spec
   ```
   
   Or if you skipped creating a spec file:
   ```bash
   pyinstaller --onefile --windowed --name HyperZip --icon=app_icon.icns hyperzip_app.py
   ```

5. **Locate the .app bundle** in the `dist` folder.

## Advanced Configuration

### Including Additional Files

If your application needs additional files (like configuration files or resources), add them to the spec file:

```python
# Add to the Analysis section
datas=[('hyperzip_config.json', '.'), ('resources/', 'resources')],
```

### Creating an Installer (Windows)

For Windows, you can create an installer using tools like:
- [Inno Setup](https://jrsoftware.org/isinfo.php)
- [NSIS](https://nsis.sourceforge.io/)

### Creating a DMG (macOS)

For macOS, you can create a DMG file:

1. Create a new folder and copy your .app bundle into it
2. Open Disk Utility
3. File > New Image > Image from Folder
4. Select your folder and create the DMG

## Troubleshooting

### Missing Modules

If you encounter "ModuleNotFoundError" when running the executable, add the missing module to the `hiddenimports` list in the spec file.

### File Not Found Errors

If your application can't find resource files, make sure they're included in the `datas` list in the spec file.

### macOS Security Issues

On macOS, you might need to sign your application to avoid security warnings:

```bash
codesign --force --deep --sign - dist/HyperZip.app
```

For distribution outside the App Store, you might need an Apple Developer certificate.
