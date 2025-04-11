import os
import subprocess
import math
import shutil
import io
from hyperzip_core import _log_func, Fore, Style
from hyperzip_utils import create_temp_folder, process_files_in_folder

# --- Archive Profiles ---
def get_archive_profiles(settings):
    """Build archive profiles configuration from settings."""
    return {
        "winrar_zip": {
            "tool_family": "winrar",
            "executable": settings['winrar_path'],
            "extension": ".zip",
            "params": "-m5 -afzip"
        },
        "winrar_rar": {
            "tool_family": "winrar",
            "executable": settings['winrar_path'],
            "extension": ".rar",
            "params": "-m5 -ma5 -rr5p"
        },
        "7zip_7z": {
            "tool_family": "7zip",
            "executable": settings['sevenzip_path'],
            "extension": ".7z",
            "params": "-mx=9 -t7z"
        },
        "7zip_zip": {
            "tool_family": "7zip",
            "executable": settings['sevenzip_path'],
            "extension": ".zip",
            "params": "-mx=9 -tzip"
        },
        "zpaq_zpaq": {
            "tool_family": "zpaq",
            "executable": settings['zpaq_path'],
            "extension": ".zpaq",
            "params": "-m5"
        }
    }

# --- Main Processing and Archiving Loop for a Single Folder ---
def process_and_archive_folder(folder_path, base_dir, settings, archive_profiles_config):
    """Copies, processes, archives (using selected profile), and adjusts quality for one folder.
       Returns final size, final PNG level, final JPEG quality."""

    # Extract settings for clarity
    initial_png_level = settings['INITIAL_PNG_OPTIMIZATION_LEVEL']
    initial_jpeg_quality = settings['INITIAL_JPEG_QUALITY']
    min_png_level = settings['MIN_PNG_OPTIMIZATION_LEVEL']
    min_jpeg_quality = settings['MIN_JPEG_QUALITY']
    jpeg_quality_step = settings['JPEG_QUALITY_STEP']
    max_size_kb = settings['max_size_kb']
    find_optimal = settings['FIND_OPTIMAL_QUALITY']
    enable_minification = settings['ENABLE_MINIFICATION']
    enable_image_compression = settings['ENABLE_IMAGE_COMPRESSION']
    tinify_api_key_valid = settings['TINIFY_API_KEY_VALID'] # Initial status
    # Get the PNG compressor setting, default to 'tinypng' if missing
    png_compressor = settings.get('png_compressor', 'tinypng').lower() 

    current_png_level = initial_png_level
    current_jpeg_quality = initial_jpeg_quality
    attempt = 1

    last_archive_size_kb = -1
    last_settings_tuple = None
    best_fit_size_kb = -1
    best_fit_settings_tuple = None

    # Get Profile Specifics from the passed config
    profile_name = settings['ARCHIVE_PROFILE']
    if profile_name not in archive_profiles_config:
        _log_func(f"{Fore.RED}Error: Profile '{profile_name}' not found in provided config.{Style.RESET_ALL}")
        return -1, initial_png_level, initial_jpeg_quality # Error state

    profile_config = archive_profiles_config[profile_name]
    tool_family = profile_config["tool_family"]
    archiver_executable = profile_config["executable"]
    archive_extension = profile_config["extension"]
    base_compression_params = profile_config["params"]

    archive_file_name = f"{os.path.basename(folder_path)}{archive_extension}"
    # Place archive in the *base_dir* (where the original folders are), not inside temp
    archive_file_path = os.path.join(base_dir, archive_file_name)

    _log_func(f"{Fore.YELLOW}Using Profile: {profile_name} (Tool: {tool_family}, Ext: {archive_extension}, Params: '{base_compression_params}'){Style.RESET_ALL}")

    while True: # Loop for quality adjustment attempts
        _log_func(f"{Fore.MAGENTA}--- Attempt {attempt} for: {os.path.basename(folder_path)} ({profile_name}) ---{Style.RESET_ALL}")
        # DEBUG: Log quality values at the START of the attempt
        # _log_func(f"  {Fore.WHITE}DEBUG: Starting Attempt {attempt} with PNG={int(current_png_level)}, JPEG={int(current_jpeg_quality)}{Style.RESET_ALL}") # Removed DEBUG log
        # _log_func(f"{Fore.MAGENTA}Settings: PNG={int(current_png_level)}, JPEG={int(current_jpeg_quality)}{Style.RESET_ALL}") # Original log, commented out for clarity

        temp_folder = None
        file_size_kb = -1
        original_image_size_sum = 0

        try:
            # 1. Create temp copy in base_dir
            temp_folder = create_temp_folder(folder_path, base_dir)
            if temp_folder is None:
                _log_func(f"{Fore.RED}Critical error: Failed to create temp folder. Skipping.{Style.RESET_ALL}")
                return -1, initial_png_level, initial_jpeg_quality

            # 2. Process files in temp copy (pass relevant settings)
            saved_bytes, original_image_size_sum, tinify_api_key_valid = process_files_in_folder(
                temp_folder, png_compressor, current_png_level, current_jpeg_quality,
                enable_minification, enable_image_compression, tinify_api_key_valid
            )
            # _log_func(f"  {Fore.WHITE}DEBUG: process_files_in_folder returned saved_bytes={saved_bytes}, original_size={original_image_size_sum}, key_valid={tinify_api_key_valid}{Style.RESET_ALL}") # Removed DEBUG log

            # If API key became invalid during processing (and we were using tinypng), stop quality adjustment
            # Oxipng doesn't rely on the key, so we can continue if that was the compressor.
            if not tinify_api_key_valid and enable_image_compression and png_compressor == 'tinypng':
                _log_func(f"{Fore.RED}TinyPNG key became invalid during processing. Cannot reliably adjust quality using TinyPNG.{Style.RESET_ALL}")
                if temp_folder and os.path.exists(temp_folder):
                    shutil.rmtree(temp_folder, ignore_errors=True)
                # Return error state or last known good state? Returning error for now.
                return -1, current_png_level, current_jpeg_quality

            # 3. Archive the temporary folder
            cmd = []
            subprocess_cwd = None
            archive_creation_successful = False
            temp_folder_basename = os.path.basename(temp_folder)

            # Get exclusions from settings
            exclusion_patterns = settings.get("ARCHIVE_EXCLUSIONS", "").split()
            exclusion_args = []

            params_list = base_compression_params.split()

            # --- Build Archiver Command ---
            if tool_family == "winrar":
                subprocess_cwd = temp_folder # Run from inside temp
                content_to_archive = "." # Archive current dir contents
                cmd = [ archiver_executable, "a", "-r", "-ep1", "-ibck", "-y" ]
                cmd.extend(params_list)
                # Add WinRAR exclusions
                for pattern in exclusion_patterns:
                    exclusion_args.append(f"-x{pattern}")
                # Exclude the temp folder itself if archiving from within (shouldn't be needed for '.')
                # exclusion_args.append(f"-x*{temp_folder_basename}{os.sep}") 
                cmd.extend(exclusion_args)
                # WinRAR needs archive path relative to CWD
                relative_archive_path = os.path.relpath(archive_file_path, start=temp_folder)
                cmd.append(relative_archive_path)
                cmd.append(content_to_archive)
            elif tool_family == "7zip":
                subprocess_cwd = temp_folder # Run from inside temp
                content_to_archive = "*" # Archive everything in current dir
                cmd = [ archiver_executable, "a", "-y", "-r" ]
                cmd.extend(params_list)
                # 7zip can use absolute path for archive
                cmd.append(archive_file_path)
                # Add 7zip exclusions
                for pattern in exclusion_patterns:
                    exclusion_args.append(f"-x!{pattern}")
                cmd.extend(exclusion_args)
                cmd.append(content_to_archive)
            elif tool_family == "zpaq":
                subprocess_cwd = base_dir # Run from the directory containing temp folder
                content_to_archive = temp_folder_basename # Archive the temp folder itself
                cmd = [ archiver_executable, "a", archive_file_path, content_to_archive]
                cmd.extend(params_list)
                # Add ZPAQ exclusions
                for pattern in exclusion_patterns:
                    exclusion_args.extend(["-not", pattern])
                cmd.extend(exclusion_args)
                cmd.append("-quiet")
            else:
                _log_func(f"{Fore.RED}Internal Error: Invalid tool_family '{tool_family}' in profile '{profile_name}'.{Style.RESET_ALL}")
                raise ValueError(f"Invalid tool family: {tool_family}")

            # --- Execute Archiving Command ---
            if cmd:
                # _log_func(f"  {Fore.WHITE}DEBUG: Executing Archiver Command:{Style.RESET_ALL}") # Removed DEBUG log
                # _log_func(f"  {Fore.WHITE}DEBUG: CWD: {subprocess_cwd}{Style.RESET_ALL}") # Removed DEBUG log
                # Safely join command parts for logging, handling potential non-string elements
                cmd_str = ' '.join(map(str, cmd))
                # _log_func(f"  {Fore.WHITE}DEBUG: CMD: {cmd_str}{Style.RESET_ALL}") # Removed DEBUG log
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, encoding='cp866', errors='ignore',
                                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), cwd=subprocess_cwd, check=False)
                    if result.returncode == 0:
                        archive_creation_successful = True
                    else:
                        # Log stderr first if available, otherwise stdout
                        error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                        if not error_msg: error_msg = f"{tool_family} failed with code {result.returncode}"
                        _log_func(f"  {Fore.RED}{tool_family} Error/Warning (Code: {result.returncode}): {error_msg}{Style.RESET_ALL}")
                        archive_creation_successful = False # Treat warnings/errors as failure for loop control

                    if not archive_creation_successful or not os.path.exists(archive_file_path):
                        _log_func(f"  {Fore.RED}Error: Archive file {archive_file_name} creation failed or file missing.{Style.RESET_ALL}")
                        if temp_folder and os.path.exists(temp_folder):
                            # Use top-level shutil
                            shutil.rmtree(temp_folder, ignore_errors=True)
                        return -1, current_png_level, current_jpeg_quality # Error state
                except FileNotFoundError:
                    _log_func(f"{Fore.RED}Error: Archiver executable not found at '{archiver_executable}'. Check path.{Style.RESET_ALL}")
                    if temp_folder and os.path.exists(temp_folder):
                        # Use top-level shutil
                        shutil.rmtree(temp_folder, ignore_errors=True)
                    return -1, current_png_level, current_jpeg_quality
                except Exception as subproc_e:
                    _log_func(f"{Fore.RED}Error running archiver: {subproc_e}{Style.RESET_ALL}")
                    if temp_folder and os.path.exists(temp_folder):
                        # Use top-level shutil
                        shutil.rmtree(temp_folder, ignore_errors=True)
                    return -1, current_png_level, current_jpeg_quality

            # 4. Check Archive Size
            try:
                file_size = os.path.getsize(archive_file_path)
                file_size_kb = file_size / 1024.0
                _log_func(f"  {Fore.CYAN}Archive size: {file_size_kb:.2f} KB{Style.RESET_ALL}")
            except FileNotFoundError:
                _log_func(f"{Fore.RED}Error: Archive file {archive_file_name} not found after supposed creation.{Style.RESET_ALL}")
                if temp_folder and os.path.exists(temp_folder):
                    # Use top-level shutil
                    shutil.rmtree(temp_folder, ignore_errors=True)
                return -1, current_png_level, current_jpeg_quality # Error state

            # ====================================
            # == Quality Adjustment Logic Start ==
            # ====================================
            # _log_func(f"  {Fore.WHITE}DEBUG: Entering Quality Adjustment Logic. Size={file_size_kb:.2f} KB, Limit={max_size_kb} KB{Style.RESET_ALL}") # Removed DEBUG log
            if file_size_kb <= max_size_kb:
                _log_func(f"  {Fore.GREEN}Success: Size ({file_size_kb:.2f} KB) <= limit ({max_size_kb} KB).{Style.RESET_ALL}")
                # _log_func(f"  {Fore.WHITE}DEBUG: Checking find_optimal: {find_optimal}{Style.RESET_ALL}") # Removed DEBUG log
                if find_optimal:
                    # _log_func(f"  {Fore.WHITE}DEBUG: find_optimal=True. Storing best fit: Size={file_size_kb:.2f}, PNG={current_png_level}, JPEG={current_jpeg_quality}{Style.RESET_ALL}") # Removed DEBUG log
                    best_fit_size_kb = file_size_kb
                    best_fit_settings_tuple = (current_png_level, current_jpeg_quality)

                    prev_png_level, prev_jpeg = current_png_level, current_jpeg_quality
                    quality_increased = False
                    # Try increasing JPEG first, then PNG
                    if current_jpeg_quality < initial_jpeg_quality:
                        current_jpeg_quality = min(initial_jpeg_quality, current_jpeg_quality + jpeg_quality_step)
                        if current_jpeg_quality > prev_jpeg: quality_increased = True
                    elif current_png_level < initial_png_level:
                        current_png_level += 1
                        quality_increased = True

                    if quality_increased:
                        attempt += 1
                        last_archive_size_kb = file_size_kb # Store the successful size
                        last_settings_tuple = (prev_png_level, prev_jpeg)
                        if temp_folder:
                            # Use top-level shutil
                            shutil.rmtree(temp_folder, ignore_errors=True)
                            temp_folder = None
                        _log_func("-" * 20) # Separator before next quality increase attempt
                        continue # Try again with higher quality
                    else: # Reached initial quality or couldn't increase further
                        _log_func(f"  {Fore.GREEN}Optimal search: Reached initial/max quality. Best fit (PNG={best_fit_settings_tuple[0]}, JPEG={best_fit_settings_tuple[1]}).{Style.RESET_ALL}")
                        if temp_folder:
                            # Use top-level shutil
                            shutil.rmtree(temp_folder, ignore_errors=True)
                        # Return the best fit found
                        # _log_func(f"  {Fore.WHITE}DEBUG: Returning best fit (initial/max quality reached).{Style.RESET_ALL}") # Removed DEBUG log
                        return best_fit_size_kb, best_fit_settings_tuple[0], best_fit_settings_tuple[1]
                else: # find_optimal == False
                    # _log_func(f"  {Fore.WHITE}DEBUG: find_optimal=False. Returning first success.{Style.RESET_ALL}") # Removed DEBUG log
                    if temp_folder:
                        # Use top-level shutil
                        shutil.rmtree(temp_folder, ignore_errors=True)
                    return file_size_kb, current_png_level, current_jpeg_quality # Return first success

            else: # file_size_kb > max_size_kb
                _log_func(f"  {Fore.YELLOW}Warning: Size ({file_size_kb:.2f} KB) > limit ({max_size_kb} KB).{Style.RESET_ALL}")

                # Debug log to see what's happening
                # _log_func(f"  {Fore.YELLOW}DEBUG: Archive size {file_size_kb:.2f} KB > limit {max_size_kb} KB. Will try to reduce quality.{Style.RESET_ALL}") # Removed DEBUG log

                # If we were searching for optimal and overshot, revert to the last good one
                # _log_func(f"  {Fore.WHITE}DEBUG: Checking if reverting to best fit (find_optimal={find_optimal}, best_fit_size_kb={best_fit_size_kb}).{Style.RESET_ALL}") # Removed DEBUG log
                if find_optimal and best_fit_size_kb != -1:
                    _log_func(f"  {Fore.GREEN}Optimal search: Exceeded limit. Reverting to best fit (Size: {best_fit_size_kb:.2f} KB, PNG={int(best_fit_settings_tuple[0])}, JPEG={int(best_fit_settings_tuple[1])}).{Style.RESET_ALL}")
                    if temp_folder:
                        # Use top-level shutil
                        shutil.rmtree(temp_folder, ignore_errors=True)
                    # _log_func(f"  {Fore.WHITE}DEBUG: Returning reverted best fit.{Style.RESET_ALL}") # Removed DEBUG log
                    return best_fit_size_kb, best_fit_settings_tuple[0], best_fit_settings_tuple[1]

                # --- Check if size reduction stopped working ---
                # If size increased or stayed same after reducing quality
                if attempt > 1 and last_archive_size_kb != -1 and file_size_kb >= last_archive_size_kb:
                    _log_func(f"  {Fore.YELLOW}STOP: Size ({file_size_kb:.2f} KB) did not decrease from previous ({last_archive_size_kb:.2f} KB) after quality reduction.{Style.RESET_ALL}")
                    _log_func(f"  {Fore.YELLOW}Using result from Attempt {attempt - 1} (Size: {last_archive_size_kb:.2f} KB, PNG={int(last_settings_tuple[0])}, JPEG={int(last_settings_tuple[1])}).{Style.RESET_ALL}")
                    if temp_folder and os.path.exists(temp_folder):
                        # Use top-level shutil
                        shutil.rmtree(temp_folder, ignore_errors=True)
                    # Return the size and settings from the PREVIOUS attempt.
                    # _log_func(f"  {Fore.WHITE}DEBUG: Returning previous attempt's result (size didn't decrease).{Style.RESET_ALL}") # Removed DEBUG log
                    return last_archive_size_kb, last_settings_tuple[0], last_settings_tuple[1]

                # --- Check if minimum quality reached ---
                # _log_func(f"  {Fore.WHITE}DEBUG: Checking min quality (Current PNG={current_png_level}, Min PNG={min_png_level}; Current JPEG={current_jpeg_quality}, Min JPEG={min_jpeg_quality}).{Style.RESET_ALL}") # Removed DEBUG log
                if current_png_level <= min_png_level and current_jpeg_quality <= min_jpeg_quality:
                    _log_func(f"  {Fore.RED}Failed: Min quality reached (PNG={min_png_level}, JPEG={min_jpeg_quality}), size ({file_size_kb:.2f} KB) still > limit.{Style.RESET_ALL}")
                    if temp_folder:
                        shutil.rmtree(temp_folder, ignore_errors=True)
                    # Return the current (oversized) state as the best possible failure
                    # _log_func(f"  {Fore.WHITE}DEBUG: Returning current oversized state (min quality reached).{Style.RESET_ALL}") # Removed DEBUG log
                    return file_size_kb, min_png_level, min_jpeg_quality

                # --- Reduce quality for the next attempt ---
                # _log_func(f"  {Fore.WHITE}DEBUG: Reducing quality... Current PNG={current_png_level}, JPEG={current_jpeg_quality}{Style.RESET_ALL}") # Removed DEBUG log
                next_png_level, next_jpeg_quality = current_png_level, current_jpeg_quality
                reduction_made = False

                # Prioritize reducing JPEG quality first
                if current_jpeg_quality > min_jpeg_quality:
                    # _log_func(f"  {Fore.WHITE}DEBUG: Attempting JPEG reduction (Current={current_jpeg_quality}, Min={min_jpeg_quality}){Style.RESET_ALL}") # Removed DEBUG log
                    # Estimate reduction needed (more aggressive if far over)
                    overshoot_kb = file_size_kb - max_size_kb
                    factor = 1.5 if overshoot_kb > max_size_kb * 0.2 else 1.0 # Be more aggressive if > 20% over
                    reduction_estimate = 0
                    if file_size_kb > 0:
                        # Estimate quality points needed based on overshoot percentage relative to quality range
                        reduction_estimate = (overshoot_kb / file_size_kb) * (initial_jpeg_quality - min_jpeg_quality) * factor
                        # _log_func(f"  {Fore.WHITE}DEBUG: Overshoot={overshoot_kb:.2f} KB, Factor={factor}, Reduction Estimate={reduction_estimate:.1f} points{Style.RESET_ALL}") # Removed DEBUG log

                    # Calculate the actual quality step, ensuring it's at least the base step
                    quality_reduction_step = max(jpeg_quality_step, math.ceil(reduction_estimate / jpeg_quality_step) * jpeg_quality_step if jpeg_quality_step > 0 else jpeg_quality_step)
                    # _log_func(f"  {Fore.WHITE}DEBUG: Calculated JPEG reduction step: {quality_reduction_step}{Style.RESET_ALL}") # Removed DEBUG log
                    proposed_jpeg_quality = max(min_jpeg_quality, current_jpeg_quality - quality_reduction_step)
                    # _log_func(f"  {Fore.WHITE}DEBUG: Proposed JPEG quality: {proposed_jpeg_quality}{Style.RESET_ALL}") # Removed DEBUG log

                    if proposed_jpeg_quality < current_jpeg_quality:
                        next_jpeg_quality = proposed_jpeg_quality
                        reduction_made = True
                        # _log_func(f"  {Fore.WHITE}DEBUG: JPEG quality reduced to {next_jpeg_quality}{Style.RESET_ALL}") # Removed DEBUG log
                    # Fallback if estimation somehow failed but quality > min
                    elif current_jpeg_quality > min_jpeg_quality:
                         alt_jpeg_quality = max(min_jpeg_quality, current_jpeg_quality - jpeg_quality_step)
                         if alt_jpeg_quality < current_jpeg_quality:
                             next_jpeg_quality = alt_jpeg_quality
                             reduction_made = True
                             # _log_func(f"  {Fore.WHITE}DEBUG: JPEG quality reduced (fallback) to {next_jpeg_quality}{Style.RESET_ALL}") # Removed DEBUG log
                         else:
                             pass # _log_func(f"  {Fore.WHITE}DEBUG: JPEG fallback reduction failed (already at min or step=0?){Style.RESET_ALL}") # Removed DEBUG log
                    else:
                         pass # _log_func(f"  {Fore.WHITE}DEBUG: JPEG reduction skipped (already at min?){Style.RESET_ALL}") # Removed DEBUG log

                # If JPEG is already at min, or no JPEG reduction happened, reduce PNG level
                if not reduction_made and current_png_level > min_png_level:
                    # _log_func(f"  {Fore.WHITE}DEBUG: Attempting PNG reduction (Current={current_png_level}, Min={min_png_level}){Style.RESET_ALL}") # Removed DEBUG log
                    next_png_level = current_png_level - 1
                    reduction_made = True
                    # _log_func(f"  {Fore.WHITE}DEBUG: PNG level reduced to {next_png_level}{Style.RESET_ALL}") # Removed DEBUG log
                elif not reduction_made:
                     pass # _log_func(f"  {Fore.WHITE}DEBUG: PNG reduction skipped (already at min or JPEG reduced){Style.RESET_ALL}") # Removed DEBUG log


                # If no reduction could be made (should only happen if already at min)
                if not reduction_made:
                    _log_func(f"  {Fore.RED}Failed: Cannot reduce quality further (Internal check: PNG={current_png_level}, JPEG={current_jpeg_quality}).{Style.RESET_ALL}")
                    if temp_folder:
                        # Use top-level shutil
                        shutil.rmtree(temp_folder, ignore_errors=True)
                    # Return current oversized state
                    # _log_func(f"  {Fore.WHITE}DEBUG: Returning current oversized state (no reduction made).{Style.RESET_ALL}") # Removed DEBUG log
                    return file_size_kb, current_png_level, current_jpeg_quality

                # --- Prepare for the next iteration ---
                last_archive_size_kb = file_size_kb # Store current size for next check
                last_settings_tuple = (current_png_level, current_jpeg_quality)
                current_png_level, current_jpeg_quality = next_png_level, next_jpeg_quality
                # _log_func(f"  {Fore.WHITE}DEBUG: Preparing for Attempt {attempt + 1} with PNG={current_png_level}, JPEG={current_jpeg_quality}{Style.RESET_ALL}") # Removed DEBUG log

                attempt += 1
                if temp_folder and os.path.exists(temp_folder):
                    # Use top-level shutil
                    shutil.rmtree(temp_folder, ignore_errors=True)
                    temp_folder = None
                _log_func("-" * 20)
                # _log_func(f"  {Fore.WHITE}DEBUG: Continuing loop for next attempt.{Style.RESET_ALL}") # Removed DEBUG log
                continue # Go to the next attempt with reduced quality

            # ==================================
            # == Quality Adjustment Logic End ==
            # _log_func(f"  {Fore.WHITE}DEBUG: Reached end of Quality Adjustment Logic block for attempt {attempt}.{Style.RESET_ALL}") # Removed DEBUG log
            # ==================================


        except Exception as e:
            _log_func(f"{Fore.RED}Critical error during folder {os.path.basename(folder_path)} attempt {attempt}: {type(e).__name__} - {str(e)}{Style.RESET_ALL}")
            import traceback
            # Capture traceback to string buffer to log it via _log_func
            exc_buffer = io.StringIO()
            traceback.print_exc(file=exc_buffer)
            _log_func(exc_buffer.getvalue())
            exc_buffer.close()
            if temp_folder and os.path.exists(temp_folder):
                # Use top-level shutil
                _log_func(f"  {Fore.WHITE}Cleaning up temp folder after exception: {temp_folder}{Style.RESET_ALL}")
                shutil.rmtree(temp_folder, ignore_errors=True)
            return -1, current_png_level, current_jpeg_quality # Return error state
        finally:
            # Ensure temp folder is cleaned up if loop breaks unexpectedly
             if temp_folder and os.path.exists(temp_folder):
                 # Use top-level shutil ONLY
                 # _log_func(f"  {Fore.WHITE}DEBUG: Cleaning up temp folder in finally block: {temp_folder}{Style.RESET_ALL}") # Removed DEBUG log
                 shutil.rmtree(temp_folder, ignore_errors=True)
