#!/bin/bash

echo "Building HyperZip for macOS..."
echo

echo "Installing required packages..."
pip3 install -r requirements.txt
echo

echo "Checking for configuration file..."
SPEC_FILE="HyperZip.spec"
if [ -f "hyperzip_config.json" ]; then
    echo "Found hyperzip_config.json, will include in build."
    echo "Creating custom spec file with config..."
    cat > temp_spec.spec << 'EOL'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['hyperzip_app.py'],
    pathex=[],
    binaries=[],
    datas=[('hyperzip_config.json', '.')],
    hiddenimports=[
        'PIL._tkinter_finder',
        'customtkinter',
        'tinify',
        'htmlmin',
        'jsmin',
        'csscompressor',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HyperZip',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS specific app bundle
app = BUNDLE(
    exe,
    name='HyperZip.app',
    icon=None,
    bundle_identifier=None,
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
    },
)
EOL
    SPEC_FILE="temp_spec.spec"
else
    echo "No configuration file found, using default spec."
fi
echo

echo "Building application bundle..."
pyinstaller $SPEC_FILE
BUILD_RESULT=$?
echo

if [ $BUILD_RESULT -eq 0 ] && [ -d "dist/HyperZip.app" ]; then
    echo "Build successful! Application bundle is located at: dist/HyperZip.app"
    
    echo "Would you like to create a DMG file? (y/n)"
    read create_dmg
    
    if [ "$create_dmg" = "y" ] || [ "$create_dmg" = "Y" ]; then
        echo "Creating DMG file..."
        mkdir -p dist/dmg_temp
        cp -R dist/HyperZip.app dist/dmg_temp/
        hdiutil create -volname "HyperZip" -srcfolder dist/dmg_temp -ov -format UDZO dist/HyperZip.dmg
        rm -rf dist/dmg_temp
        
        if [ -f "dist/HyperZip.dmg" ]; then
            echo "DMG file created successfully at: dist/HyperZip.dmg"
        else
            echo "Failed to create DMG file."
        fi
    fi
else
    echo "Build failed with error code $BUILD_RESULT. Please check the error messages above."
fi

# Clean up temporary spec file if it was created
if [ "$SPEC_FILE" = "temp_spec.spec" ]; then
    echo "Cleaning up temporary spec file..."
    rm -f temp_spec.spec
fi

echo
echo "Press Enter to exit..."
read
