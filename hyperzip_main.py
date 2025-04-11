import os
import sys
import io
import traceback
from hyperzip_core import _log_func, Fore, Style, DEFAULT_SETTINGS, set_logger
from hyperzip_utils import cleanup_temp_folders
from hyperzip_archive import get_archive_profiles, process_and_archive_folder

# --- Main Function ---
def run_packing(settings, logger_func=print):
    """Main logic: finds folders in PROJECT_FOLDER, processes them, shows summary.
       Accepts a dictionary of settings and a logger function."""
    
    # Set the logger for this run
    set_logger(logger_func)
    
    project_folder = settings.get("PROJECT_FOLDER")
    if not project_folder or not os.path.isdir(project_folder):
        _log_func(f"{Fore.RED}Error: Invalid PROJECT_FOLDER provided: {project_folder}{Style.RESET_ALL}")
        return {"success": False, "message": "Invalid project folder."}

    # Change working directory to the project folder for processing
    try:
        original_cwd = os.getcwd()
        os.chdir(project_folder)
        _log_func(f"{Fore.YELLOW}Processing in directory: {project_folder}{Style.RESET_ALL}")
    except Exception as e:
        _log_func(f"{Fore.RED}Error changing directory to {project_folder}: {e}{Style.RESET_ALL}")
        return {"success": False, "message": f"Cannot access project folder: {e}"}

    success_count = 0
    fail_count = 0
    oversized_files_final = []
    total_size_kb = 0.0
    results_summary = [] # Store detailed results per folder

    # --- Build Archiver Profiles Config from Settings ---
    archive_profiles_config = get_archive_profiles(settings)

    # --- Validate Selected Profile and Archiver Path ---
    selected_profile_name = settings['ARCHIVE_PROFILE']
    if selected_profile_name not in archive_profiles_config:
        _log_func(f"{Fore.RED}Error: Invalid ARCHIVE_PROFILE '{selected_profile_name}' selected.{Style.RESET_ALL}")
        _log_func(f"{Fore.YELLOW}Available options: {', '.join(archive_profiles_config.keys())}{Style.RESET_ALL}")
        os.chdir(original_cwd) # Change back CWD
        return {"success": False, "message": f"Invalid archive profile: {selected_profile_name}"}

    selected_profile_config = archive_profiles_config[selected_profile_name]
    archiver_path = selected_profile_config["executable"]
    profile_tool = selected_profile_config["tool_family"]
    profile_ext = selected_profile_config["extension"]
    max_size_kb_limit = settings['max_size_kb'] # Use the specific setting name

    _log_func(f"{Fore.CYAN}Selected Profile: {selected_profile_name} (Using: {profile_tool}, Output: {profile_ext}){Style.RESET_ALL}")
    _log_func(f"Target archive size: <= {max_size_kb_limit} KB")

    if not archiver_path or not os.path.exists(archiver_path):
         _log_func(f"{Fore.RED}Error: Archiver '{profile_tool}' executable not found at: {archiver_path}{Style.RESET_ALL}")
         _log_func(f"{Fore.YELLOW}Please check the path in the GUI settings.{Style.RESET_ALL}")
         os.chdir(original_cwd)
         return {"success": False, "message": f"Archiver not found: {archiver_path}"}
    else:
         _log_func(f"{Fore.GREEN}Archiver '{profile_tool}' found: {archiver_path}{Style.RESET_ALL}")

    # --- Validate TinyPNG Key ---
    tinify_api_key_valid = False
    if settings['ENABLE_IMAGE_COMPRESSION']:
        api_key = settings.get('TINIFY_API_KEY')
        if not api_key:
            _log_func(f"{Fore.RED}Warning: Image compression enabled, but TINIFY_API_KEY is missing. Disabling compression.{Style.RESET_ALL}")
            settings['ENABLE_IMAGE_COMPRESSION'] = False # Disable for this run
        else:
            try:
                import tinify
                tinify.key = api_key
                tinify.validate() # Check if key is valid
                _log_func(f"{Fore.GREEN}TinyPNG API Key validated successfully.{Style.RESET_ALL}")
                tinify_api_key_valid = True
            except Exception as e:
                _log_func(f"{Fore.RED}TinyPNG API key error: {e}. Disabling image compression.{Style.RESET_ALL}")
                settings['ENABLE_IMAGE_COMPRESSION'] = False # Disable for this run
                tinify_api_key_valid = False
    settings['TINIFY_API_KEY_VALID'] = tinify_api_key_valid # Store validation status in settings dict

    # --- Check Python Libraries (Optional - GUI should handle this) ---
    # Basic check just in case
    try:
        from PIL import Image
        import htmlmin
        import jsmin
        import csscompressor
        import tinify
    except ImportError as e:
        _log_func(f"{Fore.RED}Error: Missing required Python library: {e.name}.{Style.RESET_ALL}")
        _log_func(f"{Fore.YELLOW}Install using: pip install {e.name}{Style.RESET_ALL}")
        os.chdir(original_cwd)
        return {"success": False, "message": f"Missing library: {e.name}"}

    # --- Print Selected Options ---
    _log_func(f"{Fore.YELLOW}Minification: {'Enabled' if settings['ENABLE_MINIFICATION'] else 'Disabled'}{Style.RESET_ALL}")
    _log_func(f"{Fore.YELLOW}Image Compression: {'Enabled' if settings['ENABLE_IMAGE_COMPRESSION'] else 'Disabled'}{Style.RESET_ALL}")
    if settings['ENABLE_IMAGE_COMPRESSION']:
        _log_func(f"  PNG Level: {settings['INITIAL_PNG_OPTIMIZATION_LEVEL']} -> {settings['MIN_PNG_OPTIMIZATION_LEVEL']}")
        _log_func(f"  JPEG Quality: {settings['INITIAL_JPEG_QUALITY']} -> {settings['MIN_JPEG_QUALITY']} (Step: ~{settings['JPEG_QUALITY_STEP']})")
    _log_func(f"{Fore.CYAN}Optimal Quality Search: {'Enabled' if settings['FIND_OPTIMAL_QUALITY'] else 'Disabled'}{Style.RESET_ALL}")
    _log_func("-" * 30)

    # --- Find Folders to Process ---
    # Find folders directly inside the project_folder (current directory)
    folders_to_process = [f for f in os.listdir('.') if os.path.isdir(f) and not f.startswith('.') and not f.startswith('_') and not f.endswith('_temp')]

    if not folders_to_process:
        _log_func(f"{Fore.YELLOW}No suitable sub-folders found to process in {project_folder}.{Style.RESET_ALL}")
    else:
        _log_func(f"{Fore.CYAN}Found {len(folders_to_process)} folder(s): {', '.join(folders_to_process)}{Style.RESET_ALL}")
        _log_func("-" * 30)

    # --- Process Each Folder ---
    base_dir = os.getcwd() # The project_folder is our base now
    for folder_name in folders_to_process:
        current_folder_path = os.path.join(base_dir, folder_name) # Absolute path to the folder being processed
        archive_output_filename = f"{folder_name}{profile_ext}"
        _log_func(f"{Fore.CYAN}Processing: {folder_name} -> {archive_output_filename}{Style.RESET_ALL}")

        # Call the refactored processing function
        # _log_func(f"  {Fore.WHITE}DEBUG: Calling process_and_archive_folder for '{folder_name}'...{Style.RESET_ALL}") # Removed DEBUG log
        final_size_kb, final_png_level, final_jpeg = process_and_archive_folder(
            current_folder_path, base_dir, settings, archive_profiles_config
        )
        # _log_func(f"  {Fore.WHITE}DEBUG: process_and_archive_folder returned: size={final_size_kb}, png={final_png_level}, jpeg={final_jpeg}{Style.RESET_ALL}") # Removed DEBUG log

        # --- Analyze Result for this Folder ---
        folder_result = {
            "folder": folder_name,
            "archive_name": archive_output_filename,
            "size_kb": final_size_kb,
            "png_level": int(final_png_level),
            "jpeg_quality": int(final_jpeg),
            "status": "Error" # Default status
        }

        if final_size_kb == -1:
            _log_func(f"{Fore.RED}Failed: Critical error processing {folder_name}. Skipping.{Style.RESET_ALL}")
            fail_count += 1
            folder_result["status"] = "Error"
        elif final_size_kb > max_size_kb_limit:
            _log_func(f"{Fore.RED}Result: COULD NOT reduce {folder_name} to <= {max_size_kb_limit} KB.{Style.RESET_ALL}")
            _log_func(f"{Fore.RED}        Final size was {final_size_kb:.2f} KB (at PNG={int(final_png_level)}, JPEG={int(final_jpeg)}).{Style.RESET_ALL}")
            oversized_info = f"{folder_name} ({final_size_kb:.2f} KB @ PNG={int(final_png_level)}/JPEG={int(final_jpeg)})"
            oversized_files_final.append(oversized_info)
            fail_count += 1
            total_size_kb += final_size_kb # Add final size even if oversized
            folder_result["status"] = "Oversized"
            folder_result["message"] = oversized_info
        else: # Success
            _log_func(f"{Fore.GREEN}Result: OK {archive_output_filename} ({final_size_kb:.2f} KB) (PNG={int(final_png_level)}, JPEG={int(final_jpeg)}){Style.RESET_ALL}")
            success_count += 1
            total_size_kb += final_size_kb
            folder_result["status"] = "Success"

        results_summary.append(folder_result)
        _log_func("-" * 30)

    # --- Final Cleanup Check (in project_folder) ---
    _log_func(f"{Fore.WHITE}Final cleanup check in {project_folder}...{Style.RESET_ALL}")
    items_cleaned = cleanup_temp_folders(base_dir)

    # --- Final Summary ---
    summary_lines = []
    summary_lines.append("\n" + f"{Fore.YELLOW}=============== Summary ==============={Style.RESET_ALL}")
    summary_lines.append(f"Profile used: {selected_profile_name}")
    summary_lines.append(f"{Fore.GREEN}Successful archives (<= {max_size_kb_limit} KB): {success_count}{Style.RESET_ALL}")
    summary_lines.append(f"{Fore.RED}Failed/Oversized archives: {fail_count}{Style.RESET_ALL}")

    if success_count > 0 or fail_count > 0:
        # Calculate average size of successful archives only
        successful_size_kb_total = sum(r['size_kb'] for r in results_summary if r['status'] == 'Success')
        avg_success_size = successful_size_kb_total / success_count if success_count > 0 else 0.0

        summary_lines.append(f"{Fore.CYAN}Total size of final archives (incl. oversized): {total_size_kb:.2f} KB{Style.RESET_ALL}")
        if success_count > 0:
            summary_lines.append(f"{Fore.CYAN}Average size of successful archives: {avg_success_size:.2f} KB{Style.RESET_ALL}")

    if oversized_files_final:
        summary_lines.append("-" * 20)
        summary_lines.append(f"{Fore.RED}{len(oversized_files_final)} archive(s) exceeded {max_size_kb_limit} KB after optimization:{Style.RESET_ALL}")
        for i, file_info in enumerate(oversized_files_final, 1):
            summary_lines.append(f"{Fore.RED}{i}. {file_info}{Style.RESET_ALL}")
    elif fail_count == 0 and success_count > 0:
        summary_lines.append(f"{Fore.GREEN}All successfully created archives are within the size limit.{Style.RESET_ALL}")
    elif fail_count == 0 and success_count == 0 and not folders_to_process:
         summary_lines.append(f"{Fore.YELLOW}No folders were processed.{Style.RESET_ALL}")

    summary_lines.append(f"{Fore.YELLOW}====================================={Style.RESET_ALL}\n")

    # Log the summary
    for line in summary_lines:
        _log_func(line)

    # Change back to original directory
    os.chdir(original_cwd)

    # Return detailed results
    return {
        "success": fail_count == 0,
        "message": "Processing complete." if fail_count == 0 else f"{fail_count} folder(s) failed or were oversized.",
        "summary_lines": summary_lines, # Raw summary lines with color codes
        "results_per_folder": results_summary,
        "success_count": success_count,
        "fail_count": fail_count,
        "total_size_kb": total_size_kb
    }

