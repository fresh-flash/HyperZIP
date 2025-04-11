import os
from hyperzip_core import _log_func, Fore, Style

# Import minification libraries
try:
    import htmlmin
    import jsmin
    import csscompressor
except ImportError as e:
    _log_func(f"{Fore.RED}Error: Missing minification library: {e.name}. Install with pip.{Style.RESET_ALL}")
    raise

# --- Minifier Class ---
class Minifier:
    """Class for minification methods"""
    @staticmethod
    def minify_html(content):
        return htmlmin.minify(content, remove_empty_space=True, remove_comments=True)
    
    @staticmethod
    def minify_js(content):
        return jsmin.jsmin(content)
    
    @staticmethod
    def minify_css(content):
        return csscompressor.compress(content, preserve_exclamation_comments=False)

# --- File Minification Function ---
def minify_file(file_path):
    """Minifies HTML, JS, CSS file."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext not in ['.html', '.js', '.css']:
        return
    
    original_size = 0
    file_basename = os.path.basename(file_path)
    
    try:
        original_size = os.path.getsize(file_path)
        if original_size == 0:
            return # Skip empty files
        
        # Try common encodings
        encoding_to_try = ['utf-8', 'cp1251']
        content = None
        detected_encoding = None
        
        for enc in encoding_to_try:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                detected_encoding = enc
                break # Stop on successful read
            except UnicodeDecodeError:
                continue # Try next encoding
            except Exception as read_e:
                _log_func(f"{Fore.YELLOW}Warn: Read {file_path} with {enc} failed: {read_e}{Style.RESET_ALL}")
                continue
                
        if content is None or detected_encoding is None:
            _log_func(f"{Fore.RED}Error: Could not decode {file_path}. Skipping minif.{Style.RESET_ALL}")
            return

        minified_content = content # Default to original if minification fails
        
        try:
            if ext == '.html':
                minified_content = Minifier.minify_html(content)
            elif ext == '.js':
                minified_content = Minifier.minify_js(content)
            elif ext == '.css':
                minified_content = Minifier.minify_css(content)
        except Exception as minify_e:
            _log_func(f"{Fore.RED}Error minifying {file_basename} ({ext}): {minify_e}{Style.RESET_ALL}")
            minified_content = content # Revert to original on error

        # Only write if minified content is smaller
        minified_bytes = minified_content.encode(detected_encoding)
        if len(minified_bytes) < original_size:
            with open(file_path, 'w', encoding=detected_encoding) as f:
                f.write(minified_content)
                
    except FileNotFoundError:
        _log_func(f"{Fore.RED}Error minifying: Not found: {file_path}{Style.RESET_ALL}")
    except Exception as e:
        _log_func(f"{Fore.RED}Error processing {file_path} for minif: {type(e).__name__} - {str(e)}{Style.RESET_ALL}")
