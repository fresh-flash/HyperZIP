import os
import sys
import time
import functools
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor
from hyperzip_core import _log_func, Fore, Style, PNG_EXTENSIONS, JPEG_EXTENSIONS, IMAGE_EXTENSIONS

# Import image compression libraries
try:
    import tinify
    from PIL import Image
except ImportError as e:
    _log_func(f"{Fore.RED}Error: Missing image library: {e.name}. Install with pip.{Style.RESET_ALL}")
    raise

# --- Oxipng Compression ---
def compress_png_with_oxipng(file_path, oxipng_level):
    """Compresses a PNG image using the oxipng executable."""
    saved_bytes = 0
    original_size = 0
    oxipng_executable = "oxipng.exe" # Assumes it's in PATH or same dir

    # Check if oxipng executable exists - try multiple locations
    if not shutil.which(oxipng_executable) and not os.path.exists(oxipng_executable):
        # Try finding it in various locations
        possible_locations = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "oxipng.exe"),  # Same dir as script
            os.path.join(os.getcwd(), "oxipng.exe"),  # Current working directory
            os.path.abspath("oxipng.exe"),  # Absolute path in current directory
            os.path.join(os.path.dirname(sys.executable), "oxipng.exe"),  # Next to Python executable
            # Check in the oxipng-9.1.4-i686-pc-windows-msvc directory
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "oxipng-9.1.4-i686-pc-windows-msvc", "oxipng.exe"),
            os.path.join(os.getcwd(), "oxipng-9.1.4-i686-pc-windows-msvc", "oxipng.exe"),
        ]
        
        # For PyInstaller bundles
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                possible_locations.append(os.path.join(sys._MEIPASS, "oxipng.exe"))
                # Also check in the directory where the executable is located
                possible_locations.append(os.path.join(os.path.dirname(sys.executable), "oxipng-9.1.4-i686-pc-windows-msvc", "oxipng.exe"))
        except (ImportError, AttributeError):
            pass
            
        # Try each location
        for location in possible_locations:
            if os.path.exists(location):
                oxipng_executable = location
                _log_func(f"  {Fore.GREEN}Found oxipng.exe at: {location}{Style.RESET_ALL}")
                break
                
        # If still not found
        if not shutil.which(oxipng_executable) and not os.path.exists(oxipng_executable):
            _log_func(f"{Fore.RED}  Error: oxipng.exe not found. Cannot compress {os.path.basename(file_path)}.{Style.RESET_ALL}")
            _log_func(f"{Fore.RED}  Searched in: {', '.join(possible_locations)}{Style.RESET_ALL}")
            return 0, 0 # Saved bytes, original size

    try:
        original_size = os.path.getsize(file_path)
        if original_size == 0: return 0, 0

        # Clamp level between 0 and 6 for oxipng
        level = max(0, min(6, int(oxipng_level)))
        _log_func(f"  {Fore.CYAN}Processing {os.path.basename(file_path)} PNG with Oxipng L{level}{Style.RESET_ALL}")

        command = [
            oxipng_executable,
            "-o", str(level), # Optimization level
            "--strip", "safe", # Strip metadata
            "--quiet", # Suppress oxipng console output
            "--force", # Overwrite existing file
            file_path
        ]

        # Use CREATE_NO_WINDOW on Windows to hide console
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(command, capture_output=True, text=True, check=False, creationflags=creationflags)

        if result.returncode != 0:
            _log_func(f"{Fore.RED}  Error running oxipng on {os.path.basename(file_path)}: {result.stderr or result.stdout}{Style.RESET_ALL}")
            return 0, original_size # Return 0 saved, original size on error

        time.sleep(0.05) # Ensure file write is complete
        compressed_size = os.path.getsize(file_path)
        saved = original_size - compressed_size
        saved_bytes = saved

        if original_size > 0:
            saved_percent = (saved / original_size) * 100
            if saved > 0 : _log_func(f"    {Fore.GREEN}{os.path.basename(file_path)}: Saved {saved_percent:.1f}% ({saved/1024:.1f} KB){Style.RESET_ALL}")
            elif saved < 0: _log_func(f"    {Fore.YELLOW}{os.path.basename(file_path)}: Warn: Size increased by {-saved/1024:.1f} KB{Style.RESET_ALL}")
        elif compressed_size > 0: _log_func(f"    {Fore.YELLOW}{os.path.basename(file_path)}: Warn: Original 0, new size {compressed_size} B{Style.RESET_ALL}")

    except FileNotFoundError:
        _log_func(f"{Fore.RED}  Error: File not found during oxipng compression: {file_path}{Style.RESET_ALL}")
        saved_bytes = 0
    except Exception as e:
        _log_func(f"{Fore.RED}  Error compressing {os.path.basename(file_path)} with oxipng: {type(e).__name__} - {str(e)}{Style.RESET_ALL}")
        saved_bytes = 0
        # Attempt to get original size if possible, otherwise return 0
        try: original_size = os.path.getsize(file_path)
        except: original_size = 0

    return saved_bytes, original_size


