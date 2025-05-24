# HyperZip - Banner Archive Optimization Tool

HyperZip is a desktop application for optimizing and compressing banner folders to meet size requirements. It uses minification for HTML/CSS/JS and image compression via TinyPNG to reduce file sizes, then archives the optimized files using your preferred archiver.

![HyperZip Screenshot](screenshot.png)

## Features

- **Multiple Archive Formats**: Support for ZIP, RAR, 7Z, and ZPAQ formats
- **HTML/CSS/JS Minification**: Reduces text file sizes by removing unnecessary characters
- **Image Compression**: Optimizes PNG and JPEG images using TinyPNG API
- **Quality Adjustment**: Automatically adjusts image quality to meet target size
- **Optimal Quality Search**: Finds the highest possible quality that still meets size requirements
- **User-Friendly Interface**: Easy-to-use GUI with real-time progress logging
- **Configuration Saving**: Remembers your settings between sessions

## Installation

### Windows

1. Download the HyperZip executable
2. Run the executable
3. If prompted, install any required archivers (WinRAR, 7-Zip, or ZPAQ)

## Usage

1. **Select Project Folder**: Choose the directory containing banner folders to process
2. **Configure Archive Settings**: Select your preferred archiver and set paths
3. **Adjust Optimization Settings**:
   - Enable/disable minification
- TinyPNG API key (if using image compression)

## Installation

### From Source

1. Clone or download this repository
2. Install required packages:
   ```bash
   pip install customtkinter pillow htmlmin jsmin csscompressor tinify
   ```
3. Run the application:
   ```bash
   python hyperzip_app.py
   ```

### Building Executable

#### Windows

1. Use the one-click build script (recommended for beginners):
   ```powershell
   # In PowerShell:
   .\start-build.ps1         # One-click build script for PowerShell
   ```
   ```cmd
   # In Command Prompt:
   start-build.bat           # One-click build script for Command Prompt
   ```

   These scripts will automatically build HyperZip without requiring any additional commands.

2. Or use the interactive build helper:
   ```powershell
   # In PowerShell:
   .\build.ps1               # Interactive build helper for PowerShell
   ```
   ```cmd
   # In Command Prompt:
   build.bat                 # Interactive build helper for Command Prompt
   ```

   These helper scripts will detect your environment and guide you through the build process.

3. Or run one of the build scripts directly:
   ```powershell
   # In PowerShell:
   .\build_all.ps1            # Builds for Windows and attempts macOS build if possible
   .\build_windows.bat        # Builds for Windows only
   .\build_all.bat            # Builds for Windows and attempts macOS build if possible
   ```
   ```cmd
   # In Command Prompt:
   build_windows.bat          # Builds for Windows only
   build_all.bat              # Builds for Windows and attempts macOS build if possible
   ```
   
   > **Important Note for PowerShell Users**: 
   > In PowerShell, you must prefix script names with `.\` to run them from the current directory.
   > For example, use `.\start-build.ps1` instead of just `start-build.ps1`.
   
4. Or build manually:
   ```bash
   pip install pyinstaller
   pyinstaller HyperZip.spec
   ```
2. Find the executable in the `dist` folder

#### macOS

1. Run one of the build scripts:
   ```bash
   chmod +x build_macos.sh
   ./build_macos.sh    # Builds for macOS only
   
   chmod +x build_all.sh
   ./build_all.sh      # Builds for macOS and attempts Windows build if Wine is available
   ```
   Or manually:
   ```bash
   pip3 install pyinstaller
   pyinstaller HyperZip.spec
   ```
2. Find the application bundle in the `dist` folder

#### Building for Both Platforms

- On Windows (PowerShell): `.\build_all.ps1`
- On Windows (Command Prompt): `build_all.bat`
- On macOS: `./build_all.sh`

For detailed build instructions, see [build_instructions.md](build_instructions.md).

## Usage

1. **Select Project Folder**: Choose the directory containing banner folders to process
2. **Configure Archive Settings**: Select your preferred archiver and set paths
3. **Adjust Optimization Settings**:
   - Enable/disable minification
   - Enable/disable image compression
   - Set PNG optimization level and JPEG quality
   - Configure quality adjustment parameters
4. **Set Target Size**: Specify the maximum size in KB for the output archives
5. **Start Processing**: Click the "Start Processing" button
6. **Monitor Progress**: Watch the log area for real-time updates

## Project Structure

- `hyperzip_app.py` - Main GUI application
- `hyperzip_core.py` - Core settings and constants
- `hyperzip_minify.py` - HTML/CSS/JS minification
- `hyperzip_image.py` - Image compression via TinyPNG
- `hyperzip_utils.py` - Utility functions
- `hyperzip_archive.py` - Archive creation and optimization
- `hyperzip_main.py` - Main processing logic
- `pack.py` - Simple command-line entry point

## License

[MIT License](LICENSE)

## Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI
- [TinyPNG](https://tinypng.com/) for the image compression API
