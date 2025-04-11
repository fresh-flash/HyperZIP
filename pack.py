#!/usr/bin/env python3
"""
HyperZip - Banner Archive Optimization Tool
-------------------------------------------
This script optimizes and compresses banner folders to meet size requirements.
It uses minification for HTML/CSS/JS and image compression via TinyPNG.

This is the main entry point that imports functionality from the modular files.
"""

import sys
import os
from hyperzip_core import DEFAULT_SETTINGS
from hyperzip_main import run_packing

if __name__ == "__main__":
    # When run directly, use default settings and standard print
    print("Running pack.py with default settings...")
    
    # Use default settings defined in hyperzip_core
    current_settings = DEFAULT_SETTINGS.copy()

    # Need to determine the script's directory to find potential project folders
    try:
        if getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(sys.executable)
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    # If PROJECT_FOLDER is not set in defaults, assume it's the script's directory
    if current_settings.get("PROJECT_FOLDER") is None:
         current_settings["PROJECT_FOLDER"] = script_dir
         print(f"Assuming project folder is script directory: {script_dir}")

    # Add default paths if not set
    if not current_settings.get("winrar_path"): 
        current_settings["winrar_path"] = r"C:\Program Files\WinRAR\WinRAR.exe"
    if not current_settings.get("sevenzip_path"): 
        current_settings["sevenzip_path"] = r"C:\Program Files\7-Zip\7z.exe"
    if not current_settings.get("zpaq_path"): 
        current_settings["zpaq_path"] = r"C:\zpaq\zpaq.exe"

    try:
        # Run the main function from hyperzip_main
        result = run_packing(current_settings)
        if not result["success"]:
            print(f"Processing completed with issues: {result['message']}")
        input("Press Enter to exit...")
    except Exception as e:
        import traceback
        print("--------------------------------------------")
        print("AN UNHANDLED CRITICAL ERROR OCCURRED:")
        traceback.print_exc()
        print("--------------------------------------------")
        input("Critical error occurred. Press Enter to exit...")
        sys.exit(1)