# --- Image Compression Function (Unified) ---
def compress_image(file_path, png_compressor, png_level, jpeg_quality, tinify_api_key_valid):
    """Compresses one image using the selected PNG compressor or TinyPNG/Pillow for others.
       Requires tinify_api_key_valid status passed in."""

    original_size = 0; saved_bytes = 0
    file_basename = os.path.basename(file_path)
    current_tinify_valid = tinify_api_key_valid # Local copy for TinyPNG status

    # Check file existence early
    try:
        if not os.path.exists(file_path):
            _log_func(f"{Fore.RED}  Error: File not found before compression: {file_path}{Style.RESET_ALL}")
            return 0, 0, current_tinify_valid # Saved, Original, TinyPNG Status
        original_size = os.path.getsize(file_path)
        if original_size == 0:
             _log_func(f"{Fore.YELLOW}  Skipping empty file: {file_basename}{Style.RESET_ALL}")
             return 0, 0, current_tinify_valid
    except OSError as e:
         _log_func(f"{Fore.RED}  Error accessing file before compression {file_basename}: {e}{Style.RESET_ALL}")
         return 0, 0, current_tinify_valid

    _, ext = os.path.splitext(file_path); ext = ext.lower()
    processed = False
    min_jpeg_quality_local = 10

    try:
        # --- PNG Compression ---
        if ext in PNG_EXTENSIONS:
            processed = True
            if png_compressor == "oxipng":
                # Use Oxipng
                saved_bytes, original_size = compress_png_with_oxipng(file_path, png_level)
                # Oxipng doesn't affect TinyPNG key validity
                return saved_bytes, original_size, current_tinify_valid
            else: # Default or explicitly "tinypng"
                if not current_tinify_valid:
                    _log_func(f"{Fore.YELLOW}  Skipping TinyPNG for {file_basename} (API key issue).{Style.RESET_ALL}")
                    return 0, original_size, current_tinify_valid

                _log_func(f"  {Fore.CYAN}Processing {file_basename} PNG with TinyPNG{Style.RESET_ALL}")
                # Simplified: Single pass for TinyPNG on PNGs
                source = tinify.from_file(file_path)
                source.to_file(file_path) # Overwrites original

        # --- JPEG Compression ---
        elif ext in JPEG_EXTENSIONS:
            processed = True
            if not current_tinify_valid:
                 _log_func(f"{Fore.YELLOW}  Skipping TinyPNG for {file_basename} (API key issue). Pillow only.{Style.RESET_ALL}")
            else:
                current_jpeg_quality = max(min_jpeg_quality_local, min(95, int(jpeg_quality)))
                _log_func(f"  {Fore.CYAN}Processing {file_basename} JPEG Q{current_jpeg_quality} via TinyPNG{Style.RESET_ALL}")
                try:
                    source = tinify.from_file(file_path)
                    source.to_file(file_path) # Overwrite original
                except tinify.Error as tiny_e:
                    _log_func(f"{Fore.YELLOW}  Warn: TinyPNG failed on {file_basename}: {tiny_e}. Pillow only.{Style.RESET_ALL}")

            # Always apply Pillow quality if needed, even if TinyPNG worked/skipped, to ensure target quality
            current_jpeg_quality = max(min_jpeg_quality_local, min(95, int(jpeg_quality))) # Recalculate just in case
            if current_jpeg_quality < 95:
                _log_func(f"    {Fore.WHITE}Applying Pillow JPEG quality Q{current_jpeg_quality} to {file_basename}{Style.RESET_ALL}")
                time.sleep(0.05) # Small delay before Pillow access
                try:
                    with Image.open(file_path) as img:
                        save_options = {'quality': current_jpeg_quality, 'optimize': True, 'progressive': True}
                        img_mode = img.mode
                        if img_mode == 'RGBA' or img_mode == 'P':
                            img = img.convert('RGB')
                        if 'icc_profile' in img.info:
                            save_options['icc_profile'] = img.info['icc_profile']
                        img.save(file_path, 'JPEG', **save_options)
                        _log_func(f"    {Fore.WHITE}Pillow save completed for {file_basename} at Q{current_jpeg_quality}{Style.RESET_ALL}")
                except Exception as pil_e:
                    _log_func(f"{Fore.RED}    Error applying JPEG quality with Pillow: {str(pil_e)}{Style.RESET_ALL}")
            else:
                 _log_func(f"    {Fore.WHITE}Skipping Pillow JPEG quality for {file_basename} (Quality={current_jpeg_quality}){Style.RESET_ALL}")

        # --- Other Image Formats (WebP, GIF etc.) --- handled by TinyPNG only
        elif ext in IMAGE_EXTENSIONS:
            processed = True
            if not current_tinify_valid:
                _log_func(f"{Fore.YELLOW}  Skipping TinyPNG for {file_basename} ({ext.upper()}) (API key issue).{Style.RESET_ALL}")
                return 0, original_size, current_tinify_valid

            _log_func(f"  {Fore.CYAN}Processing {file_basename} ({ext.upper()}) via TinyPNG{Style.RESET_ALL}")
            source = tinify.from_file(file_path)
            source.to_file(file_path)

        # --- Calculate Savings (only if processed by TinyPNG/Pillow, oxipng calculates its own) ---
        if processed and png_compressor != "oxipng": # Don't recalculate if oxipng already did
            time.sleep(0.05) # Ensure file write is complete before getting size
            try:
                compressed_size = os.path.getsize(file_path)
                saved = original_size - compressed_size
                saved_bytes = saved # Can be negative if size increased
                if original_size > 0:
                    saved_percent = (saved / original_size) * 100
                    if saved > 0 : _log_func(f"    {Fore.GREEN}{file_basename}: Saved {saved_percent:.1f}% ({saved/1024:.1f} KB){Style.RESET_ALL}")
                    elif saved < 0: _log_func(f"    {Fore.YELLOW}{file_basename}: Warn: Size increased by {-saved/1024:.1f} KB{Style.RESET_ALL}")
                elif compressed_size > 0: _log_func(f"    {Fore.YELLOW}{file_basename}: Warn: Original 0, new size {compressed_size} B{Style.RESET_ALL}")
            except FileNotFoundError:
                _log_func(f"{Fore.RED}    Error: File disappeared after compression: {file_path}{Style.RESET_ALL}")
                saved_bytes = 0
            except Exception as size_e:
                _log_func(f"{Fore.RED}    Error getting size after compression: {str(size_e)}{Style.RESET_ALL}")
                saved_bytes = 0

    # --- Error Handling for TinyPNG ---
    except tinify.AccountError as e:
        _log_func(f"{Fore.RED}TinyPNG Error: {e}. Disabling compression for this run.{Style.RESET_ALL}")
        current_tinify_valid = False; saved_bytes = 0; # Reset savings, original_size already fetched
    except tinify.ClientError as e:
        _log_func(f"{Fore.RED}TinyPNG client error for {file_basename}: {str(e)}{Style.RESET_ALL}")
        saved_bytes = 0; # Don't disable key, reset savings
    except tinify.ServerError as e:
        _log_func(f"{Fore.RED}TinyPNG server error for {file_basename}: {str(e)}{Style.RESET_ALL}")
        saved_bytes = 0; # Don't disable key, reset savings
    except FileNotFoundError: # Should be caught earlier, but just in case
        _log_func(f"{Fore.RED}Error: Source image not found during processing: {file_path}{Style.RESET_ALL}")
        saved_bytes = 0; original_size = 0
    except Exception as e:
        # General catch-all for unexpected errors during compression logic
        _log_func(f"{Fore.RED}Error compressing {file_basename}: {type(e).__name__} - {str(e)}{Style.RESET_ALL}")
        saved_bytes = 0 # Reset savings

    # Return total saved bytes, original size, and potentially updated TinyPNG key status
    return saved_bytes, original_size, current_tinify_valid


