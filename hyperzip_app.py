import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import threading
import queue
import json
import io
import re # Import regex module
import time
from datetime import datetime
from colorama import Fore, Style  # Import for colored terminal output

# Import from our modular structure
from hyperzip_core import DEFAULT_SETTINGS
from hyperzip_main import run_packing

# --- Constants ---
APP_NAME = "HyperZip GUI"
CONFIG_FILE = "hyperzip_config.json"
ARCHIVE_PROFILES = [
    "winrar_zip", "winrar_rar", "7zip_7z", "7zip_zip", "zpaq_zpaq"
]

# --- File Processing Results Frame ---
class FileProcessingResultsFrame(ctk.CTkFrame):
    def __init__(self, parent, results_data, close_callback=None):
        super().__init__(parent)
        self.close_callback = close_callback
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Make the file list scrollable
        
        # Dark overlay background
        self.configure(fg_color=("#1A1A1A", "#0A0A0A"))
        
        # Header with icon
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Icon placeholder
        icon_label = ctk.CTkLabel(header_frame, text="📊", font=("Arial", 24))
        icon_label.grid(row=0, column=0, padx=10, pady=10)
        
        title_label = ctk.CTkLabel(header_frame, text="File Processing Results:", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Before/After section (summary)
        summary_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        summary_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(1, weight=0)
        summary_frame.grid_columnconfigure(2, weight=1)
        
        # Before
        before_label = ctk.CTkLabel(summary_frame, text="Before", font=("Arial", 16), text_color="#ff6b6b")
        before_label.grid(row=0, column=0, padx=20, pady=5)
        
        self.before_size = ctk.CTkLabel(summary_frame, text=f"{results_data['before_size']} MB", 
                                  font=("Arial", 28, "bold"), text_color="#ff6b6b")
        self.before_size.grid(row=1, column=0, padx=20, pady=5)
        
        before_files = ctk.CTkLabel(summary_frame, text=f"{results_data['file_count']} files", 
                                   font=("Arial", 14), text_color="#aaaaaa")
        before_files.grid(row=2, column=0, padx=20, pady=5)
        
        # Arrow
        arrow_label = ctk.CTkLabel(summary_frame, text="→", font=("Arial", 24))
        arrow_label.grid(row=1, column=1, padx=10)
        
        # After
        after_label = ctk.CTkLabel(summary_frame, text="After", font=("Arial", 16), text_color="#4ecca3")
        after_label.grid(row=0, column=2, padx=20, pady=5)
        
        self.after_size = ctk.CTkLabel(summary_frame, text=f"{results_data['after_size']} MB", 
                                 font=("Arial", 28, "bold"), text_color="#4ecca3")
        self.after_size.grid(row=1, column=2, padx=20, pady=5)
        
        after_files = ctk.CTkLabel(summary_frame, text=f"{results_data['file_count']} files", 
                                  font=("Arial", 14), text_color="#aaaaaa")
        after_files.grid(row=2, column=2, padx=20, pady=5)
        
        # File type breakdown section
        file_type_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        file_type_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        file_type_frame.grid_columnconfigure(0, weight=1)
        
        # Header for file type breakdown
        type_header = ctk.CTkLabel(file_type_frame, text="Compression by File Type:", font=("Arial", 16, "bold"))
        type_header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Create a grid for file type breakdown
        type_grid = ctk.CTkFrame(file_type_frame, fg_color="transparent")
        type_grid.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Configure columns for the type grid
        for i, width in enumerate([2, 1, 1, 1]):
            type_grid.grid_columnconfigure(i, weight=width)
        
        # Add headers for the type breakdown
        type_header_font = ("Arial", 14)
        ctk.CTkLabel(type_grid, text="File Type", font=type_header_font).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(type_grid, text="Original", font=type_header_font, text_color="#ff6b6b").grid(row=0, column=1, padx=10, pady=5, sticky="e")
        ctk.CTkLabel(type_grid, text="Optimized", font=type_header_font, text_color="#4ecca3").grid(row=0, column=2, padx=10, pady=5, sticky="e")
        ctk.CTkLabel(type_grid, text="Savings", font=type_header_font, text_color="#f4d03f").grid(row=0, column=3, padx=10, pady=5, sticky="e")
        
        # Create file type breakdown data from results if available
        self.file_type_breakdown = []
        
        # If we have actual data, we could populate this from results_data
        # For now, we'll just show a message if no data is available
        if not self.file_type_breakdown:
            no_data_label = ctk.CTkLabel(
                type_grid, 
                text="No file type breakdown available", 
                font=("Arial", 14, "italic"),
                text_color="#aaaaaa"
            )
            no_data_label.grid(row=1, column=0, columnspan=4, padx=10, pady=20, sticky="ew")
        
        # Add the file type breakdown data if available
        for i, (file_type, original, optimized, savings) in enumerate(self.file_type_breakdown):
            row_bg = "#333333" if i % 2 == 0 else "#3a3a3a"
            
            # File type
            ctk.CTkLabel(type_grid, text=file_type, fg_color=row_bg).grid(
                row=i+1, column=0, padx=10, pady=5, sticky="ew")
            
            # Original size
            ctk.CTkLabel(type_grid, text=original, fg_color=row_bg, text_color="#ff6b6b").grid(
                row=i+1, column=1, padx=10, pady=5, sticky="e")
            
            # Optimized size
            ctk.CTkLabel(type_grid, text=optimized, fg_color=row_bg, text_color="#4ecca3").grid(
                row=i+1, column=2, padx=10, pady=5, sticky="e")
            
            # Savings percentage
            ctk.CTkLabel(type_grid, text=savings, fg_color=row_bg, text_color="#f4d03f").grid(
                row=i+1, column=3, padx=10, pady=5, sticky="e")
        
        # File list table
        file_list_frame = ctk.CTkFrame(self, fg_color="#222222")
        file_list_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        file_list_frame.grid_columnconfigure(0, weight=1)
        file_list_frame.grid_rowconfigure(1, weight=1)
        
        # Table header
        table_header = ctk.CTkFrame(file_list_frame, fg_color="#333333")
        table_header.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
        
        # Configure columns for the header
        for i, width in enumerate([3, 1, 1, 1]):
            table_header.grid_columnconfigure(i, weight=width)
        
        # Header labels
        header_font = ("Arial", 14, "bold")
        ctk.CTkLabel(table_header, text="File", font=header_font).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        ctk.CTkLabel(table_header, text="Original", font=header_font, text_color="#ff6b6b").grid(row=0, column=1, padx=10, pady=8, sticky="e")
        ctk.CTkLabel(table_header, text="In Archive", font=header_font, text_color="#f4d03f").grid(row=0, column=2, padx=10, pady=8, sticky="e")
        ctk.CTkLabel(table_header, text="Savings", font=header_font, text_color="#4ecca3").grid(row=0, column=3, padx=10, pady=8, sticky="e")
        
        # Create a scrollable frame for the file list
        self.scrollable_frame = ctk.CTkScrollableFrame(file_list_frame, fg_color="transparent")
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew")
        
        # Configure columns for the scrollable frame
        for i, width in enumerate([3, 1, 1, 1]):
            self.scrollable_frame.grid_columnconfigure(i, weight=width)
        
        # Only use actual file data from results_data
        files_to_display = results_data.get("files", [])
        
        for i, (filename, original, in_archive, optimized) in enumerate(files_to_display):
            row_bg = "#2b2b2b" if i % 2 == 0 else "#333333"
            
            # File name
            ctk.CTkLabel(self.scrollable_frame, text=filename, fg_color=row_bg).grid(
                row=i, column=0, padx=10, pady=5, sticky="ew")
            
            # Original size
            ctk.CTkLabel(self.scrollable_frame, text=original, fg_color=row_bg, text_color="#ff6b6b").grid(
                row=i, column=1, padx=10, pady=5, sticky="e")
            
            # In Archive size
            ctk.CTkLabel(self.scrollable_frame, text=in_archive, fg_color=row_bg, text_color="#f4d03f").grid(
                row=i, column=2, padx=10, pady=5, sticky="e")
            
            # Savings (calculate from original and in_archive)
            try:
                # Parse sizes to calculate savings
                original_size = self.parse_size_to_bytes(original)
                archive_size = self.parse_size_to_bytes(in_archive)
                
                if original_size > 0:
                    savings_percent = (1 - archive_size / original_size) * 100
                    savings_text = f"-{savings_percent:.1f}%"
                else:
                    savings_text = "0%"
            except:
                savings_text = "N/A"
                
            ctk.CTkLabel(self.scrollable_frame, text=savings_text, fg_color=row_bg, text_color="#4ecca3").grid(
                row=i, column=3, padx=10, pady=5, sticky="e")
        
        # Add a blue scrollbar indicator on the right
        scrollbar_indicator = ctk.CTkFrame(file_list_frame, width=5, fg_color="#3498db")
        scrollbar_indicator.grid(row=0, column=1, rowspan=2, sticky="ns")
        
        # OK button to close the results view
        ok_button = ctk.CTkButton(self, text="OK", width=100, command=self.close)
        ok_button.grid(row=4, column=0, padx=10, pady=20)
    
    def close(self):
        """Close the results view."""
        if self.close_callback:
            self.close_callback()
        
    def parse_size_to_bytes(self, size_str):
        """Parse a size string like '3.2 MB' or '698 KB' to bytes."""
        try:
            # Extract the numeric part and unit
            parts = size_str.split()
            if len(parts) != 2:
                return 0
                
            value = float(parts[0])
            unit = parts[1].upper()
            
            # Convert to bytes based on unit
            if unit == 'B':
                return value
            elif unit == 'KB':
                return value * 1024
            elif unit == 'MB':
                return value * 1024 * 1024
            elif unit == 'GB':
                return value * 1024 * 1024 * 1024
            else:
                return 0
        except:
            return 0
    
    def animate_results(self, duration=1.0):
        """Animate the results with counting effect."""
        try:
            # Get the target values
            before_text = self.before_size.cget("text")
            after_text = self.after_size.cget("text")
            
            # Extract numeric values
            before_mb = float(before_text.split()[0])
            after_mb = float(after_text.split()[0])
            
            # Calculate steps for animation (20 frames)
            steps = 20
            step_time = duration / steps
            
            # Start with zero values
            self.before_size.configure(text="0.0 MB")
            self.after_size.configure(text="0.0 MB")
            
            # Animation function
            def animate_step(current_step):
                if current_step <= steps:
                    # Calculate current values based on progress
                    progress = current_step / steps
                    current_before = before_mb * progress
                    current_after = after_mb * progress
                    
                    # Update labels
                    self.before_size.configure(text=f"{current_before:.1f} MB")
                    self.after_size.configure(text=f"{current_after:.1f} MB")
                    
                    # Schedule next step
                    self.after(int(step_time * 1000), lambda: animate_step(current_step + 1))
                else:
                    # Restore final values
                    self.before_size.configure(text=before_text)
                    self.after_size.configure(text=after_text)
            
            # Start animation
            animate_step(1)
            
        except Exception as e:
            print(f"Animation error: {e}")
            # In case of error, just show the final values
            pass

# --- Main Application Class ---
class HyperZipApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("800x700") # Reduced height for better fit on smaller screens
        ctk.set_appearance_mode("System") # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue") # Themes: "blue" (default), "green", "dark-blue"

        # Create a scrollable frame for the entire content
        self.main_scrollable_frame = ctk.CTkScrollableFrame(self)
        self.main_scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure the scrollable frame
        self.main_scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Add event binding for window resize to handle UI scaling
        self.bind("<Configure>", self.on_window_resize)

        # --- Variables ---
        self.project_folder_var = tk.StringVar()
        self.archive_profile_var = tk.StringVar(value=DEFAULT_SETTINGS["ARCHIVE_PROFILE"])
        self.winrar_path_var = tk.StringVar(value=DEFAULT_SETTINGS["winrar_path"])
        self.sevenzip_path_var = tk.StringVar(value=DEFAULT_SETTINGS["sevenzip_path"])
        self.zpaq_path_var = tk.StringVar(value=DEFAULT_SETTINGS["zpaq_path"])
        self.exclusions_var = tk.StringVar(value=DEFAULT_SETTINGS["ARCHIVE_EXCLUSIONS"]) # New variable
        
        # Split minification into HTML, CSS, and JS
        self.minify_html_var = tk.BooleanVar(value=DEFAULT_SETTINGS["ENABLE_MINIFICATION"])
        self.minify_css_var = tk.BooleanVar(value=DEFAULT_SETTINGS["ENABLE_MINIFICATION"])
        self.minify_js_var = tk.BooleanVar(value=DEFAULT_SETTINGS["ENABLE_MINIFICATION"])
        
        # Split image compression into PNG and JPEG
        self.compress_png_var = tk.BooleanVar(value=DEFAULT_SETTINGS["ENABLE_IMAGE_COMPRESSION"])
        self.compress_jpeg_var = tk.BooleanVar(value=DEFAULT_SETTINGS["ENABLE_IMAGE_COMPRESSION"])
        self.tinypng_api_key_var = tk.StringVar(value=DEFAULT_SETTINGS["TINIFY_API_KEY"])
        self.png_compressor_var = tk.StringVar(value="tinypng") # Default to tinypng
        self.png_level_start_var = tk.IntVar(value=DEFAULT_SETTINGS["INITIAL_PNG_OPTIMIZATION_LEVEL"])
        self.jpeg_quality_start_var = tk.IntVar(value=DEFAULT_SETTINGS["INITIAL_JPEG_QUALITY"])
        self.png_level_min_var = tk.IntVar(value=DEFAULT_SETTINGS["MIN_PNG_OPTIMIZATION_LEVEL"])
        self.jpeg_quality_min_var = tk.IntVar(value=DEFAULT_SETTINGS["MIN_JPEG_QUALITY"])
        self.jpeg_step_var = tk.IntVar(value=DEFAULT_SETTINGS["JPEG_QUALITY_STEP"])
        self.find_optimal_var = tk.BooleanVar(value=DEFAULT_SETTINGS["FIND_OPTIMAL_QUALITY"])
        self.max_size_kb_var = tk.DoubleVar(value=DEFAULT_SETTINGS["max_size_kb"])
        
        # --- Processing state variables ---
        self.processing_start_time = None
        self.current_file = ""
        self.files_processed = 0
        self.total_files = 0
        self.processing_speed = 0  # KB/s
        
        # --- Results data for comparison ---
        self.results_data = {
            "before_size": "0.0",
            "after_size": "0.0",
            "file_count": "0",
            "saved_mb": "0.0",
            "saved_percent": "0.0",
            "images_mb": "0.0",
            "code_mb": "0.0",
            "other_mb": "0.0",
            "files": []  # List of files with their sizes
        }
        
        # --- Processing state ---
        self.is_processing = False
        self.log_queue = queue.Queue()

        # --- UI Creation ---
        self.create_widgets()
        self.update_image_compression_state() # Initial state update

        # --- Load Config ---
        self.load_config() # Load saved config if available

    def create_widgets(self):
        # --- 1. Project Folder and TinyPNG API Key ---
        project_frame = ctk.CTkFrame(self.main_scrollable_frame)
        project_frame.grid(row=0, column=0, padx=10, pady=(10, 3), sticky="ew")
        project_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(project_frame, text="Project Folder:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.project_folder_entry = ctk.CTkEntry(project_frame, textvariable=self.project_folder_var)
        self.project_folder_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        self.browse_project_button = ctk.CTkButton(project_frame, text="Browse...", width=100, command=self.browse_project_folder)
        self.browse_project_button.grid(row=0, column=2, padx=5, pady=3)
        
        # Setup drag and drop for project folder entry
        self.setup_drag_and_drop(self.project_folder_entry)
        
        # TinyPNG API Key (moved from image details section)
        ctk.CTkLabel(project_frame, text="TinyPNG API Key:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.tinypng_entry = ctk.CTkEntry(project_frame, textvariable=self.tinypng_api_key_var, show="*")
        self.tinypng_entry.grid(row=1, column=1, padx=5, pady=3, sticky="ew")
        self.save_key_button = ctk.CTkButton(project_frame, text="Save", width=100, command=self.save_config)
        self.save_key_button.grid(row=1, column=2, padx=5, pady=3)

        # --- 2. Archive Settings ---
        self.archive_frame = ctk.CTkFrame(self.main_scrollable_frame)
        self.archive_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.archive_frame.grid_columnconfigure(1, weight=1)
        self.archive_frame.grid_columnconfigure(3, weight=1)

        # Archive Profile and Max Size in the same row
        profile_size_frame = ctk.CTkFrame(self.archive_frame, fg_color="transparent")
        profile_size_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        profile_size_frame.grid_columnconfigure(1, weight=1)
        profile_size_frame.grid_columnconfigure(3, weight=1)
        
        # First row: Archive Profile and Max Size
        ctk.CTkLabel(profile_size_frame, text="Archive Profile:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.profile_combobox = ctk.CTkComboBox(profile_size_frame, variable=self.archive_profile_var, values=ARCHIVE_PROFILES, command=self.update_archiver_path_state)
        self.profile_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(profile_size_frame, text="Max Archive Size (KB):").grid(row=0, column=2, padx=(20, 5), pady=5, sticky="w")
        self.max_size_entry = ctk.CTkEntry(profile_size_frame, textvariable=self.max_size_kb_var, width=100)
        self.max_size_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # WinRAR Path
        ctk.CTkLabel(self.archive_frame, text="WinRAR Path:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.winrar_entry = ctk.CTkEntry(self.archive_frame, textvariable=self.winrar_path_var)
        self.winrar_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.browse_winrar_button = ctk.CTkButton(self.archive_frame, text="Browse...", width=100, command=lambda: self.browse_executable("WinRAR", self.winrar_path_var))
        self.browse_winrar_button.grid(row=1, column=2, padx=5, pady=5)

        # 7-Zip Path
        ctk.CTkLabel(self.archive_frame, text="7-Zip Path:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.sevenzip_entry = ctk.CTkEntry(self.archive_frame, textvariable=self.sevenzip_path_var)
        self.sevenzip_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.browse_sevenzip_button = ctk.CTkButton(self.archive_frame, text="Browse...", width=100, command=lambda: self.browse_executable("7-Zip", self.sevenzip_path_var))
        self.browse_sevenzip_button.grid(row=2, column=2, padx=5, pady=5)

        # ZPAQ Path
        ctk.CTkLabel(self.archive_frame, text="ZPAQ Path:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.zpaq_entry = ctk.CTkEntry(self.archive_frame, textvariable=self.zpaq_path_var)
        self.zpaq_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.browse_zpaq_button = ctk.CTkButton(self.archive_frame, text="Browse...", width=100, command=lambda: self.browse_executable("ZPAQ", self.zpaq_path_var))
        self.browse_zpaq_button.grid(row=3, column=2, padx=5, pady=5)
        
        # Exclusions Entry
        ctk.CTkLabel(self.archive_frame, text="Exclusions (space-separated):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.exclusions_entry = ctk.CTkEntry(self.archive_frame, textvariable=self.exclusions_var)
        self.exclusions_entry.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky="ew")


        self.update_archiver_path_state() # Initial state update

        # --- 3. Optimization Settings ---
        optim_frame = ctk.CTkFrame(self.main_scrollable_frame)
        optim_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        optim_frame.grid_columnconfigure(0, weight=1)

        # General Optimization section
        general_optim_frame = ctk.CTkFrame(optim_frame)
        general_optim_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        general_optim_frame.grid_columnconfigure(0, weight=1)
        
        # Add a header with icon
        general_header = ctk.CTkFrame(general_optim_frame)
        general_header.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        general_header.grid_columnconfigure(1, weight=1)
        
        # Icon placeholder
        general_icon = ctk.CTkLabel(general_header, text="⚡", font=("Arial", 16))
        general_icon.grid(row=0, column=0, padx=5, pady=5)
        
        general_title = ctk.CTkLabel(general_header, text="General Optimization", font=("Arial", 14, "bold"))
        general_title.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Create a frame for minification checkboxes
        minify_frame = ctk.CTkFrame(general_optim_frame, fg_color="transparent")
        minify_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        minify_frame.grid_columnconfigure(0, weight=1)
        minify_frame.grid_columnconfigure(1, weight=1)
        minify_frame.grid_columnconfigure(2, weight=1)
        
        # Add separate checkboxes for HTML, CSS, and JS minification
        self.minify_html_checkbox = ctk.CTkCheckBox(minify_frame, text="Minify HTML", 
                                                   variable=self.minify_html_var)
        self.minify_html_checkbox.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.minify_css_checkbox = ctk.CTkCheckBox(minify_frame, text="Minify CSS", 
                                                  variable=self.minify_css_var)
        self.minify_css_checkbox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        self.minify_js_checkbox = ctk.CTkCheckBox(minify_frame, text="Minify JS", 
                                                 variable=self.minify_js_var)
        self.minify_js_checkbox.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Image Optimization section
        img_optim_frame = ctk.CTkFrame(optim_frame)
        img_optim_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        img_optim_frame.grid_columnconfigure(0, weight=1)
        
        # Add a header with icon
        img_header = ctk.CTkFrame(img_optim_frame)
        img_header.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        img_header.grid_columnconfigure(1, weight=1)
        
        # Icon placeholder
        img_icon = ctk.CTkLabel(img_header, text="🖼️", font=("Arial", 16))
        img_icon.grid(row=0, column=0, padx=5, pady=5)
        
        img_title = ctk.CTkLabel(img_header, text="Image Optimization", font=("Arial", 14, "bold"))
        img_title.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Separate checkboxes for PNG and JPEG
        checkbox_frame = ctk.CTkFrame(img_optim_frame, fg_color="transparent")
        checkbox_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        checkbox_frame.grid_columnconfigure(0, weight=1)
        checkbox_frame.grid_columnconfigure(1, weight=1)
        
        self.compress_png_checkbox = ctk.CTkCheckBox(checkbox_frame, text="Optimize PNG", 
                                                    variable=self.compress_png_var, 
                                                    command=self.update_image_compression_state)
        self.compress_png_checkbox.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.compress_jpeg_checkbox = ctk.CTkCheckBox(checkbox_frame, text="Optimize JPEG", 
                                                     variable=self.compress_jpeg_var, 
                                                     command=self.update_image_compression_state)
        self.compress_jpeg_checkbox.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # --- 4. Image Compression Details ---
        self.img_details_frame = ctk.CTkFrame(self.main_scrollable_frame, fg_color="transparent") # Use transparent bg or a specific color
        self.img_details_frame.grid(row=3, column=0, padx=10, pady=0, sticky="ew")
        
        # Improve grid layout for better scaling
        for i in range(6):
            self.img_details_frame.grid_columnconfigure(i, weight=0)  # First reset all weights
        
        # Set equal weights for slider columns
        self.img_details_frame.grid_columnconfigure(1, weight=1)  # Left slider column
        self.img_details_frame.grid_columnconfigure(4, weight=1)  # Right slider column
        
        # PNG Compressor Selection
        ctk.CTkLabel(self.img_details_frame, text="PNG Compressor:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.png_compressor_combobox = ctk.CTkComboBox(self.img_details_frame, variable=self.png_compressor_var, 
                                                      values=["tinypng", "oxipng"])
        self.png_compressor_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Sliders and Labels with improved layout
        # PNG Start Level
        png_start_label = ctk.CTkLabel(self.img_details_frame, text="PNG Start Level (1-8):", width=150)
        png_start_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.png_start_slider = ctk.CTkSlider(self.img_details_frame, from_=1, to=8, number_of_steps=7, variable=self.png_level_start_var)
        self.png_start_slider.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.png_start_label = ctk.CTkLabel(self.img_details_frame, textvariable=self.png_level_start_var, width=30)
        self.png_start_label.grid(row=2, column=2, padx=5, pady=5)

        # JPEG Start Quality
        jpeg_start_label = ctk.CTkLabel(self.img_details_frame, text="JPEG Start Quality:", width=150)
        jpeg_start_label.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.jpeg_start_slider = ctk.CTkSlider(self.img_details_frame, from_=10, to=95, number_of_steps=85, variable=self.jpeg_quality_start_var)
        self.jpeg_start_slider.grid(row=2, column=4, padx=5, pady=5, sticky="ew")
        self.jpeg_start_label = ctk.CTkLabel(self.img_details_frame, textvariable=self.jpeg_quality_start_var, width=30)
        self.jpeg_start_label.grid(row=2, column=5, padx=5, pady=5)

        # PNG Min Level
        png_min_label = ctk.CTkLabel(self.img_details_frame, text="PNG Min Level (1-8):", width=150)
        png_min_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.png_min_slider = ctk.CTkSlider(self.img_details_frame, from_=1, to=8, number_of_steps=7, variable=self.png_level_min_var)
        self.png_min_slider.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.png_min_label = ctk.CTkLabel(self.img_details_frame, textvariable=self.png_level_min_var, width=30)
        self.png_min_label.grid(row=3, column=2, padx=5, pady=5)

        # JPEG Min Quality
        jpeg_min_label = ctk.CTkLabel(self.img_details_frame, text="JPEG Min Quality:", width=150)
        jpeg_min_label.grid(row=3, column=3, padx=5, pady=5, sticky="w")
        self.jpeg_min_slider = ctk.CTkSlider(self.img_details_frame, from_=10, to=95, number_of_steps=85, variable=self.jpeg_quality_min_var)
        self.jpeg_min_slider.grid(row=3, column=4, padx=5, pady=5, sticky="ew")
        self.jpeg_min_label = ctk.CTkLabel(self.img_details_frame, textvariable=self.jpeg_quality_min_var, width=30)
        self.jpeg_min_label.grid(row=3, column=5, padx=5, pady=5)

        ctk.CTkLabel(self.img_details_frame, text="JPEG Quality Step:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.jpeg_step_entry = ctk.CTkEntry(self.img_details_frame, textvariable=self.jpeg_step_var, width=50)
        self.jpeg_step_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        self.find_optimal_checkbox = ctk.CTkCheckBox(self.img_details_frame, text="Find Optimal Quality", variable=self.find_optimal_var)
        self.find_optimal_checkbox.grid(row=4, column=3, columnspan=3, padx=5, pady=5, sticky="w")


        # --- 5. Progress Bar ---
        progress_frame = ctk.CTkFrame(self.main_scrollable_frame)
        progress_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=20)
        self.progress_bar.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.progress_bar.set(0)  # Initialize to 0
        
        # Progress details frame
        progress_details_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        progress_details_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        progress_details_frame.grid_columnconfigure(1, weight=1)
        progress_details_frame.grid_columnconfigure(3, weight=1)
        progress_details_frame.grid_columnconfigure(5, weight=1)
        
        # Current file
        ctk.CTkLabel(progress_details_frame, text="Current File:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.current_file_label = ctk.CTkLabel(progress_details_frame, text="", width=200)
        self.current_file_label.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Processing speed
        ctk.CTkLabel(progress_details_frame, text="Speed:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.speed_label = ctk.CTkLabel(progress_details_frame, text="0 KB/s")
        self.speed_label.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        
        # Remaining time
        ctk.CTkLabel(progress_details_frame, text="Remaining:").grid(row=0, column=4, padx=5, pady=2, sticky="w")
        self.time_label = ctk.CTkLabel(progress_details_frame, text="--:--")
        self.time_label.grid(row=0, column=5, padx=5, pady=2, sticky="w")

        # --- 6. Start Button ---
        # Create a frame at the bottom of the window that stays fixed
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        # Add the start button to this fixed frame
        self.start_button = ctk.CTkButton(self.bottom_frame, text="Start Processing", command=self.start_processing, 
                                         fg_color="#0078d7", hover_color="#005fa3", height=40)
        self.start_button.pack(fill="x")
        
        # --- 7. Copyright Information ---
        copyright_frame = ctk.CTkFrame(self.main_scrollable_frame)
        copyright_frame.grid(row=7, column=0, padx=10, pady=(5, 10), sticky="ew")
        copyright_frame.grid_columnconfigure(0, weight=1)  # Center the copyright text
        
        # Use a standard tkinter Text widget for selectable text
        self.copyright_text = tk.Text(
            copyright_frame, 
            height=1,  # Fixed height for single line
            width=40,
            wrap="none",
            bg=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1]),  # Match CTk background
            fg=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"][1]),  # Match CTk text color
            relief="flat",
            highlightthickness=0,
            padx=5,
            pady=5
        )
        self.copyright_text.grid(row=0, column=0, pady=5, padx=5, sticky="ew")
        
        # Insert the copyright text (plain text, no links)
        copyright_content = "© svrts 2025 • svartstudio.com • sergey@svartstudio.com"
        self.copyright_text.insert("1.0", copyright_content)
        self.copyright_text.configure(state="disabled")  # Make read-only but still selectable

        # --- 8. Log Area with Export Button ---
        log_frame = ctk.CTkFrame(self.main_scrollable_frame)
        log_frame.grid(row=5, column=0, padx=10, pady=(5, 10), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        
        # Log header with buttons
        log_header = ctk.CTkFrame(log_frame)
        log_header.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)
        
        # Log title
        log_title = ctk.CTkLabel(log_header, text="Operation Log", font=("Arial", 14, "bold"))
        log_title.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Export button
        self.export_log_button = ctk.CTkButton(log_header, text="Export Log", width=100, command=self.export_log)
        self.export_log_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        
        # We don't need a show comparison button anymore as it will be shown automatically
        
        # Log text area
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", wrap="word")
        self.log_textbox.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Configure text tags for colored output
        self.log_textbox.tag_config("red", foreground="red")
        self.log_textbox.tag_config("green", foreground="green")
        self.log_textbox.tag_config("yellow", foreground="orange")
        self.log_textbox.tag_config("cyan", foreground="cyan")

    # --- Helper Methods ---
    def browse_project_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.project_folder_var.set(folder_selected)

    def browse_executable(self, tool_name, path_var):
        # Define file types based on OS if needed, simple for now
        file_selected = filedialog.askopenfilename(title=f"Select {tool_name} Executable", filetypes=[(f"{tool_name} Executable", "*.exe"), ("All files", "*.*")])
        if file_selected:
            path_var.set(file_selected)

    def update_image_compression_state(self, *args):
        """Enable/disable image compression detail widgets based on PNG and JPEG checkboxes."""
        # Get the state of PNG and JPEG compression
        png_enabled = self.compress_png_var.get()
        jpeg_enabled = self.compress_jpeg_var.get()
        
        # Common widgets (PNG compressor, etc.)
        common_state = "normal" if (png_enabled or jpeg_enabled) else "disabled"
        
        # PNG Compressor is only enabled if PNG compression is enabled
        png_compressor_state = "normal" if png_enabled else "disabled"
        try:
            # Find the PNG compressor label and combobox
            for widget in self.img_details_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "PNG Compressor:":
                    widget.configure(state=png_compressor_state)
                elif isinstance(widget, ctk.CTkComboBox) and widget == self.png_compressor_combobox:
                    widget.configure(state=png_compressor_state)
        except Exception as e:
            print(f"Error updating PNG compressor state: {e}")
        
        # Handle PNG-specific widgets
        png_state = "normal" if png_enabled else "disabled"
        if hasattr(self, 'png_start_slider'):
            # PNG Start Level
            for widget in self.img_details_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "PNG Start Level (1-8):":
                    widget.configure(state=png_state)
            self.png_start_slider.configure(state=png_state)
            self.png_start_label.configure(state=png_state)
            
            # PNG Min Level
            for widget in self.img_details_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "PNG Min Level (1-8):":
                    widget.configure(state=png_state)
            self.png_min_slider.configure(state=png_state)
            self.png_min_label.configure(state=png_state)
        
        # Handle JPEG-specific widgets
        jpeg_state = "normal" if jpeg_enabled else "disabled"
        if hasattr(self, 'jpeg_start_slider'):
            # JPEG Start Quality
            for widget in self.img_details_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "JPEG Start Quality:":
                    widget.configure(state=jpeg_state)
            self.jpeg_start_slider.configure(state=jpeg_state)
            self.jpeg_start_label.configure(state=jpeg_state)
            
            # JPEG Min Quality
            for widget in self.img_details_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "JPEG Min Quality:":
                    widget.configure(state=jpeg_state)
            self.jpeg_min_slider.configure(state=jpeg_state)
            self.jpeg_min_label.configure(state=jpeg_state)
            
            # JPEG Quality Step
            for widget in self.img_details_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "JPEG Quality Step:":
                    widget.configure(state=jpeg_state)
            self.jpeg_step_entry.configure(state=jpeg_state)
            
        # Find optimal quality checkbox is enabled if either PNG or JPEG is enabled
        if hasattr(self, 'find_optimal_checkbox'):
            self.find_optimal_checkbox.configure(state=common_state)

    def update_archiver_path_state(self, *args):
        """Enable/disable archiver path entries based on selected profile and show only the active one."""
        profile = self.archive_profile_var.get()
        winrar_needed = "winrar" in profile
        sevenzip_needed = "7zip" in profile
        zpaq_needed = "zpaq" in profile

        # Hide all archiver path rows initially
        for widget in self.archive_frame.grid_slaves():
            if isinstance(widget, ctk.CTkLabel) and any(x in widget.cget("text") for x in ["WinRAR Path:", "7-Zip Path:", "ZPAQ Path:"]):
                widget.grid_remove()
            if widget in [self.winrar_entry, self.browse_winrar_button, 
                         self.sevenzip_entry, self.browse_sevenzip_button,
                         self.zpaq_entry, self.browse_zpaq_button]:
                widget.grid_remove()

        # Show only the active archiver path
        row_index = 1  # Start after the profile/size row
        
        if winrar_needed:
            for widget in self.archive_frame.grid_slaves():
                if isinstance(widget, ctk.CTkLabel) and "WinRAR Path:" in widget.cget("text"):
                    widget.grid(row=row_index, column=0, padx=5, pady=5, sticky="w")
            self.winrar_entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
            self.browse_winrar_button.grid(row=row_index, column=2, padx=5, pady=5)
            self.winrar_entry.configure(state="normal")
            self.browse_winrar_button.configure(state="normal")
            row_index += 1
            
        if sevenzip_needed:
            for widget in self.archive_frame.grid_slaves():
                if isinstance(widget, ctk.CTkLabel) and "7-Zip Path:" in widget.cget("text"):
                    widget.grid(row=row_index, column=0, padx=5, pady=5, sticky="w")
            self.sevenzip_entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
            self.browse_sevenzip_button.grid(row=row_index, column=2, padx=5, pady=5)
            self.sevenzip_entry.configure(state="normal")
            self.browse_sevenzip_button.configure(state="normal")
            row_index += 1
            
        if zpaq_needed:
            for widget in self.archive_frame.grid_slaves():
                if isinstance(widget, ctk.CTkLabel) and "ZPAQ Path:" in widget.cget("text"):
                    widget.grid(row=row_index, column=0, padx=5, pady=5, sticky="w")
            self.zpaq_entry.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
            self.browse_zpaq_button.grid(row=row_index, column=2, padx=5, pady=5)
            self.zpaq_entry.configure(state="normal")
            self.browse_zpaq_button.configure(state="normal")
            row_index += 1
            
        # Always show exclusions at the end
        for widget in self.archive_frame.grid_slaves():
            if isinstance(widget, ctk.CTkLabel) and "Exclusions" in widget.cget("text"):
                widget.grid(row=row_index, column=0, padx=5, pady=5, sticky="w")
        self.exclusions_entry.grid(row=row_index, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

    def log_message(self, message):
        """Appends a message to the log text box."""
        self.log_textbox.configure(state="normal")

        # Define color tags based on ANSI codes (simplified)
        tag = None
        if "\033[31m" in message or "[31m" in message: tag = "red"
        elif "\033[32m" in message or "[32m" in message: tag = "green"
        elif "\033[33m" in message or "[33m" in message: tag = "yellow"
        elif "\033[36m" in message or "[36m" in message: tag = "cyan"
        # Add more colors if needed

        # Strip ALL ANSI escape codes using regex
        clean_message = re.sub(r'\x1b\[[0-9;]*[mK]', '', message)

        # Insert cleaned message with the detected tag (if any)
        if tag:
            self.log_textbox.insert("end", clean_message + "\n", (tag,))
        else:
            self.log_textbox.insert("end", clean_message + "\n")

        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end") # Auto-scroll
        
        # Also print to console for debugging and record keeping
        print(message)

    def start_processing(self):
        """Start the processing with current settings."""
        if self.is_processing:
            return  # Prevent multiple starts
            
        # --- Validation ---
        project_folder = self.project_folder_var.get()
        if not project_folder or not os.path.isdir(project_folder):
            self.log_message("Error: Please select a valid project folder.")
            messagebox.showerror("Error", "Please select a valid project folder.")
            return

        profile = self.archive_profile_var.get()
        
        # Validate archiver path based on selected profile
        if "winrar" in profile and (not self.winrar_path_var.get() or not os.path.exists(self.winrar_path_var.get())):
            self.log_message("Error: WinRAR path is invalid or not set.")
            messagebox.showerror("Error", "Please set a valid WinRAR path for this profile.")
            return
            
        if "7zip" in profile and (not self.sevenzip_path_var.get() or not os.path.exists(self.sevenzip_path_var.get())):
            self.log_message("Error: 7-Zip path is invalid or not set.")
            messagebox.showerror("Error", "Please set a valid 7-Zip path for this profile.")
            return
            
        if "zpaq" in profile and (not self.zpaq_path_var.get() or not os.path.exists(self.zpaq_path_var.get())):
            self.log_message("Error: ZPAQ path is invalid or not set.")
            messagebox.showerror("Error", "Please set a valid ZPAQ path for this profile.")
            return
            
        # Validate TinyPNG API key if PNG compression is enabled with TinyPNG
        png_compression_enabled = self.compress_png_var.get()
        using_tinypng = self.png_compressor_var.get() == "tinypng"
        if png_compression_enabled and using_tinypng and not self.tinypng_api_key_var.get():
            self.log_message("Error: TinyPNG API key is required for PNG compression with TinyPNG.")
            messagebox.showerror("Error", "Please enter a TinyPNG API key or disable PNG compression / use a different compressor.")
            return
            
        # Log settings
        self.log_message("Starting processing...")
        self.log_message(f"Project Folder: {project_folder}")
        self.log_message(f"Profile: {profile}")
        self.log_message(f"Minify HTML: {self.minify_html_var.get()}")
        self.log_message(f"Minify CSS: {self.minify_css_var.get()}")
        self.log_message(f"Minify JS: {self.minify_js_var.get()}")
        self.log_message(f"Compress PNG: {self.compress_png_var.get()}")
        self.log_message(f"Compress JPEG: {self.compress_jpeg_var.get()}")
        
        if self.compress_png_var.get() or self.compress_jpeg_var.get():
             self.log_message(f"  PNG Compressor: {self.png_compressor_var.get()}")
             self.log_message(f"  PNG Level: {self.png_level_start_var.get()} -> {self.png_level_min_var.get()}")
             self.log_message(f"  JPEG Quality: {self.jpeg_quality_start_var.get()} -> {self.jpeg_quality_min_var.get()}")
             self.log_message(f"  JPEG Step: {self.jpeg_step_var.get()}")
             self.log_message(f"  Find Optimal: {self.find_optimal_var.get()}")
        self.log_message(f"Max Size (KB): {self.max_size_kb_var.get()}")

        # Disable button and update UI during processing
        self.is_processing = True
        self.start_button.configure(state="disabled", text="Processing...")
        self.save_config()  # Save current settings
        
        # Prepare settings dictionary
        settings = {
            "PROJECT_FOLDER": project_folder,
            "ARCHIVE_PROFILE": profile,
            "winrar_path": self.winrar_path_var.get(),
            "sevenzip_path": self.sevenzip_path_var.get(),
            "zpaq_path": self.zpaq_path_var.get(),
            "ENABLE_MINIFICATION": {
                "ENABLE_HTML_MINIFICATION": self.minify_html_var.get(),
                "ENABLE_CSS_MINIFICATION": self.minify_css_var.get(),
                "ENABLE_JS_MINIFICATION": self.minify_js_var.get()
            },
            "ENABLE_PNG_COMPRESSION": self.compress_png_var.get(),
            "ENABLE_JPEG_COMPRESSION": self.compress_jpeg_var.get(),
            "TINIFY_API_KEY": self.tinypng_api_key_var.get(),
            "png_compressor": self.png_compressor_var.get(),
            "INITIAL_PNG_OPTIMIZATION_LEVEL": self.png_level_start_var.get(),
            "INITIAL_JPEG_QUALITY": self.jpeg_quality_start_var.get(),
            "MIN_PNG_OPTIMIZATION_LEVEL": self.png_level_min_var.get(),
            "MIN_JPEG_QUALITY": self.jpeg_quality_min_var.get(),
            "JPEG_QUALITY_STEP": self.jpeg_step_var.get(),
            "FIND_OPTIMAL_QUALITY": self.find_optimal_var.get(),
            "max_size_kb": self.max_size_kb_var.get(),
            "ARCHIVE_EXCLUSIONS": self.exclusions_var.get() # Add exclusions
        }
        
        # Start processing in a separate thread
        self.processing_thread = threading.Thread(
            target=self.run_processing_thread, 
            args=(settings,), 
            daemon=True
        )
        self.processing_thread.start()
        
        # Start log queue processing
        self.process_log_queue()
        
    def run_processing_thread(self, settings):
        """Run the processing in a separate thread."""
        try:
            # Redirect stdout to capture logs
            log_capture = io.StringIO()
            
            # Custom logger function to both capture and queue logs
            def logger_func(message):
                log_capture.write(message + "\n")
                self.log_queue.put(message)
            
            try:
                # Run the main processing function
                result = run_packing(settings, logger_func=logger_func)
                
                # Process completed
                self.log_queue.put(f"\n--- Processing completed ---")
            except KeyError as e:
                # Handle specific KeyError exceptions with a clear error message
                error_message = f"{Fore.RED}ERROR: '{e}'{Style.RESET_ALL}"
                self.log_queue.put(error_message)
                
                # Add traceback for debugging
                import traceback
                tb_str = traceback.format_exc()
                self.log_queue.put(f"{Fore.RED}Traceback:{Style.RESET_ALL}\n{tb_str}")
                
                # Create a minimal result dictionary with error information
                result = {
                    "success": False,
                    "message": f"Missing required setting: {e}",
                    "summary_lines": [error_message],
                    "results_per_folder": [],
                    "success_count": 0,
                    "fail_count": 0,
                    "total_size_kb": 0
                }
            except Exception as e:
                # Handle other exceptions
                error_message = f"{Fore.RED}ERROR: {str(e)}{Style.RESET_ALL}"
                self.log_queue.put(error_message)
                
                # Add traceback for debugging
                import traceback
                tb_str = traceback.format_exc()
                self.log_queue.put(f"{Fore.RED}Traceback:{Style.RESET_ALL}\n{tb_str}")
                
                # Create a minimal result dictionary with error information
                result = {
                    "success": False,
                    "message": f"Processing error: {str(e)}",
                    "summary_lines": [error_message],
                    "results_per_folder": [],
                    "success_count": 0,
                    "fail_count": 0,
                    "total_size_kb": 0
                }
            
            # Prepare data for the comparison results
            total_original_size = 0
            total_archive_size = 0
            total_optimized_size = 0
            file_count = 0
            files_data = []
            
            # Extract data from the results
            if "results_per_folder" in result and result["results_per_folder"]:
                for folder_result in result["results_per_folder"]:
                    # Add to totals (include both successful and oversized archives)
                    original_size_kb = folder_result.get("original_size_kb", 0)
                    archive_size_kb = folder_result.get("size_kb", 0)
                    optimized_size_kb = folder_result.get("optimized_size_kb", archive_size_kb)
                    
                    total_original_size += original_size_kb
                    total_archive_size += archive_size_kb
                    total_optimized_size += optimized_size_kb
                    file_count += 1
                    
                    # Use the original_size_kb from the folder_result
                    original_size_kb = folder_result.get("original_size_kb", 0)
                    original_size_str = self.format_size(original_size_kb * 1024)
                    
                    # Format other sizes for display
                    archive_size_str = self.format_size(archive_size_kb * 1024)
                    optimized_size_str = self.format_size(optimized_size_kb * 1024)
                    
                    # Add to files data (include both successful and oversized archives)
                    files_data.append((
                        folder_result["archive_name"],
                        original_size_str,
                        archive_size_str,
                        optimized_size_str
                    ))
            
            # Extract total size from the result summary lines
            total_size_kb = 0
            oversized_count = 0
            
            # Parse the summary lines to extract the actual values from the terminal output
            if "summary_lines" in result:
                for line in result["summary_lines"]:
                    # Look for the total size line
                    if "Total size of final archives" in line:
                        # Extract the KB value using regex
                        import re
                        size_match = re.search(r'(\d+\.\d+)\s*KB', line)
                        if size_match:
                            total_size_kb = float(size_match.group(1))
                    
                    # Look for the oversized archives count
                    if "archive(s) exceeded" in line:
                        # Extract the count using regex
                        count_match = re.search(r'(\d+)\s*archive\(s\) exceeded', line)
                        if count_match:
                            oversized_count = int(count_match.group(1))
            
            # Convert KB to MB for the summary
            total_original_mb = total_original_size / 1024
            total_archive_mb = total_size_kb / 1024 if total_size_kb > 0 else total_archive_size / 1024
            total_optimized_mb = total_optimized_size / 1024
            
            # Calculate saved space
            saved_mb = total_original_mb - total_archive_mb
            saved_percent = (saved_mb / total_original_mb * 100) if total_original_mb > 0 else 0
            
            # Estimate breakdown by file type (simplified)
            # In a real app, you would track this during processing
            images_mb = saved_mb * 0.6  # Assume 60% of savings from images
            code_mb = saved_mb * 0.3    # Assume 30% of savings from code
            other_mb = saved_mb * 0.1   # Assume 10% from other files
            
            # Use the actual values from the terminal output
            before_size = f"{total_original_mb:.1f}"
            after_size = f"{total_archive_mb:.1f}"
            
            # Calculate total original size from the results
            total_original_size_kb = 0
            for folder_result in result.get("results_per_folder", []):
                total_original_size_kb += folder_result.get("original_size_kb", 0)
            
            # Convert KB to MB for the summary
            total_original_mb = total_original_size_kb / 1024
            
            # Use the actual values from the terminal output and folder sizes
            before_size = f"{total_original_mb:.1f}"
            after_size = f"{total_archive_mb:.1f}"
            
            # Update the results data
            self.results_data = {
                "before_size": before_size,
                "after_size": after_size,
                "file_count": f"{file_count}",
                "saved_mb": f"{saved_mb:.1f}",
                "saved_percent": f"{saved_percent:.1f}",
                "images_mb": f"{images_mb:.1f}",
                "code_mb": f"{code_mb:.1f}",
                "other_mb": f"{other_mb:.1f}",
                "files": files_data
            }
            
            # Display detailed summary
            if "summary_lines" in result:
                for line in result["summary_lines"]:
                    self.log_queue.put(line)
            
            # Display per-folder results
            if "results_per_folder" in result and result["results_per_folder"]:
                self.log_queue.put("\n--- Detailed Results ---")
                for folder_result in result["results_per_folder"]:
                    status_color = ""
                    if folder_result["status"] == "Success":
                        status_color = "SUCCESS: "
                    elif folder_result["status"] == "Oversized":
                        status_color = "OVERSIZED: "
                    else:
                        status_color = "ERROR: "
                    
                    result_msg = f"{status_color}{folder_result['folder']} -> {folder_result['archive_name']} ({folder_result['size_kb']:.2f} KB)"
                    if folder_result["status"] != "Error":
                        result_msg += f" [PNG={folder_result['png_level']}, JPEG={folder_result['jpeg_quality']}]"
                    if "message" in folder_result:
                        result_msg += f" - {folder_result['message']}"
                    
                    self.log_queue.put(result_msg)
            
            # Final status message
            if result["success"]:
                self.log_queue.put(f"All folders processed successfully!")
            else:
                self.log_queue.put(f"Completed with issues: {result['message']}")
                
        except Exception as e:
            # Handle any unexpected errors
            import traceback
            error_text = f"ERROR: {str(e)}\n{traceback.format_exc()}"
            self.log_queue.put(error_text)
        finally:
            # Signal that processing is complete
            self.log_queue.put("__PROCESSING_DONE__")
    
    def format_size(self, size_bytes):
        """Format file size in bytes to human-readable format."""
        if size_bytes >= 1024 * 1024:  # MB
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        elif size_bytes >= 1024:  # KB
            return f"{size_bytes / 1024:.0f} KB"
        else:  # Bytes
            return f"{size_bytes:.0f} B"
    
    def update_progress(self, current, total, current_file="", speed_kb_s=0):
        """Update the progress bar and related information."""
        # Update progress bar
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        
        # Update current file (truncate if too long)
        if len(current_file) > 40:
            display_file = "..." + current_file[-37:]
        else:
            display_file = current_file
        self.current_file_label.configure(text=display_file)
        
        # Update speed
        self.speed_label.configure(text=f"{speed_kb_s:.1f} KB/s")
        
        # Update remaining time
        if speed_kb_s > 0:
            # Estimate remaining time based on files left and current speed
            files_left = total - current
            est_seconds = files_left / speed_kb_s if speed_kb_s > 0 else 0
            
            # Format time as mm:ss
            minutes = int(est_seconds // 60)
            seconds = int(est_seconds % 60)
            self.time_label.configure(text=f"{minutes:02d}:{seconds:02d}")
        else:
            self.time_label.configure(text="--:--")
    
    def process_log_queue(self):
        """Process logs from the queue and update the UI."""
        try:
            while not self.log_queue.empty():
                message = self.log_queue.get(block=False)
                
                # Check for processing completion signal
                if message == "__PROCESSING_DONE__":
                    self.is_processing = False
                    self.start_button.configure(state="normal", text="Start Processing")
                    # No need to enable the comparison button anymore
                    # Reset progress display
                    self.update_progress(1, 1, "", 0)
                    self.progress_bar.set(1.0)  # Show full progress
                    
                    # Automatically show the comparison results window
                    self.after(500, self.show_comparison_results)  # Small delay to ensure UI is updated first
                elif message.startswith("__PROGRESS__:"):
                    # Process progress update message
                    # Format: __PROGRESS__:current:total:file:speed
                    try:
                        parts = message.split(":", 4)
                        if len(parts) >= 4:
                            current = int(parts[1])
                            total = int(parts[2])
                            current_file = parts[3] if len(parts) > 3 else ""
                            speed = float(parts[4]) if len(parts) > 4 else 0
                            self.update_progress(current, total, current_file, speed)
                    except Exception as e:
                        print(f"Error parsing progress message: {e}")
                else:
                    # Regular log message
                    self.log_message(message)
                    
        except queue.Empty:
            pass
            
        # Schedule next check if still processing
        if self.is_processing or not self.log_queue.empty():
            self.after(100, self.process_log_queue)

    # --- Config Load/Savese ---
    def load_config(self):
        """Load settings from config file."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Set variables from config
                    self.project_folder_var.set(config.get("project_folder", ""))
                    self.archive_profile_var.set(config.get("archive_profile", DEFAULT_SETTINGS["ARCHIVE_PROFILE"]))
                    self.winrar_path_var.set(config.get("winrar_path", DEFAULT_SETTINGS["winrar_path"]))
                    self.sevenzip_path_var.set(config.get("sevenzip_path", DEFAULT_SETTINGS["sevenzip_path"]))
                    self.zpaq_path_var.set(config.get("zpaq_path", DEFAULT_SETTINGS["zpaq_path"]))
                    # Set minification variables
                    enable_minification = config.get("enable_minification", DEFAULT_SETTINGS["ENABLE_MINIFICATION"])
                    self.minify_html_var.set(config.get("enable_html_minification", enable_minification))
                    self.minify_css_var.set(config.get("enable_css_minification", enable_minification))
                    self.minify_js_var.set(config.get("enable_js_minification", enable_minification))
                    
                    # Set both PNG and JPEG compression from the same config value for backward compatibility
                    enable_image_compression = config.get("enable_image_compression", DEFAULT_SETTINGS["ENABLE_IMAGE_COMPRESSION"])
                    self.compress_png_var.set(enable_image_compression)
                    self.compress_jpeg_var.set(enable_image_compression)
                    self.tinypng_api_key_var.set(config.get("tinypng_api_key", DEFAULT_SETTINGS["TINIFY_API_KEY"]))
                    self.png_compressor_var.set(config.get("png_compressor", "tinypng"))
                    self.png_level_start_var.set(config.get("png_level_start", DEFAULT_SETTINGS["INITIAL_PNG_OPTIMIZATION_LEVEL"]))
                    self.jpeg_quality_start_var.set(config.get("jpeg_quality_start", DEFAULT_SETTINGS["INITIAL_JPEG_QUALITY"]))
                    self.png_level_min_var.set(config.get("png_level_min", DEFAULT_SETTINGS["MIN_PNG_OPTIMIZATION_LEVEL"]))
                    self.jpeg_quality_min_var.set(config.get("jpeg_quality_min", DEFAULT_SETTINGS["MIN_JPEG_QUALITY"]))
                    self.jpeg_step_var.set(config.get("jpeg_step", DEFAULT_SETTINGS["JPEG_QUALITY_STEP"]))
                    self.find_optimal_var.set(config.get("find_optimal", DEFAULT_SETTINGS["FIND_OPTIMAL_QUALITY"]))
                    self.max_size_kb_var.set(config.get("max_size_kb", DEFAULT_SETTINGS["max_size_kb"]))
                    self.exclusions_var.set(config.get("archive_exclusions", DEFAULT_SETTINGS["ARCHIVE_EXCLUSIONS"])) # Load exclusions

                    self.log_message("Configuration loaded.")
                    self.update_archiver_path_state() # Update UI state after loading config
        except FileNotFoundError:
            self.log_message("Config file not found, using defaults.")
        except Exception as e:
            self.log_message(f"Error loading config: {e}")

    def save_config(self):
        """Save current settings to config file."""
        config = {
            "project_folder": self.project_folder_var.get(),
            "archive_profile": self.archive_profile_var.get(),
            "winrar_path": self.winrar_path_var.get(),
            "sevenzip_path": self.sevenzip_path_var.get(),
            "zpaq_path": self.zpaq_path_var.get(),
            "enable_html_minification": self.minify_html_var.get(),
            "enable_css_minification": self.minify_css_var.get(),
            "enable_js_minification": self.minify_js_var.get(),
            "enable_png_compression": self.compress_png_var.get(),
            "enable_jpeg_compression": self.compress_jpeg_var.get(),
            "enable_image_compression": self.compress_png_var.get() or self.compress_jpeg_var.get(),
            "tinypng_api_key": self.tinypng_api_key_var.get(),
            "png_compressor": self.png_compressor_var.get(),
            "png_level_start": self.png_level_start_var.get(),
            "jpeg_quality_start": self.jpeg_quality_start_var.get(),
            "png_level_min": self.png_level_min_var.get(),
            "jpeg_quality_min": self.jpeg_quality_min_var.get(),
            "jpeg_step": self.jpeg_step_var.get(),
            "find_optimal": self.find_optimal_var.get(),
            "max_size_kb": self.max_size_kb_var.get(),
            "archive_exclusions": self.exclusions_var.get() # Save exclusions
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            self.log_message(f"Error saving config: {e}")

    def on_window_resize(self, event):
        """Handle window resize events to ensure UI elements scale properly."""
        # Only process if this is a root window event (not a child widget)
        if event.widget == self:
            # Get window dimensions
            window_width = event.width
            window_height = event.height
            
            # Scale font sizes based on window width
            base_font_size = max(9, min(12, int(window_width / 80)))
            
            # Update font sizes for key UI elements
            if hasattr(self, 'log_textbox'):
                self.log_textbox.configure(font=("TkDefaultFont", base_font_size))
            
            # Adjust padding and spacing for frames based on window size
            padding_x = max(5, min(10, int(window_width / 100)))
            padding_y = max(3, min(8, int(window_width / 120)))
            
            # Update grid configurations for main frames
            for row in range(8):  # Update all main rows
                for widget in self.grid_slaves(row=row, column=0):
                    if isinstance(widget, ctk.CTkFrame) or isinstance(widget, ctk.CTkButton):
                        widget.grid_configure(padx=padding_x, pady=padding_y)
            
            # Ensure slider widths are balanced
            if hasattr(self, 'img_details_frame'):
                try:
                    # Force the frame to update its layout
                    self.img_details_frame.update_idletasks()
                    
                    # Get the current width of the frame
                    frame_width = self.img_details_frame.winfo_width()
                    
                    # Ensure minimum width for proper display
                    if frame_width > 100:  # Only adjust if we have a reasonable width
                        # Calculate appropriate column widths to ensure equal slider sizes
                        # and prevent text truncation
                        
                        # First reset all weights to ensure clean recalculation
                        for i in range(6):
                            self.img_details_frame.grid_columnconfigure(i, weight=0)
                        
                        # Set equal weights for slider columns
                        self.img_details_frame.grid_columnconfigure(1, weight=1)  # Left slider
                        self.img_details_frame.grid_columnconfigure(4, weight=1)  # Right slider
                        
                        # Update copyright font size based on window width
                        if hasattr(self, 'copyright_text'):
                            copyright_font_size = max(10, min(13, int(window_width / 70)))
                            self.copyright_text.configure(font=("TkDefaultFont", copyright_font_size))
                except Exception as e:
                    # Silently handle any errors during resize
                    pass
    
    # Removed open_website method as it's no longer needed
    
    def setup_drag_and_drop(self, widget):
        """Setup drag and drop functionality for a widget using native tkinter."""
        # Since TkDND might not be available, we'll just create a context menu
        # for paste functionality as a fallback
        self.create_context_menu(widget)
        
        # Log that drag and drop is not implemented in this version
        print("Drag and drop requires TkDND library which is not included in this build")
    
    def create_context_menu(self, widget):
        """Create a right-click context menu for a widget."""
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Paste", command=lambda: self.paste_from_clipboard(widget))
        
        # Bind the menu to right-click
        if isinstance(widget, ctk.CTkEntry):
            widget._entry.bind("<Button-3>", lambda e: self.show_context_menu(e, context_menu))
        else:
            widget.bind("<Button-3>", lambda e: self.show_context_menu(e, context_menu))
    
    def show_context_menu(self, event, menu):
        """Show the context menu at the event position."""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def paste_from_clipboard(self, widget):
        """Paste clipboard content into the widget."""
        try:
            clipboard_text = self.clipboard_get()
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, tk.END)
                widget.insert(0, clipboard_text)
            elif hasattr(widget, 'insert'):
                widget.insert(tk.INSERT, clipboard_text)
        except Exception as e:
            print(f"Paste error: {e}")
    
    def export_log(self):
        """Export the log to a file."""
        # Get the log content
        self.log_textbox.configure(state="normal")
        log_content = self.log_textbox.get("1.0", "end-1c")  # Get all text without the final newline
        self.log_textbox.configure(state="disabled")
        
        if not log_content.strip():
            messagebox.showinfo("Export Log", "No log content to export.")
            return
        
        # Ask for a file to save to
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Log"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
            messagebox.showinfo("Export Log", f"Log exported successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export log: {str(e)}")
    
    def show_comparison_results(self):
        """Show the comparison results overlay in the main interface."""
        # Import the ComparisonResultsFrame class
        from hyperzip_comparison import ComparisonResultsFrame
        
        # Use only the actual data from the processing results
        # Never use example data, even if there are no files
        
        # Create the results frame as an overlay
        self.comparison_frame = ComparisonResultsFrame(self, self.results_data, close_callback=self.hide_comparison_results)
        self.comparison_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.95)
        
        # Start the animation
        self.comparison_frame.animate_results(duration=1.0)
    
    def hide_comparison_results(self):
        """Hide the comparison results overlay."""
        if hasattr(self, 'comparison_frame') and self.comparison_frame:
            self.comparison_frame.destroy()
            self.comparison_frame = None
    
    def on_closing(self):
        """Handle window closing."""
        if self.is_processing:
            if not messagebox.askyesno("Quit", "Processing is still running. Are you sure you want to quit?"):
                return
        self.save_config() # Save config on close
        self.destroy()


if __name__ == "__main__":
    app = HyperZipApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
