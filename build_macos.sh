#!/bin/bash

echo "Building HyperZip for macOS..."
echo

echo "Installing required packages..."
pip3 install -r requirements.txt
echo

echo "Removing previous build directory..."
if [ -d "dist" ]; then
    rm -rf dist
fi
echo

echo "Building application bundle with HyperZip.spec..."
pyinstaller --clean HyperZip.spec
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

echo
echo "Press Enter to exit..."
read
