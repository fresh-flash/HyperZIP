import os
import shutil
from hyperzip_core import _log_func, Fore, Style

# --- Calculate Folder Size ---
def get_folder_size(folder_path):
    """Calculate the total size of a folder in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(file_path)
            except (FileNotFoundError, PermissionError):
                # Skip files that can't be accessed
                pass
    return total_size

# --- Temp Folder Function ---
def create_temp_folder(original_folder, base_dir):
    """Creates a temporary copy of the folder for processing inside base_dir."""
    temp_folder_name = os.path.basename(original_folder) + '_temp'
    temp_folder_path = os.path.join(base_dir, temp_folder_name)
    
    # _log_func(f"  {Fore.WHITE}Attempting to use temp folder: {temp_folder_path}{Style.RESET_ALL}") # Less verbose
    
    if os.path.exists(temp_folder_path):
        # _log_func(f"  {Fore.YELLOW}Temporary folder exists. Removing...{Style.RESET_ALL}") # Less verbose
        try:
            shutil.rmtree(temp_folder_path)
        except OSError as e:
            _log_func(f"{Fore.RED}  Error removing existing temp {temp_folder_path}: {e}{Style.RESET_ALL}")
            return None
            
    try:
        # Define patterns to ignore during copy
        ignore_patterns = shutil.ignore_patterns(
            '*.zip', '*.rar', '*.7z', '*.zpaq', # Archives
            '*.psd', '*.fla', '*.ai', '*.pdf', # Source/Design files
            '.*', # Hidden files/folders
            '*_temp', # Other temp folders
            'Thumbs.db', '*.ini', '*.db' # System/config files
        )
        
        shutil.copytree(original_folder, temp_folder_path, ignore=ignore_patterns)
        # _log_func(f"  {Fore.GREEN}Created temp folder: {temp_folder_path}{Style.RESET_ALL}") # Less verbose
        
        return temp_folder_path
        
    except Exception as e:
        _log_func(f"{Fore.RED}  Error copying to temp folder {temp_folder_path}: {e}{Style.RESET_ALL}")
        return None

# --- Process Files in Folder ---
def process_files_in_folder(folder_path, png_compressor, current_png_level, current_jpeg_quality,
                            process_settings, enable_image_compression, tinify_api_key_valid):
    """Minifies text files and compresses images in the specified folder using the selected PNG compressor.
       Returns total saved bytes, total original size, and updated tinify_api_key_valid status."""
    
    from hyperzip_minify import minify_file
    from hyperzip_image import process_images_in_folder
    
    total_saved_image_bytes = 0
    total_original_image_size = 0
    current_tinify_valid = tinify_api_key_valid

    # Collect all files
    file_list = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_list.append(os.path.join(root, file))

    # 1. Minify Text Files
    enable_minification = process_settings.get('ENABLE_MINIFICATION', False)
    if enable_minification:
        # _log_func(f"  {Fore.YELLOW}Minifying text files...{Style.RESET_ALL}") # Less verbose
        minify_tasks = [p for p in file_list if os.path.splitext(p)[1].lower() in ['.html', '.js', '.css']]
        if minify_tasks:
            processed_count = 0
            for file_path in minify_tasks:
                minify_file(file_path)
                processed_count += 1
            # _log_func(f"  {Fore.GREEN}Minification attempted for {processed_count} file(s).{Style.RESET_ALL}") # Less verbose

    # 2. Compress Images
    # Note: We attempt compression even if tinify key is invalid, as oxipng might be selected.
    # process_images_in_folder will handle the tinify key check internally if needed.
    if enable_image_compression:
        # Check if we have the new separate compression settings
        enable_png = True
        enable_jpeg = True
        
        # If this is a dictionary with separate settings, use them
        if isinstance(process_settings, dict):
            # Check if we have separate PNG and JPEG settings in the parent settings
            if 'ENABLE_PNG_COMPRESSION' in process_settings:
                enable_png = process_settings.get('ENABLE_PNG_COMPRESSION', True)
            if 'ENABLE_JPEG_COMPRESSION' in process_settings:
                enable_jpeg = process_settings.get('ENABLE_JPEG_COMPRESSION', True)
        
        total_saved_image_bytes, total_original_image_size, current_tinify_valid = process_images_in_folder(
            folder_path, png_compressor, current_png_level, current_jpeg_quality, tinify_api_key_valid,
            enable_png_compression=enable_png, enable_jpeg_compression=enable_jpeg
        )

    return total_saved_image_bytes, total_original_image_size, current_tinify_valid

# --- Cleanup Temp Folders ---
def cleanup_temp_folders(base_dir):
    """Removes any leftover temporary folders in the base directory.
    Enhanced with multiple attempts and Windows-specific handling."""
    import time
    import platform
    import subprocess
    
    items_cleaned = 0
    items_failed = 0
    max_attempts = 3
    
    try:
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if item.endswith('_temp') and os.path.isdir(item_path):
                _log_func(f"  Removing leftover temp: {item}")
                
                # Try multiple times with increasing delays
                for attempt in range(max_attempts):
                    try:
                        # First attempt with standard method
                        if attempt == 0:
                            shutil.rmtree(item_path)
                            items_cleaned += 1
                            break
                        
                        # On Windows, try more aggressive methods for subsequent attempts
                        elif platform.system() == 'Windows':
                            _log_func(f"  Retry #{attempt+1} with Windows-specific method...")
                            
                            # Force close any open handles (Windows only)
                            try:
                                # Use robocopy to empty the directory first (Windows trick)
                                empty_dir = os.path.join(base_dir, f"empty_dir_temp_{int(time.time())}")
                                os.makedirs(empty_dir, exist_ok=True)
                                subprocess.run(
                                    f'robocopy "{empty_dir}" "{item_path}" /MIR /NFL /NDL /NJH /NJS /NC /NS /NP', 
                                    shell=True, 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL
                                )
                                os.rmdir(empty_dir)
                                
                                # Now try to remove the emptied directory
                                os.rmdir(item_path)
                                items_cleaned += 1
                                break
                            except Exception as inner_e:
                                _log_func(f"{Fore.YELLOW}  Windows cleanup method failed: {str(inner_e)}{Style.RESET_ALL}")
                                
                                # Last resort: use rd /s /q (Windows only)
                                if attempt == max_attempts - 1:
                                    try:
                                        subprocess.run(
                                            f'rd /s /q "{item_path}"', 
                                            shell=True, 
                                            stdout=subprocess.DEVNULL, 
                                            stderr=subprocess.DEVNULL
                                        )
                                        if not os.path.exists(item_path):
                                            items_cleaned += 1
                                            _log_func(f"{Fore.GREEN}  Removed using Windows rd command{Style.RESET_ALL}")
                                            break
                                    except Exception:
                                        pass
                        
                        # Non-Windows or if Windows-specific methods failed
                        time.sleep(0.5 * (attempt + 1))  # Increasing delay between attempts
                        shutil.rmtree(item_path)
                        items_cleaned += 1
                        break
                        
                    except Exception as e:
                        if attempt == max_attempts - 1:
                            _log_func(f"{Fore.RED}  Failed to remove {item} after {max_attempts} attempts: {str(e)}{Style.RESET_ALL}")
                            items_failed += 1
                        # Otherwise continue to next attempt
                
        if items_cleaned > 0:
            _log_func(f"{Fore.GREEN}  Successfully removed {items_cleaned} temp folder(s).{Style.RESET_ALL}")
        if items_failed > 0:
            _log_func(f"{Fore.YELLOW}  Failed to remove {items_failed} temp folder(s). They may need manual cleanup.{Style.RESET_ALL}")
        if items_cleaned == 0 and items_failed == 0:
            _log_func("  No leftover temp folders found.")
            
    except Exception as e:
        _log_func(f"{Fore.RED}  Error during cleanup check: {e}{Style.RESET_ALL}")
        
    return items_cleaned
