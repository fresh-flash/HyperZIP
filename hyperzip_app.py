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

# Import from our modular structure
from hyperzip_core import DEFAULT_SETTINGS
from hyperzip_main import run_packing

# --- Constants ---
APP_NAME = "HyperZip GUI"
CONFIG_FILE = "hyperzip_config.json"
ARCHIVE_PROFILES = [
    "winrar_zip", "winrar_rar", "7zip_7z", "7zip_zip", "zpaq_zpaq"
]

# --- Main Application Class ---
class HyperZipApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("800x750") # Adjusted size for better layout
        ctk.set_appearance_mode("System") # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue") # Themes: "blue" (default), "green", "dark-blue"

        # Improve UI scaling by configuring grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1) # Configure log area row to expand
        
        # Add event binding for window resize to handle UI scaling
        self.bind("<Configure>", self.on_window_resize)

        # --- Variables ---
        self.project_folder_var = tk.StringVar()
        self.archive_profile_var = tk.StringVar(value=DEFAULT_SETTINGS["ARCHIVE_PROFILE"])
        self.winrar_path_var = tk.StringVar(value=DEFAULT_SETTINGS["winrar_path"])
        self.sevenzip_path_var = tk.StringVar(value=DEFAULT_SETTINGS["sevenzip_path"])
        self.zpaq_path_var = tk.StringVar(value=DEFAULT_SETTINGS["zpaq_path"])
        self.exclusions_var = tk.StringVar(value=DEFAULT_SETTINGS["ARCHIVE_EXCLUSIONS"]) # New variable
        self.minify_var = tk.BooleanVar(value=DEFAULT_SETTINGS["ENABLE_MINIFICATION"])
        self.compress_images_var = tk.BooleanVar(value=DEFAULT_SETTINGS["ENABLE_IMAGE_COMPRESSION"])
        self.tinypng_api_key_var = tk.StringVar(value=DEFAULT_SETTINGS["TINIFY_API_KEY"])
        self.png_compressor_var = tk.StringVar(value="tinypng") # Default to tinypng
        self.png_level_start_var = tk.IntVar(value=DEFAULT_SETTINGS["INITIAL_PNG_OPTIMIZATION_LEVEL"])
        self.jpeg_quality_start_var = tk.IntVar(value=DEFAULT_SETTINGS["INITIAL_JPEG_QUALITY"])
        self.png_level_min_var = tk.IntVar(value=DEFAULT_SETTINGS["MIN_PNG_OPTIMIZATION_LEVEL"])
        self.jpeg_quality_min_var = tk.IntVar(value=DEFAULT_SETTINGS["MIN_JPEG_QUALITY"])
        self.jpeg_step_var = tk.IntVar(value=DEFAULT_SETTINGS["JPEG_QUALITY_STEP"])
        self.find_optimal_var = tk.BooleanVar(value=DEFAULT_SETTINGS["FIND_OPTIMAL_QUALITY"])
        self.max_size_kb_var = tk.DoubleVar(value=DEFAULT_SETTINGS["max_size_kb"])
        
        # --- Processing state ---
        self.is_processing = False
        self.log_queue = queue.Queue()

        # --- UI Creation ---
        self.create_widgets()
        self.update_image_compression_state() # Initial state update

        # --- Load Config ---
        self.load_config() # Load saved config if available

    def create_widgets(self):
        # --- 1. Project Folder ---
        project_frame = ctk.CTkFrame(self)
        project_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        project_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(project_frame, text="Project Folder:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.project_folder_entry = ctk.CTkEntry(project_frame, textvariable=self.project_folder_var)
        self.project_folder_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.browse_project_button = ctk.CTkButton(project_frame, text="Browse...", width=100, command=self.browse_project_folder)
        self.browse_project_button.grid(row=0, column=2, padx=5, pady=5)

        # --- 2. Archive Settings ---
        archive_frame = ctk.CTkFrame(self)
        archive_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        archive_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(archive_frame, text="Archive Profile:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.profile_combobox = ctk.CTkComboBox(archive_frame, variable=self.archive_profile_var, values=ARCHIVE_PROFILES, command=self.update_archiver_path_state)
        self.profile_combobox.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        # WinRAR Path
        ctk.CTkLabel(archive_frame, text="WinRAR Path:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.winrar_entry = ctk.CTkEntry(archive_frame, textvariable=self.winrar_path_var)
        self.winrar_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.browse_winrar_button = ctk.CTkButton(archive_frame, text="Browse...", width=100, command=lambda: self.browse_executable("WinRAR", self.winrar_path_var))
        self.browse_winrar_button.grid(row=1, column=2, padx=5, pady=5)

        # 7-Zip Path
        ctk.CTkLabel(archive_frame, text="7-Zip Path:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.sevenzip_entry = ctk.CTkEntry(archive_frame, textvariable=self.sevenzip_path_var)
        self.sevenzip_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.browse_sevenzip_button = ctk.CTkButton(archive_frame, text="Browse...", width=100, command=lambda: self.browse_executable("7-Zip", self.sevenzip_path_var))
        self.browse_sevenzip_button.grid(row=2, column=2, padx=5, pady=5)

        # ZPAQ Path
        ctk.CTkLabel(archive_frame, text="ZPAQ Path:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.zpaq_entry = ctk.CTkEntry(archive_frame, textvariable=self.zpaq_path_var)
        self.zpaq_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.browse_zpaq_button = ctk.CTkButton(archive_frame, text="Browse...", width=100, command=lambda: self.browse_executable("ZPAQ", self.zpaq_path_var))
        self.browse_zpaq_button.grid(row=3, column=2, padx=5, pady=5)
        
        # Exclusions Entry
        ctk.CTkLabel(archive_frame, text="Exclusions (space-separated):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.exclusions_entry = ctk.CTkEntry(archive_frame, textvariable=self.exclusions_var)
        self.exclusions_entry.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky="ew")


        self.update_archiver_path_state() # Initial state update

        # --- 3. Optimization Settings ---
        optim_frame = ctk.CTkFrame(self)
        optim_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.minify_checkbox = ctk.CTkCheckBox(optim_frame, text="Enable Minification (HTML/CSS/JS)", variable=self.minify_var)
        self.minify_checkbox.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.compress_images_checkbox = ctk.CTkCheckBox(optim_frame, text="Enable Image Compression (TinyPNG)", variable=self.compress_images_var, command=self.update_image_compression_state)
        self.compress_images_checkbox.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # --- 4. Image Compression Details ---
        self.img_details_frame = ctk.CTkFrame(self, fg_color="transparent") # Use transparent bg or a specific color
        self.img_details_frame.grid(row=3, column=0, padx=10, pady=0, sticky="ew")
        
        # Improve grid layout for better scaling
        for i in range(6):
            self.img_details_frame.grid_columnconfigure(i, weight=0)  # First reset all weights
        
        # Set equal weights for slider columns
        self.img_details_frame.grid_columnconfigure(1, weight=1)  # Left slider column
        self.img_details_frame.grid_columnconfigure(4, weight=1)  # Right slider column

        ctk.CTkLabel(self.img_details_frame, text="TinyPNG API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tinypng_entry = ctk.CTkEntry(self.img_details_frame, textvariable=self.tinypng_api_key_var, show="*")
        self.tinypng_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        
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


        # --- 5. Target Size ---
        target_frame = ctk.CTkFrame(self)
        target_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(target_frame, text="Max Archive Size (KB):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.max_size_entry = ctk.CTkEntry(target_frame, textvariable=self.max_size_kb_var, width=100)
        self.max_size_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # --- 6. Start Button ---
        self.start_button = ctk.CTkButton(self, text="Start Processing", command=self.start_processing)
        self.start_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")
        
        # --- 7. Copyright Information ---
        copyright_frame = ctk.CTkFrame(self)
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

        # --- 8. Log Area ---
        self.log_textbox = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self.log_textbox.grid(row=5, column=0, padx=10, pady=(5, 10), sticky="nsew")
        
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
        """Enable/disable image compression detail widgets."""
        state = "normal" if self.compress_images_var.get() else "disabled"
        for widget in self.img_details_frame.winfo_children():
            try:
                widget.configure(state=state)
            except tk.TclError: # Some widgets like Labels don't have state
                pass
        # Ensure sliders update their visual state correctly
        if hasattr(self, 'png_start_slider'): # Check if widgets exist
            self.png_start_slider.configure(state=state)
            self.jpeg_start_slider.configure(state=state)
            self.png_min_slider.configure(state=state)
            self.jpeg_min_slider.configure(state=state)
            # Entry and Checkbox already handled by the loop

    def update_archiver_path_state(self, *args):
        """Enable/disable archiver path entries based on selected profile."""
        profile = self.archive_profile_var.get()
        print(f"[DEBUG] update_archiver_path_state called. Profile: '{profile}'") # DEBUG log
        winrar_needed = "winrar" in profile
        sevenzip_needed = "7zip" in profile
        zpaq_needed = "zpaq" in profile
        print(f"[DEBUG] winrar_needed={winrar_needed}, sevenzip_needed={sevenzip_needed}, zpaq_needed={zpaq_needed}") # DEBUG log

        winrar_state = "normal" if winrar_needed else "disabled"
        print(f"[DEBUG] Setting WinRAR widgets state to: '{winrar_state}'") # DEBUG log
        self.winrar_entry.configure(state=winrar_state)
        self.browse_winrar_button.configure(state=winrar_state)
        sevenzip_state = "normal" if sevenzip_needed else "disabled"
        self.sevenzip_entry.configure(state=sevenzip_state)
        self.browse_sevenzip_button.configure(state=sevenzip_state)
        zpaq_state = "normal" if zpaq_needed else "disabled"
        self.zpaq_entry.configure(state=zpaq_state)
        self.browse_zpaq_button.configure(state=zpaq_state)

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
            
        # Validate TinyPNG API key if image compression is enabled
        if self.compress_images_var.get() and not self.tinypng_api_key_var.get():
            self.log_message("Error: TinyPNG API key is required for image compression.")
            messagebox.showerror("Error", "Please enter a TinyPNG API key or disable image compression.")
            return
            
        # Log settings
        self.log_message("Starting processing...")
        self.log_message(f"Project Folder: {project_folder}")
        self.log_message(f"Profile: {profile}")
        self.log_message(f"Minify: {self.minify_var.get()}")
        self.log_message(f"Compress Images: {self.compress_images_var.get()}")
        if self.compress_images_var.get():
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
            "ENABLE_MINIFICATION": self.minify_var.get(),
            "ENABLE_IMAGE_COMPRESSION": self.compress_images_var.get(),
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
            
            # Run the main processing function
            result = run_packing(settings, logger_func=logger_func)
            
            # Process completed
            self.log_queue.put(f"\n--- Processing completed ---")
            
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
    
    def process_log_queue(self):
        """Process logs from the queue and update the UI."""
        try:
            while not self.log_queue.empty():
                message = self.log_queue.get(block=False)
                
                # Check for processing completion signal
                if message == "__PROCESSING_DONE__":
                    self.is_processing = False
                    self.start_button.configure(state="normal", text="Start Processing")
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
                    self.minify_var.set(config.get("enable_minification", DEFAULT_SETTINGS["ENABLE_MINIFICATION"]))
                    self.compress_images_var.set(config.get("enable_image_compression", DEFAULT_SETTINGS["ENABLE_IMAGE_COMPRESSION"]))
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
            "enable_minification": self.minify_var.get(),
            "enable_image_compression": self.compress_images_var.get(),
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
