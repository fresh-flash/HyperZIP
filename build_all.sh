#!/bin/bash

echo "Building HyperZip for macOS and Windows..."
echo

echo "Installing required packages..."
pip3 install -r requirements.txt
echo

echo "Removing previous build directory..."
if [ -d "dist" ]; then
    rm -rf dist
fi
echo

echo "===== Building for macOS ====="
echo "Building application bundle with HyperZip.spec..."
pyinstaller --clean HyperZip.spec
MACOS_BUILD_RESULT=$?
echo

if [ $MACOS_BUILD_RESULT -eq 0 ] && [ -d "dist/HyperZip.app" ]; then
    echo "macOS build successful! Application bundle is located at: dist/HyperZip.app"
    
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
    echo "macOS build failed with error code $MACOS_BUILD_RESULT. Please check the error messages above."
    exit 1
fi

echo
echo "===== Building for Windows ====="
echo "Note: This will only work if run on a system with Wine or appropriate cross-compilation tools."
echo

# Check if we can run Windows commands
if command -v wine >/dev/null 2>&1; then
    echo "Wine found. Attempting Windows build..."
    
    # Backup the dist directory with macOS build
    echo "Backing up macOS build..."
    mkdir -p dist_macos_backup
    cp -R dist/* dist_macos_backup/
    
    # Run Windows build using Wine
    echo "Running Windows build with Wine..."
    wine cmd /c build_windows.bat
    WINDOWS_BUILD_RESULT=$?
    
    if [ $WINDOWS_BUILD_RESULT -eq 0 ] && [ -f "dist/HyperZip.exe" ]; then
        echo "Windows build successful! Executable is located at: dist/HyperZip.exe"
        
        # Move Windows build to a separate directory
        echo "Moving Windows build to dist_windows directory..."
        mkdir -p dist_windows
        mv dist/HyperZip.exe dist_windows/
        
        # Restore macOS build
        echo "Restoring macOS build to dist directory..."
        cp -R dist_macos_backup/* dist/
        
        # Clean up
        rm -rf dist_macos_backup
    else
        echo "Windows build failed. Please check the error messages above."
        
        # Restore macOS build
        echo "Restoring macOS build to dist directory..."
        rm -rf dist
        mv dist_macos_backup dist
    fi
else
    echo "Wine not found. Skipping Windows build as it requires Wine or a Windows system."
fi

echo
echo "Build process completed."
echo "Press Enter to exit..."
read