# --- Script Entry Point (for standalone execution) ---
if __name__ == "__main__":
    # When run directly, use default settings and standard print
    print("Running hyperzip_main.py directly with default settings...")
    # Use default settings defined at the top
    current_settings = DEFAULT_SETTINGS.copy()

    # Need to determine the script's directory to find potential project folders if not specified
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

    # Add dummy paths if not set, just for standalone run (won't work unless paths are real)
    if not current_settings.get("winrar_path"): current_settings["winrar_path"] = "winrar.exe"
    if not current_settings.get("sevenzip_path"): current_settings["sevenzip_path"] = "7z.exe"
    if not current_settings.get("zpaq_path"): current_settings["zpaq_path"] = "zpaq.exe"

    try:
        run_packing(current_settings, logger_func=print) # Use standard print
    except Exception as e:
        print(f"{Fore.RED}--------------------------------------------{Style.RESET_ALL}")
        print(f"{Fore.RED}AN UNHANDLED CRITICAL ERROR OCCURRED:{Style.RESET_ALL}")
        traceback.print_exc()
        print(f"{Fore.RED}--------------------------------------------{Style.RESET_ALL}")
        input("Critical error occurred. Press Enter to exit...")
        sys.exit(1)
    else:
         input("Processing finished (standalone mode). Press Enter to exit...")
         sys.exit(0)
