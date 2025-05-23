import customtkinter as ctk
import tkinter as tk

class ComparisonResultsFrame(ctk.CTkFrame):
    """A frame that displays the comparison results between original and compressed files."""
    
    def __init__(self, parent, results_data, close_callback=None):
        super().__init__(parent)
        self.close_callback = close_callback
        self.results_data = results_data
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Dark overlay background
        self.configure(fg_color=("#1A1A1A", "#0A0A0A"))
        
        # Create a main content frame that will be scrollable
        self.main_content = ctk.CTkScrollableFrame(self)
        self.main_content.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_content.grid_columnconfigure(0, weight=1)
        
        # Make the frame take up all available space
        self.grid_rowconfigure(0, weight=1)
        
        # Header with icon
        header_frame = ctk.CTkFrame(self.main_content)
        header_frame.grid(row=0, column=0, pady=10, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Icon placeholder (colorful folder icon)
        icon_label = ctk.CTkLabel(header_frame, text="📊", font=("Arial", 24))
        icon_label.grid(row=0, column=0, padx=10, pady=10)
        
        title_label = ctk.CTkLabel(header_frame, text="Comparison Results", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Before/After section (summary)
        summary_frame = ctk.CTkFrame(self.main_content, fg_color="#2b2b2b")
        summary_frame.grid(row=1, column=0, pady=10, sticky="ew")
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
        
        # Space Saved section
        saved_frame = ctk.CTkFrame(self.main_content, fg_color="#2b3b2b")  # Slightly greener background
        saved_frame.grid(row=2, column=0, pady=10, sticky="ew")
        saved_frame.grid_columnconfigure(1, weight=1)
        
        # Space Saved label
        saved_label = ctk.CTkLabel(saved_frame, text="Space Saved:", font=("Arial", 16, "bold"))
        saved_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Space Saved value with percentage
        saved_value = ctk.CTkLabel(
            saved_frame, 
            text=f"{results_data['saved_mb']} MB ({results_data['saved_percent']}%)", 
            font=("Arial", 20, "bold"), 
            text_color="#4ecca3"
        )
        saved_value.grid(row=0, column=1, padx=20, pady=10, sticky="e")
        
        # Breakdown by type
        breakdown_frame = ctk.CTkFrame(saved_frame, fg_color="transparent")
        breakdown_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        breakdown_frame.grid_columnconfigure(0, weight=1)
        breakdown_frame.grid_columnconfigure(1, weight=1)
        breakdown_frame.grid_columnconfigure(2, weight=1)
        
        # Images
        images_label = ctk.CTkLabel(breakdown_frame, text="Images:", font=("Arial", 14))
        images_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        images_value = ctk.CTkLabel(
            breakdown_frame, 
            text=f"{results_data['images_mb']} MB", 
            font=("Arial", 14, "bold"), 
            text_color="#4ecca3"
        )
        images_value.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        # Code
        code_label = ctk.CTkLabel(breakdown_frame, text="Code:", font=("Arial", 14))
        code_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        code_value = ctk.CTkLabel(
            breakdown_frame, 
            text=f"{results_data['code_mb']} MB", 
            font=("Arial", 14, "bold"), 
            text_color="#4ecca3"
        )
        code_value.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        
        # Other
        other_label = ctk.CTkLabel(breakdown_frame, text="Other:", font=("Arial", 14))
        other_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        other_value = ctk.CTkLabel(
            breakdown_frame, 
            text=f"{results_data['other_mb']} MB", 
            font=("Arial", 14, "bold"), 
            text_color="#4ecca3"
        )
        other_value.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        
        # Size comparison bars
        bars_frame = ctk.CTkFrame(self.main_content, fg_color="#2b2b2b")
        bars_frame.grid(row=3, column=0, pady=10, sticky="ew")
        bars_frame.grid_columnconfigure(0, weight=1)
        
        # Original Size bar
        original_label = ctk.CTkLabel(bars_frame, text="Original Size", font=("Arial", 14))
        original_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        original_bar = ctk.CTkProgressBar(bars_frame, height=30, progress_color="#ff6b6b", fg_color="#444444")
        original_bar.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        original_bar.set(1.0)  # Full bar
        
        # Compressed Size bar
        compressed_label = ctk.CTkLabel(bars_frame, text="Compressed Size", font=("Arial", 14))
        compressed_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        # Calculate the ratio for the compressed bar
        try:
            before_mb = float(results_data['before_size'])
            after_mb = float(results_data['after_size'])
            compressed_ratio = after_mb / before_mb if before_mb > 0 else 0
        except:
            compressed_ratio = 0.5  # Default fallback
        
        compressed_bar = ctk.CTkProgressBar(bars_frame, height=30, progress_color="#4ecca3", fg_color="#444444")
        compressed_bar.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        compressed_bar.set(compressed_ratio)
        
        # File list section - MOVED UP to appear right after the graph
        file_list_frame = ctk.CTkFrame(self.main_content, fg_color="#2b2b2b")
        file_list_frame.grid(row=4, column=0, pady=10, sticky="nsew")
        file_list_frame.grid_columnconfigure(0, weight=1)
        file_list_frame.grid_rowconfigure(1, weight=1)
        
        # Table header
        file_list_header = ctk.CTkFrame(file_list_frame, fg_color="#333333")
        file_list_header.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
        
        # Configure columns for the header
        for i, width in enumerate([3, 1, 1, 1]):
            file_list_header.grid_columnconfigure(i, weight=width)
        
        # Header labels
        header_font = ("Arial", 14, "bold")
        ctk.CTkLabel(file_list_header, text="File", font=header_font).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        ctk.CTkLabel(file_list_header, text="Original", font=header_font, text_color="#ff6b6b").grid(row=0, column=1, padx=10, pady=8, sticky="e")
        ctk.CTkLabel(file_list_header, text="Compressed", font=header_font, text_color="#4ecca3").grid(row=0, column=2, padx=10, pady=8, sticky="e")
        ctk.CTkLabel(file_list_header, text="Savings", font=header_font, text_color="#f4d03f").grid(row=0, column=3, padx=10, pady=8, sticky="e")
        
        # Create a scrollable frame for the file list
        self.file_scrollable_frame = ctk.CTkScrollableFrame(file_list_frame, fg_color="transparent")
        self.file_scrollable_frame.grid(row=1, column=0, sticky="nsew")
        
        # Configure columns for the scrollable frame
        for i, width in enumerate([3, 1, 1, 1]):
            self.file_scrollable_frame.grid_columnconfigure(i, weight=width)
        
        # Add file rows from results_data
        files_to_display = results_data.get("files", [])
        
        for i, (filename, original, compressed, optimized) in enumerate(files_to_display):
            row_bg = "#2b2b2b" if i % 2 == 0 else "#333333"
            
            # File name
            ctk.CTkLabel(self.file_scrollable_frame, text=filename, fg_color=row_bg).grid(
                row=i, column=0, padx=10, pady=5, sticky="ew")
            
            # Original size
            ctk.CTkLabel(self.file_scrollable_frame, text=original, fg_color=row_bg, text_color="#ff6b6b").grid(
                row=i, column=1, padx=10, pady=5, sticky="e")
            
            # Compressed size
            ctk.CTkLabel(self.file_scrollable_frame, text=compressed, fg_color=row_bg, text_color="#4ecca3").grid(
                row=i, column=2, padx=10, pady=5, sticky="e")
            
            # Calculate savings percentage
            try:
                # Parse sizes to calculate savings
                original_size = self.parse_size_to_bytes(original)
                compressed_size = self.parse_size_to_bytes(compressed)
                
                if original_size > 0:
                    savings_percent = (1 - compressed_size / original_size) * 100
                    savings_text = f"-{savings_percent:.1f}%"
                else:
                    savings_text = "0%"
            except:
                savings_text = "N/A"
                
            # Display savings
            ctk.CTkLabel(self.file_scrollable_frame, text=savings_text, fg_color=row_bg, text_color="#f4d03f").grid(
                row=i, column=3, padx=10, pady=5, sticky="e")
        
        
        
        # Create a footer frame that stays at the bottom and doesn't scroll
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        footer_frame.grid_columnconfigure(0, weight=1)
        
        # OK button to close the results view
        ok_button = ctk.CTkButton(
            footer_frame, 
            text="OK", 
            width=100, 
            command=self.close,
            fg_color="#0078d7",
            hover_color="#005fa3"
        )
        ok_button.grid(row=0, column=0, pady=10)
    
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
    
    def close(self):
        """Close the results view."""
        if self.close_callback:
            self.close_callback()
    
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