# --- Process Images in Folder ---
def process_images_in_folder(folder_path, png_compressor, current_png_level, current_jpeg_quality, tinify_api_key_valid):
    """Compresses images in the specified folder using the selected method.
       Returns total saved bytes, total original size, and updated tinify_api_key_valid status."""
    image_files = []
    total_original_image_size = 0
    total_saved_image_bytes = 0
    current_tinify_valid = tinify_api_key_valid # Track validity changes during processing

    # Collect image files
    file_list = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_list.append(os.path.join(root, file))

    # Find images to compress - always process images, even if tinify API key is invalid
    # (oxipng doesn't need a valid API key)
    for file_path in file_list:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in IMAGE_EXTENSIONS:
                try:
                    fsize = os.path.getsize(file_path)
                    if fsize == 0: continue # Skip empty files
                    # Limit based on TinyPNG free tier (5MB) if using tinypng
                    if png_compressor == "tinypng" and fsize >= 5 * 1000 * 1000:
                         _log_func(f"{Fore.YELLOW}  Skipping large image {os.path.basename(file_path)} (>{fsize/1024/1024:.1f}MB) for TinyPNG.{Style.RESET_ALL}")
                         continue # Skip this file for TinyPNG
                    # Oxipng has no practical size limit we need to enforce here
                    image_files.append(file_path)
                except OSError as e:
                    _log_func(f"{Fore.RED}  Error getting size for {os.path.basename(file_path)}: {e}{Style.RESET_ALL}")

    # Compress images concurrently
    if image_files:
        log_compressor = "TinyPNG/Pillow" if png_compressor == "tinypng" else "Oxipng (PNGs) / TinyPNG/Pillow (Others)"
        _log_func(f"  {Fore.YELLOW}Compressing {len(image_files)} images via {log_compressor}...{Style.RESET_ALL}")

        # Use functools.partial to pass fixed arguments to compress_image
        compress_func = functools.partial(compress_image,
                                          png_compressor=png_compressor,
                                          png_level=current_png_level,
                                          jpeg_quality=current_jpeg_quality,
                                          tinify_api_key_valid=current_tinify_valid)

        # --- Run sequentially instead of concurrently to avoid potential issues ---
        # _log_func(f"  {Fore.WHITE}DEBUG: Running image compression sequentially.{Style.RESET_ALL}") # Removed DEBUG log
        for image_file in image_files:
            try:
                saved, original, key_still_valid = compress_func(image_file)
                total_saved_image_bytes += saved
                total_original_image_size += original
                # Update TinyPNG validity status if the key became invalid
                if png_compressor != "oxipng" and not key_still_valid:
                    current_tinify_valid = False
                    # _log_func(f"  {Fore.YELLOW}DEBUG: TinyPNG key became invalid during sequential processing.{Style.RESET_ALL}") # Removed DEBUG log
            except Exception as seq_e:
                 _log_func(f"{Fore.RED}  Error during sequential compression of {os.path.basename(image_file)}: {seq_e}{Style.RESET_ALL}")
                 # Attempt to get original size if possible, otherwise add 0
                 try: total_original_image_size += os.path.getsize(image_file)
                 except: pass
        # _log_func(f"  {Fore.WHITE}DEBUG: Sequential image compression finished.{Style.RESET_ALL}") # Removed DEBUG log
        # --- End Sequential Execution ---

    elif not image_files:
        pass # _log_func(f"  {Fore.WHITE}No suitable images found for compression.{Style.RESET_ALL}") # Less verbose

    # Return totals and the potentially updated TinyPNG key status
    return total_saved_image_bytes, total_original_image_size, current_tinify_valid
